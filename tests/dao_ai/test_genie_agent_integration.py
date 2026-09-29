"""Live integration tests: Genie Agent Mode reasoning over the real API.

Runs only when ``GENIE_AGENT_ID`` names an Agent Mode-enabled Genie space;
auth comes from the default ``WorkspaceClient`` chain (e.g.
``DATABRICKS_CONFIG_PROFILE``). Example::

    GENIE_AGENT_ID=<space_id> DATABRICKS_CONFIG_PROFILE=<profile> \\
        uv run pytest tests/dao_ai/test_genie_agent_integration.py -m integration

The question asks for a comparison so Genie plans before querying — simple
lookups can skip the reasoning step entirely.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

import pytest
from langchain.agents import create_agent
from langchain_core.messages import AIMessageChunk, HumanMessage

from dao_ai.genie.agent_chat_model import (
    CONVERSATION_ID_METADATA_KEY,
    GenieAgentChatModel,
)
from dao_ai.models import _split_content

AGENT_ID: str | None = os.environ.get("GENIE_AGENT_ID")
QUESTION: str = (
    "What are the top 5 products by total sales, and how does that compare "
    "to their average price?"
)

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.skipif(not AGENT_ID, reason="GENIE_AGENT_ID not set"),
]


def _model() -> GenieAgentChatModel:
    from databricks.sdk import WorkspaceClient

    return GenieAgentChatModel(agent_id=AGENT_ID, workspace_client=WorkspaceClient())


def test_astream_surfaces_reasoning_before_answer() -> None:
    async def _collect() -> tuple[list[dict[str, Any]], AIMessageChunk]:
        blocks: list[dict[str, Any]] = []
        acc: AIMessageChunk | None = None
        async for chunk in _model().astream([HumanMessage(QUESTION)]):
            if isinstance(chunk.content, list):
                blocks.extend(chunk.content)
            acc = chunk if acc is None else acc + chunk
        return blocks, acc

    blocks, acc = asyncio.run(_collect())
    kinds: list[str] = [block["type"] for block in blocks]
    assert "reasoning" in kinds, kinds
    assert kinds.index("reasoning") < kinds.index("text")
    assert acc.text.strip()
    assert all(
        block["reasoning"] not in acc.text
        for block in blocks
        if block["type"] == "reasoning"
    )
    assert acc.response_metadata.get(CONVERSATION_ID_METADATA_KEY)


def test_langgraph_messages_stream_carries_reasoning() -> None:
    """The path dao-ai's Responses layer consumes: an agent graph streamed with
    ``stream_mode="messages"``, each chunk split by ``_split_content``."""
    agent = create_agent(model=_model(), tools=[])

    async def _split() -> tuple[str, str]:
        text, reasoning = "", ""
        async for message, _metadata in agent.astream(
            {"messages": [HumanMessage(QUESTION)]}, stream_mode="messages"
        ):
            if isinstance(message, AIMessageChunk) and message.content:
                t, r = _split_content(message.content)
                text, reasoning = text + t, reasoning + r
        return text, reasoning

    text, reasoning = asyncio.run(_split())
    assert reasoning.strip()
    assert text.strip()
