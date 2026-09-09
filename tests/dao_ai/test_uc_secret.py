"""Tests for Unity Catalog secrets as a dao-ai credential source.

Covers the ``UnityCatalogSecretModel`` variable, its place in the
``AnyVariable`` union, the ``get_uc_secret`` provider read path, the
``is_uc_secret_variable`` guard used by the deploy env-var injection paths,
and the deploy-time READ SECRET grant (collector + grant helper).
"""

from unittest.mock import MagicMock, patch

import pytest
from databricks.sdk.errors import NotFound
from pydantic import TypeAdapter, ValidationError

from dao_ai.config import (
    AnyVariable,
    CompositeVariableModel,
    EnvironmentVariableModel,
    SecretVariableModel,
    UnityCatalogSecretModel,
    is_uc_secret_variable,
)


@pytest.mark.unit
def test_uc_secret_short_name_with_schema() -> None:
    m = UnityCatalogSecretModel.model_validate(
        {"schema": {"catalog_name": "main", "schema_name": "default"}, "name": "k"}
    )
    assert m.full_name == "main.default.k"


@pytest.mark.unit
def test_uc_secret_fully_qualified_name_without_schema() -> None:
    m = UnityCatalogSecretModel.model_validate({"name": "main.default.k"})
    assert m.schema_model is None
    assert m.full_name == "main.default.k"


@pytest.mark.unit
def test_uc_secret_requires_qualified_name_without_schema() -> None:
    with pytest.raises(ValidationError):
        UnityCatalogSecretModel.model_validate({"name": "bare_key"})


@pytest.mark.unit
def test_uc_secret_alias_round_trip() -> None:
    """``schema`` alias must round-trip so dump/reload survives extra=forbid."""
    m = UnityCatalogSecretModel.model_validate(
        {"schema": {"catalog_name": "main", "schema_name": "default"}, "name": "k"}
    )
    dumped = m.model_dump(by_alias=True)
    assert "schema" in dumped and "schema_model" not in dumped
    reloaded = UnityCatalogSecretModel.model_validate(dumped)
    assert reloaded.full_name == "main.default.k"


@pytest.mark.unit
def test_any_variable_union_discrimination() -> None:
    """Disjoint required fields keep the untagged union unambiguous."""
    ta: TypeAdapter = TypeAdapter(AnyVariable)
    scope_secret = ta.validate_python({"scope": "s", "secret": "k"})
    uc_secret = ta.validate_python(
        {"schema": {"catalog_name": "main", "schema_name": "default"}, "name": "k"}
    )
    uc_fq = ta.validate_python({"name": "main.default.k"})
    assert isinstance(scope_secret, SecretVariableModel)
    assert isinstance(uc_secret, UnityCatalogSecretModel)
    assert isinstance(uc_fq, UnityCatalogSecretModel)


@pytest.mark.unit
def test_uc_secret_in_variables_registry() -> None:
    """The reusable ``variables:`` registry (dict[str, AnyVariable]) UX."""
    ta: TypeAdapter = TypeAdapter(dict[str, AnyVariable])
    variables = ta.validate_python(
        {
            "sp_secret": {
                "schema": {"catalog_name": "main", "schema_name": "default"},
                "name": "client_secret",
            }
        }
    )
    assert isinstance(variables["sp_secret"], UnityCatalogSecretModel)
    assert variables["sp_secret"].full_name == "main.default.client_secret"


@pytest.mark.unit
def test_uc_secret_as_value_reads_via_provider() -> None:
    m = UnityCatalogSecretModel.model_validate({"name": "main.default.k"})
    with patch("dao_ai.providers.databricks.DatabricksProvider") as provider_cls:
        provider_cls.return_value.get_uc_secret.return_value = "resolved-value"
        assert m.as_value() == "resolved-value"
        provider_cls.return_value.get_uc_secret.assert_called_once_with(
            "main.default.k", None
        )


@pytest.mark.unit
def test_composite_with_uc_secret_option() -> None:
    c = CompositeVariableModel.model_validate(
        {
            "options": [
                {
                    "schema": {"catalog_name": "main", "schema_name": "default"},
                    "name": "k",
                }
            ]
        }
    )
    assert isinstance(c.options[0], UnityCatalogSecretModel)


@pytest.mark.unit
def test_is_uc_secret_variable() -> None:
    uc = UnityCatalogSecretModel.model_validate({"name": "main.default.k"})
    assert is_uc_secret_variable(uc) is True
    assert is_uc_secret_variable(CompositeVariableModel(options=[uc])) is True
    assert is_uc_secret_variable(SecretVariableModel(scope="s", secret="k")) is False
    assert is_uc_secret_variable(EnvironmentVariableModel(env="X")) is False
    assert is_uc_secret_variable("literal") is False


@pytest.mark.unit
def test_get_uc_secret_success() -> None:
    """Reads the value via the typed secrets_uc.get_secret (include_value=True)."""
    from dao_ai.providers.databricks import DatabricksProvider

    w = MagicMock()
    w.secrets_uc.get_secret.return_value = MagicMock(effective_value="super-secret")
    provider = DatabricksProvider(w=w)
    assert provider.get_uc_secret("main.default.k") == "super-secret"
    w.secrets_uc.get_secret.assert_called_once_with(
        "main.default.k", include_value=True
    )


@pytest.mark.unit
def test_get_uc_secret_no_value_returns_default() -> None:
    """effective_value is None (no READ SECRET) → fall back to default."""
    from dao_ai.providers.databricks import DatabricksProvider

    w = MagicMock()
    w.secrets_uc.get_secret.return_value = MagicMock(effective_value=None)
    provider = DatabricksProvider(w=w)
    assert provider.get_uc_secret("main.default.k", "fallback") == "fallback"


@pytest.mark.unit
def test_get_uc_secret_not_found_returns_default() -> None:
    from dao_ai.providers.databricks import DatabricksProvider

    w = MagicMock()
    w.secrets_uc.get_secret.side_effect = NotFound("nope")
    provider = DatabricksProvider(w=w)
    assert provider.get_uc_secret("main.default.missing", "fallback") == "fallback"


@pytest.mark.unit
def test_collect_uc_secret_full_names_walks_and_dedupes() -> None:
    from dao_ai.providers.databricks import _collect_uc_secret_full_names

    uc1 = UnityCatalogSecretModel.model_validate(
        {"schema": {"catalog_name": "main", "schema_name": "default"}, "name": "a"}
    )
    uc2 = UnityCatalogSecretModel.model_validate({"name": "main.default.b"})
    comp = CompositeVariableModel(
        options=[uc2, SecretVariableModel(scope="s", secret="k")]
    )
    tree = {"x": uc1, "y": [comp, "literal", 42], "z": {"w": uc1}}
    assert set(_collect_uc_secret_full_names(tree)) == {
        "main.default.a",
        "main.default.b",
    }


@pytest.mark.unit
def test_grant_uc_secret_read_to_principal() -> None:
    from dao_ai.providers.databricks import _grant_uc_secret_read_to_principal

    w = MagicMock()
    _grant_uc_secret_read_to_principal(w, "app-sp", ["main.default.a"])
    w.api_client.do.assert_called_once_with(
        "PATCH",
        "/api/2.1/unity-catalog/permissions/secret/main.default.a",
        body={"changes": [{"principal": "app-sp", "add": ["READ_SECRET"]}]},
    )


@pytest.mark.unit
def test_grant_uc_secret_read_is_graceful() -> None:
    """A grant failure (no MANAGE) is swallowed so the deploy still completes."""
    from dao_ai.providers.databricks import _grant_uc_secret_read_to_principal

    w = MagicMock()
    w.api_client.do.side_effect = Exception("PERMISSION_DENIED")
    _grant_uc_secret_read_to_principal(w, "app-sp", ["main.default.a"])  # no raise


@pytest.mark.unit
def test_uc_secret_skipped_in_app_env_var_injection() -> None:
    """UC secrets are not injectable as Apps env vars — they resolve at runtime."""
    from types import SimpleNamespace

    from dao_ai.apps.resources import _extract_env_vars_from_config

    uc = UnityCatalogSecretModel.model_validate({"name": "main.default.k"})
    scope = SecretVariableModel(scope="s", secret="k")
    cfg = SimpleNamespace(
        app=SimpleNamespace(
            environment_vars={"UC_CRED": uc, "SCOPE_CRED": scope, "PLAIN": "hi"}
        )
    )
    out = {e["name"]: e for e in _extract_env_vars_from_config(cfg)}
    assert "UC_CRED" not in out
    assert out["SCOPE_CRED"]["valueFrom"] == "s_k"
    assert out["PLAIN"]["value"] == "hi"
