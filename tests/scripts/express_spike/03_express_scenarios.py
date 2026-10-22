# Databricks notebook source
# ruff: noqa: E402, F821 -- Databricks notebook: dbutils/spark are runtime globals
# Express-deployment integration scenarios, run in a real Databricks serverless
# environment by tests/dao_ai/test_express_deployment_integration.py. Exercises the
# requirement handling behind express (constrained pip install, extras, URL pins,
# dev-wheel check) against the serverless image's real preinstalled packages, and
# asserts pip never changes an already-installed package.
dbutils.widgets.text(name="wheel", defaultValue="")
_wheel: str = dbutils.widgets.get("wheel")
# MAGIC %pip install --quiet '{_wheel}'
# MAGIC %restart_python

# COMMAND ----------

import importlib.metadata
import json
import os
import platform

from mlflow.utils.env_pack import EnvPackConfig

from dao_ai.providers.databricks import (
    _dev_wheel_mismatches,
    _missing_requirements,
    _prepare_express_env,
)

ENV = EnvPackConfig(name="databricks_model_serving", install_dependencies=False)


def installed() -> dict[str, str]:
    return {
        d.metadata["Name"].lower(): d.version
        for d in importlib.metadata.distributions()
        if d.metadata["Name"]
    }


def version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


results: dict = {
    "runtime": os.environ.get("DATABRICKS_RUNTIME_VERSION"),
    "arch": os.environ.get("DATABRICKS_CPU_ARCH") or platform.machine(),
}
before: dict[str, str] = installed()

# 1. A requirement that conflicts with an installed package must fall back and
#    leave that package untouched.
packaging_version: str = version("packaging")
conflict: str = f"packaging!={packaging_version}"
results["conflict"] = {
    "detected_missing": _missing_requirements([conflict]) == [conflict],
    "fell_back": _prepare_express_env(ENV, [conflict]) is None,
    "unchanged": version("packaging") == packaging_version,
}

# 2. A package that is not installed is added (constraints file accepted by pip).
results["add"] = {
    "was_installed": version("humanize") is not None,
    "detected_missing": _missing_requirements(["humanize>=4.0"]) == ["humanize>=4.0"],
    "kept_express": _prepare_express_env(ENV, ["humanize>=4.0"]) is ENV,
    "now_installed": version("humanize"),
}

# 3. Extras: uvicorn is installed with dao-ai, uvicorn[standard] adds more.
uvicorn_version: str | None = version("uvicorn")
extras_req: str = "uvicorn[standard]>=0.32.0"
extras_missing: bool = _missing_requirements([extras_req]) == [extras_req]
extras_result = _prepare_express_env(ENV, [extras_req])
results["extras"] = {
    "uvicorn_version": uvicorn_version,
    "uvloop_before": before.get("uvloop"),
    "detected_missing": extras_missing,
    "kept_express": extras_result is ENV,
    "satisfied_after": _missing_requirements([extras_req]) == [],
    "uvloop_after": version("uvloop"),
    "uvicorn_unchanged": version("uvicorn") == uvicorn_version,
}

# 4. Direct-URL pins can't be verified from installed metadata.
url_req: str = "humanize @ https://example.invalid/humanize-0.0.1-py3-none-any.whl"
results["url"] = {"detected_missing": _missing_requirements([url_req]) == [url_req]}

# 5. The dev wheel must be the exact dao-ai build installed.
dao_version: str = version("dao-ai")
results["dev_wheel"] = {
    "installed": dao_version,
    "match_ok": _dev_wheel_mismatches([f"code/dao_ai-{dao_version}-py3-none-any.whl"])
    == [],
    "mismatch_detected": _dev_wheel_mismatches(["code/dao_ai-0.0.1-py3-none-any.whl"])
    == ["code/dao_ai-0.0.1-py3-none-any.whl"],
    "mismatch_falls_back": _prepare_express_env(
        ENV, ["code/dao_ai-0.0.1-py3-none-any.whl"]
    )
    is None,
}

# Across every scenario: pip only ever added packages.
after: dict[str, str] = installed()
results["changed_versions"] = {
    name: [before[name], after[name]]
    for name in before
    if name in after and before[name] != after[name]
}
results["removed"] = sorted(set(before) - set(after))
results["added"] = sorted(set(after) - set(before))

dbutils.notebook.exit(json.dumps(results))
