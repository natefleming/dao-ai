"""`agent up` rebuild decision for an already-staged bundle.

Regression: `up --overwrite -s DIR` ignored --overwrite for a user-supplied
staging dir, so an edited config was silently deployed from the stale staged
copy.
"""

from argparse import Namespace
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dao_ai import cli


def _options(staging_dir: Path, *, overwrite: bool) -> Namespace:
    return Namespace(
        mode="model_serving",
        as_mcp=False,
        with_connection=False,
        direct=False,
        overwrite=overwrite,
        development=None,
        staging_dir=str(staging_dir),
        config="agent.yaml",
        dry_run=True,
        profile=None,
        var=[],
    )


def _run_up(
    tmp_path: Path, *, overwrite: bool, is_default_dir: bool, stale: bool
) -> MagicMock:
    (tmp_path / "databricks.yaml").write_text("bundle: {}\n")
    stage = MagicMock()
    with (
        patch.object(cli, "_load_app_config", return_value=MagicMock(unsafe=True)),
        patch.object(
            cli, "_resolve_bundle_dir", return_value=(tmp_path, is_default_dir)
        ),
        patch.object(cli, "_config_checksum", return_value="checksum"),
        patch.object(cli, "_staged_config_is_stale", return_value=stale),
        patch.object(cli, "_mode_writer", return_value=MagicMock()),
        patch.object(cli, "_stage_app_bundle", stage),
        patch.object(cli, "_run_ms_job_bundle"),
    ):
        cli._deploy_run_destroy_app_bundle(
            _options(tmp_path, overwrite=overwrite),
            kind="agent",
            deploy=True,
            run=True,
            destroy=False,
        )
    return stage


@pytest.mark.unit
@pytest.mark.parametrize("is_default_dir", [True, False])
def test_overwrite_restages_any_staging_dir(tmp_path: Path, is_default_dir: bool):
    stage = _run_up(tmp_path, overwrite=True, is_default_dir=is_default_dir, stale=True)

    stage.assert_called_once()
    assert stage.call_args.kwargs["overwrite"] is True
    assert stage.call_args.kwargs["is_default_dir"] is is_default_dir


@pytest.mark.unit
def test_stale_default_dir_restages_without_overwrite(tmp_path: Path):
    stage = _run_up(tmp_path, overwrite=False, is_default_dir=True, stale=True)

    stage.assert_called_once()


@pytest.mark.unit
def test_stale_user_dir_is_not_restaged_without_overwrite(tmp_path: Path):
    stage = _run_up(tmp_path, overwrite=False, is_default_dir=False, stale=True)

    stage.assert_not_called()


@pytest.mark.unit
def test_current_default_dir_is_not_restaged(tmp_path: Path):
    stage = _run_up(tmp_path, overwrite=False, is_default_dir=True, stale=False)

    stage.assert_not_called()
