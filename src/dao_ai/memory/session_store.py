"""Databricks Session Store checkpointer backend for dao-ai thread state.

Implements LangGraph's :class:`~langgraph.checkpoint.base.BaseCheckpointSaver`
by delegating to ``DatabricksSessionStoreSaver`` (from the
``databricks-agentbricks`` package), which persists conversation thread state —
channel blobs, versions, pending writes, parent chains — via the Databricks
**Session Store** REST API.

The saver resolves its workspace client from the ambient Databricks runtime, so
all four dao-ai auth modes work unchanged; only the configured store name is
required. Unlike the Lakebase/Postgres backends there is no connection pool to
open, so the saver is constructed eagerly and cached per manager instance.

Session scoping — the saver resolves a session by ``session_id`` (derived from
``thread_id`` + ``checkpoint_ns``) and uses ``actor_id`` only to label the actor
that *owns* a session at creation; it still **requires** a non-empty
``configurable.actor_id`` on every call. dao-ai reaches the checkpointer from
several places that only carry a ``thread_id`` (``get_state_snapshot_async``, the
Apps session helpers, LangGraph internals), so :class:`_SessionScopedSaver`
**defaults** ``actor_id`` to the ``thread_id`` when the caller didn't supply one —
mirroring the library's own ``thread_config`` (``actor or session_id``). A
supplied ``actor_id`` (e.g. the signed-in user, set in ``models.py`` from the
``user_id``/``actor_id`` identity) is respected, so a user's sessions can be owned
by them; because lookup is by ``session_id``, the ``thread_id``-only read paths
still resolve the same session regardless.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator, Sequence
from typing import Any, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    ChannelVersions,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
)
from loguru import logger

from dao_ai.config import CheckpointerModel, value_of
from dao_ai.memory.base import CheckpointManagerBase


def _scope_config(config: Optional[RunnableConfig]) -> Optional[RunnableConfig]:
    """Default ``configurable.actor_id`` to the ``thread_id`` when none was supplied.

    Mirrors the library's ``thread_config`` (``actor_id = actor or session_id``):
    a caller-supplied ``actor_id`` is respected (per-user session ownership), and
    the ``thread_id``-only paths get ``actor_id = thread_id`` so the saver's
    non-empty-``actor_id`` requirement is met. Left untouched when an ``actor_id``
    is already present or there is no ``thread_id`` to derive from (the saver
    raises its own clear error for the latter).
    """
    if not config:
        return config
    configurable: dict[str, Any] = config.get("configurable") or {}
    if configurable.get("actor_id"):
        return config
    thread_id: Any = configurable.get("thread_id")
    if thread_id is None:
        return config
    return {
        **config,
        "configurable": {**configurable, "actor_id": thread_id},
    }


class _SessionScopedSaver(BaseCheckpointSaver):
    """Wraps ``DatabricksSessionStoreSaver`` to default ``actor_id`` to ``thread_id``.

    Every config-bearing method normalizes the config (via :func:`_scope_config`)
    before delegating: a supplied ``actor_id`` is respected; otherwise it defaults
    to the ``thread_id`` so the saver's non-empty-``actor_id`` requirement is met on
    dao-ai's ``thread_id``-only paths. Any attribute not overridden here forwards to
    the wrapped saver.
    """

    def __init__(self, inner: BaseCheckpointSaver) -> None:
        super().__init__(serde=inner.serde)
        self._inner = inner

    def __getattr__(self, name: str) -> Any:
        # Only reached for attributes not found on the wrapper itself. Guard the
        # pre-``_inner`` window (e.g. copy/pickle attribute probes) so a miss
        # raises AttributeError, not KeyError — preserving getattr()/hasattr().
        try:
            inner = self.__dict__["_inner"]
        except KeyError:
            raise AttributeError(name) from None
        return getattr(inner, name)

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        return self._inner.get_tuple(_scope_config(config))

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        return await self._inner.aget_tuple(_scope_config(config))

    def list(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        return self._inner.list(
            _scope_config(config),
            filter=filter,
            before=_scope_config(before),
            limit=limit,
        )

    async def alist(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[CheckpointTuple]:
        async for item in self._inner.alist(
            _scope_config(config),
            filter=filter,
            before=_scope_config(before),
            limit=limit,
        ):
            yield item

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        return self._inner.put(
            _scope_config(config), checkpoint, metadata, new_versions
        )

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        return await self._inner.aput(
            _scope_config(config), checkpoint, metadata, new_versions
        )

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        return self._inner.put_writes(_scope_config(config), writes, task_id, task_path)

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        return await self._inner.aput_writes(
            _scope_config(config), writes, task_id, task_path
        )

    def delete_thread(self, thread_id: str, actor_id: str = "") -> None:
        return self._inner.delete_thread(thread_id, actor_id or thread_id)

    async def adelete_thread(self, thread_id: str, actor_id: str = "") -> None:
        return await self._inner.adelete_thread(thread_id, actor_id or thread_id)

    def get_next_version(
        self, current: Optional[Any], channel: Optional[str] = None
    ) -> str:
        return self._inner.get_next_version(current, channel)


class SessionStoreCheckpointerManager(CheckpointManagerBase):
    """Checkpointer backed by ``DatabricksSessionStoreSaver``.

    Resolves the configured session-store name and constructs the saver (wrapped
    by :class:`_SessionScopedSaver`) on first :meth:`checkpointer` call, caching
    the instance for subsequent calls.
    """

    def __init__(self, checkpointer_model: CheckpointerModel) -> None:
        self.checkpointer_model = checkpointer_model
        self._checkpointer: BaseCheckpointSaver | None = None

    def checkpointer(self) -> BaseCheckpointSaver:
        if self._checkpointer is not None:
            return self._checkpointer

        session_store = self.checkpointer_model.session_store
        if session_store is None:
            raise ValueError(
                "Session store configuration is required for the Session Store "
                "checkpointer"
            )

        session_store_name: str = value_of(session_store.name)

        # Imported lazily: databricks_agentkit does not re-export the saver from
        # its ``langgraph`` package, so reach it by submodule path.
        from databricks_agentkit.langgraph.session_store import (
            DatabricksSessionStoreSaver,
        )

        self._checkpointer = _SessionScopedSaver(
            DatabricksSessionStoreSaver(session_store_name=session_store_name)
        )
        logger.debug(
            "Session Store checkpointer created",
            checkpointer=self.checkpointer_model.name,
            session_store=session_store_name,
        )
        return self._checkpointer
