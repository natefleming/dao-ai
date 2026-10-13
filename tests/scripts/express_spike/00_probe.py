# Databricks notebook source
# ruff: noqa: E402, F821 -- Databricks notebook: dbutils/spark are runtime globals
# Express-deployment spike, step 1: does a serverless *job task* qualify for
# ``env_pack``? Prints the runtime version, then logs + registers a trivial
# custom pyfunc with ``env_pack`` and checks the packed artifacts exist.
import os
import sys

import mlflow
from mlflow.utils.databricks_utils import DatabricksRuntimeVersion

dbutils.widgets.text(name="model_name", defaultValue="")
model_name: str = dbutils.widgets.get("model_name")

print(f"DATABRICKS_RUNTIME_VERSION={os.environ.get('DATABRICKS_RUNTIME_VERSION')}")
print(f"parsed={DatabricksRuntimeVersion.parse()}")
print(f"python={sys.version}")
print(f"mlflow={mlflow.__version__}")

# COMMAND ----------

import time

from mlflow.utils.env_pack import EnvPackConfig


class Echo(mlflow.pyfunc.PythonModel):
    def predict(self, context, model_input):
        return model_input


mlflow.set_registry_uri("databricks-uc")
mlflow.set_experiment(f"/Users/{spark.sql('select current_user()').first()[0]}/express_spike_experiment")

with mlflow.start_run(run_name="express_probe"):
    info = mlflow.pyfunc.log_model(
        name="model", python_model=Echo(), input_example={"x": [1]}
    )

start = time.time()
mv = mlflow.register_model(
    model_uri=info.model_uri,
    name=model_name,
    env_pack=EnvPackConfig(name="databricks_model_serving", install_dependencies=False),
)
print(f"registered {mv.name} v{mv.version} in {time.time() - start:.1f}s")

# COMMAND ----------

files = [
    f.path
    for f in mlflow.artifacts.list_artifacts(
        artifact_uri=f"models:/{mv.name}/{mv.version}/_databricks"
    )
]
print(f"_databricks artifacts: {files}")
assert any(p.endswith("model_environment.tar") for p in files), "env not packed"
dbutils.notebook.exit(f"{mv.name}:{mv.version}")
