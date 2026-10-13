# Databricks notebook source
# ruff: noqa: E402, F821 -- Databricks notebook: dbutils/spark are runtime globals
# Express-deployment spike: deploy express_full (custom code + 3rd-party libs) from an
# INTERACTIVE serverless notebook. In testing, interactive serverless ran on x86 while
# serverless job tasks ran on ARM, so this is the path where env_pack applies.
# Installs the same packages the bundle's job environment does, so the packed env
# carries dao-ai, its pins, and app.pip_requirements.
# MAGIC %pip install --quiet '../dist/dao_ai-0.2.22+dev1791821658-py3-none-any.whl' 'databricks-agents==1.11.0' 'databricks-langchain[memory]==0.20.0' 'databricks-mcp==0.9.0' 'databricks-sdk[openai]==0.146.0' 'langchain==1.3.14' 'langchain-mcp-adapters==0.3.0' 'langchain-openai==1.3.5' 'langgraph==1.2.9' 'langgraph-checkpoint-postgres==3.0.5' 'langgraph-prebuilt==1.1.0' 'loguru==0.7.3' 'mcp==1.28.1' 'mlflow==3.14.0' 'nest-asyncio==1.6.0' 'psycopg[binary,pool]==3.3.4' 'pydantic==2.13.4' 'pyyaml==6.0.3' 'unitycatalog-ai[databricks]==0.3.2' 'unitycatalog-langchain[databricks]==0.3.0' 'deepagents==0.6.12' 'humanize>=4.0' 'rapidfuzz>=3.0' 
# MAGIC %restart_python

# COMMAND ----------

import os
import platform

print(
    f"runtime={os.environ.get('DATABRICKS_RUNTIME_VERSION')} "
    f"arch={os.environ.get('DATABRICKS_CPU_ARCH')} machine={platform.machine()}"
)

# COMMAND ----------

import time

from dao_ai.config import AppConfig, ServingMode

config_path: str = os.path.abspath("../config/express_interactive.yaml")
config: AppConfig = AppConfig.from_file(path=config_path)

start: float = time.time()
config.create_agent(development=True)
print(f"create_agent (log + register) took {time.time() - start:.0f}s")

start = time.time()
config.deploy_agent(mode=ServingMode.MODEL_SERVING, development=True)
print(f"deploy_agent returned after {time.time() - start:.0f}s")
