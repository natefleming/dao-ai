"""Tests for Databricks App Space support (``AppModel.app_space``).

Covers the config surface (bare-name coercion, the deprecated ``space`` alias)
and the deploy-time preflight in ``dao_ai.apps.resources`` that validates a
config against the live space. The Apps API rejects ``user_api_scopes`` and app
``resources`` on an in-space app, so everything dao-ai would normally declare
must be granted by the space instead.
"""

from __future__ import annotations

import warnings
from typing import Any
from unittest.mock import MagicMock

import pytest
import yaml
from databricks.sdk.errors.platform import NotFound
from databricks.sdk.service.apps import (
    App,
    AppResource,
    AppResourceSqlWarehouse,
    AppResourceSqlWarehouseSqlWarehousePermission,
    Space,
    SpaceStatus,
    SpaceStatusSpaceState,
)

from dao_ai.apps.resources import (
    assert_app_space_unchanged,
    generate_app_yaml,
    is_shared_space_principal,
    validate_app_space,
)
from dao_ai.config import (
    AgentModel,
    AppConfig,
    AppModel,
    AppSpaceModel,
    InferenceEndpointModel,
    ServicePrincipalModel,
)

DATA_AI_SCOPES: list[str] = [
    "sql:restricted-query",
    "genie",
    "catalog.catalogs:read",
    "catalog.schemas:read",
    "catalog.tables:read",
    "files",
    "model-serving",
    "ai-functions",
    "ai-gateway",
    "mcp.external",
    "mcp.functions",
    "iam.current-user:read",
    "iam.access-control:read",
]

WAREHOUSE: dict[str, Any] = {
    "name": "sql-warehouse",
    "sql_warehouse": {"id": "abc123", "permission": "CAN_USE"},
}
EXPERIMENT: dict[str, Any] = {
    "name": "experiment",
    "experiment": {"experiment_id": "42", "permission": "CAN_EDIT"},
}


def _space(
    *,
    state: SpaceStatusSpaceState = SpaceStatusSpaceState.SPACE_ACTIVE,
    scopes: list[str] | None = None,
    resources: list[AppResource] | None = None,
    service_principal_client_id: str | None = None,
) -> Space:
    return Space(
        name="team-space",
        id="space-id",
        status=SpaceStatus(state=state, message="Space is ready."),
        effective_user_api_scopes=DATA_AI_SCOPES if scopes is None else scopes,
        resources=resources,
        service_principal_client_id=service_principal_client_id,
    )


def _client(space: Space | Exception) -> MagicMock:
    w = MagicMock()
    if isinstance(space, Exception):
        w.apps.get_space.side_effect = space
    else:
        w.apps.get_space.return_value = space
    return w


def _app(**fields: Any) -> AppModel:
    return AppModel(
        name="space-agent",
        agents=[
            AgentModel(
                name="greeter",
                description="test agent",
                model=InferenceEndpointModel(name="databricks-gpt-5-4-mini"),
            )
        ],
        **fields,
    )


def _config(**app_fields: Any) -> AppConfig:
    return AppConfig(app=_app(app_space="team-space", **app_fields))


@pytest.mark.unit
class TestAppSpaceConfig:
    def test_bare_name_is_coerced(self) -> None:
        app = _app(app_space="team-space")
        assert isinstance(app.app_space, AppSpaceModel)
        assert app.app_space.resolved_name == "team-space"

    def test_mapping_form_is_accepted(self) -> None:
        app = _app(app_space={"name": "team-space"})
        assert app.app_space.resolved_name == "team-space"

    def test_unset_by_default(self) -> None:
        assert _app().app_space is None

    def test_deprecated_space_alias(self) -> None:
        with pytest.warns(DeprecationWarning, match="app_space"):
            app = _app(space="team-space")
        assert app.app_space.resolved_name == "team-space"

    def test_app_space_wins_over_deprecated_alias(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            app = _app(space="old", app_space="new")
        assert app.app_space.resolved_name == "new"

    def test_round_trips_through_yaml(self) -> None:
        dumped = _app(app_space="team-space").model_dump(exclude_none=True)
        assert dumped["app_space"] == {"name": "team-space"}
        reparsed = AppModel(**yaml.safe_load(yaml.safe_dump(dumped)))
        assert reparsed.app_space.resolved_name == "team-space"


@pytest.mark.unit
class TestResolve:
    def test_missing_space_fails_fast(self) -> None:
        w = _client(NotFound("nope"))
        with pytest.raises(ValueError, match="does not exist"):
            AppSpaceModel(name="team-space").resolve(w)

    def test_inactive_space_fails_fast(self) -> None:
        w = _client(_space(state=SpaceStatusSpaceState.SPACE_CREATING))
        with pytest.raises(ValueError, match="not active"):
            AppSpaceModel(name="team-space").resolve(w)

    def test_active_space_is_cached(self) -> None:
        w = _client(_space())
        model = AppSpaceModel(name="team-space")
        assert model.resolve(w) is model.resolve(w)
        w.apps.get_space.assert_called_once_with(name="team-space")


@pytest.mark.unit
class TestValidateAppSpace:
    def test_compatible_config_passes(self) -> None:
        w = _client(_space())
        space = validate_app_space(_config(), [EXPERIMENT], ["genie"], w=w)
        assert space.name == "team-space"

    def test_disallowed_scope_is_listed(self) -> None:
        w = _client(_space())
        with pytest.raises(ValueError, match=r"vector-search"):
            validate_app_space(_config(), [], ["vector-search", "genie"], w=w)

    def test_scope_aliases_are_equivalent(self) -> None:
        w = _client(_space())
        validate_app_space(
            _config(), [], ["dashboards.genie", "serving.serving-endpoints"], w=w
        )

    def test_mcp_companion_scopes_ignored_without_mcp_tools(self) -> None:
        w = _client(_space())
        validate_app_space(_config(), [], ["genie", "mcp.genie"], w=w)

    def test_unshared_resource_is_listed(self) -> None:
        w = _client(_space())
        with pytest.raises(ValueError, match=r"sql_warehouse abc123"):
            validate_app_space(_config(), [WAREHOUSE], [], w=w)

    def test_shared_resource_is_accepted(self) -> None:
        shared = AppResource(
            name="wh",
            sql_warehouse=AppResourceSqlWarehouse(
                id="ABC123",
                permission=AppResourceSqlWarehouseSqlWarehousePermission.CAN_USE,
            ),
        )
        w = _client(_space(resources=[shared]))
        validate_app_space(_config(), [WAREHOUSE], [], w=w)

    def test_experiment_resource_is_exempt(self) -> None:
        w = _client(_space())
        validate_app_space(_config(), [EXPERIMENT], [], w=w)

    def test_missing_secret_resource_suggests_uc_secret(self) -> None:
        secret = {
            "name": "s_k",
            "secret": {"scope": "s", "key": "k", "permission": "READ"},
        }
        w = _client(_space())
        with pytest.raises(ValueError) as exc:
            validate_app_space(_config(), [secret], [], w=w)
        message = str(exc.value)
        assert "secret s/k" in message
        assert "Unity Catalog secret" in message
        assert "on_behalf_of_user" not in message

    def test_all_problems_reported_together(self) -> None:
        config = _config(
            workload_size="Large",
            service_principal=ServicePrincipalModel(
                client_id="cid", client_secret="secret"
            ),
        )
        w = _client(_space())
        with pytest.raises(ValueError) as exc:
            validate_app_space(config, [WAREHOUSE], ["vector-search"], w=w)
        message = str(exc.value)
        for expected in (
            "service_principal",
            "workload_size=Large",
            "vector-search",
            "sql_warehouse",
        ):
            assert expected in message


@pytest.mark.unit
class TestSharedPrincipal:
    def test_beta_space_without_principal(self) -> None:
        assert not is_shared_space_principal(_space(), "app-sp")

    def test_matching_shared_principal(self) -> None:
        space = _space(service_principal_client_id="space-sp")
        assert is_shared_space_principal(space, "space-sp")
        assert not is_shared_space_principal(space, "app-sp")


@pytest.mark.unit
class TestAssertAppSpaceUnchanged:
    def test_new_app_is_fine(self) -> None:
        w = MagicMock()
        w.apps.get.side_effect = NotFound("missing")
        assert_app_space_unchanged(w, "space-agent", "team-space")

    def test_same_space_is_fine(self) -> None:
        w = MagicMock()
        w.apps.get.return_value = App(name="space-agent", space="team-space")
        assert_app_space_unchanged(w, "space-agent", "team-space")

    def test_standalone_app_is_refused(self) -> None:
        w = MagicMock()
        w.apps.get.return_value = App(name="space-agent")
        with pytest.raises(ValueError, match="outside any App Space"):
            assert_app_space_unchanged(w, "space-agent", "team-space")

    def test_other_space_is_refused(self) -> None:
        w = MagicMock()
        w.apps.get.return_value = App(name="space-agent", space="other")
        with pytest.raises(ValueError, match="in App Space 'other'"):
            assert_app_space_unchanged(w, "space-agent", "team-space")


@pytest.mark.unit
class TestGenerateAppYaml:
    def _env(self, content: str) -> dict[str, dict[str, str]]:
        return {e["name"]: e for e in yaml.safe_load(content)["env"]}

    def test_experiment_bound_by_resource_by_default(self) -> None:
        env = self._env(generate_app_yaml(_config(), include_resources=False))
        assert env["MLFLOW_EXPERIMENT_ID"] == {
            "name": "MLFLOW_EXPERIMENT_ID",
            "valueFrom": "experiment",
        }

    def test_experiment_pinned_literally_when_given(self) -> None:
        env = self._env(
            generate_app_yaml(_config(), include_resources=False, experiment_id="42")
        )
        assert env["MLFLOW_EXPERIMENT_ID"] == {
            "name": "MLFLOW_EXPERIMENT_ID",
            "value": "42",
        }
