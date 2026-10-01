"""Agentbricks long-term memory tools for DAO AI agents.

Wraps ``databricks_agentkit.langgraph.memory_tools`` (from the
``databricks-agentbricks`` package), which returns two tools — ``remember`` and
``recall`` — backed by the Databricks Agents Managed Memory API. The ``actor``
owning the memories is captured in the tool closures (per-user isolation) and is
never exposed to the model.

This is distinct from the agent's auto-attached ``store`` tools: it is an
explicit, config-selected toolkit a given agent can call to persist and recall
facts.
"""

from __future__ import annotations

from langchain_core.tools import BaseTool, BaseToolkit
from loguru import logger
from pydantic import ConfigDict, Field

from dao_ai.config import AnyVariable, value_of


class AgentbricksMemoryToolkit(BaseToolkit):
    """Toolkit bundling the agentbricks ``remember`` and ``recall`` tools."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    tools: list[BaseTool] = Field(default_factory=list)

    def get_tools(self) -> list[BaseTool]:
        return self.tools


def _resolve_actor(actor: AnyVariable | None) -> str:
    """Resolve the memory ``actor`` — the partition these tools read and write.

    When ``actor`` is configured it is used verbatim. Otherwise the ambient
    identity (deploy service principal / OBO user) is resolved. This is a single
    partition captured for the life of the built tools — it is NOT per request, so
    in a multi-user deployment configure a per-deployment ``actor`` to avoid
    co-mingling different callers' memories.

    Fails closed: if no ``actor`` is configured and the ambient identity cannot be
    resolved to a non-empty value, raise rather than silently reading/writing an
    unpartitioned (empty-actor) bucket — the Managed Memory API rejects an empty
    ``actor_id`` anyway.
    """
    actor_value: str | None = value_of(actor) if actor is not None else None
    if actor_value:
        return str(actor_value)

    from databricks.sdk import WorkspaceClient

    try:
        resolved: str = WorkspaceClient().current_user.me().user_name
    except Exception as exc:  # noqa: BLE001 - surfaced as a clear ValueError below
        raise ValueError(
            "Could not resolve an identity for the agentbricks memory 'actor'; "
            "set 'actor' explicitly on the agentbricks_memory tool."
        ) from exc
    if not resolved:
        raise ValueError(
            "Resolved an empty agentbricks memory 'actor'; set 'actor' explicitly "
            "on the agentbricks_memory tool."
        )
    logger.debug("Resolved agentbricks memory actor from runtime", actor=resolved)
    return resolved


def create_agentbricks_memory_tools(
    store: AnyVariable | None = None,
    actor: AnyVariable | None = None,
) -> AgentbricksMemoryToolkit:
    """Create the agentbricks ``remember``/``recall`` memory toolkit.

    Args:
        store: Databricks Agents memory-store name. When ``None``, the library
            resolves it from the ``AGENT_MEMORY_STORE`` environment variable.
        actor: Identity owning the memories (a single partition for the built
            tools, not per request). When ``None``, resolves the ambient identity
            and raises if it cannot be resolved.

    Returns:
        An :class:`AgentbricksMemoryToolkit` exposing the ``remember`` and
        ``recall`` tools (empty when no store is configured).
    """
    store_value: str | None = value_of(store) if store is not None else None
    actor_value: str = _resolve_actor(actor)

    # Imported lazily so the base install need not eagerly load the agentbricks
    # runtime; ``memory_tools`` is re-exported from the ``langgraph`` package.
    from databricks_agentkit.langgraph import memory_tools

    tools: list[BaseTool] = list(memory_tools(actor=actor_value, store=store_value))
    logger.debug(
        "Created agentbricks memory toolkit",
        store=store_value,
        tool_count=len(tools),
        tools=[tool.name for tool in tools if isinstance(tool, BaseTool)],
    )
    return AgentbricksMemoryToolkit(tools=tools)
