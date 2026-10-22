"""
Genie One MCP tools with conversation continuity.

Genie One MCP (``system.ai.genie_one_mcp``, selected with ``genie: true``) is
asynchronous: ``genie_ask`` starts a turn and returns a ``conversation_id`` and
``response_id``, then ``genie_poll_response`` / ``genie_get_query_result`` /
``genie_cancel_response`` act on that conversation.

The tools mirror the server exactly (names and schemas come from
``tools/list``). The only addition is that the Genie ``conversation_id`` is kept
in ``session.genie.spaces["genie_one"]``, so a follow-up ``genie_ask`` continues
the same Genie conversation (across requests when a checkpointer persists the
thread) and the id is echoed in ``custom_outputs.session`` like the
``type: genie`` tool's.
"""

import json
from pathlib import Path
from typing import Any

from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.runnables.base import RunnableLike
from langchain_core.tools import tool as create_tool
from langgraph.types import Command
from loguru import logger
from mcp.types import CallToolResult, Tool
from tenacity import (
    AsyncRetrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from dao_ai.config import McpFunctionModel
from dao_ai.state import AgentState, Context, SessionState
from dao_ai.tools.tracing import ResourceInfo, set_resource_attributes

#: Session key for the Genie One conversation in ``session.genie.spaces``.
GENIE_ONE_SESSION_KEY: str = "genie_one"

GENIE_ASK_TOOL: str = "genie_ask"

#: ``tools/list`` snapshot of ``system.ai.genie_one_mcp``, used where the live
#: listing cannot run (see :func:`uses_static_genie_one_tools`).
_TOOL_DEFINITIONS_PATH: Path = Path(__file__).with_name("genie_one_tools.json")


def genie_one_tool_definitions() -> list[Tool]:
    """Return the Genie One MCP tools as the server lists them (bundled snapshot)."""
    return [
        Tool.model_validate(definition)
        for definition in json.loads(_TOOL_DEFINITIONS_PATH.read_text())
    ]


def uses_static_genie_one_tools(function: McpFunctionModel) -> bool:
    """Whether to use the bundled tool definitions instead of ``tools/list``.

    An OBO Genie One server on Model Serving has no user identity at model load,
    so the load-time listing cannot authenticate. The bundled definitions stand
    in, and each call still runs as the requesting user. Elsewhere the live
    listing is used.
    """
    from dao_ai.utils import is_in_model_serving

    return (
        function.is_genie_one
        and bool(function.on_behalf_of_user)
        and is_in_model_serving()
    )


def create_genie_one_tool(function: McpFunctionModel, mcp_tool: Tool) -> RunnableLike:
    """Wrap one Genie One MCP tool so it reads and writes the session conversation.

    Args:
        function: The ``genie: true`` (or ``service: system.ai.genie_one_mcp``)
            MCP function model.
        mcp_tool: The tool as listed by the server.

    Returns:
        A LangChain tool with the server's name and schema that returns a
        ``Command`` updating ``messages`` and ``session``.
    """
    from dao_ai.tools.mcp import (
        _build_mcp_client,
        _call_tool_with_capabilities,
        _extract_text_content,
        _get_auth_resource,
        _is_transient_http_error,
        _resolve_meta,
    )

    # genie_ask starts a Genie turn, so a retry could ask twice; the other
    # tools only read or cancel and are safe to retry on gateway 5xx/429.
    max_attempts: int = 1 if mcp_tool.name == GENIE_ASK_TOOL else 4

    accepts_conversation_id: bool = "conversation_id" in (
        mcp_tool.inputSchema.get("properties") or {}
    )

    @create_tool(
        mcp_tool.name,
        description=mcp_tool.description or f"MCP tool: {mcp_tool.name}",
        args_schema=mcp_tool.inputSchema,
    )
    async def genie_one_tool(
        runtime: ToolRuntime[Context, AgentState],
        **kwargs: Any,
    ) -> Command:
        """Call the Genie One MCP tool, threading the conversation via session."""
        auth_resource = _get_auth_resource(function)
        set_resource_attributes(
            ResourceInfo("mcp", auth_resource.on_behalf_of_user, mcp_tool.name)
        )

        session: SessionState = runtime.state.get("session") or SessionState()
        stored_conversation_id: str | None = session.genie.get_conversation_id(
            GENIE_ONE_SESSION_KEY
        )
        if (
            accepts_conversation_id
            and not kwargs.get("conversation_id")
            and stored_conversation_id
        ):
            kwargs["conversation_id"] = stored_conversation_id
            logger.debug(
                "Continuing Genie One conversation from session",
                tool_name=mcp_tool.name,
                conversation_id=stored_conversation_id,
            )

        async def _call() -> CallToolResult:
            client = _build_mcp_client(function, runtime.context)
            async with client.session("mcp_function") as mcp_session:
                return await _call_tool_with_capabilities(
                    function,
                    mcp_session,
                    mcp_tool.name,
                    kwargs,
                    _resolve_meta(function.meta),
                )

        result: CallToolResult = await AsyncRetrying(
            retry=retry_if_exception(_is_transient_http_error),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            stop=stop_after_attempt(max_attempts),
            reraise=True,
        )(_call)

        update: dict[str, Any] = {
            "messages": [
                ToolMessage(
                    _extract_text_content(result), tool_call_id=runtime.tool_call_id
                )
            ]
        }

        if mcp_tool.name == GENIE_ASK_TOOL and not result.isError:
            payload: dict[str, Any] = result.structuredContent or {}
            conversation_id: str | None = payload.get("conversation_id")
            if conversation_id:
                session.genie.update_space(
                    space_id=GENIE_ONE_SESSION_KEY,
                    conversation_id=conversation_id,
                    last_query=kwargs.get("question"),
                    message_id=payload.get("response_id"),
                )
                update["session"] = session

        return Command(update=update)

    return genie_one_tool
