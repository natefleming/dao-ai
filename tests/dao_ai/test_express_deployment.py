"""Express-deployment (``register_model(env_pack=...)``) selection and wiring."""

import importlib.metadata
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import mlflow
import pytest
from mlflow.utils.env_pack import EnvPackConfig
from packaging.requirements import Requirement

from dao_ai.config import AppConfig
from dao_ai.providers.databricks import (
    DatabricksProvider,
    _dev_wheel_mismatches,
    _express_env_pack,
    _installed_constraints,
    _missing_requirements,
    _prepare_express_env,
    _requirement_satisfied,
)

EXPRESS_CONFIGS: Path = Path(__file__).parents[1] / "config" / "express"
BASIC: Path = EXPRESS_CONFIGS / "basic" / "express_basic.yaml"
CODE: Path = EXPRESS_CONFIGS / "express_code.yaml"
FULL: Path = EXPRESS_CONFIGS / "express_full.yaml"

RUNNING_PYTHON: str = f"{sys.version_info.major}.{sys.version_info.minor}"
ENV_PACK = EnvPackConfig(name="databricks_model_serving", install_dependencies=False)
# A dev-wheel entry matching the dao-ai build installed in this environment.
INSTALLED_DEV_WHEEL: str = (
    f"code/dao_ai-{importlib.metadata.version('dao-ai')}-py3-none-any.whl"
)


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
    config: AppConfig,
    pip_side_effect: Exception | None = None,
    register_side_effect: Any = None,
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
            mlflow,
            "register_model",
            return_value=MagicMock(version="1"),
            side_effect=register_side_effect,
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
        # env_pack is only passed when express applies.
        "env_pack": mock_register.call_args.kwargs.get("env_pack"),
        "register_calls": [c.kwargs for c in mock_register.call_args_list],
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
            env_pack, [INSTALLED_DEV_WHEEL, "dao-ai-nonexistent-package-xyz>=1"]
        )

    assert result is env_pack
    args: list[str] = mock_run.call_args.args[0]
    assert args[:4] == [sys.executable, "-m", "pip", "install"]
    assert "--constraint" in args
    assert args[-1] == "dao-ai-nonexistent-package-xyz>=1"
    assert INSTALLED_DEV_WHEEL not in args


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


# --- Review fixes ----------------------------------------------------------------


def _fake_metadata(
    monkeypatch: pytest.MonkeyPatch,
    versions: dict[str, str],
    requires: dict[str, list[str]] | None = None,
) -> None:
    """Make the provider see exactly these installed distributions."""

    def version(name: str) -> str:
        try:
            return versions[name]
        except KeyError:
            raise importlib.metadata.PackageNotFoundError(name) from None

    monkeypatch.setattr(
        "dao_ai.providers.databricks.importlib.metadata.version", version
    )
    monkeypatch.setattr(
        "dao_ai.providers.databricks.importlib.metadata.requires",
        lambda name: (requires or {}).get(name),
    )


@pytest.mark.unit
def test_extras_unsatisfied_when_extra_dependency_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``pkg[extra]==X`` needs the extra's dependencies, not just pkg X (#1)."""
    _fake_metadata(
        monkeypatch,
        versions={"dao-ai": "1.0", "base-dep": "2.0"},
        requires={
            "dao-ai": [
                "base-dep>=1",
                "vector-lib>=0.4; extra == 'search'",
                "other-lib>=1; extra == 'other'",
            ]
        },
    )
    assert _missing_requirements(["dao-ai[search]==1.0"]) == ["dao-ai[search]==1.0"]
    # The unrequested extra and the base package alone stay satisfied.
    assert _missing_requirements(["dao-ai[other]==1.0"]) == ["dao-ai[other]==1.0"]
    assert _missing_requirements(["dao-ai==1.0"]) == []


@pytest.mark.unit
def test_extras_satisfied_when_extra_dependencies_installed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fake_metadata(
        monkeypatch,
        versions={"dao-ai": "1.0", "vector-lib": "0.5"},
        requires={"dao-ai": ["vector-lib>=0.4; extra == 'search'"]},
    )
    assert _missing_requirements(["dao-ai[search]==1.0"]) == []


@pytest.mark.unit
def test_extras_checks_extra_dependency_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fake_metadata(
        monkeypatch,
        versions={"dao-ai": "1.0", "vector-lib": "0.1"},
        requires={"dao-ai": ["vector-lib>=0.4; extra == 'search'"]},
    )
    assert _missing_requirements(["dao-ai[search]==1.0"]) == ["dao-ai[search]==1.0"]


@pytest.mark.unit
def test_nested_extras_followed(monkeypatch: pytest.MonkeyPatch) -> None:
    """``dao-ai[all]`` lists ``dao-ai[search]``; its dependencies must count."""
    _fake_metadata(
        monkeypatch,
        versions={"dao-ai": "1.0"},
        requires={
            "dao-ai": [
                "dao-ai[search]; extra == 'all'",
                "vector-lib>=0.4; extra == 'search'",
            ]
        },
    )
    assert _missing_requirements(["dao-ai[all]==1.0"]) == ["dao-ai[all]==1.0"]


@pytest.mark.unit
def test_self_referencing_extra_terminates(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_metadata(
        monkeypatch,
        versions={"pkg": "1.0"},
        requires={"pkg": ["pkg[loop]; extra == 'loop'"]},
    )
    assert _requirement_satisfied(Requirement("pkg[loop]"))


@pytest.mark.unit
def test_url_requirement_always_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """An installed version can't prove it came from the pinned artifact (#5)."""
    _fake_metadata(monkeypatch, versions={"mylib": "1.0"})
    spec: str = "mylib @ https://example.com/mylib-2.0-py3-none-any.whl"
    assert _missing_requirements([spec]) == [spec]


@pytest.mark.unit
def test_marker_with_extra_does_not_raise(monkeypatch: pytest.MonkeyPatch) -> None:
    """Markers that reference ``extra`` evaluate as not-requested (#6)."""
    _fake_metadata(monkeypatch, versions={})
    assert _missing_requirements(['foo>=1; extra == "bar"']) == []


@pytest.mark.unit
@pytest.mark.parametrize(
    ("installed", "wheel", "mismatched"),
    [
        ("0.2.22+dev1", "code/dao_ai-0.2.22+dev1-py3-none-any.whl", False),
        ("0.2.22", "code/dao_ai-0.2.22+dev1-py3-none-any.whl", True),
        ("0.2.21", "code/dao_ai-0.2.22-py3-none-any.whl", True),
        (None, "code/dao_ai-0.2.22-py3-none-any.whl", True),
        ("0.2.22", "code/not-a-wheel.txt", True),
    ],
    ids=["match", "published-vs-dev", "older", "not-installed", "bad-name"],
)
def test_dev_wheel_mismatches(
    monkeypatch: pytest.MonkeyPatch,
    installed: str | None,
    wheel: str,
    mismatched: bool,
) -> None:
    """Express serves the packed env, so the dev wheel must already be installed (#4)."""
    _fake_metadata(monkeypatch, versions={"dao-ai": installed} if installed else {})
    assert _dev_wheel_mismatches([wheel, "humanize>=4"]) == (
        [wheel] if mismatched else []
    )


@pytest.mark.unit
def test_prepare_express_env_falls_back_on_dev_wheel_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fake_metadata(monkeypatch, versions={"dao-ai": "0.2.21"})
    with patch("dao_ai.providers.databricks.subprocess.run") as mock_run:
        assert (
            _prepare_express_env(ENV_PACK, ["code/dao_ai-0.2.22-py3-none-any.whl"])
            is None
        )
    mock_run.assert_not_called()


@pytest.mark.unit
def test_installed_constraints_pin_running_environment() -> None:
    constraints: list[str] = _installed_constraints()
    assert f"pytest=={pytest.__version__}" in constraints
    assert len(constraints) == len({c.split("==")[0].lower() for c in constraints})


@pytest.mark.unit
def test_pip_install_constrained_to_installed_versions() -> None:
    """pip may only add packages, never change one already imported (#3)."""
    seen: dict[str, Any] = {}

    def fake_run(args: list[str], **_: Any) -> None:
        constraint_file: str = args[args.index("--constraint") + 1]
        seen["constraints"] = Path(constraint_file).read_text().splitlines()
        seen["args"] = args

    with patch("dao_ai.providers.databricks.subprocess.run", side_effect=fake_run):
        assert _prepare_express_env(ENV_PACK, ["dao-ai-nonexistent-xyz"]) is ENV_PACK

    assert f"pytest=={pytest.__version__}" in seen["constraints"]
    assert seen["args"][-1] == "dao-ai-nonexistent-xyz"


@pytest.mark.unit
def test_pip_conflict_with_installed_versions_falls_back() -> None:
    """A requirement that would change an installed package aborts express (#3)."""
    with patch(
        "dao_ai.providers.databricks.subprocess.run",
        side_effect=subprocess.CalledProcessError(
            1, "pip", output="ResolutionImpossible: conflicting constraint"
        ),
    ):
        assert _prepare_express_env(ENV_PACK, ["pytest<1"]) is None


@pytest.mark.unit
def test_express_skipped_on_old_mlflow(
    monkeypatch: pytest.MonkeyPatch, basic_config: AppConfig
) -> None:
    """Express needs mlflow >= 3.12 (#7)."""
    _set_runtime(monkeypatch, "client.6.3", "x86_64")
    monkeypatch.setattr("dao_ai.providers.databricks.mlflow.__version__", "3.10.1")
    assert _express_env_pack(basic_config) is None


@pytest.mark.unit
def test_express_skipped_without_env_pack_support(
    monkeypatch: pytest.MonkeyPatch, basic_config: AppConfig
) -> None:
    """An MLflow without ``mlflow.utils.env_pack`` disables express only (#7)."""
    _set_runtime(monkeypatch, "client.6.3", "x86_64")
    monkeypatch.setattr("dao_ai.providers.databricks.EnvPackConfig", None)
    assert _express_env_pack(basic_config) is None


@pytest.mark.unit
def test_register_model_gets_no_env_pack_kwarg_without_express(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Older MLflow ``register_model`` has no ``env_pack`` parameter (#7)."""
    _set_runtime(monkeypatch, None, None)
    config: AppConfig = AppConfig.from_file(path=BASIC.as_posix())
    captured: dict[str, Any] = _run_create_agent(config)
    assert "env_pack" not in captured["register_calls"][0]


@pytest.mark.unit
def test_python_version_default_does_not_warn(monkeypatch: pytest.MonkeyPatch) -> None:
    """The "3.12" default is not a user pin, so it must not warn (#8)."""
    _set_runtime(monkeypatch, "client.6.3", "x86_64")
    config: AppConfig = AppConfig.from_file(path=BASIC.as_posix())
    assert "python_version" not in config.app.model_fields_set
    monkeypatch.setattr(
        "dao_ai.providers.databricks.sys.version_info",
        SimpleNamespace(major=3, minor=99),
    )
    with patch("dao_ai.providers.databricks.logger") as mock_logger:
        assert _express_env_pack(config) is not None
    warnings: list[str] = [c.args[0] for c in mock_logger.warning.call_args_list]
    assert not any("python_version" in w for w in warnings)


@pytest.mark.unit
def test_create_agent_retries_standard_registration_when_pack_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A packing failure inside register_model falls back instead of failing (#2)."""
    _set_runtime(monkeypatch, "client.6.3", "x86_64")
    config: AppConfig = AppConfig.from_file(path=BASIC.as_posix())

    captured: dict[str, Any] = _run_create_agent(
        config,
        register_side_effect=[
            ValueError("Runtime version mismatch"),
            MagicMock(version="1"),
        ],
    )

    first, second = captured["register_calls"]
    assert first["env_pack"] == ENV_PACK
    assert "env_pack" not in second
    assert second["name"] == first["name"]


@pytest.mark.unit
def test_create_agent_registration_error_without_express_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_runtime(monkeypatch, None, None)
    config: AppConfig = AppConfig.from_file(path=BASIC.as_posix())
    with pytest.raises(RuntimeError, match="registry down"):
        _run_create_agent(config, register_side_effect=RuntimeError("registry down"))
