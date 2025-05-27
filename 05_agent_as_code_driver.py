# Databricks notebook source


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
import dbutils

display_graph(app)


# COMMAND ----------

# from pathlib import Path
# from agent_as_code import app
# from retail_ai.models import save_image

# path: Path = Path("docs") / "architecture.png"
# save_image(app, path)

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

from agent_as_code import config


model_names: set = set()
for _, model  in config.get("resources").get("llms", {}).items():
    model_name: str = model["name"]
    model_names.add(model_name)

vector_indexes: set = set()
for _, vector_store  in config.get("resources").get("vector_stores", {}).items():
    index_name: str = vector_store["index_name"]
    vector_indexes.add(index_name)

warehouse_ids: set = set()
for _, warehouse  in config.get("resources").get("warehouses", {}).items():
    warehouse_id: str = warehouse["warehouse_id"]
    warehouse_ids.add(warehouse_id)

space_ids: set = set()
for _, genie_room  in config.get("resources").get("genie_rooms", {}).items():
    space_id: str = genie_room["space_id"]
    space_ids.add(space_id)

tables_names: set = set()
for _, table  in config.get("resources").get("tables", {}).items():
    tables_name: str = table["name"]
    tables_names.add(tables_name)

function_names: set = set()
for _, function  in config.get("resources").get("functions", {}).items():
    function_name: str = function["name"]
    function_names.add(function_name)

connection_names: set = set()
for _, connection  in config.get("resources").get("connections", {}).items():
    connection_name: str = connection["name"]
    connection_names.add(connection_name)


resources: list[DatabricksResource] = []

resources += [DatabricksServingEndpoint(endpoint_name=m) for m in model_names if m]
resources += [DatabricksVectorSearchIndex(index_name=v) for v in vector_indexes if v]
resources += [DatabricksSQLWarehouse(warehouse_id=w) for w in warehouse_ids if w]
resources += [DatabricksGenieSpace(genie_space_id=s) for s in space_ids if s]
resources += [DatabricksFunction(function_name=f) for f in function_names if f]
resources += [DatabricksTable(table_name=t) for t in tables_names if t]
resources += [DatabricksUCConnection(connection_name=c) for c in connection_names if c]

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
        "sql.statement-execution", 
        "sql.warehouses",
        "catalog.connections",
        "dashboards.genie",
    ]
)
auth_policy: AuthPolicy = AuthPolicy(
    system_auth_policy=system_auth_policy,
    user_auth_policy=user_auth_policy
)

with mlflow.start_run(run_name="agent"):
    mlflow.set_tag("type", "agent")
    mlflow.set_registry_uri("databricks-uc")
    
    logged_agent_info: ModelInfo = mlflow.pyfunc.log_model(
        python_model="agent_as_code.py",
        code_paths=["retail_ai"],
        model_config=config.to_dict(),
        artifact_path="agent",
        pip_requirements="requirements.txt",
        resources=resources,
        registered_model_name=config.get("app").get("registered_model_name")
        #auth_policy=auth_policy,
    )

# COMMAND ----------

# Model registration is now handled automatically in the log_model call above
# The logged_agent_info.registered_model_version contains the registered model version

# COMMAND ----------

# Deployment is now handled in 07_deploy_agent.py

# COMMAND ----------

# Evaluation is now handled in 06_evaluate_agent.py

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

# Permissions are now handled in 07_deploy_agent.py

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