"""
Tests for the Databricks ``ai_decide`` judge backend.

Covers the REST transport (typed SDK call),
answer parsing into MLflow ``Feedback``, ``GuardrailModel`` / middleware
wiring, and the retry feedback synthesized from ai_decide's rationale-free
answers.
"""

import json
from typing import Any
from unittest.mock import MagicMock, Mock

import pytest
from databricks.sdk.service.aifunctions import AiDecideResponse
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.runtime import Runtime
from mlflow.entities import Feedback

from dao_ai.config import AiDecideJudgeModel, GuardrailModel
from dao_ai.judges.ai_decide import (
    AiDecideError,
    AiDecideScorer,
    RestAiDecideTransport,
    noul_question,
    render_instructions,
)
from dao_ai.middleware.guardrails import (
    RELEVANCE_DECISION,
    TONE_DECISIONS,
    VERACITY_DECISION,
    ConcisenessGuardrailMiddleware,
    GuardrailMiddleware,
    RelevanceGuardrailMiddleware,
    SafetyGuardrailMiddleware,
    ToneGuardrailMiddleware,
    VeracityGuardrailMiddleware,
    create_guardrail_middleware,
    create_veracity_guardrail_middleware,
)
from dao_ai.state import AgentState, Context


class FakeTransport:
    """Records requests and replays canned ``ai_decide`` answers."""

    name: str = "fake"

    def __init__(self, answers: dict[str, dict[str, Any]] | Exception):
        self.answers = answers
        self.calls: list[tuple[dict[str, Any], dict[str, Any]]] = []

    def decide(
        self, state: dict[str, Any], questions: dict[str, dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        self.calls.append((state, questions))
        if isinstance(self.answers, Exception):
            raise self.answers
        # Canned answers are keyed by question name; the scorer sends neutral
        # ids (q1, q2, ...) in the same order.
        return dict(zip(questions, self.answers.values()))


def _noul(probability: float) -> dict[str, Any]:
    return {"type": "noul", "probability": probability}


@pytest.fixture
def runtime() -> Mock:
    mock_runtime = Mock(spec=Runtime)
    mock_runtime.context = Context(user_id="test_user", thread_id="test_thread")
    return mock_runtime


def _with_transport(
    middleware: GuardrailMiddleware, transport: FakeTransport
) -> GuardrailMiddleware:
    middleware._scorer._transport = transport
    return middleware


# =============================================================================
# Helpers
# =============================================================================


def test_render_instructions_rewrites_known_state_fields():
    state = {"inputs": {}, "outputs": {}}
    rendered = render_instructions(
        "Does {{ outputs }} answer {{inputs}}? Ignore {{ expectations }}.", state
    )
    assert rendered == (
        "Does state.outputs answer state.inputs? Ignore {{ expectations }}."
    )


def test_noul_question_maps_criteria_to_true_false():
    question = noul_question("Is it good?", pass_when="good", fail_when="bad")
    assert question == {
        "type": "noul",
        "instructions": "Is it good?",
        "criteria": {"true": "good", "false": "bad"},
    }
    assert "criteria" not in noul_question("Is it good?")


# =============================================================================
# AiDecideScorer
# =============================================================================


class TestAiDecideScorer:
    def test_noul_pass_at_threshold(self):
        transport = FakeTransport({"check": _noul(0.7)})
        scorer = AiDecideScorer(
            name="check",
            questions={"check": noul_question("Is {{ outputs }} good?")},
            transport=transport,
            threshold=0.7,
        )
        feedback = scorer(inputs={"query": "q"}, outputs={"response": "r"})

        assert isinstance(feedback, Feedback)
        assert feedback.value is True
        assert feedback.metadata["ai_decide.probability"] == "0.7"
        assert feedback.metadata["ai_decide.threshold"] == "0.7"
        state, questions = transport.calls[0]
        assert state == {"inputs": {"query": "q"}, "outputs": {"response": "r"}}
        assert questions["q1"]["instructions"] == "Is state.outputs good?"

    def test_noul_fail_synthesizes_rationale_from_fail_criteria(self):
        scorer = AiDecideScorer(
            name="check",
            questions={
                "check": noul_question("Is it good?", fail_when="It is not good.")
            },
            transport=FakeTransport({"check": _noul(0.2)}),
            threshold=0.5,
        )
        feedback = scorer(inputs={}, outputs={})

        assert feedback.value is False
        assert feedback.rationale.startswith("It is not good.")
        assert "probability 0.20" in feedback.rationale
        assert "threshold 0.50" in feedback.rationale

    def test_noul_fail_without_criteria_uses_instructions(self):
        scorer = AiDecideScorer(
            name="check",
            questions={"check": noul_question("Is it good?")},
            transport=FakeTransport({"check": _noul(0.0)}),
        )
        assert scorer(inputs={}, outputs={}).rationale.startswith(
            "Criterion not met: Is it good?"
        )

    def test_multiple_questions_single_call_returns_feedback_list(self):
        transport = FakeTransport(
            {
                "relevant": _noul(0.9),
                "team": {
                    "type": "choice",
                    "choice": "billing",
                    "probabilities": {"billing": 0.8, "support": 0.2},
                    "confidence": 0.9,
                },
                "urgency": {
                    "type": "score",
                    "score": 1.6,
                    "probabilities": {"0": 0.1, "1": 0.2, "2": 0.7},
                    "legend": {"0": "low", "1": "mid", "2": "high"},
                    "confidence": 0.8,
                },
            }
        )
        scorer = AiDecideScorer(
            name="multi",
            questions={
                "relevant": noul_question("Relevant?"),
                "team": {
                    "type": "choice",
                    "instructions": "Which team?",
                    "criteria": {"billing": None, "support": None},
                },
                "urgency": {
                    "type": "score",
                    "instructions": "How urgent?",
                    "criteria": ["low", "mid", "high"],
                },
            },
            transport=transport,
        )
        feedbacks = scorer(inputs={}, outputs={})

        assert len(transport.calls) == 1
        assert [fb.name for fb in feedbacks] == ["relevant", "team", "urgency"]
        assert feedbacks[0].value is True
        assert feedbacks[1].value == "billing"
        assert json.loads(feedbacks[1].metadata["ai_decide.probabilities"]) == {
            "billing": 0.8,
            "support": 0.2,
        }
        assert feedbacks[2].value == pytest.approx(1.6)
        assert json.loads(feedbacks[2].metadata["ai_decide.legend"])["2"] == "high"

    def test_expectations_are_added_to_state(self):
        transport = FakeTransport({"check": _noul(1)})
        scorer = AiDecideScorer(
            name="check",
            questions={"check": noul_question("Matches {{ expectations }}?")},
            transport=transport,
        )
        scorer(inputs={}, outputs={}, expectations={"expected_response": "x"})

        state, questions = transport.calls[0]
        assert state["expectations"] == {"expected_response": "x"}
        assert questions["q1"]["instructions"] == "Matches state.expectations?"

    def test_missing_answer_raises(self):
        scorer = AiDecideScorer(
            name="check",
            questions={"check": noul_question("Q?")},
            transport=FakeTransport({}),
        )
        with pytest.raises(AiDecideError, match="no answer"):
            scorer(inputs={}, outputs={})

    def test_type_mismatch_raises(self):
        scorer = AiDecideScorer(
            name="check",
            questions={"check": noul_question("Q?")},
            transport=FakeTransport({"check": {"type": "choice", "choice": "x"}}),
        )
        with pytest.raises(AiDecideError, match="expected 'noul'"):
            scorer(inputs={}, outputs={})

    def test_requires_questions(self):
        with pytest.raises(ValueError):
            AiDecideScorer(name="x", questions={}, transport=FakeTransport({}))


# =============================================================================
# Transports
# =============================================================================


class TestRestTransport:
    def test_calls_sdk_and_returns_answers(self):
        client = MagicMock()
        client.ai_functions.ai_decide.return_value = AiDecideResponse(
            response={"answers": {"q": _noul(0.4)}}
        )
        transport = RestAiDecideTransport(
            workspace_client_factory=lambda: client, version="1.0"
        )

        answers = transport.decide({"inputs": "x"}, {"q": noul_question("Q?")})

        assert answers == {"q": _noul(0.4)}
        kwargs = client.ai_functions.ai_decide.call_args.kwargs
        assert kwargs["state"] == {"inputs": "x"}
        assert kwargs["questions"] == {"q": noul_question("Q?")}
        assert kwargs["options"].version == "1.0"

    def test_creates_client_lazily_once(self):
        client = MagicMock()
        client.ai_functions.ai_decide.return_value = AiDecideResponse(
            response={"answers": {}}
        )
        factory = Mock(return_value=client)
        transport = RestAiDecideTransport(workspace_client_factory=factory)
        factory.assert_not_called()

        transport.decide({}, {})
        transport.decide({}, {})
        factory.assert_called_once()

    def test_missing_answers_raises(self):
        client = MagicMock()
        client.ai_functions.ai_decide.return_value = AiDecideResponse(response=None)
        transport = RestAiDecideTransport(workspace_client_factory=lambda: client)
        with pytest.raises(AiDecideError, match="no answers"):
            transport.decide({}, {})


# =============================================================================
# Config
# =============================================================================


class TestAiDecideJudgeModel:
    def test_defaults_to_rest(self):
        model = AiDecideJudgeModel()
        assert model.threshold == 0.5
        assert isinstance(model.as_transport(), RestAiDecideTransport)

    def test_threshold_bounds(self):
        with pytest.raises(ValueError):
            AiDecideJudgeModel(threshold=1.5)


class TestGuardrailModelAiDecide:
    def test_ai_decide_mode(self):
        guardrail = GuardrailModel(
            name="helpful",
            prompt="Does {{ outputs }} answer {{ inputs }}?",
            ai_decide={"threshold": 0.8},
            criteria={"fail_when": "The response does not answer the question."},
        )
        scorer = guardrail.as_scorer()

        assert isinstance(scorer, AiDecideScorer)
        assert scorer._threshold == 0.8
        assert scorer._questions["helpful"] == {
            "type": "noul",
            "instructions": "Does {{ outputs }} answer {{ inputs }}?",
            "criteria": {"false": "The response does not answer the question."},
        }

    def test_ai_decide_requires_prompt(self):
        with pytest.raises(ValueError, match="'prompt' is required"):
            GuardrailModel(name="x", ai_decide={})

    def test_ai_decide_rejects_model(self):
        with pytest.raises(ValueError, match="Cannot combine 'ai_decide'"):
            GuardrailModel(name="x", prompt="p", model="m", ai_decide={})

    def test_ai_decide_rejects_scorer(self):
        with pytest.raises(ValueError, match="Cannot combine 'ai_decide'"):
            GuardrailModel(name="x", scorer="a.B", ai_decide=True)

    def test_criteria_requires_ai_decide(self):
        with pytest.raises(ValueError, match="only supported with 'ai_decide'"):
            GuardrailModel(
                name="x", model="m", prompt="p", criteria={"pass_when": "ok"}
            )

    def test_llm_mode_unchanged(self):
        guardrail = GuardrailModel(name="x", model="m", prompt="p")
        assert guardrail.ai_decide is None


# =============================================================================
# Middleware
# =============================================================================


def _turn(response: str, tool_output: str | None = None) -> AgentState:
    messages: list[Any] = [HumanMessage(content="What is the refund policy?")]
    if tool_output is not None:
        messages.append(
            AIMessage(
                content="",
                tool_calls=[{"name": "lookup", "args": {}, "id": "call_1"}],
            )
        )
        messages.append(
            ToolMessage(content=tool_output, name="lookup", tool_call_id="call_1")
        )
    messages.append(AIMessage(content=response))
    return {"messages": messages}


class TestGuardrailMiddlewareAiDecide:
    def test_failed_decision_triggers_retry_with_fail_criteria(self, runtime):
        middleware = _with_transport(
            GuardrailMiddleware(
                name="helpful",
                prompt="unused when decision is set",
                ai_decide={},
                decision=noul_question("Helpful?", fail_when="Answer the question."),
                num_retries=2,
            ),
            FakeTransport({"helpful": _noul(0.1)}),
        )
        result = middleware.after_model(_turn("I like turtles."), runtime)

        retry_message = result["messages"][0]
        assert isinstance(retry_message, HumanMessage)
        assert "What is the refund policy?" in retry_message.content
        assert "Answer the question." in retry_message.content
        assert "probability 0.10" in retry_message.content

    def test_passing_decision_lets_response_through(self, runtime):
        middleware = _with_transport(
            GuardrailMiddleware(name="helpful", prompt="Helpful?", ai_decide={}),
            FakeTransport({"helpful": _noul(0.95)}),
        )
        assert middleware.after_model(_turn("30 days."), runtime) is None

    def test_prompt_becomes_noul_question(self):
        middleware = GuardrailMiddleware(
            name="helpful", prompt="Does {{ outputs }} help?", ai_decide={}
        )
        assert middleware._scorer._questions == {
            "helpful": {"type": "noul", "instructions": "Does {{ outputs }} help?"}
        }

    def test_transport_error_respects_fail_on_error(self, runtime):
        lenient = _with_transport(
            GuardrailMiddleware(name="g", prompt="Q?", ai_decide={}),
            FakeTransport(AiDecideError("boom")),
        )
        assert lenient.after_model(_turn("x" * 50), runtime) is None

        strict = _with_transport(
            GuardrailMiddleware(
                name="g", prompt="Q?", ai_decide={}, fail_on_error=True
            ),
            FakeTransport(AiDecideError("boom")),
        )
        result = strict.after_model(_turn("x" * 50), runtime)
        assert "Quality Check Error" in result["messages"][0].content

    def test_rejects_ai_decide_with_model(self):
        with pytest.raises(ValueError, match="both 'model'"):
            GuardrailMiddleware(name="g", model="m", prompt="p", ai_decide={})

    def test_factory_judge_selection(self):
        with pytest.raises(ValueError, match="needs a judge"):
            create_guardrail_middleware(name="g", prompt="p")
        with pytest.raises(ValueError, match="both 'model'"):
            create_guardrail_middleware(name="g", prompt="p", model="m", ai_decide={})
        middleware = create_guardrail_middleware(
            name="g", prompt="p", ai_decide={"threshold": 0.9}
        )
        assert middleware._scorer._threshold == 0.9


class TestBuiltinGuardrailsAiDecide:
    def test_veracity_uses_builtin_decision_and_tool_context(self, runtime):
        transport = FakeTransport({"veracity": _noul(0.05)})
        middleware = _with_transport(
            create_veracity_guardrail_middleware(ai_decide={"threshold": 0.6}),
            transport,
        )
        result = middleware.after_model(
            _turn("Refunds within 90 days.", tool_output="Refunds within 30 days."),
            runtime,
        )

        state, questions = transport.calls[0]
        assert questions["q1"]["instructions"] == (VERACITY_DECISION["instructions"])
        assert "Refunds within 30 days." in state["inputs"]["context"]
        assert VERACITY_DECISION["criteria"]["false"] in (result["messages"][0].content)

    def test_veracity_still_skips_without_tool_context(self, runtime):
        transport = FakeTransport({"veracity": _noul(0)})
        middleware = _with_transport(
            VeracityGuardrailMiddleware(ai_decide={}), transport
        )
        assert middleware.after_model(_turn("Hello!"), runtime) is None
        assert transport.calls == []

    def test_relevance_decision(self):
        middleware = RelevanceGuardrailMiddleware(ai_decide={})
        assert middleware._scorer._questions["relevance"] == RELEVANCE_DECISION
        assert middleware._apply_to == "output"

    def test_tone_preset_and_custom_guidelines(self):
        preset = ToneGuardrailMiddleware(tone="empathetic", ai_decide={})
        assert (
            preset._scorer._questions["tone_empathetic"]
            == (TONE_DECISIONS["empathetic"])
        )

        custom = ToneGuardrailMiddleware(
            tone="brand",
            custom_guidelines="Is {{ outputs }} upbeat?",
            ai_decide={},
        )
        assert custom._scorer._questions["tone_brand"] == {
            "type": "noul",
            "instructions": "Is {{ outputs }} upbeat?",
        }

    def test_all_tone_profiles_have_decisions(self):
        assert set(TONE_DECISIONS) == set(ToneGuardrailMiddleware.AVAILABLE_PROFILES)

    def test_conciseness_length_check_runs_before_ai_decide(self, runtime):
        transport = FakeTransport({"conciseness": _noul(1)})
        middleware = _with_transport(
            ConcisenessGuardrailMiddleware(ai_decide={}, max_length=10),
            transport,
        )
        result = middleware.after_model(_turn("x" * 50), runtime)
        assert "exceeds the maximum" in result["messages"][0].content
        assert transport.calls == []

    def test_builtins_reject_model_plus_ai_decide(self):
        for cls in (
            VeracityGuardrailMiddleware,
            RelevanceGuardrailMiddleware,
            ToneGuardrailMiddleware,
            ConcisenessGuardrailMiddleware,
        ):
            assert isinstance(cls(ai_decide=True)._scorer, AiDecideScorer)
            with pytest.raises(ValueError, match="both 'model'"):
                cls(model="databricks:/m", ai_decide={})


class TestSafetyGuardrailAiDecide:
    def test_blocks_unsafe_response(self, runtime):
        middleware = SafetyGuardrailMiddleware(ai_decide={})
        middleware._ai_decide_scorer._transport = FakeTransport(
            {"safety_guardrail": _noul(0.02)}
        )
        result = middleware.after_agent(_turn("unsafe"), runtime)
        assert result["jump_to"] == "end"

    def test_allows_safe_response(self, runtime):
        middleware = SafetyGuardrailMiddleware(ai_decide={})
        middleware._ai_decide_scorer._transport = FakeTransport(
            {"safety_guardrail": _noul(0.99)}
        )
        assert middleware.after_agent(_turn("safe"), runtime) is None

    def test_rejects_both_judges(self):
        with pytest.raises(ValueError, match="both 'model'"):
            SafetyGuardrailMiddleware(safety_model="m", ai_decide={})


# =============================================================================
# Retry loop through a real agent graph
# =============================================================================


class TestGuardrailRetryReinvokesModel:
    """A failed guardrail must re-run the model, not just append feedback."""

    def _agent(self, middleware: list[Any], responses: list[str]):
        from langchain.agents import create_agent
        from langchain_core.language_models.fake_chat_models import (
            FakeMessagesListChatModel,
        )

        model = FakeMessagesListChatModel(
            responses=[AIMessage(content=text) for text in responses]
        )
        return create_agent(model=model, tools=[], middleware=middleware)

    def test_failed_guardrail_retries_and_returns_corrected_answer(self):
        transport = FakeTransport({})
        answers = iter([_noul(0.0), _noul(0.99)])
        transport.decide = lambda state, questions: {
            next(iter(questions)): next(answers)
        }
        guardrail = _with_transport(
            GuardrailMiddleware(
                name="no_competitors",
                prompt="Is {{ outputs }} free of competitor names?",
                ai_decide={},
                num_retries=3,
                apply_to="output",
            ),
            transport,
        )
        agent = self._agent(
            [guardrail],
            ["Home Depot is cheaper.", "Our drills start at $79."],
        )

        result = agent.invoke({"messages": [HumanMessage(content="Drill prices?")]})

        ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
        assert [m.content for m in ai_messages] == [
            "Home Depot is cheaper.",
            "Our drills start at $79.",
        ]
        assert result["messages"][-1].content == "Our drills start at $79."

    def test_conciseness_length_retry_reinvokes_model(self):
        guardrail = ConcisenessGuardrailMiddleware(
            ai_decide={},
            max_length=30,
            min_length=5,
            check_verbosity=False,
            num_retries=3,
        )
        agent = self._agent([guardrail], ["x" * 100, "Short answer."])

        result = agent.invoke({"messages": [HumanMessage(content="Explain.")]})

        assert result["messages"][-1].content == "Short answer."

    def test_guardrails_judge_original_question_after_retry(self):
        seen_queries: list[str] = []

        class Recorder:
            name = "fake"

            def __init__(self, answers):
                self.answers = iter(answers)

            def decide(self, state, questions):
                seen_queries.append(state["inputs"]["query"])
                return {next(iter(questions)): next(self.answers)}

        first = _with_transport(
            GuardrailMiddleware(
                name="no_competitors",
                prompt="Competitor free?",
                ai_decide={},
                apply_to="output",
            ),
            Recorder([_noul(0.0), _noul(1.0)]),
        )
        second = _with_transport(
            GuardrailMiddleware(
                name="relevance",
                prompt="Relevant?",
                ai_decide={},
                apply_to="output",
            ),
            Recorder([_noul(1.0)]),
        )
        agent = self._agent(
            [second, first], ["Home Depot sells DeWalt.", "We sell DeWalt."]
        )

        result = agent.invoke({"messages": [HumanMessage(content="Drill brands?")]})

        assert result["messages"][-1].content == "We sell DeWalt."
        assert seen_queries == ["Drill brands?"] * 3

    def _counting_agent(self, middleware: list[Any]):
        from langchain.agents import create_agent
        from langchain_core.language_models.fake_chat_models import (
            FakeMessagesListChatModel,
        )

        model = FakeMessagesListChatModel(
            responses=[AIMessage(content=f"answer {i}") for i in range(50)]
        )
        return create_agent(model=model, tools=[], middleware=middleware), model

    def _scripted(self, name: str, probabilities: list[float]) -> GuardrailMiddleware:
        answers = iter(probabilities)
        transport = FakeTransport({})
        transport.decide = lambda state, questions: {
            next(iter(questions)): _noul(next(answers))
        }
        return _with_transport(
            GuardrailMiddleware(
                name=name,
                prompt=f"{name}?",
                ai_decide={},
                num_retries=2,
                apply_to="output",
            ),
            transport,
        )

    def test_exhausted_guardrail_ends_turn(self):
        always_fails = self._scripted("strict", [0.0] * 10)
        judged: list[str] = []
        observer = self._scripted("observer", [1.0] * 10)
        observer._scorer._transport.decide = lambda state, questions: (
            judged.append(state["outputs"]["response"])
            or {next(iter(questions)): _noul(1.0)}
        )
        agent, model = self._counting_agent([observer, always_fails])

        result = agent.invoke({"messages": [HumanMessage(content="Q?")]})

        assert "Quality Check Failed" in result["messages"][-1].content
        assert model.i == 2  # first answer + one retry (num_retries=2)
        assert all("Quality Check Failed" not in text for text in judged)

    def test_conflicting_guardrails_are_bounded_per_turn(self):
        # a fails whenever b passed last, and vice versa -- would loop forever
        a = self._scripted("a", [0.0, 1.0] * 10)
        b = self._scripted("b", [0.0, 1.0] * 10)
        agent, model = self._counting_agent([b, a])

        result = agent.invoke({"messages": [HumanMessage(content="Q?")]})

        assert "Quality Check Failed" in result["messages"][-1].content
        assert model.i <= 1 + (a.num_retries - 1) + (b.num_retries - 1)

    def test_retry_budget_resets_on_next_turn(self):
        guardrail = self._scripted("strict", [0.0, 1.0, 0.0, 1.0])
        agent, model = self._counting_agent([guardrail])

        first = agent.invoke({"messages": [HumanMessage(content="Q1?")]})
        second = agent.invoke(
            {"messages": [*first["messages"], HumanMessage(content="Q2?")]}
        )

        assert second["messages"][-1].content == "answer 3"


# =============================================================================
# Evaluation
# =============================================================================


def _evaluation(**kwargs: Any):
    from dao_ai.config import EvaluationModel

    return EvaluationModel(
        model={"name": "databricks-claude-sonnet-5"},
        table={"name": "evaluation"},
        num_evals=1,
        **kwargs,
    )


class TestDecisionQuestionModel:
    def test_question_specs(self):
        from dao_ai.config import DecisionQuestionModel

        assert DecisionQuestionModel(
            name="ok", instructions="Is {{ outputs }} ok?", fail_when="bad"
        ).as_question() == {
            "type": "noul",
            "instructions": "Is {{ outputs }} ok?",
            "criteria": {"false": "bad"},
        }
        assert DecisionQuestionModel(
            name="team",
            type="choice",
            instructions="Which team?",
            choices={"billing": "Payments", "support": None},
        ).as_question()["criteria"] == {"billing": "Payments", "support": None}
        assert DecisionQuestionModel(
            name="urgency",
            type="score",
            instructions="How urgent?",
            levels=["low", "high"],
        ).as_question()["criteria"] == ["low", "high"]

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"type": "choice"},
            {"type": "score", "levels": ["only one"]},
            {"type": "noul", "choices": {"a": None}},
            {"type": "choice", "choices": {"a": None}, "pass_when": "x"},
            {"type": "noul", "levels": ["a", "b"]},
        ],
    )
    def test_invalid_criteria(self, kwargs):
        from dao_ai.config import DecisionQuestionModel

        with pytest.raises(ValueError):
            DecisionQuestionModel(name="q", instructions="Q?", **kwargs)


class TestEvaluationAiDecide:
    def test_ai_decide_false_keeps_mlflow_judges(self):
        from mlflow.genai.scorers import Safety

        from dao_ai.evaluation import build_scorers

        scorers = build_scorers(_evaluation(ai_decide=False))
        assert any(isinstance(s, Safety) for s in scorers)
        assert not any(isinstance(s, AiDecideScorer) for s in scorers)

    def test_ai_decide_replaces_builtin_llm_judges(self):
        from mlflow.genai.scorers import Safety, ToolCallEfficiency

        from dao_ai.evaluation import build_scorers

        scorers = build_scorers(
            _evaluation(
                ai_decide={"threshold": 0.6},
                decisions=[
                    {
                        "name": "intent",
                        "type": "choice",
                        "instructions": "What does {{ inputs }} want?",
                        "choices": {"product_info": None, "store_info": None},
                    }
                ],
            )
        )

        assert [type(s) for s in scorers] == [AiDecideScorer, ToolCallEfficiency]
        assert not any(isinstance(s, Safety) for s in scorers)
        ai_decide = scorers[0]
        assert list(ai_decide._questions) == [
            "safety",
            "completeness",
            "relevance_to_query",
            "intent",
        ]
        assert ai_decide._threshold == 0.6

    def test_decision_names_unique(self):
        with pytest.raises(ValueError, match="unique"):
            _evaluation(
                ai_decide={},
                decisions=[
                    {"name": "q", "instructions": "Q?"},
                    {"name": "q", "instructions": "Q2?"},
                ],
            )

    def test_ai_decide_guidelines_share_one_call(self):
        from mlflow.genai.scorers import Guidelines

        from dao_ai.config import GuidelineModel
        from dao_ai.evaluation import create_guidelines_scorers

        scorers = create_guidelines_scorers(
            [
                GuidelineModel(
                    name="llm_judged", guidelines=["Be kind"], ai_decide=False
                ),
                GuidelineModel(name="tone", guidelines=["Be polite"], ai_decide={}),
                GuidelineModel(
                    name="accuracy",
                    guidelines=["Cite tools", "No guessing"],
                    ai_decide={},
                ),
            ]
        )

        assert isinstance(scorers[0], Guidelines)
        assert len(scorers) == 2
        ai_decide = scorers[1]
        assert isinstance(ai_decide, AiDecideScorer)
        assert list(ai_decide._questions) == ["tone", "accuracy"]
        assert (
            "- Cite tools\n- No guessing"
            in (ai_decide._questions["accuracy"]["instructions"])
        )

    def test_scorer_feedback_names_match_builtins(self):
        from dao_ai.evaluation import build_scorers

        scorer = build_scorers(_evaluation(ai_decide={}))[0]
        scorer._transport = FakeTransport(
            {
                "safety": _noul(1),
                "completeness": _noul(0.2),
                "relevance_to_query": _noul(0.9),
            }
        )
        feedbacks = scorer(inputs={"messages": []}, outputs={"output": []})
        assert {fb.name: fb.value for fb in feedbacks} == {
            "safety": True,
            "completeness": False,
            "relevance_to_query": True,
        }

    def test_monitoring_skips_ai_decide_scorers(self, monkeypatch):
        import dao_ai.evaluation as evaluation
        from dao_ai.config import GuidelineModel, MonitoringModel

        registered: list[str] = []
        monkeypatch.setattr(evaluation.mlflow, "set_experiment", lambda **_: None)
        monkeypatch.setattr(evaluation, "list_scorers", lambda: [])
        monkeypatch.setattr(
            evaluation,
            "_ensure_scorer_running",
            lambda scorer, name, desired_rate, existing_scorers: (
                registered.append(name) or scorer
            ),
        )

        evaluation.register_monitoring_scorers(
            MonitoringModel(
                scorers=[
                    "safety",
                    GuardrailModel(name="aid_guard", prompt="Q?", ai_decide={}),
                ],
                guidelines=[
                    GuidelineModel(name="llm_g", guidelines=["x"]),
                    GuidelineModel(name="aid_g", guidelines=["y"], ai_decide={}),
                ],
            ),
            experiment_id="1",
        )

        assert "aid_guard" not in registered
        assert "aid_g" not in registered
        assert "llm_g" in registered


# =============================================================================
# pass_if: violation-detection questions
# =============================================================================


class TestPassIfNo:
    def test_noul_question_swaps_criteria(self):
        question = noul_question(
            "Does it name a competitor?",
            pass_when="No competitor named.",
            fail_when="Names a competitor.",
            pass_if="no",
        )
        assert question == {
            "type": "noul",
            "instructions": "Does it name a competitor?",
            "criteria": {
                "true": "Names a competitor.",
                "false": "No competitor named.",
            },
            "pass_if": "no",
        }

    @pytest.mark.parametrize(
        "probability,expected", [(0.9, False), (0.6, False), (0.4, True), (0.0, True)]
    )
    def test_yes_means_fail(self, probability, expected):
        transport = FakeTransport({"c": _noul(probability)})
        scorer = AiDecideScorer(
            name="c",
            questions={
                "c": noul_question(
                    "Does it name a competitor?",
                    fail_when="Names a competitor.",
                    pass_if="no",
                )
            },
            transport=transport,
            threshold=0.5,
        )
        feedback = scorer(inputs={}, outputs={})

        assert feedback.value is expected
        assert feedback.metadata["ai_decide.pass_if"] == "no"
        assert feedback.metadata["ai_decide.probability"] == json.dumps(probability)
        if not expected:
            assert feedback.rationale.startswith("Names a competitor.")
        # pass_if is DAO AI-only and never sent to ai_decide
        _, sent = transport.calls[0]
        assert "pass_if" not in sent["q1"]
        assert sent["q1"]["criteria"] == {"true": "Names a competitor."}

    def test_guardrail_model_pass_if(self):
        scorer = GuardrailModel(
            name="no_comp",
            prompt="Does {{ outputs }} name a competitor?",
            ai_decide={},
            pass_if="no",
            criteria={"fail_when": "Names a competitor."},
        ).as_scorer()
        assert scorer._questions["no_comp"]["pass_if"] == "no"
        assert scorer._questions["no_comp"]["criteria"] == {
            "true": "Names a competitor."
        }

    def test_pass_if_requires_ai_decide(self):
        with pytest.raises(ValueError, match="'pass_if' is only supported"):
            GuardrailModel(name="x", model="m", prompt="p", pass_if="no")

    def test_decision_pass_if_only_for_noul(self):
        from dao_ai.config import DecisionQuestionModel

        assert (
            DecisionQuestionModel(
                name="q", instructions="Violation?", pass_if="no"
            ).as_question()["pass_if"]
            == "no"
        )
        with pytest.raises(ValueError):
            DecisionQuestionModel(
                name="q",
                type="choice",
                instructions="Which?",
                choices={"a": None},
                pass_if="no",
            )

    def test_builtin_conciseness_is_violation_question(self):
        from dao_ai.middleware.guardrails import CONCISENESS_DECISION

        assert CONCISENESS_DECISION["pass_if"] == "no"
        assert TONE_DECISIONS["professional"]["pass_if"] == "no"
        assert "pass_if" not in RELEVANCE_DECISION


class TestNeutralQuestionIds:
    """ai_decide reads question ids as part of the question, so names stay local."""

    def test_sends_neutral_ids_and_maps_answers_back(self):
        sent: list[dict[str, Any]] = []

        class Recorder:
            name = "fake"

            def decide(self, state, questions):
                sent.append(questions)
                return {"q1": _noul(0.9), "q2": _noul(0.1)}

        scorer = AiDecideScorer(
            name="multi",
            questions={
                "no_competitor_mentions": noul_question("Names a competitor?"),
                "relevance": noul_question("Relevant?"),
            },
            transport=Recorder(),
        )
        feedbacks = scorer(inputs={}, outputs={})

        assert list(sent[0]) == ["q1", "q2"]
        assert {fb.name: fb.value for fb in feedbacks} == {
            "no_competitor_mentions": True,
            "relevance": False,
        }


class TestSafetyIgnoresGuardrailNotices:
    def test_safety_judges_the_answer_not_the_quality_notice(self):
        from langchain.agents import create_agent
        from langchain_core.language_models.fake_chat_models import (
            FakeMessagesListChatModel,
        )

        judged: list[str] = []
        safety = SafetyGuardrailMiddleware(ai_decide={})
        safety._ai_decide_scorer._transport.decide = lambda state, questions: (
            judged.append(state["outputs"]["response"])
            or {next(iter(questions)): _noul(1.0)}
        )
        strict = _with_transport(
            GuardrailMiddleware(
                name="strict",
                prompt="Q?",
                ai_decide={},
                num_retries=1,
                apply_to="output",
            ),
            FakeTransport({"strict": _noul(0.0)}),
        )
        model = FakeMessagesListChatModel(responses=[AIMessage(content="The answer.")])
        agent = create_agent(model=model, tools=[], middleware=[safety, strict])

        result = agent.invoke({"messages": [HumanMessage(content="Q?")]})

        assert "Quality Check Failed" in result["messages"][-1].content
        assert judged == ["The answer."]


class TestScorerTracing:
    def test_no_standalone_trace_outside_an_active_trace(self, monkeypatch):
        import dao_ai.judges.ai_decide as module

        started: list[str] = []
        monkeypatch.setattr(
            module.mlflow,
            "start_span",
            lambda **kwargs: started.append(kwargs["name"]) or _NullSpan(),
        )
        monkeypatch.setattr(module.mlflow, "get_current_active_span", lambda: None)
        scorer = AiDecideScorer(
            name="check",
            questions={"check": noul_question("Q?")},
            transport=FakeTransport({"check": _noul(1)}),
        )

        assert scorer(inputs={}, outputs={}).value is True
        assert started == []

    def test_span_nested_under_active_trace(self, monkeypatch):
        import dao_ai.judges.ai_decide as module

        started: list[str] = []
        monkeypatch.setattr(
            module.mlflow,
            "start_span",
            lambda **kwargs: started.append(kwargs["name"]) or _NullSpan(),
        )
        monkeypatch.setattr(module.mlflow, "get_current_active_span", lambda: object())
        scorer = AiDecideScorer(
            name="check",
            questions={"check": noul_question("Q?")},
            transport=FakeTransport({"check": _noul(1)}),
        )

        scorer(inputs={}, outputs={})
        assert started == ["ai_decide:check"]


class _NullSpan:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def set_inputs(self, *_):
        pass

    def set_outputs(self, *_):
        pass


# =============================================================================
# Review fixes
# =============================================================================


class TestReviewFixes:
    def test_score_levels_capped_at_ten(self):
        from dao_ai.config import DecisionQuestionModel

        DecisionQuestionModel(
            name="q",
            type="score",
            instructions="How?",
            levels=[f"level {i}" for i in range(10)],
        )
        with pytest.raises(ValueError, match="2-10 'levels'"):
            DecisionQuestionModel(
                name="q",
                type="score",
                instructions="How?",
                levels=[f"level {i}" for i in range(11)],
            )

    @pytest.mark.parametrize("name", ["safety", "completeness", "relevance_to_query"])
    def test_decisions_cannot_shadow_builtin_metrics(self, name):
        with pytest.raises(ValueError, match="built-in"):
            _evaluation(ai_decide={}, decisions=[{"name": name, "instructions": "Q?"}])

    def test_retry_tracker_is_bounded(self, runtime, monkeypatch):
        import dao_ai.middleware.guardrails as guardrails

        monkeypatch.setattr(guardrails, "_MAX_TRACKED_THREADS", 3)
        middleware = _with_transport(
            GuardrailMiddleware(
                name="g", prompt="Q?", ai_decide={}, num_retries=5, apply_to="output"
            ),
            FakeTransport({"g": _noul(0.0)}),
        )
        for i in range(10):
            runtime.context = Context(user_id="u", thread_id=f"thread-{i}")
            middleware.after_model(_turn("answer"), runtime)

        assert len(middleware._retry_counts) == 3
        assert list(middleware._retry_counts) == ["thread-7", "thread-8", "thread-9"]

    def test_reserved_metric_names_match_builtin_questions(self):
        from dao_ai.config import EvaluationModel
        from dao_ai.evaluation import AI_DECIDE_BUILTIN_QUESTIONS

        assert EvaluationModel._AI_DECIDE_BUILTIN_METRICS == set(
            AI_DECIDE_BUILTIN_QUESTIONS
        )


# =============================================================================
# Judge selection: LLM judge by default, ai_decide opt-in
# =============================================================================


class TestJudgeSelection:
    """model -> LLM judge (default); ai_decide: true / settings -> ai_decide."""

    def test_resolver_truth_table(self):
        from dao_ai.config import resolve_ai_decide

        configured = AiDecideJudgeModel(threshold=0.8)
        assert resolve_ai_decide(None) is None
        assert resolve_ai_decide(False) is None
        assert resolve_ai_decide(True) == AiDecideJudgeModel()
        assert resolve_ai_decide({}) == AiDecideJudgeModel()
        assert resolve_ai_decide({"threshold": 0.8}) == configured
        assert resolve_ai_decide(configured) is configured

    @pytest.mark.parametrize(
        "factory",
        [
            "create_veracity_guardrail_middleware",
            "create_relevance_guardrail_middleware",
            "create_tone_guardrail_middleware",
            "create_conciseness_guardrail_middleware",
        ],
    )
    def test_builtins_need_a_judge(self, factory):
        import dao_ai.middleware.guardrails as guardrails
        from dao_ai.middleware.guardrails import JudgeScorer

        build = getattr(guardrails, factory)
        with pytest.raises(ValueError, match="needs a judge"):
            build()
        with pytest.raises(ValueError, match="needs a judge"):
            build(ai_decide=False)
        assert isinstance(build(model="databricks:/m")._scorer, JudgeScorer)
        assert isinstance(build(ai_decide=True)._scorer, AiDecideScorer)
        assert build(ai_decide={"threshold": 0.8})._scorer._threshold == 0.8

    @pytest.mark.parametrize("ai_decide", [True, {}, {"threshold": 0.8}])
    def test_model_and_ai_decide_conflict(self, ai_decide):
        with pytest.raises(ValueError, match="both 'model'"):
            RelevanceGuardrailMiddleware(model="databricks:/m", ai_decide=ai_decide)

    def test_generic_factory(self):
        from dao_ai.middleware.guardrails import JudgeScorer

        with pytest.raises(ValueError, match="needs a judge"):
            create_guardrail_middleware(name="g", prompt="Helpful?")
        assert isinstance(
            create_guardrail_middleware(
                name="g", prompt="Is {{ outputs }} ok?", model="databricks:/m"
            )._scorer,
            JudgeScorer,
        )
        assert isinstance(
            create_guardrail_middleware(name="g", prompt="p", ai_decide=True)._scorer,
            AiDecideScorer,
        )

    def test_safety_requires_a_judge(self):
        with pytest.raises(ValueError, match="needs a judge"):
            SafetyGuardrailMiddleware()
        assert SafetyGuardrailMiddleware(ai_decide=True)._ai_decide_scorer is not None
        llm = SafetyGuardrailMiddleware(safety_model="databricks:/m")
        assert llm._ai_decide_scorer is None
        assert llm.model_endpoint == "databricks:/m"

    def test_guardrail_model(self):
        from dao_ai.middleware.guardrails import JudgeScorer

        with pytest.raises(ValueError, match="Either 'scorer'"):
            GuardrailModel(name="g", prompt="Q?")
        assert isinstance(
            GuardrailModel(
                name="g", prompt="Is {{ outputs }} ok?", model="m"
            ).as_scorer(),
            JudgeScorer,
        )
        for value in (True, {}, {"threshold": 0.9}):
            scorer = GuardrailModel(name="g", prompt="Q?", ai_decide=value).as_scorer()
            assert isinstance(scorer, AiDecideScorer)
        with pytest.raises(ValueError, match="Cannot combine 'ai_decide'"):
            GuardrailModel(name="g", prompt="Q?", model="m", ai_decide=True)
        with pytest.raises(ValueError, match="only supported with 'ai_decide'"):
            GuardrailModel(name="g", prompt="Q?", model="m", pass_if="no")

    def test_evaluation_defaults_to_llm_judges(self):
        from mlflow.genai.scorers import Safety, ToolCallEfficiency

        from dao_ai.evaluation import build_scorers

        scorers = build_scorers(_evaluation())
        assert any(isinstance(s, Safety) for s in scorers)
        assert not any(isinstance(s, AiDecideScorer) for s in scorers)
        scorers = build_scorers(_evaluation(ai_decide=True))
        assert [type(s) for s in scorers] == [AiDecideScorer, ToolCallEfficiency]

    def test_decisions_require_ai_decide(self):
        for value in ({}, {"ai_decide": False}):
            with pytest.raises(ValueError, match="'decisions' need ai_decide"):
                _evaluation(decisions=[{"name": "q", "instructions": "Q?"}], **value)
        _evaluation(ai_decide=True, decisions=[{"name": "q", "instructions": "Q?"}])

    def test_guidelines_default_to_llm_judge(self):
        from mlflow.genai.scorers import Guidelines

        from dao_ai.config import GuidelineModel
        from dao_ai.evaluation import create_guidelines_scorers

        assert isinstance(
            create_guidelines_scorers(
                [GuidelineModel(name="g", guidelines=["Be kind"])]
            )[0],
            Guidelines,
        )
        assert isinstance(
            create_guidelines_scorers(
                [GuidelineModel(name="g", guidelines=["Be kind"], ai_decide=True)]
            )[0],
            AiDecideScorer,
        )
