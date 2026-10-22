"""Tests for Genie One MCP (``genie: true``) tools and conversation continuity."""

import asyncio
import json
import os
import time
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from langchain.tools import ToolRuntime
from langgraph.types import Command
from mcp.types import CallToolResult, TextContent, Tool

from dao_ai.config import McpFunctionModel
from dao_ai.state import SessionState
from dao_ai.tools.genie_one import GENIE_ONE_SESSION_KEY, create_genie_one_tool

GENIE_ASK = Tool(
    name="genie_ask",
    description="Ask Genie a question.",
    inputSchema={
        "type": "object",
        "properties": {
            "question": {"type": "string"},
            "conversation_id": {"type": "string"},
        },
        "required": ["question"],
    },
)
GENIE_POLL = Tool(
    name="genie_poll_response",
    description="Poll a Genie response.",
    inputSchema={
        "type": "object",
        "properties": {
            "conversation_id": {"type": "string"},
            "response_id": {"type": "string"},
        },
        "required": ["conversation_id", "response_id"],
    },
)


def _runtime(state: dict[str, Any]) -> ToolRuntime:
    return ToolRuntime(
        state=state,
        context=None,
        config=None,
        stream_writer=lambda *_: None,
        tool_call_id="call_1",
        store=None,
        execution_info=None,
        server_info=None,
    )


def _result(payload: dict[str, Any]) -> CallToolResult:
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(payload))],
        structuredContent=payload,
    )


def _http_error(status: int) -> httpx.HTTPStatusError:
    return httpx.HTTPStatusError(
        str(status),
        request=httpx.Request("POST", "https://h"),
        response=httpx.Response(status),
    )


def _run(
    mcp_tool: Tool, state: dict[str, Any], call: AsyncMock, **kwargs: Any
) -> Command:
    """Run a Genie One tool with ``call`` standing in for the MCP tools/call."""
    function = McpFunctionModel(genie=True, workspace_host="https://host")

    @asynccontextmanager
    async def _session(_name: str):
        yield MagicMock()

    client = MagicMock()
    client.session = _session
    with (
        patch("dao_ai.tools.mcp._build_mcp_client", return_value=client),
        patch("dao_ai.tools.mcp._call_tool_with_capabilities", call),
        patch("asyncio.sleep", new=AsyncMock()),
    ):
        tool = create_genie_one_tool(function, mcp_tool)
        return asyncio.run(tool.coroutine(runtime=_runtime(state), **kwargs))


def _invoke(
    mcp_tool: Tool, state: dict[str, Any], result: CallToolResult, **kwargs: Any
) -> tuple[Command, AsyncMock]:
    """Run a Genie One tool returning ``result``; return (Command, call)."""
    call = AsyncMock(return_value=result)
    return _run(mcp_tool, state, call, **kwargs), call


def _sent_args(call: AsyncMock) -> dict[str, Any]:
    return call.await_args.args[3]


@pytest.mark.unit
class TestGenieOneConversationContinuity:
    def test_tool_mirrors_server_name_and_schema(self) -> None:
        tool = create_genie_one_tool(
            McpFunctionModel(genie=True, workspace_host="https://host"), GENIE_ASK
        )
        assert tool.name == "genie_ask"
        assert set(tool.args) == {"question", "conversation_id"}

    def test_first_ask_persists_conversation_id(self) -> None:
        command, call = _invoke(
            GENIE_ASK,
            {"messages": []},
            _result({"conversation_id": "c1", "response_id": "r1"}),
            question="How many trips?",
        )
        assert "conversation_id" not in _sent_args(call)
        session: SessionState = command.update["session"]
        space = session.genie.spaces[GENIE_ONE_SESSION_KEY]
        assert space.conversation_id == "c1"
        assert space.message_id == "r1"
        assert space.last_query == "How many trips?"
        assert command.update["messages"][0].tool_call_id == "call_1"

    def test_follow_up_ask_continues_stored_conversation(self) -> None:
        session = SessionState()
        session.genie.update_space(space_id=GENIE_ONE_SESSION_KEY, conversation_id="c1")
        _, call = _invoke(
            GENIE_ASK,
            {"messages": [], "session": session},
            _result({"conversation_id": "c1", "response_id": "r2"}),
            question="And last month?",
        )
        assert _sent_args(call)["conversation_id"] == "c1"

    def test_explicit_conversation_id_wins(self) -> None:
        session = SessionState()
        session.genie.update_space(space_id=GENIE_ONE_SESSION_KEY, conversation_id="c1")
        command, call = _invoke(
            GENIE_ASK,
            {"messages": [], "session": session},
            _result({"conversation_id": "c9", "response_id": "r1"}),
            question="New topic",
            conversation_id="c9",
        )
        assert _sent_args(call)["conversation_id"] == "c9"
        assert (
            command.update["session"]
            .genie.spaces[GENIE_ONE_SESSION_KEY]
            .conversation_id
            == "c9"
        )

    def test_poll_passes_through_without_session_update(self) -> None:
        command, call = _invoke(
            GENIE_POLL,
            {"messages": []},
            _result({"status": "completed", "final_answer": "42"}),
            conversation_id="c1",
            response_id="r1",
        )
        assert _sent_args(call) == {"conversation_id": "c1", "response_id": "r1"}
        assert "session" not in command.update
        assert "42" in command.update["messages"][0].content

    def test_poll_retries_transient_gateway_error(self) -> None:
        ok = _result({"status": "completed", "final_answer": "42"})
        call = AsyncMock(side_effect=[_http_error(504), ok])
        command = _run(
            GENIE_POLL, {"messages": []}, call, conversation_id="c1", response_id="r1"
        )
        assert call.await_count == 2
        assert "42" in command.update["messages"][0].content

    def test_ask_is_not_retried(self) -> None:
        call = AsyncMock(side_effect=_http_error(504))
        with pytest.raises(httpx.HTTPStatusError):
            _run(GENIE_ASK, {"messages": []}, call, question="q")
        assert call.await_count == 1

    def test_error_result_does_not_persist(self) -> None:
        result = _result({"conversation_id": "c1"})
        result.isError = True
        command, _ = _invoke(GENIE_ASK, {"messages": []}, result, question="q")
        assert "session" not in command.update


@pytest.mark.unit
class TestGenieOneRouting:
    def test_create_mcp_tools_uses_genie_one_wrapper(self) -> None:
        from dao_ai.tools import mcp

        function = McpFunctionModel(genie=True, workspace_host="https://host")
        with patch.object(
            mcp, "_fetch_tools_from_server", return_value=[GENIE_ASK, GENIE_POLL]
        ):
            tools = mcp.create_mcp_tools(function)
        assert [t.name for t in tools] == ["genie_ask", "genie_poll_response"]
        # Genie One wrappers require the injected runtime (they return a Command).
        assert all(t.coroutine.__name__ == "genie_one_tool" for t in tools)

    def test_other_servers_use_generic_wrapper(self) -> None:
        from dao_ai.tools import mcp

        function = McpFunctionModel(sql=True, workspace_host="https://host")
        with patch.object(mcp, "_fetch_tools_from_server", return_value=[GENIE_POLL]):
            tools = mcp.create_mcp_tools(function)
        assert tools[0].coroutine.__name__ == "tool_wrapper"


@pytest.mark.unit
class TestGenieOneStaticDefinitions:
    """OBO Genie One on Model Serving skips load-time tools/list (no user yet)."""

    def test_bundled_definitions_mirror_server_tools(self) -> None:
        from dao_ai.tools.genie_one import genie_one_tool_definitions

        tools = {t.name: t for t in genie_one_tool_definitions()}
        assert set(tools) == {
            "genie_ask",
            "genie_poll_response",
            "genie_get_query_result",
            "genie_cancel_response",
        }
        assert tools["genie_ask"].inputSchema["required"] == ["question"]

    @pytest.mark.parametrize(
        ("function", "in_serving", "expected"),
        [
            (McpFunctionModel(genie=True, on_behalf_of_user=True), True, True),
            (McpFunctionModel(genie=True, on_behalf_of_user=True), False, False),
            (McpFunctionModel(genie=True), True, False),
            (McpFunctionModel(sql=True, on_behalf_of_user=True), True, False),
            (
                McpFunctionModel(
                    service="system.ai.genie_one_mcp", on_behalf_of_user=True
                ),
                True,
                True,
            ),
        ],
    )
    def test_uses_static_only_for_obo_genie_one_in_serving(
        self, function: McpFunctionModel, in_serving: bool, expected: bool
    ) -> None:
        from dao_ai.tools.genie_one import uses_static_genie_one_tools

        with patch("dao_ai.utils.is_in_model_serving", return_value=in_serving):
            assert uses_static_genie_one_tools(function) is expected

    def test_fetch_skips_server_when_static(self) -> None:
        from dao_ai.tools import mcp

        function = McpFunctionModel(
            genie=True, on_behalf_of_user=True, workspace_host="https://host"
        )
        with (
            patch("dao_ai.utils.is_in_model_serving", return_value=True),
            patch.object(mcp, "_build_mcp_client") as build,
        ):
            tools = mcp._fetch_tools_from_server(function)
        build.assert_not_called()
        assert tools[0].name == "genie_ask"


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("DATABRICKS_HOST") and not os.getenv("DATABRICKS_CONFIG_PROFILE"),
    reason="needs DATABRICKS_HOST or DATABRICKS_CONFIG_PROFILE",
)
class TestGenieOneMcpLive:
    """Live Genie One MCP round trip through the dao-ai wrappers."""

    def _tools(self) -> dict[str, Any]:
        from dao_ai.tools.mcp import create_mcp_tools

        tools = create_mcp_tools(McpFunctionModel(genie=True))
        return {t.name: t for t in tools}

    def test_lists_genie_one_tools(self) -> None:
        names = set(self._tools())
        assert {"genie_ask", "genie_poll_response", "genie_get_query_result"} <= names

    def test_bundled_definitions_match_live_server(self) -> None:
        """Guard against drift between the bundled snapshot and the server."""
        from dao_ai.tools.genie_one import genie_one_tool_definitions
        from dao_ai.tools.mcp import _fetch_tools_from_server

        live = {
            t.name: t.inputSchema
            for t in _fetch_tools_from_server(McpFunctionModel(genie=True))
        }
        bundled = {t.name: t.inputSchema for t in genie_one_tool_definitions()}
        assert bundled == live

    def test_ask_poll_and_follow_up_reuse_conversation(self) -> None:
        tools = self._tools()
        state: dict[str, Any] = {"messages": []}

        def call(name: str, **kwargs: Any) -> Command:
            command = asyncio.run(
                tools[name].coroutine(runtime=_runtime(state), **kwargs)
            )
            if "session" in command.update:
                state["session"] = command.update["session"]
            return command

        def ask_and_wait(question: str) -> tuple[str, str]:
            ask = json.loads(
                call("genie_ask", question=question).update["messages"][0].content
            )
            conversation_id, response_id = ask["conversation_id"], ask["response_id"]
            for _ in range(60):
                text = (
                    call(
                        "genie_poll_response",
                        conversation_id=conversation_id,
                        response_id=response_id,
                    )
                    .update["messages"][0]
                    .content
                )
                if "Status:** completed" in text:
                    return conversation_id, text
                time.sleep(3)
            pytest.fail("Genie One response did not complete")

        first_id, first = ask_and_wait(
            "How many tables are in the samples.nyctaxi schema?"
        )
        assert "trips" in first
        follow_id, _ = ask_and_wait("What columns does that table have?")
        assert follow_id == first_id
        assert (
            state["session"].genie.spaces[GENIE_ONE_SESSION_KEY].conversation_id
            == first_id
        )


@pytest.mark.unit
class TestTransientErrorDetection:
    def test_wrapped_listing_error_is_transient(self) -> None:
        """tools/list failures are re-raised as RuntimeError; retry must see through."""
        from dao_ai.tools.mcp import _is_transient_http_error

        try:
            try:
                raise ExceptionGroup("tg", [_http_error(504)])
            except ExceptionGroup as e:
                raise RuntimeError("Failed to list MCP tools") from e
        except RuntimeError as wrapped:
            assert _is_transient_http_error(wrapped)

    def test_non_transient_status_is_not_retried(self) -> None:
        from dao_ai.tools.mcp import _is_transient_http_error

        try:
            raise RuntimeError("Failed") from _http_error(403)
        except RuntimeError as wrapped:
            assert not _is_transient_http_error(wrapped)
