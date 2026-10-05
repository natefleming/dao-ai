"""Bundle emission tests for ``AppModel.app_space`` (Databricks App Spaces).

Locks in the contract that ``_build_app_block`` emits
``resources.apps.<name>.space`` only when ``app.app_space`` is set, and that an
in-space app declares neither ``resources`` nor ``user_api_scopes`` (the Apps
API rejects both on an in-space app) — so ``MLFLOW_EXPERIMENT_ID`` is pinned to
the experiment id instead of ``value_from: experiment``.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from databricks.sdk.errors.platform import NotFound
from databricks.sdk.service.apps import Space, SpaceStatus, SpaceStatusSpaceState

from dao_ai.apps.bundle import _build_app_block
from dao_ai.config import (
    AgentModel,
    AppConfig,
    AppModel,
    InferenceEndpointModel,
)


def _config(*, app_space: str | None = None) -> AppConfig:
    extra: dict = {}
    if app_space is not None:
        extra["app_space"] = app_space
    return AppConfig(
        app=AppModel(
            name="dao-ai-space-test",
            description="test agent",
            enable_chat_proxy=False,
            agents=[
                AgentModel(
                    name="greeter",
                    description="test agent",
                    model=InferenceEndpointModel(name="databricks-gpt-5-4-mini"),
                )
            ],
            **extra,
        ),
    )


@pytest.fixture
def workspace() -> Iterator[MagicMock]:
    w = MagicMock()
    w.apps.get_space.return_value = Space(
        name="retail-builders",
        status=SpaceStatus(state=SpaceStatusSpaceState.SPACE_ACTIVE),
        effective_user_api_scopes=["genie", "model-serving"],
    )
    w.apps.get.side_effect = NotFound("not created yet")
    with patch("databricks.sdk.WorkspaceClient", return_value=w):
        yield w


def _app_def(config: AppConfig) -> dict[str, Any]:
    _, _, apps_block = _build_app_block(config, "dao_ai.yaml")
    (app_def,) = apps_block.values()
    return app_def


@pytest.mark.unit
class TestAppSpaceEmission:
    def test_omits_space_when_unset(self) -> None:
        app_def = _app_def(_config())
        assert "space" not in app_def
        assert "lifecycle" not in app_def
        assert app_def["resources"]

    def test_emits_space_when_set(self, workspace: MagicMock) -> None:
        app_def = _app_def(_config(app_space="retail-builders"))
        assert app_def["space"] == "retail-builders"
        # DABs' default ``no_compute: true`` create is rejected for in-space apps.
        assert app_def["lifecycle"] == {"started": True}
        workspace.apps.get_space.assert_called_once_with(name="retail-builders")

    def test_in_space_app_declares_no_resources_or_scopes(
        self, workspace: MagicMock
    ) -> None:
        app_def = _app_def(_config(app_space="retail-builders"))
        assert "resources" not in app_def
        assert "user_api_scopes" not in app_def
        assert "compute_size" not in app_def

    def test_experiment_env_pinned_without_resource(
        self, workspace: MagicMock
    ) -> None:
        app_def = _app_def(_config(app_space="retail-builders"))
        env = {e["name"]: e for e in app_def["config"]["env"]}
        assert env["MLFLOW_EXPERIMENT_ID"] == {
            "name": "MLFLOW_EXPERIMENT_ID",
            "value": "${resources.experiments.dao-ai-space-test-experiment.id}",
        }

    def test_existing_standalone_app_is_refused(self, workspace: MagicMock) -> None:
        from databricks.sdk.service.apps import App

        workspace.apps.get.side_effect = None
        workspace.apps.get.return_value = App(name="dao-ai-space-test")
        with pytest.raises(ValueError, match="outside any App Space"):
            _app_def(_config(app_space="retail-builders"))
