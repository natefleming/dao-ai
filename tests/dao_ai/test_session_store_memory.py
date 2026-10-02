"""Unit tests for the Databricks Session Store checkpointer + agentbricks memory tools.

The ``databricks-agentbricks`` package may be absent from the local mirror, and
the live round-trip is covered by fevm e2e; here we stub
``databricks_agentkit.langgraph`` in ``sys.modules`` and verify the config
selection / validation / dispatch logic.
"""

from __future__ import annotations

import sys
import types

import pytest

from dao_ai.config import (
    AgentbricksMemoryToolModel,
    CheckpointerModel,
    FunctionType,
    SessionStoreModel,
    StorageType,
    ToolModel,
)


@pytest.fixture
def stub_agentkit(monkeypatch: pytest.MonkeyPatch):
    """Inject a fake ``databricks_agentkit.langgraph`` with the two symbols used."""

    class FakeSaver:
        serde = None

        def __init__(self, session_store_name: str) -> None:
            self.session_store_name = session_store_name

    captured: dict = {}

    def fake_memory_tools(actor: str, store: str | None = None):
        from langchain_core.tools import tool

        captured["actor"] = actor
        captured["store"] = store

        @tool
        def remember(fact: str, topic: str) -> str:
            """Persist a fact."""
            return "ok"

        @tool
        def recall(query: str) -> str:
            """Recall facts."""
            return "ok"

        return [remember, recall]

    pkg = types.ModuleType("databricks_agentkit")
    lg = types.ModuleType("databricks_agentkit.langgraph")
    ss = types.ModuleType("databricks_agentkit.langgraph.session_store")
    ss.DatabricksSessionStoreSaver = FakeSaver
    lg.memory_tools = fake_memory_tools
    pkg.langgraph = lg

    monkeypatch.setitem(sys.modules, "databricks_agentkit", pkg)
    monkeypatch.setitem(sys.modules, "databricks_agentkit.langgraph", lg)
    monkeypatch.setitem(sys.modules, "databricks_agentkit.langgraph.session_store", ss)
    return captured


# ---------------------------------------------------------------------------
# Checkpointer config
# ---------------------------------------------------------------------------


class TestSessionStoreCheckpointer:
    def test_storage_type_is_session_store(self) -> None:
        c = CheckpointerModel(name="c", session_store=SessionStoreModel(name="s"))
        assert c.storage_type == StorageType.SESSION_STORE

    def test_database_without_session_store_is_postgres(self) -> None:
        c = CheckpointerModel(name="c", database={"name": "db", "project": "proj"})
        assert c.storage_type == StorageType.POSTGRES

    def test_no_backend_is_memory(self) -> None:
        assert CheckpointerModel(name="c").storage_type == StorageType.MEMORY

    def test_database_and_session_store_are_mutually_exclusive(self) -> None:
        with pytest.raises(ValueError, match="cannot set both"):
            CheckpointerModel(
                name="c",
                database={"name": "db", "project": "proj"},
                session_store=SessionStoreModel(name="s"),
            )

    def test_manager_dispatch_and_cache(self, stub_agentkit) -> None:
        from dao_ai.memory import CheckpointManager
        from dao_ai.memory.session_store import SessionStoreCheckpointerManager

        c = CheckpointerModel(
            name="c", session_store=SessionStoreModel(name="my_store")
        )
        mgr = CheckpointManager.instance(c)
        assert isinstance(mgr, SessionStoreCheckpointerManager)
        # cached by session-store name
        assert CheckpointManager.instance(c) is mgr

        ckpt = mgr.checkpointer()
        assert ckpt.session_store_name == "my_store"
        # saver instance is cached on the manager
        assert mgr.checkpointer() is ckpt


# ---------------------------------------------------------------------------
# Agentbricks memory tools
# ---------------------------------------------------------------------------


class TestAgentbricksMemoryTools:
    def test_type_dispatches_to_model(self) -> None:
        m = ToolModel.model_validate(
            {
                "name": "agent_memory",
                "function": {
                    "type": "agentbricks_memory",
                    "store": "s",
                    "actor": "alice",
                },
            }
        )
        assert isinstance(m.function, AgentbricksMemoryToolModel)
        assert m.function.type == FunctionType.AGENTBRICKS_MEMORY.value

    def test_as_tools_returns_remember_and_recall(self, stub_agentkit) -> None:
        model = AgentbricksMemoryToolModel(store="my_store", actor="alice")
        tools = model.as_tools()
        assert [t.name for t in tools] == ["remember", "recall"]
        assert stub_agentkit == {"actor": "alice", "store": "my_store"}

    def test_actor_falls_back_to_current_user(
        self, stub_agentkit, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import dao_ai.tools.session_store as mod

        class _Me:
            user_name = "resolved-user"

        class _CurrentUser:
            def me(self):
                return _Me()

        class _WorkspaceClient:
            def __init__(self, *a, **k):
                pass

            current_user = _CurrentUser()

        sdk = types.ModuleType("databricks.sdk")
        sdk.WorkspaceClient = _WorkspaceClient
        monkeypatch.setitem(sys.modules, "databricks.sdk", sdk)

        mod.create_agentbricks_memory_tools(store="s", actor=None)
        assert stub_agentkit["actor"] == "resolved-user"

    def test_unresolvable_actor_fails_closed(
        self, stub_agentkit, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # No actor configured + ambient identity unresolvable -> raise rather than
        # silently writing/reading an empty, unpartitioned actor bucket.
        import dao_ai.tools.session_store as mod

        class _CurrentUser:
            def me(self):
                raise RuntimeError("token lacks scope")

        class _WorkspaceClient:
            def __init__(self, *a, **k):
                pass

            current_user = _CurrentUser()

        sdk = types.ModuleType("databricks.sdk")
        sdk.WorkspaceClient = _WorkspaceClient
        monkeypatch.setitem(sys.modules, "databricks.sdk", sdk)

        with pytest.raises(ValueError, match="actor"):
            mod.create_agentbricks_memory_tools(store="s", actor=None)


# ---------------------------------------------------------------------------
# user_id / actor_id aliasing — lets the Session Store checkpointer (which
# requires actor_id) be swapped in without changing client payloads.
# ---------------------------------------------------------------------------


class TestUserActorAliasing:
    def _context(self, configurable: dict):
        from dao_ai.models import LanggraphChatModel

        # _convert_to_context does not touch instance state.
        model = object.__new__(LanggraphChatModel)
        return model._convert_to_context(
            {"custom_inputs": {"configurable": configurable}}
        )

    def test_client_actor_id_resolves_identity(self) -> None:
        # A client may send actor_id instead of user_id; both mean the identity.
        ctx = self._context({"actor_id": "alice@x.com", "thread_id": "t1"})
        assert ctx.user_id == "alice@x_com"

    def test_client_user_id_resolves_identity(self) -> None:
        ctx = self._context({"user_id": "bob@x.com", "thread_id": "t2"})
        assert ctx.user_id == "bob@x_com"

    def test_user_id_wins_when_both_sent(self) -> None:
        ctx = self._context(
            {"user_id": "bob@x.com", "actor_id": "alice@x.com", "thread_id": "t3"}
        )
        assert ctx.user_id == "bob@x_com"

    def test_identity_flows_as_actor_id(self) -> None:
        # The resolved identity is carried as actor_id so the Session Store
        # checkpointer owns each session by the signed-in user. actor_id keeps the
        # real principal (un-normalized), while user_id is namespace-normalized.
        ctx = self._context({"user_id": "carol@x.com", "thread_id": "t4"})
        assert ctx.actor_id == "carol@x.com"
        assert ctx.user_id == "carol@x_com"

    def test_no_actor_id_when_no_identity(self) -> None:
        # No identity -> no actor_id carried; the saver wrapper defaults it to
        # the thread_id for the Session Store backend.
        ctx = self._context({"thread_id": "t5"})
        assert ctx.user_id is None
        assert getattr(ctx, "actor_id", None) is None


# ---------------------------------------------------------------------------
# _SessionScopedSaver — defaults actor_id to thread_id when none is supplied, so
# dao-ai's thread_id-only read paths meet the saver's non-empty-actor_id rule.
# ---------------------------------------------------------------------------


class TestSessionScopedSaver:
    def _wrapper(self):
        from dao_ai.memory.session_store import _SessionScopedSaver

        class _Inner:
            serde = object()

            def __init__(self):
                self.seen: list = []

            def get_tuple(self, config):
                self.seen.append(config)
                return None

        inner = _Inner()
        return _SessionScopedSaver(inner), inner

    def test_actor_id_defaults_to_thread_id_when_absent(self) -> None:
        from dao_ai.memory.session_store import _scope_config

        scoped = _scope_config({"configurable": {"thread_id": "t1"}})
        assert scoped["configurable"]["actor_id"] == "t1"

    def test_supplied_actor_id_is_respected(self) -> None:
        from dao_ai.memory.session_store import _scope_config

        scoped = _scope_config(
            {"configurable": {"thread_id": "t1", "actor_id": "alice@x_com"}}
        )
        # per-user session ownership: a supplied actor is NOT overridden
        assert scoped["configurable"]["actor_id"] == "alice@x_com"

    def test_delegates_with_scoped_config(self) -> None:
        wrapper, inner = self._wrapper()
        wrapper.get_tuple({"configurable": {"thread_id": "abc"}})
        assert inner.seen[0]["configurable"]["actor_id"] == "abc"
