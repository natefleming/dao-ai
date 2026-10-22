"""Express-deployment requirement handling in a real Databricks serverless env.

Runs ``tests/scripts/express_spike/03_express_scenarios.py`` as a one-time
serverless job against the dev wheel built from this checkout, then asserts on
the JSON it returns. Opt-in: set ``DAO_AI_EXPRESS_IT_PROFILE`` to a Databricks
CLI profile (it uses real compute and needs internet access for pip).
"""

import base64
import json
import os
import uuid
from pathlib import Path
from typing import Any

import pytest
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import compute, jobs
from databricks.sdk.service.workspace import ImportFormat, Language

from dao_ai.providers.databricks import _build_wheel

PROFILE: str | None = os.environ.get("DAO_AI_EXPRESS_IT_PROFILE")
REPO_ROOT: Path = Path(__file__).parents[2]
SCENARIOS: Path = (
    REPO_ROOT / "tests" / "scripts" / "express_spike" / "03_express_scenarios.py"
)

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    # One serverless run: cold start + pip installs take several minutes.
    pytest.mark.timeout(1800),
    pytest.mark.skipif(not PROFILE, reason="DAO_AI_EXPRESS_IT_PROFILE not set"),
]


@pytest.fixture(scope="module")
def scenario_results() -> dict[str, Any]:
    w = WorkspaceClient(profile=PROFILE)
    folder: str = f"/Users/{w.current_user.me().user_name}/.dao_ai_express_it/{uuid.uuid4().hex[:8]}"
    w.workspace.mkdirs(folder)
    try:
        wheel: Path = _build_wheel(REPO_ROOT)
        wheel_path: str = f"{folder}/{wheel.name}"
        w.workspace.upload(wheel_path, wheel.read_bytes(), format=ImportFormat.AUTO)
        w.workspace.import_(
            f"{folder}/scenarios",
            content=base64.b64encode(SCENARIOS.read_bytes()).decode(),
            format=ImportFormat.SOURCE,
            language=Language.PYTHON,
            overwrite=True,
        )
        run = w.jobs.submit_and_wait(
            run_name="dao-ai-express-integration",
            tasks=[
                jobs.SubmitTask(
                    task_key="scenarios",
                    notebook_task=jobs.NotebookTask(
                        notebook_path=f"{folder}/scenarios",
                        base_parameters={"wheel": f"/Workspace{wheel_path}"},
                    ),
                    environment_key="env",
                )
            ],
            environments=[
                jobs.JobEnvironment(
                    environment_key="env",
                    # psycopg pinned like the deploy-job environment: an
                    # unpinned resolve can pull a libpq binary that aborts the
                    # interpreter on ARM serverless at import time.
                    spec=compute.Environment(
                        environment_version="5",
                        dependencies=["psycopg[binary,pool]==3.3.4"],
                    ),
                )
            ],
        )
        # Serverless retries a failed attempt (e.g. on another architecture);
        # the final attempt is the one whose output counts.
        final = max(run.tasks, key=lambda t: t.attempt_number or 0)
        output = w.jobs.get_run_output(final.run_id)
        assert output.notebook_output and output.notebook_output.result, (
            f"scenario run produced no result: {output.error} {output.error_trace}"
        )
        return json.loads(output.notebook_output.result)
    finally:
        w.workspace.delete(folder, recursive=True)


def test_runs_on_serverless(scenario_results: dict[str, Any]) -> None:
    assert scenario_results["runtime"].startswith("client.")


def test_conflicting_requirement_falls_back_untouched(
    scenario_results: dict[str, Any],
) -> None:
    conflict = scenario_results["conflict"]
    assert conflict == {"detected_missing": True, "fell_back": True, "unchanged": True}


def test_missing_requirement_installed_with_constraints(
    scenario_results: dict[str, Any],
) -> None:
    """The constraints file built from the real serverless image is accepted."""
    add = scenario_results["add"]
    assert not add["was_installed"]
    assert add["detected_missing"] and add["kept_express"]
    assert add["now_installed"]


def test_extras_detected_and_handled_without_changing_installed(
    scenario_results: dict[str, Any],
) -> None:
    extras = scenario_results["extras"]
    assert extras["uvicorn_version"], "uvicorn should come with dao-ai"
    assert extras["detected_missing"]
    assert extras["uvicorn_unchanged"]
    if extras["kept_express"]:
        assert extras["satisfied_after"] and extras["uvloop_after"]


def test_url_requirement_reported_missing(scenario_results: dict[str, Any]) -> None:
    assert scenario_results["url"]["detected_missing"]


def test_dev_wheel_check(scenario_results: dict[str, Any]) -> None:
    dev_wheel = scenario_results["dev_wheel"]
    assert "+dev" in dev_wheel["installed"]
    assert dev_wheel["match_ok"]
    assert dev_wheel["mismatch_detected"] and dev_wheel["mismatch_falls_back"]


def test_pip_never_changed_an_installed_package(
    scenario_results: dict[str, Any],
) -> None:
    assert scenario_results["changed_versions"] == {}
    assert scenario_results["removed"] == []
    assert "humanize" in scenario_results["added"]
