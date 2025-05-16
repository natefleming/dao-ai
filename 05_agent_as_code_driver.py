# Databricks notebook source
from typing import Sequence

pip_requirements: Sequence[str] = (
  "langgraph",
  "langchain",
  "databricks-langchain",
  "unitycatalog-langchain[databricks]",
  "langgraph-checkpoint-postgres",
  "duckduckgo-search",
  "databricks-agents",
  "psycopg[binary,pool]", 
  "databricks-sdk",
  "langgraph-reflection",
  "openevals",
  "mlflow",
  "pydantic",
  "python-dotenv",
  "uv",
  "grandalf",
  "loguru",
)

pip_requirements: str = " ".join(pip_requirements)

%pip install --quiet --upgrade {pip_requirements}
%restart_python

# COMMAND ----------

from importlib.metadata import version

from typing import Sequence

from importlib.metadata import version

pip_requirements: Sequence[str] = [
    f"langgraph=={version('langgraph')}",
    f"langchain=={version('langchain')}",
    f"databricks-langchain=={version('databricks-langchain')}",
    f"unitycatalog-langchain[databricks]=={version('unitycatalog-langchain')}",
    f"langgraph-checkpoint-postgres=={version('langgraph-checkpoint-postgres')}",
    f"duckduckgo-search=={version('duckduckgo-search')}",
    f"databricks-sdk=={version('databricks-sdk')}",
    f"langgraph-reflection=={version('langgraph-reflection')}",
    f"openevals=={version('openevals')}",
    f"mlflow=={version('mlflow')}",
    f"psycopg[binary,pool]=={version('psycopg')}",
    f"databricks-agents=={version('databricks-agents')}",
    f"pydantic=={version('pydantic')}",
    f"loguru=={version('loguru')}",
]
print("\n".join(pip_requirements))

# COMMAND ----------

# MAGIC %load_ext autoreload
# MAGIC %autoreload 2

# COMMAND ----------

# MAGIC %%writefile agent_as_code.py
# MAGIC
# MAGIC from typing import Sequence
# MAGIC import sys
# MAGIC
# MAGIC import mlflow
# MAGIC from mlflow.models import ModelConfig
# MAGIC
# MAGIC from langchain_core.runnables import RunnableSequence
# MAGIC from langgraph.graph.state import CompiledStateGraph
# MAGIC from mlflow.pyfunc import ChatModel
# MAGIC from retail_ai.graph import create_retail_ai_graph
# MAGIC from retail_ai.models import create_agent 
# MAGIC
# MAGIC from loguru import logger
# MAGIC
# MAGIC
# MAGIC mlflow.langchain.autolog()
# MAGIC
# MAGIC config: ModelConfig = ModelConfig(development_config="model_config.yaml")
# MAGIC log_level: str = config.get("app").get("log_level")
# MAGIC
# MAGIC logger.add(sys.stderr, level=log_level)
# MAGIC
# MAGIC graph: CompiledStateGraph = create_retail_ai_graph(model_config=config)
# MAGIC
# MAGIC app: ChatModel = create_agent(graph)
# MAGIC
# MAGIC mlflow.models.set_model(app)
# MAGIC

# COMMAND ----------

from agent_as_code import app
from retail_ai.models import display_graph

display_graph(app)


# COMMAND ----------

from pathlib import Path
from agent_as_code import app
from retail_ai.models import save_image

path: Path = Path("docs") / "architecture.png"
save_image(app, path)

# COMMAND ----------

from typing import Any, Sequence, Optional

from mlflow.models.resources import (
    DatabricksResource,
    DatabricksVectorSearchIndex,
    DatabricksTable,
    DatabricksUCConnection,
    DatabricksSQLWarehouse,
    DatabricksGenieSpace,
    DatabricksFunction,
    DatabricksServingEndpoint,
)
from mlflow.models.auth_policy import (
    SystemAuthPolicy, 
    UserAuthPolicy, 
    AuthPolicy
)
import mlflow
from mlflow.models.model import ModelInfo

from dataclasses import dataclass, field, asdict
from agent_as_code import config


model_names: set = set()
for _, model  in config.get("resources").get("llms").items():
    model_names.add(model["model_name"])

index_name: str = config.get("retriever").get("index_name")
space_id: str = config.get("resources").get("genie").get("space_id")
functions: Sequence[str] = config.get("resources").get("functions")
tables: Sequence[str] = config.get("resources").get("tables")
warehouses: Sequence[str] = config.get("resources").get("warehouses")

resources: Sequence[DatabricksResource] = [
    DatabricksVectorSearchIndex(index_name=index_name),
    DatabricksGenieSpace(genie_space_id=space_id),
]

resources += [DatabricksServingEndpoint(endpoint_name=m) for m in model_names]
resources += [DatabricksFunction(function_name=f) for f in functions]
resources += [DatabricksTable(table_name=t) for t in tables]
resources += [DatabricksSQLWarehouse(warehouse_id=w) for w in warehouses]

input_example: dict[str, Any] = config.get("app").get("diy_example")

system_auth_policy: SystemAuthPolicy = SystemAuthPolicy(resources=resources)

# Api Scopes
# Vector Search:            serving.serving-endpoints, vectorsearch.vector-search-endpoints, vectorsearch.vector-search-indexes
# Model Serving Endpoints:  serving.serving-endpoints
# SQL Wareshouse:           sql.statement-execution, sql.warehouses
# UC Connections:           catalog.connections
# Genie:                    dashboards.genie

user_auth_policy: UserAuthPolicy = UserAuthPolicy(
    api_scopes=[
        "serving.serving-endpoints",
        "vectorsearch.vector-search-endpoints",
        "vectorsearch.vector-search-indexes",
    ]
)
auth_policy: AuthPolicy = AuthPolicy(
    system_auth_policy=system_auth_policy,
    user_auth_policy=user_auth_policy
)

with mlflow.start_run(run_name="agent"):
    mlflow.set_tag("type", "agent")
    logged_agent_info: ModelInfo = mlflow.pyfunc.log_model(
        python_model="agent_as_code.py",
        code_paths=["retail_ai"],
        model_config=config.to_dict(),
        artifact_path="agent",
        pip_requirements=pip_requirements,
        #resources=resources,
        auth_policy=auth_policy,
    )

# COMMAND ----------

import mlflow
from mlflow.entities.model_registry.model_version import ModelVersion

from agent_as_code import config


mlflow.set_registry_uri("databricks-uc")

registered_model_name: str = config.get("app").get("registered_model_name")

model_version: ModelVersion = mlflow.register_model(
    name=registered_model_name, model_uri=logged_agent_info.model_uri
)

# COMMAND ----------

from mlflow import MlflowClient
from mlflow.entities.model_registry.model_version import ModelVersion

client: MlflowClient = MlflowClient()

client.set_registered_model_alias(
    name=registered_model_name, alias="Champion", version=model_version.version
)
champion_model: ModelVersion = client.get_model_version_by_alias(
    registered_model_name, "Champion"
)
print(champion_model)

# COMMAND ----------

from databricks import agents
from retail_ai.models import get_latest_model_version
from agent_as_code import config


registered_model_name: str = config.get("app").get("registered_model_name")
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

# COMMAND ----------

import mlflow
from mlflow.models.model import ModelInfo
from mlflow.entities.model_registry.model_version import ModelVersion
from mlflow.models.evaluation import EvaluationResult

import pandas as pd

from agent_as_code import config


model_info: mlflow.models.model.ModelInfo
evaluation_result: EvaluationResult

evaluation_table_name: str = config.get("evaluation").get("table_name")

evaluation_pdf: pd.DataFrame = spark.table(evaluation_table_name).toPandas()

global_guidelines = {
    "English": ["The response must be in English"],
    "Clarity": ["The response must be clear, coherent, and concise"],
}

model_uri: str = f"models:/{registered_model_name}@Champion"

with mlflow.start_run():
    mlflow.set_tag("type", "evaluation")
    eval_results = mlflow.evaluate(
        data=evaluation_pdf,
        model=model_uri,
        model_type="databricks-agent",
        evaluator_config={"databricks-agent": {"global_guidelines": global_guidelines}},
    )

# COMMAND ----------

from typing import Any
from agent_as_code import config

example_input: dict[str, Any] = config.get("app").get("diy_example")

mlflow.models.predict(
    model_uri=logged_agent_info.model_uri,
    input_data=example_input,
    env_manager="uv",
)

# COMMAND ----------

from typing import Any, Sequence

from databricks.agents import set_permissions, PermissionLevel

from agent_as_code import config

registered_model_name: str = config.get("app").get("registered_model_name")
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


# COMMAND ----------

from typing import Any
from mlflow.deployments import get_deploy_client
from rich import print as pprint
from agent_as_code import config

endpoint_name: str = config.get("app").get("endpoint_name")
example_input: dict[str, Any] = config.get("app").get("inventory_example")

response = get_deploy_client("databricks").predict(
    endpoint=endpoint_name,
    inputs=example_input,
)

pprint(response)

# COMMAND ----------

from typing import Any
from mlflow.deployments import get_deploy_client

from agent_as_code import config
from rich import print as pprint


endpoint_name: str = config.get("app").get("endpoint_name")
example_input: dict[str, Any] = config.get("app").get("recommendation_example")

response = get_deploy_client("databricks").predict(
    endpoint=endpoint_name,
    inputs=example_input,
)

pprint(response)

# COMMAND ----------

from databricks.sdk import WorkspaceClient
from rich import print as pprint

w: WorkspaceClient = WorkspaceClient()

openai_client = w.serving_endpoints.get_open_ai_client()

response = openai_client.chat.completions.create(
    model=endpoint_name,
    messages=example_input["messages"],
    extra_body={"custom_inputs": example_input["custom_inputs"]}
)

pprint(response)

# COMMAND ----------

from databricks.sdk import WorkspaceClient
from rich import print as pprint


w: WorkspaceClient = WorkspaceClient()

openai_client = w.serving_endpoints.get_open_ai_client()


example_input: dict[str, Any] = config.get("app").get("recommendation_example")

messages = example_input["messages"]

# Create a streaming request with custom inputs properly placed in extra_body
response_stream = openai_client.chat.completions.create(
    model=endpoint_name,
    messages=messages,
    temperature=0.0,
    max_tokens=100,
    stream=True,  # Enable streaming
    extra_body={"custom_inputs": example_input["custom_inputs"]},
)

# Process the streaming response
print("Streaming response:")
collected_content = ""
for chunk in response_stream:
    if hasattr(chunk.choices[0], "delta") and hasattr(
        chunk.choices[0].delta, "content"
    ):
        content = chunk.choices[0].delta.content
        if content is not None:  # Check for None explicitly
            collected_content += content
            print(content, end="", flush=True)  # Print chunks as they arrive

print("\n\nFull collected response:")
print(collected_content)

# COMMAND ----------

from agent_as_code import graph

from typing import Any
from agent_as_code import app, config

example_input: dict[str, Any] = config.get("app").get("diy_example")

result = app.invoke(example_input)

# COMMAND ----------

from mlflow.types.llm import (
    # Non-streaming helper classes
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChunk,
    ChatMessage,
    ChatChoice,
    ChatParams,
    # Helper classes for streaming agent output
    ChatChoiceDelta,
    ChatChunkChoice,
)

ChatMessage(**messages[0])

# COMMAND ----------

messages

# COMMAND ----------

from databricks.sdk import WorkspaceClient
from rich import print as pprint


w: WorkspaceClient = WorkspaceClient()

openai_client = w.serving_endpoints.get_open_ai_client()


example_input: dict[str, Any] = config.get("app").get("recommendation_example")

messages = example_input["messages"]
custom_inputs = example_input["custom_inputs"]

# Create a streaming request with custom inputs properly placed in extra_body
response = openai_client.chat.completions.create(
    model=endpoint_name,
    messages=messages,
    temperature=0.0,
    max_tokens=100,
    extra_body={"custom_inputs": custom_inputs},
)

print(response)
