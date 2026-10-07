"""
Guardrail middleware for DAO AI agents.

This module provides middleware implementations for applying guardrails
to agent responses, including LLM-based judging, content validation,
and MLflow Scorer-based evaluation.

Guardrails can be powered by:

1. **MLflow judges** (``JudgeScorer``) -- LLM-based evaluation using
   ``mlflow.genai.judges.make_judge``.  The prompt determines what gets
   evaluated (tone, completeness, veracity, or any custom criteria).
2. **MLflow Scorer instances** -- any ``mlflow.genai.scorers.base.Scorer``
   subclass, including built-in ``GuardrailsScorer`` validators from
   ``mlflow.genai.scorers.guardrails`` (e.g. ``ToxicLanguage``,
   ``DetectPII``).
3. **Databricks ai_decide** (``AiDecideScorer``) -- jev-style yes/no
   decisions with calibrated probabilities and a tunable pass threshold.

All scorers are wrapped in ``GuardrailMiddleware`` which handles the
agent lifecycle (retry logic, message extraction, feedback interpretation).

Factory functions are provided for consistent configuration via the
DAO AI middleware factory pattern.
"""

import re
from typing import Any, Literal, Optional

from langchain.agents.middleware import hook_config
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langgraph.runtime import Runtime
from loguru import logger
from mlflow.entities.assessment import Feedback
from mlflow.genai.judges import make_judge
from mlflow.genai.scorers.base import Scorer
from pydantic import PrivateAttr

from dao_ai.config import AiDecideJudgeModel, PromptModel
from dao_ai.judges.ai_decide import AiDecideScorer, noul_question
from dao_ai.messages import last_ai_message, last_human_message
from dao_ai.middleware._prompt_utils import resolve_prompt
from dao_ai.middleware.base import AgentMiddleware
from dao_ai.models import _extract_text_content as _extract_raw_content
from dao_ai.state import AgentState, Context


def _extract_text_content(message: BaseMessage) -> str:
    """Extract text content from a message, handling both string and list formats.

    Delegates to ``dao_ai.models._extract_text_content`` which handles
    JSON-stringified content blocks from ``ChatDatabricks`` and all
    provider-specific reasoning/thinking block formats.
    """
    return _extract_raw_content(message.content)


def _extract_tool_context(messages: list[BaseMessage], max_length: int = 8000) -> str:
    """
    Extract and format all ToolMessage content from the conversation as
    reference context for grounding evaluation.

    Args:
        messages: The full message history
        max_length: Maximum total character length for extracted context.
            Tool outputs are truncated to stay within this budget.

    Returns:
        Formatted string of tool results, or empty string if none found
    """
    tool_contents: list[str] = []
    total_length: int = 0

    for msg in messages:
        if isinstance(msg, ToolMessage) and msg.content:
            tool_name: str = msg.name or "tool"
            content: str = str(msg.content)

            remaining: int = max_length - total_length
            if remaining <= 100:
                break
            if len(content) > remaining:
                content = content[:remaining] + "... [truncated]"

            tool_contents.append(f"[{tool_name}]: {content}")
            total_length += len(content)

    return "\n\n".join(tool_contents)


# Marks the HumanMessage a guardrail adds to request a retry, so later
# evaluations judge the user's actual question rather than the feedback.
_GUARDRAIL_FEEDBACK_KEY: str = "dao_ai_guardrail_feedback"


def _retry_message(content: str) -> HumanMessage:
    """Build the feedback message that asks the model to retry."""
    return HumanMessage(
        content=content, additional_kwargs={_GUARDRAIL_FEEDBACK_KEY: True}
    )


# Marks the AIMessage a guardrail adds when it gives up (retries exhausted or
# the judge errored), so later checks judge the agent's answer, not the notice.
_GUARDRAIL_NOTICE_KEY: str = "dao_ai_guardrail_notice"


def _guardrail_notice(content: str) -> AIMessage:
    """Build the notice a guardrail appends when it ends the turn."""
    return AIMessage(content=content, additional_kwargs={_GUARDRAIL_NOTICE_KEY: True})


def _last_agent_message(messages: list[BaseMessage]) -> AIMessage | None:
    """Return the last AIMessage that is not a guardrail notice."""
    for message in reversed(messages):
        if isinstance(message, AIMessage) and not message.additional_kwargs.get(
            _GUARDRAIL_NOTICE_KEY
        ):
            return message
    return None


def _last_user_message(messages: list[BaseMessage]) -> HumanMessage | None:
    """Return the last HumanMessage that is not guardrail retry feedback."""
    for message in reversed(messages):
        if isinstance(message, HumanMessage) and not message.additional_kwargs.get(
            _GUARDRAIL_FEEDBACK_KEY
        ):
            return message
    return None


def _turn_id(message: HumanMessage) -> str:
    """Identify the user turn a retry budget belongs to."""
    return message.id or str(hash(_extract_text_content(message)))


def _get_thread_id(runtime: Runtime[Context]) -> str:
    """Extract a thread identifier from runtime context for state keying.

    Returns the default key when no Context is bound on the runtime
    (which happens for direct invocations that don't go through
    ``ChatModel.predict`` / ``ResponsesAgent.predict``).
    """
    context: Context | None = runtime.context
    if context is None:
        return "__default__"
    thread_id: str | None = context.thread_id
    if thread_id:
        return thread_id
    return "__default__"


class JudgeScorer(Scorer):
    """MLflow Scorer that wraps ``mlflow.genai.judges.make_judge``.

    Bridges the existing LLM-judge guardrail pattern with the MLflow
    ``Scorer`` interface so that custom prompt-based guardrails and
    built-in ``GuardrailsScorer`` validators share the same middleware.

    Args:
        name: Name identifying this scorer / guardrail.
        instructions: Jinja2 evaluation prompt with ``{{ inputs }}`` and
            ``{{ outputs }}`` template variables.
        model: MLflow model URI for the judge
            (e.g. ``"databricks:/databricks-claude-3-7-sonnet"``).
    """

    _evaluator: Any = PrivateAttr()

    def __init__(self, name: str, instructions: str, model: str):
        super().__init__(name=name)
        self._evaluator = make_judge(
            name=name,
            instructions=instructions,
            feedback_value_type=bool,
            model=model,
        )

    def __call__(
        self,
        *,
        inputs: Any = None,
        outputs: Any = None,
        expectations: dict[str, Any] | None = None,
        trace: Any = None,
        **kwargs: Any,
    ) -> Feedback:
        return self._evaluator(inputs=inputs, outputs=outputs)


def _interpret_feedback(
    result: Feedback | bool | str | int | float,
) -> tuple[bool, str]:
    """Map a Scorer return value to ``(passed, comment)``.

    Handles ``Feedback`` objects (with ``CategoricalRating.YES/NO`` or
    ``bool`` values), raw booleans, strings, and numeric types.
    """
    if isinstance(result, Feedback):
        value = result.value
        comment = result.rationale or ""
    else:
        value, comment = result, ""

    if isinstance(value, bool):
        return value, comment

    if isinstance(value, (int, float)):
        return bool(value), comment

    return str(value).lower() in ("yes", "true", "pass", "safe"), comment


def _as_ai_decide(
    ai_decide: AiDecideJudgeModel | dict[str, Any] | None,
) -> AiDecideJudgeModel | None:
    """Accept ``ai_decide`` settings as a model or a raw YAML dict."""
    if ai_decide is None or isinstance(ai_decide, AiDecideJudgeModel):
        return ai_decide
    return AiDecideJudgeModel.model_validate(ai_decide)


def _require_one_judge(
    guardrail: str, model: str | None, ai_decide: AiDecideJudgeModel | None
) -> None:
    if (model is None) == (ai_decide is None):
        raise ValueError(
            f"The '{guardrail}' guardrail needs exactly one of 'model' "
            "(LLM judge) or 'ai_decide'."
        )


__all__ = [
    "JudgeScorer",
    "GuardrailMiddleware",
    "ContentFilterMiddleware",
    "SafetyGuardrailMiddleware",
    "VeracityGuardrailMiddleware",
    "RelevanceGuardrailMiddleware",
    "ToneGuardrailMiddleware",
    "ConcisenessGuardrailMiddleware",
    "create_guardrail_middleware",
    "create_scorer_guardrail_middleware",
    "create_content_filter_middleware",
    "create_safety_guardrail_middleware",
    "create_veracity_guardrail_middleware",
    "create_relevance_guardrail_middleware",
    "create_tone_guardrail_middleware",
    "create_conciseness_guardrail_middleware",
]


class GuardrailMiddleware(AgentMiddleware[AgentState, Context]):
    """
    Middleware that applies guardrails to agent responses using an MLflow
    ``Scorer``.

    The scorer can be:

    * A ``JudgeScorer`` wrapping ``mlflow.genai.judges.make_judge`` for
      custom prompt-based evaluation (created automatically when *model*
      and *prompt* are supplied).
    * Any ``mlflow.genai.scorers.base.Scorer`` subclass, including
      built-in ``GuardrailsScorer`` validators such as ``ToxicLanguage``
      or ``DetectPII``.
    * An ``AiDecideScorer`` asking a yes/no question through Databricks
      ``ai_decide`` (created automatically when *ai_decide* is supplied).

    Tool context from ``ToolMessage`` objects in the conversation history
    is automatically extracted and included in the ``inputs`` dict, so
    veracity/groundedness prompts can reference it via ``{{ inputs }}``.

    Args:
        name: Name identifying this guardrail.
        scorer: An MLflow ``Scorer`` instance to use for evaluation.
            Mutually exclusive with *model*/*prompt*.
        model: MLflow model string for the judge
            (e.g. ``"databricks:/databricks-claude-3-7-sonnet"``).
            Creates a ``JudgeScorer`` internally.  Requires *prompt*.
        prompt: Evaluation instructions using ``{{ inputs }}`` and
            ``{{ outputs }}`` template variables.  Accepts a plain string
            or a ``PromptModel``.  Requires *model* or *ai_decide*.
        ai_decide: ``ai_decide`` judge settings (model or dict).  Asks
            *decision* -- or *prompt* as a yes/no question -- through
            Databricks ``ai_decide``.  Mutually exclusive with *scorer* and
            *model*.
        decision: ``ai_decide`` question spec used with *ai_decide* instead
            of *prompt* (see ``dao_ai.judges.ai_decide.noul_question``).
        num_retries: Maximum number of retry attempts (default: 3).
        fail_on_error: If True, block responses when the scorer call
            itself errors (e.g. exception, network timeout).  If False
            (default), let responses through on evaluation errors.
        max_context_length: Maximum character length for extracted tool
            context (default: 8000).
        apply_to: When to run this guardrail -- ``"input"`` runs before
            the model (on user messages), ``"output"`` runs after the
            model (on agent responses), ``"both"`` runs in both places
            (default: ``"both"``).

    Raises:
        ValueError: If no judge (*scorer*, *model*/*prompt*, or
            *ai_decide*) is provided, or if more than one is provided.
    """

    def __init__(
        self,
        name: str,
        scorer: Scorer | None = None,
        model: str | None = None,
        prompt: str | PromptModel | None = None,
        ai_decide: AiDecideJudgeModel | dict[str, Any] | None = None,
        decision: dict[str, Any] | None = None,
        num_retries: int = 3,
        fail_on_error: bool = False,
        max_context_length: int = 8000,
        apply_to: Literal["input", "output", "both"] = "both",
    ):
        super().__init__()
        self.guardrail_name = name
        self.num_retries = num_retries
        self.fail_on_error = fail_on_error
        self.max_context_length = max_context_length
        self._apply_to: Literal["input", "output", "both"] = apply_to
        # thread_id -> (turn_id, retries used in that turn)
        self._retry_counts: dict[str, tuple[str, int]] = {}
        ai_decide_model: AiDecideJudgeModel | None = _as_ai_decide(ai_decide)

        if ai_decide_model is not None:
            if scorer is not None or model is not None:
                raise ValueError("Cannot combine 'ai_decide' with 'scorer' or 'model'.")
            if decision is None:
                if prompt is None:
                    raise ValueError(
                        "'ai_decide' requires a 'prompt' or a 'decision' question."
                    )
                decision = noul_question(resolve_prompt(prompt, jinja=True))
            self._scorer = AiDecideScorer(
                name=name,
                questions={name: decision},
                transport=ai_decide_model.as_transport(),
                threshold=ai_decide_model.threshold,
            )
            self.model_endpoint = None
            self.prompt = decision["instructions"]
        elif scorer is not None:
            if model is not None or prompt is not None:
                raise ValueError(
                    "Cannot specify both 'scorer' and 'model'/'prompt'. "
                    "Provide either a Scorer instance or model+prompt for "
                    "a JudgeScorer."
                )
            self._scorer: Scorer = scorer
            self.model_endpoint: str | None = None
            self.prompt: str | None = None
        elif model is not None and prompt is not None:
            resolved_prompt: str = resolve_prompt(prompt, jinja=True)
            self._scorer = JudgeScorer(
                name=name,
                instructions=resolved_prompt,
                model=model,
            )
            self.model_endpoint = model
            self.prompt = resolved_prompt
        else:
            raise ValueError(
                "Either 'scorer' or both 'model' and 'prompt' must be "
                "provided to GuardrailMiddleware."
            )

    @property
    def name(self) -> str:
        """Return the guardrail name for middleware identification."""
        return self.guardrail_name

    def _get_retry_count(self, thread_id: str, turn_id: str | None = None) -> int:
        """Get the retries used for a thread in *turn_id* (or its latest turn)."""
        turn, count = self._retry_counts.get(thread_id, ("", 0))
        return count if turn_id is None or turn == turn_id else 0

    def _increment_retry_count(self, thread_id: str, turn_id: str = "") -> int:
        """Increment and return the retries used for a thread in this turn.

        Counts are scoped to the user turn and are not reset when the
        guardrail passes, so guardrails with conflicting criteria cannot
        keep re-triggering each other within one turn.
        """
        count: int = self._get_retry_count(thread_id, turn_id) + 1
        self._retry_counts[thread_id] = (turn_id, count)
        return count

    def _reset_retry_count(self, thread_id: str) -> None:
        """Reset retry count for a thread."""
        self._retry_counts.pop(thread_id, None)

    @hook_config(can_jump_to=["end"])
    def before_model(
        self, state: AgentState, runtime: Runtime[Context]
    ) -> dict[str, Any] | None:
        """Evaluate the user's input before the model runs.

        Only active when ``apply_to`` is ``"input"`` or ``"both"``.
        On failure the conversation is immediately ended with a block
        message (no retries).
        """
        if self._apply_to == "output":
            return None

        messages: list[BaseMessage] = state.get("messages", [])
        if not messages:
            return None

        human_message: HumanMessage | None = _last_user_message(messages)
        if not human_message:
            return None

        human_content: str = _extract_text_content(human_message)
        if not human_content:
            return None

        logger.debug(
            "Evaluating input with guardrail",
            guardrail_name=self.guardrail_name,
            input_length=len(human_content),
            apply_to=self._apply_to,
        )

        try:
            result = self._scorer(
                inputs={"query": human_content},
                outputs={"response": human_content},
            )
            passed, comment = _interpret_feedback(result)
        except Exception as e:
            logger.error(
                "Guardrail input check failed",
                guardrail_name=self.guardrail_name,
                error=str(e),
            )
            if self.fail_on_error:
                block_message = (
                    f"⚠️ **Input Check Error**\n\n"
                    f"The '{self.guardrail_name}' input check encountered an error "
                    f"and could not validate the request.\n\n"
                    f"**Error:** {e}"
                )
                return {
                    "messages": [AIMessage(content=block_message)],
                    "jump_to": "end",
                }
            logger.warning(
                "Guardrail input evaluation error - letting request through",
                guardrail_name=self.guardrail_name,
            )
            return None

        if passed:
            logger.debug(
                "Input approved by guardrail",
                guardrail_name=self.guardrail_name,
                comment=comment,
            )
            return None

        logger.warning(
            "Guardrail blocked input",
            guardrail_name=self.guardrail_name,
            comment=comment,
        )
        block_message = (
            f"⚠️ **Input Blocked**\n\n"
            f"Your message did not pass the '{self.guardrail_name}' safety check.\n\n"
            f"**Reason:** {comment}\n\n"
            f"Please rephrase your request."
        )
        return {
            "messages": [AIMessage(content=block_message)],
            "jump_to": "end",
        }

    @hook_config(can_jump_to=["model", "end"])
    def after_model(
        self, state: AgentState, runtime: Runtime[Context]
    ) -> dict[str, Any] | None:
        """
        Evaluate the model's response using an MLflow judge.

        If the response doesn't meet the guardrail criteria, returns a
        HumanMessage with feedback to trigger a retry.

        Tool context from ToolMessage objects in the conversation is
        automatically extracted and included in the inputs dict for the
        judge, enabling veracity/groundedness prompts.

        Only active when ``apply_to`` is ``"output"`` or ``"both"``.
        """
        if self._apply_to == "input":
            return None

        messages: list[BaseMessage] = state.get("messages", [])

        if not messages:
            return None

        ai_message: AIMessage | None = last_ai_message(messages)
        human_message: HumanMessage | None = _last_user_message(messages)

        if not ai_message or not human_message:
            return None

        # Skip evaluation if the AI message has tool calls (not the final response yet)
        if ai_message.tool_calls:
            logger.trace(
                "Guardrail skipping evaluation - AI message contains tool calls",
                guardrail_name=self.guardrail_name,
            )
            return None

        # Skip evaluation if the AI message has no content to evaluate
        if not ai_message.content:
            logger.trace(
                "Guardrail skipping evaluation - AI message has no content",
                guardrail_name=self.guardrail_name,
            )
            return None

        thread_id: str = _get_thread_id(runtime)

        # Extract text content from messages (handles both string and structured content)
        human_content: str = _extract_text_content(human_message)
        ai_content: str = _extract_text_content(ai_message)

        # Extract tool context for grounding evaluation
        tool_context: str = _extract_tool_context(
            messages, max_length=self.max_context_length
        )

        logger.debug(
            "Evaluating response with guardrail",
            guardrail_name=self.guardrail_name,
            input_length=len(human_content),
            output_length=len(ai_content),
            tool_context_length=len(tool_context),
        )

        try:
            result = self._scorer(
                inputs={"query": human_content, "context": tool_context},
                outputs={"response": ai_content},
            )
            passed, comment = _interpret_feedback(result)
        except Exception as e:
            logger.error(
                "Guardrail judge call failed",
                guardrail_name=self.guardrail_name,
                error=str(e),
            )
            if self.fail_on_error:
                self._reset_retry_count(thread_id)
                failure_message = (
                    f"⚠️ **Quality Check Error**\n\n"
                    f"The '{self.guardrail_name}' quality check encountered an error "
                    f"and could not validate the response.\n\n"
                    f"**Error:** {e}"
                )
                # End the turn so later guardrails don't judge this notice.
                return {
                    "messages": [_guardrail_notice(failure_message)],
                    "jump_to": "end",
                }
            else:
                logger.warning(
                    "Guardrail evaluation error - letting response through",
                    guardrail_name=self.guardrail_name,
                )
                self._reset_retry_count(thread_id)
                return None

        if passed:
            logger.debug(
                "Response approved by guardrail",
                guardrail_name=self.guardrail_name,
                comment=comment,
            )
            return None
        else:
            retry_count: int = self._increment_retry_count(
                thread_id, _turn_id(human_message)
            )

            if retry_count >= self.num_retries:
                logger.warning(
                    "Guardrail failed - max retries reached",
                    guardrail_name=self.guardrail_name,
                    retry_count=retry_count,
                    max_retries=self.num_retries,
                    critique=comment,
                )
                self._reset_retry_count(thread_id)

                # Add system message to inform user of guardrail failure
                failure_message = (
                    f"⚠️ **Quality Check Failed**\n\n"
                    f"The response did not meet the '{self.guardrail_name}' quality standards "
                    f"after {self.num_retries} attempts.\n\n"
                    f"**Issue:** {comment}\n\n"
                    f"The best available response has been provided, but please be aware it may not fully meet quality expectations."
                )
                # End the turn so later guardrails don't judge this notice.
                return {
                    "messages": [_guardrail_notice(failure_message)],
                    "jump_to": "end",
                }

            logger.warning(
                "Guardrail requested improvements",
                guardrail_name=self.guardrail_name,
                retry=retry_count,
                max_retries=self.num_retries,
                critique=comment,
            )

            human_text: str = _extract_text_content(human_message)
            content: str = "\n".join([human_text, comment])
            # Re-run the model on the feedback. Without an explicit jump the
            # agent loop ends here (the last AIMessage has no tool calls) and
            # the failing response is returned as-is.
            return {"messages": [_retry_message(content)], "jump_to": "model"}


class ContentFilterMiddleware(AgentMiddleware[AgentState, Context]):
    """
    Middleware that filters responses containing banned keywords.

    This is a deterministic guardrail that blocks responses containing
    specified keywords. Keywords are compiled into a single regex pattern
    for efficient matching.

    Args:
        banned_keywords: List of keywords to block
        block_message: Message to return when content is blocked
    """

    def __init__(
        self,
        banned_keywords: list[str],
        block_message: str = "I cannot provide that response. Please rephrase your request.",
    ):
        super().__init__()
        self.banned_keywords = [kw.lower() for kw in banned_keywords]
        self.block_message = block_message
        # Compile keywords into a single regex for efficient matching
        escaped: list[str] = [re.escape(kw) for kw in self.banned_keywords]
        self._pattern: re.Pattern[str] = re.compile("|".join(escaped), re.IGNORECASE)

    @hook_config(can_jump_to=["end"])
    def before_agent(
        self, state: AgentState, runtime: Runtime[Context]
    ) -> dict[str, Any] | None:
        """Block requests containing banned keywords."""
        messages: list[BaseMessage] = state.get("messages", [])

        if not messages:
            return None

        human_msg: HumanMessage | None = last_human_message(messages)
        if not human_msg:
            return None

        content: str = _extract_text_content(human_msg)

        match: re.Match[str] | None = self._pattern.search(content)
        if match:
            logger.warning(
                "Content filter blocked request",
                keyword=match.group(),
            )
            return {
                "messages": [AIMessage(content=self.block_message)],
                "jump_to": "end",
            }

        return None

    @hook_config(can_jump_to=["end"])
    def after_model(
        self, state: AgentState, runtime: Runtime[Context]
    ) -> dict[str, Any] | None:
        """Block responses containing banned keywords."""
        messages: list[BaseMessage] = state.get("messages", [])

        if not messages:
            return None

        ai_msg: AIMessage | None = last_ai_message(messages)
        if not ai_msg:
            return None

        content: str = _extract_text_content(ai_msg)

        match: re.Match[str] | None = self._pattern.search(content)
        if match:
            logger.warning("Content filter blocked response", keyword=match.group())
            # Return a new message instead of mutating the existing one
            return {
                "messages": [AIMessage(content=self.block_message)],
                "jump_to": "end",
            }

        return None


class SafetyGuardrailMiddleware(AgentMiddleware[AgentState, Context]):
    """
    Model-based safety guardrail middleware.

    Uses an MLflow judge to evaluate whether responses are safe and appropriate.
    This is applied after the agent completes to validate the final output.

    Args:
        safety_model: MLflow model string for the safety judge
            (e.g. ``"databricks:/databricks-claude-3-7-sonnet"``).
            Defaults to ``"openai:/gpt-4o-mini"`` if neither it nor
            *ai_decide* is provided.
        fail_on_error: If True, block responses when the judge call
            itself errors.  If False (default), let responses through
            on evaluation errors.
        ai_decide: Judge safety with Databricks ``ai_decide`` instead of
            an LLM.  Mutually exclusive with *safety_model*.
    """

    def __init__(
        self,
        safety_model: Optional[str] = None,
        fail_on_error: bool = False,
        ai_decide: AiDecideJudgeModel | dict[str, Any] | None = None,
    ):
        super().__init__()
        self.fail_on_error = fail_on_error
        ai_decide_model: AiDecideJudgeModel | None = _as_ai_decide(ai_decide)
        self._ai_decide_scorer: AiDecideScorer | None = None
        if ai_decide_model is not None:
            if safety_model is not None:
                raise ValueError(
                    "Cannot combine 'safety_model' with 'ai_decide' in the safety guardrail."
                )
            self.model_endpoint: str | None = None
            self._ai_decide_scorer = AiDecideScorer(
                name="safety_guardrail",
                questions={"safety_guardrail": SAFETY_DECISION},
                transport=ai_decide_model.as_transport(),
                threshold=ai_decide_model.threshold,
            )
            return
        self.model_endpoint = safety_model or "openai:/gpt-4o-mini"
        self._safety_judge = make_judge(
            name="safety_guardrail",
            instructions=(
                "Evaluate if the following response is safe and appropriate.\n\n"
                "Response: {{ outputs }}\n\n"
                "Check for:\n"
                "- Harmful, dangerous, or illegal content\n"
                "- Personally identifiable information exposure\n"
                "- Hate speech, discrimination, or harassment\n"
                "- Instructions for dangerous activities\n\n"
                "Rate as 'safe' if the response is appropriate, 'unsafe' if it contains "
                "any of the above issues."
            ),
            feedback_value_type=Literal["safe", "unsafe"],
            model=self.model_endpoint,
        )

    @hook_config(can_jump_to=["end"])
    def after_agent(
        self, state: AgentState, runtime: Runtime[Context]
    ) -> dict[str, Any] | None:
        """Evaluate response safety before returning to user."""
        messages: list[BaseMessage] = state.get("messages", [])

        if not messages:
            return None

        ai_msg: AIMessage | None = _last_agent_message(messages)
        if not ai_msg:
            return None

        ai_content: str = _extract_text_content(ai_msg)

        try:
            if self._ai_decide_scorer is not None:
                passed, _ = _interpret_feedback(
                    self._ai_decide_scorer(outputs={"response": ai_content})
                )
                is_unsafe: bool = not passed
            else:
                feedback = self._safety_judge(
                    outputs={"response": ai_content},
                )
                is_unsafe = feedback.value == "unsafe"
        except Exception as e:
            logger.error(
                "Safety guardrail judge call failed",
                error=str(e),
            )
            if self.fail_on_error:
                return {
                    "messages": [
                        AIMessage(
                            content="I cannot provide that response due to a safety check error. Please try again."
                        )
                    ],
                    "jump_to": "end",
                }
            else:
                logger.warning(
                    "Safety guardrail evaluation error - letting response through"
                )
                return None

        if is_unsafe:
            logger.warning("Safety guardrail blocked unsafe response")
            return {
                "messages": [
                    AIMessage(
                        content="I cannot provide that response. Please rephrase your request."
                    )
                ],
                "jump_to": "end",
            }

        return None


# =============================================================================
# Built-in Prompt Constants for Specialized Guardrails
# =============================================================================

VERACITY_INSTRUCTIONS = """\
Evaluate whether the agent's response is grounded in and faithful to the \
provided tool/retrieval context.

User query: {{ inputs }}
Agent response: {{ outputs }}

Carefully check:
1. **Fabrication** -- Does the response include claims, facts, numbers, or \
details that are NOT supported by the tool context?
2. **Misrepresentation** -- Does the response distort, exaggerate, or \
inaccurately paraphrase information from the tool context?
3. **Omission** -- Does the response omit critical information from the \
tool context that would change the meaning of the answer?
4. **Attribution** -- When the response cites specific data, does it \
accurately reflect what the tool actually returned?

Rate as true if ALL claims in the response are supported by the tool context. \
Rate as false if ANY claim is fabricated, distorted, or unsupported. \
Provide specific feedback identifying which claims are not grounded."""

RELEVANCE_INSTRUCTIONS = """\
Evaluate whether the agent's response is relevant to and directly addresses \
the user's query.

User query: {{ inputs }}
Agent response: {{ outputs }}

Check for:
1. **Direct relevance** -- Does the response answer the specific question \
that was asked?
2. **Topic drift** -- Does the response wander off-topic or discuss \
unrelated subjects?
3. **Question coverage** -- If the user asked multiple questions or a \
multi-part question, does the response address all parts?
4. **Appropriate scope** -- Is the response appropriately scoped to the \
question (not too broad, not too narrow)?

Rate as true if the response directly and fully addresses the user's query. \
Rate as false if the response is off-topic, only partially relevant, or \
answers a different question than what was asked. Provide specific feedback."""

TONE_PROFILES: dict[str, str] = {
    "professional": """\
Evaluate whether the response maintains a professional tone appropriate \
for business or customer-facing communication.

User query: {{ inputs }}
Agent response: {{ outputs }}

The response should:
- Use formal, polished language without slang, colloquialisms, or \
excessive informality
- Be respectful, courteous, and service-oriented
- Use clear, precise wording without unnecessary filler
- Maintain a calm, confident, and helpful demeanor
- Avoid sarcasm, humor at the user's expense, or dismissiveness

Rate as true if the response is professional. Rate as false if it \
contains unprofessional language or tone. Provide specific feedback.""",
    "casual": """\
Evaluate whether the response maintains a friendly, casual tone.

User query: {{ inputs }}
Agent response: {{ outputs }}

The response should:
- Use approachable, conversational language
- Feel natural and not overly stiff or robotic
- Be warm and personable without being unprofessional
- Avoid overly formal or bureaucratic phrasing
- Still be clear and helpful

Rate as true if the response is appropriately casual. Rate as false if \
it is too formal or too informal. Provide specific feedback.""",
    "technical": """\
Evaluate whether the response maintains an appropriate technical tone.

User query: {{ inputs }}
Agent response: {{ outputs }}

The response should:
- Use precise, domain-appropriate technical terminology
- Be structured and logically organized
- Provide sufficient technical detail for the audience
- Avoid unnecessary simplification that loses accuracy
- Include relevant code, examples, or references where appropriate

Rate as true if the response has appropriate technical depth and accuracy. \
Rate as false if it is too shallow, too jargon-heavy, or imprecise. \
Provide specific feedback.""",
    "empathetic": """\
Evaluate whether the response maintains an empathetic, supportive tone.

User query: {{ inputs }}
Agent response: {{ outputs }}

The response should:
- Acknowledge the user's situation, feelings, or frustration
- Show understanding before providing solutions
- Use patient, compassionate language
- Avoid dismissive or minimizing phrases
- Offer reassurance and clear next steps

Rate as true if the response demonstrates appropriate empathy. Rate as \
false if it is cold, dismissive, or fails to acknowledge the user's \
concerns. Provide specific feedback.""",
    "concise": """\
Evaluate whether the response maintains a concise, to-the-point tone.

User query: {{ inputs }}
Agent response: {{ outputs }}

The response should:
- Get to the point quickly without unnecessary preamble
- Use short, clear sentences
- Avoid repetition and filler phrases
- Present information efficiently
- Still be complete enough to answer the question

Rate as true if the response is appropriately concise. Rate as false if \
it is verbose, repetitive, or padded with unnecessary content. Provide \
specific feedback.""",
}

CONCISENESS_INSTRUCTIONS = """\
Evaluate whether the response is appropriately concise -- not overly verbose \
and not unnecessarily brief.

User query: {{ inputs }}
Agent response: {{ outputs }}

Check for:
1. **Unnecessary verbosity** -- Does the response contain filler phrases, \
excessive hedging, repetitive statements, or overly long introductions?
2. **Information density** -- Is the useful information-to-word ratio \
reasonable?
3. **Repetition** -- Does the response repeat the same point in different \
words?
4. **Appropriate brevity** -- Is the response long enough to fully answer \
the question but short enough to respect the user's time?

Rate as true if the response is well-balanced in length and information \
density. Rate as false if it is too verbose, repetitive, or padded. \
Provide specific feedback on what to cut or tighten."""


# =============================================================================
# Built-in ai_decide (jev-style) Questions for Specialized Guardrails
# =============================================================================
#
# ai_decide answers short yes/no questions with a probability and no
# rationale, so these are phrased as single questions with pass/fail criteria
# rather than reusing the long LLM-judge rubrics above. ai_decide detects that
# something is present more reliably than it confirms an absence, so where it
# measured better against known-good/bad responses a question asks whether a
# violation is present (pass_if="no"); the rest ask whether the response passes.
# The guardrail state is {"inputs": {"query", "context"}, "outputs":
# {"response"}}; ai_decide reads it through ``state.*`` references.

VERACITY_DECISION: dict[str, Any] = noul_question(
    "Is every claim in state.outputs.response supported by the tool results "
    "in state.inputs.context, with no fabricated, distorted, or unsupported "
    "facts, numbers, or details?",
    pass_when="Every claim in the response is supported by the tool results.",
    fail_when="The response includes claims, facts, or numbers that the tool "
    "results do not support. Answer only from the tool results.",
)

RELEVANCE_DECISION: dict[str, Any] = noul_question(
    "Does state.outputs.response directly answer state.inputs.query, stay on "
    "topic, and cover every part of the question?",
    pass_when="The response directly and fully answers the user's question.",
    fail_when="The response is off-topic, only partially relevant, or misses "
    "part of the user's question. Answer exactly what was asked.",
)

TONE_DECISIONS: dict[str, dict[str, Any]] = {
    "professional": noul_question(
        "Does state.outputs.response use slang, sarcasm, rudeness, or casual or "
        "dismissive language that would be unprofessional with a customer?",
        pass_when="The response is professional and courteous.",
        fail_when="The response uses unprofessional, informal, or dismissive "
        "language. Rewrite it in a polished, professional tone.",
        pass_if="no",
    ),
    "casual": noul_question(
        "Is state.outputs.response written in a friendly, conversational tone "
        "that is warm and approachable without being stiff or bureaucratic?",
        pass_when="The response is friendly and conversational.",
        fail_when="The response is too formal, stiff, or robotic. Rewrite it in "
        "a friendly, conversational tone.",
    ),
    "technical": noul_question(
        "Is state.outputs.response technically precise, logically organized, "
        "and detailed enough for a technical audience?",
        pass_when="The response is technically precise and well organized.",
        fail_when="The response is imprecise, too shallow, or poorly organized "
        "for a technical audience. Add precise technical detail.",
    ),
    "empathetic": noul_question(
        "Does state.outputs.response acknowledge the user's situation or "
        "feelings in state.inputs.query and respond with patient, supportive "
        "language before offering next steps?",
        pass_when="The response is empathetic and supportive.",
        fail_when="The response is cold or dismissive. Acknowledge the user's "
        "situation and respond supportively.",
    ),
    "concise": noul_question(
        "Does state.outputs.response include preamble, repetition, or filler "
        "instead of getting straight to the point?",
        pass_when="The response is concise and complete.",
        fail_when="The response is verbose, repetitive, or padded. Tighten it.",
        pass_if="no",
    ),
}

CONCISENESS_DECISION: dict[str, Any] = noul_question(
    "Does state.outputs.response contain filler, repetition, needless "
    "preamble, or padding that could be cut without losing any information?",
    pass_when="The response is well balanced in length and information density.",
    fail_when="The response is verbose, repetitive, or padded. Cut filler and "
    "repetition while keeping the answer complete.",
    pass_if="no",
)

SAFETY_DECISION: dict[str, Any] = noul_question(
    "Is state.outputs.response safe and appropriate: free of harmful, "
    "dangerous, or illegal content, exposed personal information, hate "
    "speech, harassment, and instructions for dangerous activities?",
    pass_when="The response is safe and appropriate.",
    fail_when="The response contains harmful, dangerous, illegal, hateful, "
    "or privacy-violating content.",
)


# =============================================================================
# Specialized Guardrail Middleware Classes
# =============================================================================


class VeracityGuardrailMiddleware(GuardrailMiddleware):
    """
    Specialized guardrail that checks if responses are grounded in
    tool/retrieval context.

    Automatically extracts tool context from ``ToolMessage`` objects in the
    conversation and evaluates whether the agent's response is faithful to
    that data. **Skips evaluation when no tool context is present** (there
    is nothing to ground against).

    No prompt is needed -- the built-in veracity evaluation prompt is used.

    Args:
        model: MLflow model string for the judge
        num_retries: Maximum retry attempts (default: 2)
        fail_on_error: Block responses on evaluation error (default: False)
        max_context_length: Max chars for extracted tool context (default: 8000)
        ai_decide: Judge with Databricks ``ai_decide`` (jev-style yes/no)
            instead of an LLM.  Mutually exclusive with *model*.
    """

    def __init__(
        self,
        model: str | None = None,
        num_retries: int = 2,
        fail_on_error: bool = False,
        max_context_length: int = 8000,
        ai_decide: AiDecideJudgeModel | dict[str, Any] | None = None,
    ):
        ai_decide_model: AiDecideJudgeModel | None = _as_ai_decide(ai_decide)
        _require_one_judge("veracity", model, ai_decide_model)
        super().__init__(
            name="veracity",
            model=model,
            prompt=None if ai_decide_model else VERACITY_INSTRUCTIONS,
            ai_decide=ai_decide_model,
            decision=VERACITY_DECISION,
            num_retries=num_retries,
            fail_on_error=fail_on_error,
            max_context_length=max_context_length,
            # Grounding is only meaningful on the agent's response. The base class
            # defaults to "both", whose before_model input check evaluates the user
            # query against itself and wrongly blocks ordinary turns (greetings,
            # clarifications). Response-quality guardrails must be output-only.
            apply_to="output",
        )

    @hook_config(can_jump_to=["model", "end"])
    def after_model(
        self, state: AgentState, runtime: Runtime[Context]
    ) -> dict[str, Any] | None:
        """
        Evaluate response veracity against tool context.

        Skips evaluation when no tool context is present in the
        conversation -- there is nothing to ground against.
        """
        messages: list[BaseMessage] = state.get("messages", [])

        # Short-circuit: skip if there is no tool context to ground against
        tool_context: str = _extract_tool_context(
            messages, max_length=self.max_context_length
        )
        if not tool_context:
            logger.trace(
                "Veracity guardrail skipping - no tool context to ground against",
                guardrail_name=self.guardrail_name,
            )
            return None

        # Delegate to the parent class for full evaluation
        return super().after_model(state, runtime)


class RelevanceGuardrailMiddleware(GuardrailMiddleware):
    """
    Specialized guardrail that checks if responses are relevant to
    the user's query.

    Evaluates whether the response directly addresses the question,
    detects topic drift, and checks multi-part question coverage.

    No prompt is needed -- the built-in relevance evaluation prompt is used.

    Args:
        model: MLflow model string for the judge
        num_retries: Maximum retry attempts (default: 2)
        fail_on_error: Block responses on evaluation error (default: False)
        ai_decide: Judge with Databricks ``ai_decide`` (jev-style yes/no)
            instead of an LLM.  Mutually exclusive with *model*.
    """

    def __init__(
        self,
        model: str | None = None,
        num_retries: int = 2,
        fail_on_error: bool = False,
        ai_decide: AiDecideJudgeModel | dict[str, Any] | None = None,
    ):
        ai_decide_model: AiDecideJudgeModel | None = _as_ai_decide(ai_decide)
        _require_one_judge("relevance", model, ai_decide_model)
        super().__init__(
            name="relevance",
            model=model,
            prompt=None if ai_decide_model else RELEVANCE_INSTRUCTIONS,
            ai_decide=ai_decide_model,
            decision=RELEVANCE_DECISION,
            num_retries=num_retries,
            fail_on_error=fail_on_error,
            # Response-quality guardrail: evaluate the answer, not the input. See
            # VeracityGuardrailMiddleware for why "both" is wrong here.
            apply_to="output",
        )


class ToneGuardrailMiddleware(GuardrailMiddleware):
    """
    Specialized guardrail that validates response tone against a
    configurable profile.

    Provides preset tone profiles (``professional``, ``casual``,
    ``technical``, ``empathetic``, ``concise``) with built-in evaluation
    prompts. Users can also supply custom tone guidelines.

    No prompt is needed -- select a profile and the built-in prompt is used.

    Args:
        model: MLflow model string for the judge
        tone: Preset tone profile name (default: ``"professional"``)
        custom_guidelines: Custom tone guidelines. If provided,
            overrides the preset tone profile. Accepts a plain string
            or a ``PromptModel`` from the prompt registry.
        num_retries: Maximum retry attempts (default: 2)
        fail_on_error: Block responses on evaluation error (default: False)
        ai_decide: Judge with Databricks ``ai_decide`` (jev-style yes/no)
            instead of an LLM.  Mutually exclusive with *model*.

    Raises:
        ValueError: If ``tone`` is not a recognized profile and no
            ``custom_guidelines`` are provided.
    """

    AVAILABLE_PROFILES: frozenset[str] = frozenset(TONE_PROFILES.keys())

    def __init__(
        self,
        model: str | None = None,
        tone: str = "professional",
        custom_guidelines: str | PromptModel | None = None,
        num_retries: int = 2,
        fail_on_error: bool = False,
        ai_decide: AiDecideJudgeModel | dict[str, Any] | None = None,
    ):
        ai_decide_model: AiDecideJudgeModel | None = _as_ai_decide(ai_decide)
        _require_one_judge(f"tone_{tone}", model, ai_decide_model)
        if custom_guidelines:
            prompt: str | PromptModel = custom_guidelines
        elif tone in TONE_PROFILES:
            prompt = TONE_PROFILES[tone]
        else:
            raise ValueError(
                f"Unknown tone profile '{tone}'. "
                f"Available profiles: {', '.join(sorted(TONE_PROFILES.keys()))}. "
                f"Or provide custom_guidelines."
            )

        self.tone = tone

        # Custom guidelines are asked as-is; presets use the jev question.
        decision: dict[str, Any] | None = (
            TONE_DECISIONS[tone] if ai_decide_model and not custom_guidelines else None
        )

        super().__init__(
            name=f"tone_{tone}",
            model=model,
            prompt=prompt,
            ai_decide=ai_decide_model,
            decision=decision,
            num_retries=num_retries,
            fail_on_error=fail_on_error,
            # Response-quality guardrail: evaluate the answer, not the input.
            apply_to="output",
        )


class ConcisenessGuardrailMiddleware(GuardrailMiddleware):
    """
    Hybrid deterministic + LLM guardrail for response length and verbosity.

    Performs a fast deterministic length check first (no LLM cost).
    If the response passes length checks and ``check_verbosity`` is enabled,
    an LLM judge evaluates whether the response is appropriately concise.

    Args:
        model: MLflow model string for the judge
        max_length: Maximum response character length (default: 3000)
        min_length: Minimum response character length (default: 20)
        check_verbosity: Enable LLM verbosity evaluation after length
            check passes (default: True)
        num_retries: Maximum retry attempts (default: 2)
        fail_on_error: Block responses on evaluation error (default: False)
        ai_decide: Judge with Databricks ``ai_decide`` (jev-style yes/no)
            instead of an LLM.  Mutually exclusive with *model*.
    """

    def __init__(
        self,
        model: str | None = None,
        max_length: int = 3000,
        min_length: int = 20,
        check_verbosity: bool = True,
        num_retries: int = 2,
        fail_on_error: bool = False,
        ai_decide: AiDecideJudgeModel | dict[str, Any] | None = None,
    ):
        ai_decide_model: AiDecideJudgeModel | None = _as_ai_decide(ai_decide)
        _require_one_judge("conciseness", model, ai_decide_model)
        super().__init__(
            name="conciseness",
            model=model,
            prompt=None if ai_decide_model else CONCISENESS_INSTRUCTIONS,
            ai_decide=ai_decide_model,
            decision=CONCISENESS_DECISION,
            num_retries=num_retries,
            fail_on_error=fail_on_error,
            # Response-quality guardrail: evaluate the answer, not the input.
            apply_to="output",
        )
        self.max_length = max_length
        self.min_length = min_length
        self.check_verbosity = check_verbosity

    @hook_config(can_jump_to=["model", "end"])
    def after_model(
        self, state: AgentState, runtime: Runtime[Context]
    ) -> dict[str, Any] | None:
        """
        Hybrid length + verbosity check.

        Deterministic length check runs first. If it fails, retry feedback
        is returned immediately without an LLM call. If length passes and
        ``check_verbosity`` is True, the parent LLM judge evaluates conciseness.
        """
        messages: list[BaseMessage] = state.get("messages", [])

        if not messages:
            return None

        ai_message: AIMessage | None = last_ai_message(messages)
        human_message: HumanMessage | None = _last_user_message(messages)

        if not ai_message or not human_message:
            return None

        # Skip evaluation if the AI message has tool calls
        if ai_message.tool_calls:
            return None

        # Skip evaluation if the AI message has no content
        if not ai_message.content:
            return None

        ai_content: str = _extract_text_content(ai_message)
        content_length: int = len(ai_content)
        thread_id: str = _get_thread_id(runtime)

        # --- Deterministic length check (fast, no LLM) ---
        if content_length > self.max_length:
            retry_count: int = self._increment_retry_count(
                thread_id, _turn_id(human_message)
            )

            if retry_count >= self.num_retries:
                logger.warning(
                    "Conciseness guardrail failed - max retries reached (too long)",
                    guardrail_name=self.guardrail_name,
                    content_length=content_length,
                    max_length=self.max_length,
                )
                self._reset_retry_count(thread_id)
                failure_message = (
                    f"⚠️ **Quality Check Failed**\n\n"
                    f"The response exceeded the maximum length of {self.max_length} characters "
                    f"after {self.num_retries} attempts."
                )
                # End the turn so later guardrails don't judge this notice.
                return {
                    "messages": [_guardrail_notice(failure_message)],
                    "jump_to": "end",
                }

            logger.warning(
                "Conciseness guardrail - response too long",
                guardrail_name=self.guardrail_name,
                content_length=content_length,
                max_length=self.max_length,
                retry=retry_count,
            )
            human_text: str = _extract_text_content(human_message)
            feedback: str = (
                f"Your response is {content_length} characters, which exceeds the "
                f"maximum of {self.max_length}. Please provide a more concise response."
            )
            return {
                "messages": [_retry_message("\n".join([human_text, feedback]))],
                "jump_to": "model",
            }

        if content_length < self.min_length:
            retry_count = self._increment_retry_count(
                thread_id, _turn_id(human_message)
            )

            if retry_count >= self.num_retries:
                logger.warning(
                    "Conciseness guardrail failed - max retries reached (too short)",
                    guardrail_name=self.guardrail_name,
                    content_length=content_length,
                    min_length=self.min_length,
                )
                self._reset_retry_count(thread_id)
                failure_message = (
                    f"⚠️ **Quality Check Failed**\n\n"
                    f"The response was shorter than the minimum of {self.min_length} characters "
                    f"after {self.num_retries} attempts."
                )
                # End the turn so later guardrails don't judge this notice.
                return {
                    "messages": [_guardrail_notice(failure_message)],
                    "jump_to": "end",
                }

            logger.warning(
                "Conciseness guardrail - response too short",
                guardrail_name=self.guardrail_name,
                content_length=content_length,
                min_length=self.min_length,
                retry=retry_count,
            )
            human_text = _extract_text_content(human_message)
            feedback = (
                f"Your response is only {content_length} characters, which is below "
                f"the minimum of {self.min_length}. Please provide a more complete response."
            )
            return {
                "messages": [_retry_message("\n".join([human_text, feedback]))],
                "jump_to": "model",
            }

        # --- LLM verbosity check (optional) ---
        if self.check_verbosity:
            return super().after_model(state, runtime)

        # Length passes and verbosity check disabled
        return None


# =============================================================================
# Factory Functions
# =============================================================================


def create_guardrail_middleware(
    name: str,
    model: str | None = None,
    prompt: str | PromptModel | None = None,
    num_retries: int = 3,
    fail_on_error: bool = False,
    max_context_length: int = 8000,
    apply_to: Literal["input", "output", "both"] = "output",
    ai_decide: AiDecideJudgeModel | dict[str, Any] | None = None,
) -> GuardrailMiddleware:
    """
    Create a GuardrailMiddleware instance.

    Factory function for creating LLM-based guardrail middleware that evaluates
    agent responses against specified criteria using an MLflow judge.

    The prompt determines the type of evaluation. Tool context from the
    conversation is automatically included in the inputs dict, enabling
    veracity/groundedness prompts that reference ``{{ inputs }}``.

    Args:
        name: Name identifying this guardrail
        model: MLflow model string for the judge (e.g. ``"databricks:/databricks-claude-3-7-sonnet"``)
        prompt: The evaluation instructions using ``{{ inputs }}`` and ``{{ outputs }}`` template variables.
            Accepts a plain string or a ``PromptModel`` from the prompt registry.
        num_retries: Maximum number of retry attempts (default: 3)
        fail_on_error: If True, block responses when the judge call errors (default: False)
        max_context_length: Maximum character length for extracted tool context (default: 8000)
        apply_to: When to run -- ``"output"`` (default), ``"input"``, or ``"both"``.
            Defaults to ``"output"`` because an LLM-judge before_model check scores
            the user query against itself and wrongly blocks ordinary turns; pass
            ``"input"``/``"both"`` only for guardrails meant to inspect user input.
        ai_decide: Judge with Databricks ``ai_decide`` (jev-style yes/no)
            instead of an LLM; *prompt* is asked as a yes/no question that
            is true when the response passes.  Accepts ``AiDecideJudgeModel``
            fields as a dict.  Mutually exclusive with *model*.

    Returns:
        GuardrailMiddleware configured with the specified parameters

    Example:
        middleware = create_guardrail_middleware(
            name="tone_check",
            model="databricks:/databricks-claude-3-7-sonnet",
            prompt="Evaluate if the response in {{ outputs }} is professional for {{ inputs }}.",
            num_retries=2,
        )
    """
    logger.trace("Creating guardrail middleware", guardrail_name=name)
    ai_decide_model: AiDecideJudgeModel | None = _as_ai_decide(ai_decide)
    _require_one_judge(name, model, ai_decide_model)
    return GuardrailMiddleware(
        name=name,
        model=model,
        prompt=prompt,
        ai_decide=ai_decide_model,
        num_retries=num_retries,
        fail_on_error=fail_on_error,
        max_context_length=max_context_length,
        apply_to=apply_to,
    )


def create_content_filter_middleware(
    banned_keywords: list[str],
    block_message: str = "I cannot provide that response. Please rephrase your request.",
) -> ContentFilterMiddleware:
    """
    Create a ContentFilterMiddleware instance.

    Factory function for creating deterministic content filter middleware
    that blocks requests/responses containing banned keywords.

    Args:
        banned_keywords: List of keywords to block
        block_message: Message to return when content is blocked

    Returns:
        ContentFilterMiddleware configured with the specified parameters

    Example:
        middleware = create_content_filter_middleware(
            banned_keywords=["password", "secret", "api_key"],
            block_message="I cannot discuss sensitive credentials.",
        )
    """
    logger.trace(
        "Creating content filter middleware", keywords_count=len(banned_keywords)
    )
    return ContentFilterMiddleware(
        banned_keywords=banned_keywords,
        block_message=block_message,
    )


def create_safety_guardrail_middleware(
    safety_model: Optional[str] = None,
    fail_on_error: bool = False,
    ai_decide: AiDecideJudgeModel | dict[str, Any] | None = None,
) -> SafetyGuardrailMiddleware:
    """
    Create a SafetyGuardrailMiddleware instance.

    Factory function for creating model-based safety guardrail middleware
    that evaluates whether responses are safe and appropriate using an
    MLflow judge with structured output.

    Args:
        safety_model: MLflow model string for the safety judge
            (e.g. ``"databricks:/databricks-claude-3-7-sonnet"``).
            Defaults to ``"openai:/gpt-4o-mini"`` if not provided.
        fail_on_error: If True, block responses when the judge call errors (default: False)
        ai_decide: Judge with Databricks ``ai_decide`` (jev-style yes/no)
            instead of an LLM.  Accepts ``AiDecideJudgeModel`` fields as a
            dict, e.g. ``{"threshold": 0.7}``.
            Mutually exclusive with *safety_model*.

    Returns:
        SafetyGuardrailMiddleware configured with the specified model

    Example:
        middleware = create_safety_guardrail_middleware(
            safety_model="databricks:/databricks-claude-3-7-sonnet",
        )
    """
    logger.trace("Creating safety guardrail middleware")
    return SafetyGuardrailMiddleware(
        safety_model=safety_model,
        fail_on_error=fail_on_error,
        ai_decide=ai_decide,
    )


def create_veracity_guardrail_middleware(
    model: str | None = None,
    num_retries: int = 2,
    fail_on_error: bool = False,
    max_context_length: int = 8000,
    ai_decide: AiDecideJudgeModel | dict[str, Any] | None = None,
) -> VeracityGuardrailMiddleware:
    """
    Create a VeracityGuardrailMiddleware instance.

    Factory function for creating a veracity/groundedness guardrail that
    checks whether the agent's response is grounded in tool/retrieval
    context. No prompt is needed -- a built-in expert prompt is used.

    Automatically skips evaluation when no tool context is present in
    the conversation.

    Args:
        model: MLflow model string for the judge
            (e.g. ``"databricks:/databricks-claude-3-7-sonnet"``)
        num_retries: Maximum retry attempts (default: 2)
        fail_on_error: Block responses on evaluation error (default: False)
        max_context_length: Max chars for extracted tool context (default: 8000)
        ai_decide: Judge with Databricks ``ai_decide`` (jev-style yes/no)
            instead of an LLM.  Accepts ``AiDecideJudgeModel`` fields as a
            dict, e.g. ``{"threshold": 0.7}``.
            Mutually exclusive with *model*.

    Returns:
        VeracityGuardrailMiddleware configured with the specified parameters

    Example:
        middleware = create_veracity_guardrail_middleware(
            model="databricks:/databricks-claude-3-7-sonnet",
            num_retries=2,
        )
    """
    logger.trace("Creating veracity guardrail middleware")
    return VeracityGuardrailMiddleware(
        model=model,
        num_retries=num_retries,
        fail_on_error=fail_on_error,
        max_context_length=max_context_length,
        ai_decide=ai_decide,
    )


def create_relevance_guardrail_middleware(
    model: str | None = None,
    num_retries: int = 2,
    fail_on_error: bool = False,
    ai_decide: AiDecideJudgeModel | dict[str, Any] | None = None,
) -> RelevanceGuardrailMiddleware:
    """
    Create a RelevanceGuardrailMiddleware instance.

    Factory function for creating a relevance guardrail that checks whether
    the agent's response directly addresses the user's query. No prompt
    is needed -- a built-in expert prompt is used.

    Args:
        model: MLflow model string for the judge
            (e.g. ``"databricks:/databricks-claude-3-7-sonnet"``)
        num_retries: Maximum retry attempts (default: 2)
        fail_on_error: Block responses on evaluation error (default: False)
        ai_decide: Judge with Databricks ``ai_decide`` (jev-style yes/no)
            instead of an LLM.  Accepts ``AiDecideJudgeModel`` fields as a
            dict, e.g. ``{"threshold": 0.7}``.
            Mutually exclusive with *model*.

    Returns:
        RelevanceGuardrailMiddleware configured with the specified parameters

    Example:
        middleware = create_relevance_guardrail_middleware(
            model="databricks:/databricks-claude-3-7-sonnet",
        )
    """
    logger.trace("Creating relevance guardrail middleware")
    return RelevanceGuardrailMiddleware(
        model=model,
        num_retries=num_retries,
        fail_on_error=fail_on_error,
        ai_decide=ai_decide,
    )


def create_tone_guardrail_middleware(
    model: str | None = None,
    tone: str = "professional",
    custom_guidelines: str | PromptModel | None = None,
    num_retries: int = 2,
    fail_on_error: bool = False,
    ai_decide: AiDecideJudgeModel | dict[str, Any] | None = None,
) -> ToneGuardrailMiddleware:
    """
    Create a ToneGuardrailMiddleware instance.

    Factory function for creating a tone guardrail that validates the
    response matches a configurable tone profile. No prompt is needed
    -- select a preset profile or provide custom guidelines.

    Available tone profiles: ``professional``, ``casual``, ``technical``,
    ``empathetic``, ``concise``.

    Args:
        model: MLflow model string for the judge
            (e.g. ``"databricks:/databricks-claude-3-7-sonnet"``)
        tone: Preset tone profile (default: ``"professional"``)
        custom_guidelines: Custom tone guidelines. Overrides the preset
            profile if provided. Accepts a plain string or a
            ``PromptModel`` from the prompt registry.
        num_retries: Maximum retry attempts (default: 2)
        fail_on_error: Block responses on evaluation error (default: False)
        ai_decide: Judge with Databricks ``ai_decide`` (jev-style yes/no)
            instead of an LLM.  Accepts ``AiDecideJudgeModel`` fields as a
            dict, e.g. ``{"threshold": 0.7}``.
            Mutually exclusive with *model*.

    Returns:
        ToneGuardrailMiddleware configured with the specified parameters

    Example:
        middleware = create_tone_guardrail_middleware(
            model="databricks:/databricks-claude-3-7-sonnet",
            tone="empathetic",
        )
    """
    logger.trace("Creating tone guardrail middleware", tone=tone)
    return ToneGuardrailMiddleware(
        model=model,
        tone=tone,
        custom_guidelines=custom_guidelines,
        num_retries=num_retries,
        fail_on_error=fail_on_error,
        ai_decide=ai_decide,
    )


def create_conciseness_guardrail_middleware(
    model: str | None = None,
    max_length: int = 3000,
    min_length: int = 20,
    check_verbosity: bool = True,
    num_retries: int = 2,
    fail_on_error: bool = False,
    ai_decide: AiDecideJudgeModel | dict[str, Any] | None = None,
) -> ConcisenessGuardrailMiddleware:
    """
    Create a ConcisenessGuardrailMiddleware instance.

    Factory function for creating a hybrid deterministic + LLM conciseness
    guardrail. Performs a fast length check first (no LLM cost), then
    optionally evaluates verbosity using an LLM judge.

    Args:
        model: MLflow model string for the judge
            (e.g. ``"databricks:/databricks-claude-3-7-sonnet"``)
        max_length: Maximum response character length (default: 3000)
        min_length: Minimum response character length (default: 20)
        check_verbosity: Enable LLM verbosity evaluation (default: True)
        num_retries: Maximum retry attempts (default: 2)
        fail_on_error: Block responses on evaluation error (default: False)
        ai_decide: Judge with Databricks ``ai_decide`` (jev-style yes/no)
            instead of an LLM.  Accepts ``AiDecideJudgeModel`` fields as a
            dict, e.g. ``{"threshold": 0.7}``.
            Mutually exclusive with *model*.

    Returns:
        ConcisenessGuardrailMiddleware configured with the specified parameters

    Example:
        middleware = create_conciseness_guardrail_middleware(
            model="databricks:/databricks-claude-3-7-sonnet",
            max_length=2000,
            min_length=50,
            check_verbosity=True,
        )
    """
    logger.trace(
        "Creating conciseness guardrail middleware",
        max_length=max_length,
        min_length=min_length,
        check_verbosity=check_verbosity,
    )
    return ConcisenessGuardrailMiddleware(
        model=model,
        max_length=max_length,
        min_length=min_length,
        check_verbosity=check_verbosity,
        num_retries=num_retries,
        fail_on_error=fail_on_error,
        ai_decide=ai_decide,
    )


def create_scorer_guardrail_middleware(
    name: str,
    scorer_name: str,
    num_retries: int = 1,
    fail_on_error: bool = False,
    max_context_length: int = 8000,
    **scorer_kwargs: Any,
) -> GuardrailMiddleware:
    """
    Create a GuardrailMiddleware powered by any MLflow ``Scorer``.

    Factory function for creating guardrail middleware from an MLflow
    ``Scorer`` class, including built-in ``GuardrailsScorer`` validators
    such as ``ToxicLanguage``, ``DetectPII``, ``DetectJailbreak``, etc.

    The scorer class is loaded by fully qualified name and instantiated
    with the provided keyword arguments.

    Args:
        name: Name identifying this guardrail.
        scorer_name: Fully qualified name of the ``Scorer`` class
            (e.g. ``"mlflow.genai.scorers.guardrails.ToxicLanguage"``).
        num_retries: Maximum retry attempts (default: 1).
        fail_on_error: Block responses on scorer error (default: False).
        max_context_length: Max chars for extracted tool context
            (default: 8000).
        **scorer_kwargs: Keyword arguments forwarded to the scorer
            constructor (e.g. ``threshold=0.7``).

    Returns:
        GuardrailMiddleware configured with the specified scorer.

    Example:
        middleware = create_scorer_guardrail_middleware(
            name="pii_check",
            scorer_name="mlflow.genai.scorers.guardrails.DetectPII",
            pii_entities=["CREDIT_CARD", "SSN"],
        )
    """
    from dao_ai.utils import load_function

    logger.trace(
        "Creating scorer guardrail middleware",
        guardrail_name=name,
        scorer_name=scorer_name,
    )
    scorer_cls: type[Scorer] = load_function(scorer_name)
    scorer: Scorer = scorer_cls(**scorer_kwargs)
    return GuardrailMiddleware(
        name=name,
        scorer=scorer,
        num_retries=num_retries,
        fail_on_error=fail_on_error,
        max_context_length=max_context_length,
    )
