"""Express-deployment (``register_model(env_pack=...)``) selection and wiring."""

import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import mlflow
import pytest
from mlflow.utils.env_pack import EnvPackConfig

from dao_ai.config import AppConfig
from dao_ai.providers.databricks import (
    DatabricksProvider,
    _express_env_pack,
    _missing_requirements,
    _prepare_express_env,
)

EXPRESS_CONFIGS: Path = Path(__file__).parents[1] / "config" / "express"
BASIC: Path = EXPRESS_CONFIGS / "basic" / "express_basic.yaml"
CODE: Path = EXPRESS_CONFIGS / "express_code.yaml"
FULL: Path = EXPRESS_CONFIGS / "express_full.yaml"

RUNNING_PYTHON: str = f"{sys.version_info.major}.{sys.version_info.minor}"


def _set_runtime(
    monkeypatch: pytest.MonkeyPatch, runtime: str | None, arch: str | None
) -> None:
    for name, value in (
        ("DATABRICKS_RUNTIME_VERSION", runtime),
        ("DATABRICKS_CPU_ARCH", arch),
    ):
        if value is None:
            monkeypatch.delenv(name, raising=False)
        else:
            monkeypatch.setenv(name, value)


@pytest.fixture
def basic_config() -> AppConfig:
    config: AppConfig = AppConfig.from_file(path=BASIC.as_posix())
    config.app.python_version = RUNNING_PYTHON
    return config


@pytest.mark.unit
def test_express_deployment_defaults_on(basic_config: AppConfig) -> None:
    assert basic_config.app.express_deployment is True
    dumped: dict[str, Any] = basic_config.app.model_dump(exclude_none=True)
    assert dumped["express_deployment"] is True


@pytest.mark.unit
@pytest.mark.parametrize("arch", ["x86_64", "amd64", None])
def test_env_pack_on_x86_serverless(
    monkeypatch: pytest.MonkeyPatch, basic_config: AppConfig, arch: str | None
) -> None:
    _set_runtime(monkeypatch, "client.5.12", arch)
    with patch("dao_ai.providers.databricks.platform.machine", return_value="x86_64"):
        env_pack = _express_env_pack(basic_config)

    assert env_pack == EnvPackConfig(
        name="databricks_model_serving", install_dependencies=False
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    ("runtime", "arch"),
    [
        (None, "x86_64"),  # local machine / CI
        ("15.4", "x86_64"),  # classic cluster
        ("client.5.12", "aarch64"),  # ARM serverless job
        ("client.5.12", "ARM64"),
    ],
)
def test_env_pack_skipped_off_x86_serverless(
    monkeypatch: pytest.MonkeyPatch,
    basic_config: AppConfig,
    runtime: str | None,
    arch: str,
) -> None:
    _set_runtime(monkeypatch, runtime, arch)
    assert _express_env_pack(basic_config) is None


@pytest.mark.unit
def test_env_pack_skipped_when_disabled(
    monkeypatch: pytest.MonkeyPatch, basic_config: AppConfig
) -> None:
    _set_runtime(monkeypatch, "client.5.12", "x86_64")
    basic_config.app.express_deployment = False
    assert _express_env_pack(basic_config) is None


@pytest.mark.unit
def test_env_pack_arm_falls_back_to_platform_machine(
    monkeypatch: pytest.MonkeyPatch, basic_config: AppConfig
) -> None:
    _set_runtime(monkeypatch, "client.5.12", None)
    with patch("dao_ai.providers.databricks.platform.machine", return_value="aarch64"):
        assert _express_env_pack(basic_config) is None


@pytest.mark.unit
def test_env_pack_warns_on_python_version_mismatch(
    monkeypatch: pytest.MonkeyPatch, basic_config: AppConfig
) -> None:
    _set_runtime(monkeypatch, "client.5.12", "x86_64")
    basic_config.app.python_version = "3.9"
    with patch("dao_ai.providers.databricks.logger") as mock_logger:
        assert _express_env_pack(basic_config) is not None

    warnings: list[str] = [c.args[0] for c in mock_logger.warning.call_args_list]
    assert any("python_version is ignored" in w for w in warnings)


def _run_create_agent(
    config: AppConfig, pip_side_effect: Exception | None = None
) -> dict[str, Any]:
    """Run a published-mode ``create_agent`` with MLflow mocked; return the
    captured ``register_model`` / ``log_model`` arguments."""
    experiment = MagicMock(experiment_id="exp-1", name="/Users/test/express")
    with (
        patch.object(
            DatabricksProvider, "get_or_create_experiment", return_value=experiment
        ),
        patch.object(mlflow, "set_experiment"),
        patch.object(mlflow, "set_registry_uri"),
        patch.object(mlflow, "start_run"),
        patch.object(mlflow, "set_tag"),
        patch.object(
            mlflow.pyfunc,
            "log_model",
            return_value=MagicMock(model_uri="runs:/1/agent"),
        ) as mock_log_model,
        patch.object(
            mlflow, "register_model", return_value=MagicMock(version="1")
        ) as mock_register,
        patch("dao_ai.providers.databricks.MlflowClient"),
        patch("dao_ai.utils.is_published", return_value=True),
        # Express installs requirements the running env lacks; never pip for real.
        patch(
            "dao_ai.providers.databricks.subprocess.run", side_effect=pip_side_effect
        ),
    ):
        DatabricksProvider(w=MagicMock()).create_agent(config=config, development=False)

    log_kwargs: dict[str, Any] = mock_log_model.call_args.kwargs
    return {
        "env_pack": mock_register.call_args.kwargs["env_pack"],
        "code_paths": log_kwargs["code_paths"],
        "pip": log_kwargs["conda_env"]["dependencies"][-1]["pip"],
    }


@pytest.mark.unit
@pytest.mark.parametrize(
    ("config_path", "expected_code", "expected_pip"),
    [
        (BASIC, [], []),
        (CODE, ["express_lib", "express_tools", "skills"], []),
        (
            FULL,
            ["express_lib", "express_tools", "skills"],
            ["humanize>=4.0", "rapidfuzz>=3.0"],
        ),
    ],
    ids=["basic", "code", "full"],
)
def test_create_agent_registers_with_env_pack_and_keeps_artifacts(
    monkeypatch: pytest.MonkeyPatch,
    config_path: Path,
    expected_code: list[str],
    expected_pip: list[str],
) -> None:
    """Express must not drop custom code, skills, or user pip requirements."""
    _set_runtime(monkeypatch, "client.5.12", "x86_64")
    config: AppConfig = AppConfig.from_file(path=config_path.as_posix())

    captured: dict[str, Any] = _run_create_agent(config)

    assert captured["env_pack"] == EnvPackConfig(
        name="databricks_model_serving", install_dependencies=False
    )
    shipped: list[str] = [Path(p).name for p in captured["code_paths"]]
    for name in expected_code:
        assert name in shipped, f"{name} missing from code_paths: {shipped}"
    for req in expected_pip:
        assert req in captured["pip"], f"{req} missing from pip: {captured['pip']}"


@pytest.mark.unit
def test_create_agent_registers_without_env_pack_off_serverless(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_runtime(monkeypatch, None, None)
    config: AppConfig = AppConfig.from_file(path=FULL.as_posix())

    captured: dict[str, Any] = _run_create_agent(config)

    assert captured["env_pack"] is None
    assert "humanize>=4.0" in captured["pip"]


@pytest.mark.unit
def test_missing_requirements_reports_only_unsatisfied() -> None:
    pytest_version: str = pytest.__version__
    missing: list[str] = _missing_requirements(
        [
            f"pytest=={pytest_version}",  # satisfied
            "pytest<1",  # installed, wrong version
            "dao-ai-nonexistent-package-xyz",  # not installed
            "code/dao_ai-0.0.0-py3-none-any.whl",  # dev wheel: skipped
            "pytest<1; python_version < '3.0'",  # marker false: skipped
            "git+https://example.com/repo.git",  # unparseable: reported
        ]
    )
    assert missing == [
        "pytest<1",
        "dao-ai-nonexistent-package-xyz",
        "git+https://example.com/repo.git",
    ]


@pytest.mark.unit
def test_prepare_express_env_noop_when_satisfied() -> None:
    env_pack = EnvPackConfig(
        name="databricks_model_serving", install_dependencies=False
    )
    with patch("dao_ai.providers.databricks.subprocess.run") as mock_run:
        assert (
            _prepare_express_env(env_pack, [f"pytest=={pytest.__version__}"])
            is env_pack
        )
    mock_run.assert_not_called()


@pytest.mark.unit
def test_prepare_express_env_installs_missing() -> None:
    env_pack = EnvPackConfig(
        name="databricks_model_serving", install_dependencies=False
    )
    with patch("dao_ai.providers.databricks.subprocess.run") as mock_run:
        result = _prepare_express_env(
            env_pack, ["code/dao_ai.whl", "dao-ai-nonexistent-package-xyz>=1"]
        )

    assert result is env_pack
    args: list[str] = mock_run.call_args.args[0]
    assert args[:4] == [sys.executable, "-m", "pip", "install"]
    assert args[-1] == "dao-ai-nonexistent-package-xyz>=1"
    assert "code/dao_ai.whl" not in args


@pytest.mark.unit
def test_prepare_express_env_falls_back_when_install_fails() -> None:
    env_pack = EnvPackConfig(
        name="databricks_model_serving", install_dependencies=False
    )
    with patch(
        "dao_ai.providers.databricks.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "pip", output="no such package"),
    ):
        assert (
            _prepare_express_env(env_pack, ["dao-ai-nonexistent-package-xyz"]) is None
        )


@pytest.mark.unit
def test_create_agent_falls_back_when_requirements_cannot_install(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A notebook env missing user pip requirements must not be packed incomplete."""
    _set_runtime(monkeypatch, "client.6.3", "x86_64")
    config: AppConfig = AppConfig.from_file(path=FULL.as_posix())
    config.app.python_version = RUNNING_PYTHON

    captured: dict[str, Any] = _run_create_agent(
        config,
        pip_side_effect=subprocess.CalledProcessError(1, "pip", output="offline"),
    )

    assert captured["env_pack"] is None


@pytest.mark.unit
def test_create_agent_installs_requirements_before_log_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``log_model`` imports the model, so missing requirements must be installed
    first: a tool module that imports a pip requirement at load time would
    otherwise fail the log before anything is packed."""
    _set_runtime(monkeypatch, "client.6.3", "x86_64")
    config: AppConfig = AppConfig.from_file(path=FULL.as_posix())
    config.app.python_version = RUNNING_PYTHON

    order: list[str] = []
    with (
        patch(
            "dao_ai.providers.databricks._prepare_express_env",
            side_effect=lambda env_pack, _: order.append("prepare") or env_pack,
        ),
        patch.object(
            mlflow.pyfunc,
            "log_model",
            side_effect=lambda **_: (
                order.append("log_model") or MagicMock(model_uri="runs:/1/agent")
            ),
        ),
        patch.object(DatabricksProvider, "get_or_create_experiment"),
        patch.object(mlflow, "set_experiment"),
        patch.object(mlflow, "set_registry_uri"),
        patch.object(mlflow, "start_run"),
        patch.object(mlflow, "set_tag"),
        patch.object(mlflow, "register_model", return_value=MagicMock(version="1")),
        patch("dao_ai.providers.databricks.MlflowClient"),
        patch("dao_ai.utils.is_published", return_value=True),
    ):
        DatabricksProvider(w=MagicMock()).create_agent(config=config, development=False)

    assert order == ["prepare", "log_model"]
