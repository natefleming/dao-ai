# Databricks notebook source

import mlflow
from mlflow import MlflowClient
from mlflow.entities.model_registry.model_version import ModelVersion
from mlflow.models import ModelConfig

# COMMAND ----------

# Load configuration
config: ModelConfig = ModelConfig(development_config="model_config.yaml")

# Set up MLflow registry
mlflow.set_registry_uri("databricks-uc")

# Get model details from config
registered_model_name: str = config.get("app").get("registered_model_name")

# COMMAND ----------

# Get the latest model version
client: MlflowClient = MlflowClient()

# Get all versions and find the latest
versions = client.search_model_versions(f"name='{registered_model_name}'")
if not versions:
    raise ValueError(f"No versions found for model {registered_model_name}")

latest_version = max(versions, key=lambda v: int(v.version))
print(f"Latest model version: {latest_version.version}")

# COMMAND ----------

# Set the Champion alias to the latest version
client.set_registered_model_alias(
    name=registered_model_name, 
    alias="Champion", 
    version=latest_version.version
)

# Verify the alias was set
champion_model: ModelVersion = client.get_model_version_by_alias(
    registered_model_name, "Champion"
)
print(f"Champion alias set to version: {champion_model.version}")
print(f"Champion model details: {champion_model}")

# COMMAND ----------

from databricks import agents
from retail_ai.models import get_latest_model_version

endpoint_name: str = config.get("app").get("endpoint_name")
tags: dict[str, str] = config.get("app").get("tags")
latest_version: int = get_latest_model_version(registered_model_name)

agents.deploy(
    model_name=registered_model_name,
    model_version=latest_version,
    scale_to_zero=True,
    environment_vars={},
    workload_size="Small",
    endpoint_name=endpoint_name,
    tags=tags,
)

print(f"Agent deployed to endpoint: {endpoint_name}")

# COMMAND ----------

from typing import Any, Sequence
from databricks.agents import set_permissions, PermissionLevel

permissions: Sequence[dict[str, Any]] = config.get("app").get("permissions") 

for permission in permissions:
    principals: Sequence[str] = permission.get("principals")
    entitlements: Sequence[str] = permission.get("entitlements")

    for entitlement in entitlements:
        set_permissions(
            model_name=registered_model_name,
            users=principals,
            permission_level=PermissionLevel[entitlement]
        )

print("Permissions set successfully")

# COMMAND ---------- 