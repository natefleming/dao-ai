"""Every shipped example YAML loads through ``AppConfig``.

The examples are the documented surface of the config schema, and they are
edited whenever a field is renamed or a default moves. Nothing checked that
they still parse: ``test_git_source.py`` walks the same tree but only asserts
the *discovery* heuristic recognizes them as dao-ai configs, which a config
with a bad field passes fine.

``initialize=False`` keeps this offline — no workspace client, no resource
resolution — so it stays a pure schema check.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from dao_ai.config import AppConfig
from dao_ai.config_vars import ConfigVariableError, WorkspaceVariableError

EXAMPLES: Path = Path(__file__).parents[2] / "examples"

# Files that live under examples/ but are not dao-ai configs. Same set as
# ``test_git_source.py::test_every_shipped_example_config_is_recognized``.
NOT_CONFIGS: frozenset[str] = frozenset(
    {"examples.yaml", "app.yaml", "environment.yaml"}
)

# Known-broken example, failing before this test existed: every agent requires
# a ``model``, and ``general_agent`` declares none. Listed rather than skipped
# silently so fixing it is a one-line deletion here.
KNOWN_INVALID: frozenset[str] = frozenset(
    {"12_middleware/tool_selector_middleware.yaml"}
)


def _example_configs() -> list[Path]:
    if not EXAMPLES.is_dir():
        return []
    return sorted(
        path
        for path in EXAMPLES.rglob("*.yaml")
        if path.name not in NOT_CONFIGS
        and path.relative_to(EXAMPLES).as_posix() not in KNOWN_INVALID
    )


def _load_example(config_path: Path) -> AppConfig:
    """Load an example config offline, tolerating the two legitimate reasons a
    shipped example can't be parsed with no caller input.

    - ``WorkspaceVariableError``: the example uses ``${workspace.*}`` (e.g.
      current_user), resolved at load time against a live WorkspaceClient
      regardless of ``initialize=False``. Skip — the parse reached variable
      resolution, which is as far as an offline check can go.
    - ``ConfigVariableError`` with only *missing required* params: an example
      may legitimately require caller-supplied identifiers (catalog, schema,
      Genie space IDs). That is not an authoring error — fill the
      declared-but-unset params with placeholders and re-validate, so the schema
      is still fully exercised offline rather than skipped. An ``undeclared``
      reference (a ``${var.X}`` nobody declared) IS a real authoring bug and
      still fails. If the ``"placeholder"`` string can't satisfy a typed or
      format-validated required field (a numeric id, an enum, an N-part UC name),
      the re-validate raises ``ValidationError`` — skip, since a valid value
      can't be synthesized offline; the parse still reached schema validation.
    """
    try:
        return AppConfig.from_file(config_path, initialize=False)
    except WorkspaceVariableError as exc:
        pytest.skip(f"needs workspace auth: {exc}")
    except ConfigVariableError as exc:
        if exc.undeclared:
            raise
        placeholders = {name: "placeholder" for name in exc.missing_required}
        try:
            return AppConfig.from_file(
                config_path, params=placeholders, initialize=False
            )
        except ValidationError as verr:
            pytest.skip(f"required param needs a real value: {verr}")


@pytest.mark.unit
@pytest.mark.parametrize(
    "config_path", _example_configs(), ids=lambda p: p.relative_to(EXAMPLES).as_posix()
)
def test_every_shipped_example_validates(config_path: Path) -> None:
    _load_example(config_path)


@pytest.mark.unit
@pytest.mark.parametrize(
    "config_path", _example_configs(), ids=lambda p: p.relative_to(EXAMPLES).as_posix()
)
def test_no_example_provisions_a_schema_in_the_system_catalog(
    config_path: Path,
) -> None:
    """Entries under top-level ``schemas:`` are provisioned (CREATE SCHEMA) and
    SP-granted at deploy (``01_ingest_and_transform.py``, ``service_principal``).
    The reserved ``system`` catalog is neither — deploying such an example
    fails or over-privileges. To qualify a UC-securable model name, the schema
    belongs *inline* on the model, which is not provisioned. (PR #294 review:
    the AI Gateway example declared ``system.ai`` here.)"""
    config = _load_example(config_path)

    offenders = [
        key
        for key, schema in (config.schemas or {}).items()
        if (schema.catalog_name or "").lower() == "system"
    ]
    assert not offenders, (
        f"{config_path.relative_to(EXAMPLES)} declares top-level schema(s) "
        f"{offenders} in the reserved 'system' catalog; put the schema inline "
        f"on the model instead."
    )


@pytest.mark.unit
def test_the_example_walk_actually_found_configs() -> None:
    """Guards the guard: an empty parametrize list would make this file green
    while checking nothing."""
    if not EXAMPLES.is_dir():
        pytest.skip("examples/ not present in this checkout")
    assert len(_example_configs()) > 50
