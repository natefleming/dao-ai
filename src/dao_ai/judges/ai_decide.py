"""
Jev-style judges backed by Databricks ``ai_decide``.

MLflow 3.17 introduced "Jev decision" judges (``make_judge`` with a
``typesafe:/`` model): structured ``bool`` / ``Literal`` verdicts with
calibrated probabilities and no free-text rationale. MLflow only reaches the
external TypeSafe API or the OSS MLflow gateway for these. Databricks serves
the same decision model on-platform as ``ai_decide``, so this module adapts
it to the MLflow ``Scorer`` interface used by DAO AI guardrails and
evaluation.

Decisions go to ``POST /api/2.0/ai-functions/ai-decide`` through the typed
SDK call ``WorkspaceClient.ai_functions.ai_decide`` (``RestAiDecideTransport``).

Question types follow the ``ai_decide`` contract:

* ``noul`` -- probability that a yes/no question is true. Mapped to a
  ``bool`` Feedback using a configurable threshold. A question either passes
  on "yes" (``pass_if="yes"``) or asks whether a violation is present and
  passes on "no" (``pass_if="no"``). ai_decide is markedly more reliable at
  detecting that something is present than at confirming it is absent, so
  checks such as "does it name a competitor" work best as ``pass_if="no"``.
* ``choice`` -- one label out of ``criteria``. Mapped to the label.
* ``score`` -- probability-weighted ordinal level. Mapped to a float.
"""

from __future__ import annotations

import json
import re
import time
from contextlib import nullcontext
from typing import Any, Callable, Literal, Protocol

import mlflow
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.aifunctions import AiDecideOptions, AiDecideResponse
from loguru import logger
from mlflow.entities import SpanType
from mlflow.entities.assessment import Feedback
from mlflow.entities.assessment_source import AssessmentSource, AssessmentSourceType
from mlflow.genai.scorers.base import Scorer
from pydantic import PrivateAttr

AI_DECIDE_SOURCE_ID: str = "databricks:/ai_decide"

# DAO AI-only key on a noul question spec: "yes" (default) or "no". Stripped
# before the question is sent to ai_decide.
PASS_IF_KEY: str = "pass_if"

_STATE_REFERENCE_PATTERN: re.Pattern[str] = re.compile(
    r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}"
)


class AiDecideError(RuntimeError):
    """Raised when ``ai_decide`` fails or returns an unusable answer."""


class AiDecideTransport(Protocol):
    """Sends one ``ai_decide`` request and returns ``response.answers``."""

    name: str

    def decide(
        self, state: dict[str, Any], questions: dict[str, dict[str, Any]]
    ) -> dict[str, dict[str, Any]]: ...


def _answers_from(response: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(response, dict) or not isinstance(response.get("answers"), dict):
        raise AiDecideError("ai_decide returned no answers.")
    return response["answers"]


class RestAiDecideTransport:
    """Calls ``ai_decide`` through the Databricks REST API (typed SDK)."""

    name: str = "rest"

    def __init__(
        self,
        workspace_client_factory: Callable[[], WorkspaceClient] = WorkspaceClient,
        version: str = "1.0",
    ):
        self._workspace_client_factory = workspace_client_factory
        self._workspace_client: WorkspaceClient | None = None
        self.version = version

    def decide(
        self, state: dict[str, Any], questions: dict[str, dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        if self._workspace_client is None:
            self._workspace_client = self._workspace_client_factory()
        result: AiDecideResponse = self._workspace_client.ai_functions.ai_decide(
            state=state,
            questions=questions,
            options=AiDecideOptions(version=self.version),
        )
        return _answers_from(result.response)


def render_instructions(instructions: str, state: dict[str, Any]) -> str:
    """Rewrite ``{{ field }}`` template references to ``state.field``.

    ``ai_decide`` reads the evaluation payload from ``state`` and expects
    instructions to point at it, so MLflow-style ``{{ inputs }}`` /
    ``{{ outputs }}`` references become ``state.inputs`` / ``state.outputs``.
    References to fields absent from ``state`` are left untouched.
    """

    def replace(match: re.Match[str]) -> str:
        field: str = match.group(1)
        return f"state.{field}" if field in state else match.group(0)

    return _STATE_REFERENCE_PATTERN.sub(replace, instructions)


def noul_question(
    instructions: str,
    pass_when: str | None = None,
    fail_when: str | None = None,
    pass_if: Literal["yes", "no"] = "yes",
) -> dict[str, Any]:
    """Build a yes/no (``noul``) question spec.

    Args:
        instructions: The yes/no question.
        pass_when: Describes a passing response.
        fail_when: Describes a failing response; fed back on retries.
        pass_if: ``"yes"`` when a yes answer passes; ``"no"`` when the
            question asks whether a violation is present.
    """
    question: dict[str, Any] = {"type": "noul", "instructions": instructions}
    yes_means, no_means = (
        (pass_when, fail_when) if pass_if == "yes" else (fail_when, pass_when)
    )
    criteria: dict[str, str] = {}
    if yes_means:
        criteria["true"] = yes_means
    if no_means:
        criteria["false"] = no_means
    if criteria:
        question["criteria"] = criteria
    if pass_if == "no":
        question[PASS_IF_KEY] = "no"
    return question


def _probability(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AiDecideError(f"ai_decide returned a non-numeric value: {value!r}")
    return float(value)


def _to_feedback(
    name: str,
    question: dict[str, Any],
    answer: dict[str, Any],
    threshold: float,
) -> Feedback:
    answer_type: Any = answer.get("type")
    if answer_type != question["type"]:
        raise AiDecideError(
            f"ai_decide answer '{name}' has type {answer_type!r}, "
            f"expected {question['type']!r}."
        )

    metadata: dict[str, str] = {"ai_decide.type": answer_type}
    criteria: Any = question.get("criteria")
    value: bool | str | float
    rationale: str

    match answer_type:
        case "noul":
            probability: float = _probability(answer.get("probability"))
            passes_on_yes: bool = question.get(PASS_IF_KEY, "yes") == "yes"
            pass_probability: float = (
                probability if passes_on_yes else 1.0 - probability
            )
            value = pass_probability >= threshold
            metadata["ai_decide.probability"] = json.dumps(probability)
            metadata["ai_decide.pass_if"] = "yes" if passes_on_yes else "no"
            metadata["ai_decide.pass_probability"] = json.dumps(
                round(pass_probability, 6)
            )
            metadata["ai_decide.threshold"] = json.dumps(threshold)
            # ai_decide returns no rationale; synthesize one from the question
            # so guardrail retries can tell the model what to fix.
            answered_yes: bool = value == passes_on_yes
            outcome: str | None = (
                criteria.get("true" if answered_yes else "false")
                if isinstance(criteria, dict)
                else None
            )
            if value:
                rationale = outcome or "Criterion met."
            elif passes_on_yes:
                rationale = outcome or f"Criterion not met: {question['instructions']}"
            else:
                rationale = outcome or f"Check failed: {question['instructions']}"
            rationale += (
                f" (ai_decide pass probability {pass_probability:.2f}, "
                f"threshold {threshold:.2f})"
            )
        case "choice":
            choice: Any = answer.get("choice")
            if not isinstance(choice, str):
                raise AiDecideError(f"ai_decide answer '{name}' has no choice.")
            value = choice
            confidence: float = _probability(answer.get("confidence"))
            metadata["ai_decide.probabilities"] = json.dumps(
                answer.get("probabilities", {}), sort_keys=True
            )
            metadata["ai_decide.confidence"] = json.dumps(confidence)
            rationale = f"ai_decide chose '{choice}' (confidence {confidence:.2f})"
        case "score":
            score: float = _probability(answer.get("score"))
            value = score
            confidence = _probability(answer.get("confidence"))
            metadata["ai_decide.probabilities"] = json.dumps(
                answer.get("probabilities", {}), sort_keys=True
            )
            metadata["ai_decide.legend"] = json.dumps(
                answer.get("legend", {}), sort_keys=True
            )
            metadata["ai_decide.confidence"] = json.dumps(confidence)
            rationale = f"ai_decide score {score:.2f} (confidence {confidence:.2f})"
        case _:
            raise AiDecideError(
                f"ai_decide answer '{name}' has unsupported type {answer_type!r}."
            )

    return Feedback(
        name=name,
        value=value,
        rationale=rationale,
        source=AssessmentSource(
            source_type=AssessmentSourceType.LLM_JUDGE,
            source_id=AI_DECIDE_SOURCE_ID,
        ),
        metadata=metadata,
    )


class AiDecideScorer(Scorer):
    """MLflow ``Scorer`` that answers one or more questions with ``ai_decide``.

    All questions are answered in a single ``ai_decide`` call. With one
    question the scorer returns a single ``Feedback`` named after the scorer;
    with several it returns one ``Feedback`` per question, named by question
    id.

    Args:
        name: Name identifying this scorer.
        questions: Mapping of question id to an ``ai_decide`` question spec
            (``type``, ``instructions``, optional ``criteria``). Instructions
            may use ``{{ inputs }}`` / ``{{ outputs }}`` / ``{{ expectations }}``.
        transport: Transport used to reach ``ai_decide``.
        threshold: Probability at or above which a ``noul`` answer passes.
    """

    _questions: dict[str, dict[str, Any]] = PrivateAttr()
    _transport: AiDecideTransport = PrivateAttr()
    _threshold: float = PrivateAttr()

    def __init__(
        self,
        name: str,
        questions: dict[str, dict[str, Any]],
        transport: AiDecideTransport,
        threshold: float = 0.5,
    ):
        super().__init__(name=name)
        if not questions:
            raise ValueError("AiDecideScorer requires at least one question.")
        self._questions = questions
        self._transport = transport
        self._threshold = threshold

    def __call__(
        self,
        *,
        inputs: Any = None,
        outputs: Any = None,
        expectations: dict[str, Any] | None = None,
        trace: Any = None,
        **kwargs: Any,
    ) -> Feedback | list[Feedback]:
        state: dict[str, Any] = {"inputs": inputs, "outputs": outputs}
        if expectations is not None:
            state["expectations"] = expectations

        # ai_decide treats a question id as part of the question (an id like
        # "no_competitor_mentions" can override instructions that ask the
        # opposite), so send neutral ids and map answers back to names.
        wire_ids: dict[str, str] = {
            question_id: f"q{index}"
            for index, question_id in enumerate(self._questions, start=1)
        }
        questions: dict[str, dict[str, Any]] = {
            wire_ids[question_id]: {
                **{k: v for k, v in question.items() if k != PASS_IF_KEY},
                "instructions": render_instructions(question["instructions"], state),
            }
            for question_id, question in self._questions.items()
        }

        # Nest a span under the caller's trace (guardrails run inside the agent
        # trace). Outside one -- e.g. scoring in mlflow.genai.evaluate -- skip
        # it rather than log a standalone trace per scorer call.
        span_context: Any = (
            mlflow.start_span(
                name=f"ai_decide:{self.name}", span_type=SpanType.EVALUATOR
            )
            if mlflow.get_current_active_span() is not None
            else nullcontext()
        )
        with span_context as span:
            if span is not None:
                span.set_inputs(
                    {
                        "transport": self._transport.name,
                        "questions": list(self._questions),
                        "state_chars": len(json.dumps(state, default=str)),
                    }
                )
            started: float = time.perf_counter()
            answers: dict[str, dict[str, Any]] = self._transport.decide(
                json.loads(json.dumps(state, default=str)), questions
            )
            latency_ms: int = round((time.perf_counter() - started) * 1000)

            feedbacks: list[Feedback] = []
            for question_id, question in self._questions.items():
                answer: Any = answers.get(wire_ids[question_id])
                if not isinstance(answer, dict):
                    raise AiDecideError(
                        f"ai_decide returned no answer for question '{question_id}'."
                    )
                feedback_name: str = self.name if len(questions) == 1 else question_id
                feedbacks.append(
                    _to_feedback(feedback_name, question, answer, self._threshold)
                )

            if span is not None:
                span.set_outputs(
                    {fb.name: {"value": fb.value, **fb.metadata} for fb in feedbacks}
                )

        logger.debug(
            "ai_decide judged",
            scorer=self.name,
            transport=self._transport.name,
            latency_ms=latency_ms,
            results={fb.name: fb.value for fb in feedbacks},
            pass_probabilities={
                fb.name: fb.metadata.get("ai_decide.pass_probability")
                for fb in feedbacks
                if "ai_decide.pass_probability" in fb.metadata
            },
            threshold=self._threshold,
        )
        return feedbacks[0] if len(feedbacks) == 1 else feedbacks
