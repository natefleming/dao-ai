# Databricks notebook source
# MAGIC %md
# MAGIC # Walmart Pharmacy → Genie One — deploy & try it
# MAGIC
# MAGIC This notebook stands up the **Walmart Pharmacy pharmacy assistant** and lets you
# MAGIC talk to it — all from here, no command line required. Run the cells top to bottom.
# MAGIC
# MAGIC **What you'll do, in order:**
# MAGIC 1. Fill in the boxes at the top (your catalog, schema, the three Genie space IDs, and the model).
# MAGIC 2. Pick **where to deploy** — a Databricks *App* (for use inside Genie One) or a *Model Serving* endpoint.
# MAGIC 3. Chat with the assistant **right here in the notebook** and watch its answer stream in, with a link to the trace.
# MAGIC 4. Deploy it, then ask the **live** assistant a question the same way.
# MAGIC
# MAGIC **Before you start**, these must already exist (see `RUNBOOK.md` in this folder):
# MAGIC the three **Genie spaces**, the pharmacy **source table + metric views**, and an
# MAGIC **OpenAI-flavored model endpoint** (Walmart can't use Claude, so the default is
# MAGIC `databricks-gpt-oss-120b`). This notebook only *deploys and tests* — it does not create those.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Install the toolkit
# MAGIC
# MAGIC Installs the `dao-ai` toolkit (and everything it needs) into this notebook's session,
# MAGIC then restarts Python so the fresh install is picked up. If you're working from a repo
# MAGIC checkout that has a freshly built wheel under `dist/`, that local build is used instead.

# COMMAND ----------

# `[all]` pulls every optional feature extra this notebook uses (MCP client,
# langchain, openai, ...). `%restart_python` reloads Python so the install takes.
# MAGIC %pip install --quiet 'dao-ai[all]'
# MAGIC %restart_python

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Guard against a known serverless quirk
# MAGIC
# MAGIC On serverless (v5+) the default Postgres driver can crash on import. Selecting the
# MAGIC pure-Python driver **before** loading the toolkit avoids it. Harmless everywhere else.

# COMMAND ----------

import os

# Must be set before `dao_ai.config` is imported anywhere below.
os.environ["PSYCOPG_IMPL"] = "python"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Fill in your settings
# MAGIC
# MAGIC Each box below becomes a widget at the top of the notebook — edit them there or here.
# MAGIC
# MAGIC - **Required:** `catalog`, `schema`, and the three Genie space IDs (`clinical_space_id`,
# MAGIC   `growth_space_id`, `digital_space_id`).
# MAGIC - **`llm`** — the OpenAI-flavored model serving endpoint the assistant thinks with.
# MAGIC - **`deploy_mode`** — `apps` (a Databricks App, the shape Genie One consumes) or
# MAGIC   `model_serving` (a REST endpoint).
# MAGIC - **`as_mcp` / `with_connection`** — for `apps` mode: leave both `true` to publish the
# MAGIC   assistant as an **MCP server + Unity Catalog connection** (so Genie One can find it).
# MAGIC - The `on_behalf_of_user` / OAuth / `system.ai` boxes are advanced options — the defaults
# MAGIC   are fine for a first run.

# COMMAND ----------

# Config location — the assistant's blueprint lives next to this notebook.
dbutils.widgets.text(name="config_path", defaultValue="walmart_pharmacy_genie_one.yaml", label="Config YAML path")

# Required targets.
dbutils.widgets.text(name="catalog", defaultValue="", label="Catalog (required)")
dbutils.widgets.text(name="schema", defaultValue="", label="Schema (required)")
dbutils.widgets.text(name="clinical_space_id", defaultValue="", label="Clinical Genie space id (required)")
dbutils.widgets.text(name="growth_space_id", defaultValue="", label="Growth Genie space id (required)")
dbutils.widgets.text(name="digital_space_id", defaultValue="", label="Digital Genie space id (required)")

# Model + deployment choices.
dbutils.widgets.text(name="llm", defaultValue="databricks-gpt-oss-120b", label="Model serving endpoint (llm)")
dbutils.widgets.dropdown(name="deploy_mode", defaultValue="apps", choices=["apps", "model_serving"], label="Deploy to")
dbutils.widgets.dropdown(name="as_mcp", defaultValue="true", choices=["true", "false"], label="apps: publish as MCP server")
dbutils.widgets.dropdown(name="with_connection", defaultValue="true", choices=["true", "false"], label="apps: register UC connection")

# Advanced — per-user identity (OBO/U2M) and the external system.ai services.
dbutils.widgets.dropdown(name="on_behalf_of_user", defaultValue="false", choices=["false", "true"], label="Run tools on-behalf-of-user")
dbutils.widgets.text(name="mcp_oauth_client_id", defaultValue="", label="OAuth client id (OBO only)")
dbutils.widgets.text(name="mcp_oauth_client_secret", defaultValue="", label="OAuth client secret (OBO only)")
dbutils.widgets.text(name="microsoft_365_service", defaultValue="system.ai.microsoft_365", label="Microsoft 365 service")
dbutils.widgets.text(name="atlassian_service", defaultValue="system.ai.atlassian", label="Atlassian service")
dbutils.widgets.text(name="google_drive_service", defaultValue="system.ai.google_drive", label="Google Drive service")

# COMMAND ----------

# Read the widgets into typed variables and validate the required ones up front.
config_path: str = dbutils.widgets.get("config_path")
deploy_mode: str = dbutils.widgets.get("deploy_mode")
as_mcp: bool = dbutils.widgets.get("as_mcp") == "true"
with_connection: bool = dbutils.widgets.get("with_connection") == "true"

# Every config parameter, passed through to AppConfig.from_file(params=...). The
# YAML resolves ${var.<name>} placeholders from this mapping.
params: dict[str, str] = {
    "catalog": dbutils.widgets.get("catalog").strip(),
    "schema": dbutils.widgets.get("schema").strip(),
    "clinical_space_id": dbutils.widgets.get("clinical_space_id").strip(),
    "growth_space_id": dbutils.widgets.get("growth_space_id").strip(),
    "digital_space_id": dbutils.widgets.get("digital_space_id").strip(),
    "llm": dbutils.widgets.get("llm").strip(),
    "on_behalf_of_user": dbutils.widgets.get("on_behalf_of_user"),
    "mcp_oauth_client_id": dbutils.widgets.get("mcp_oauth_client_id").strip(),
    "mcp_oauth_client_secret": dbutils.widgets.get("mcp_oauth_client_secret").strip(),
    "microsoft_365_service": dbutils.widgets.get("microsoft_365_service").strip(),
    "atlassian_service": dbutils.widgets.get("atlassian_service").strip(),
    "google_drive_service": dbutils.widgets.get("google_drive_service").strip(),
}

_required: tuple[str, ...] = ("catalog", "schema", "clinical_space_id", "growth_space_id", "digital_space_id")
_missing: list[str] = [name for name in _required if not params[name]]
if _missing:
    raise ValueError(
        f"Fill in the required widget(s) before continuing: {', '.join(_missing)}. "
        "These identify the Unity Catalog target and the three Genie spaces the assistant fronts."
    )

print(f"Config:      {config_path}")
print(f"Deploy to:   {deploy_mode}" + (f"  (as_mcp={as_mcp}, with_connection={with_connection})" if deploy_mode == "apps" else ""))
print(f"Model (llm): {params['llm']}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Turn on tracing
# MAGIC
# MAGIC MLflow **traces** record every step the assistant takes (which Genie room it asked,
# MAGIC what came back). They appear automatically under the notebook's experiment and inline
# MAGIC below each answer, so you can see *why* it responded the way it did.

# COMMAND ----------

import mlflow
import nest_asyncio

from dao_ai.logging import suppress_autolog_context_warnings

# Record traces for every agent call in this notebook.
mlflow.langchain.autolog(run_tracer_inline=True)
# Silence expected cross-thread autolog warnings (see dao_ai.logging).
suppress_autolog_context_warnings()
# Allow the agent's async graph to run inside the notebook's event loop.
nest_asyncio.apply()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Build the assistant from its blueprint
# MAGIC
# MAGIC Loads the config YAML (with your settings filled in) and assembles the assistant in
# MAGIC memory. Nothing is deployed yet — this is the same agent you'll deploy below, so you
# MAGIC can try it first.

# COMMAND ----------

from dao_ai.config import AppConfig

config: AppConfig = AppConfig.from_file(path=config_path, params=params)

print(f"App name:              {config.app.name}")
print(f"Model Serving endpoint: {config.app.endpoint_name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. See how the assistant is wired (optional)
# MAGIC
# MAGIC A quick diagram of the assistant's decision flow — which tools and Genie rooms it can reach.

# COMMAND ----------

config.display_graph()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Chat with the assistant (in memory)
# MAGIC
# MAGIC Ask a question and watch the answer **stream in word by word**, then open the trace to
# MAGIC see which Genie room answered. This runs entirely in the notebook — no deployment needed —
# MAGIC so it's the fastest way to sanity-check the assistant before you publish it.
# MAGIC
# MAGIC Change `question` to anything a pharmacy leader might ask (refill rates, completion
# MAGIC rates, digital account growth, ...).

# COMMAND ----------

from typing import Any

from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import ResponsesAgentRequest, ResponsesAgentStreamEvent

# The in-memory assistant (an MLflow ResponsesAgent).
agent: ResponsesAgent = config.as_responses_agent()

question: str = "What is our year-to-date successful completion rate, and how does it compare to last year?"

request: ResponsesAgentRequest = ResponsesAgentRequest(
    input=[{"role": "user", "content": question}],
    custom_inputs={"configurable": {"thread_id": "notebook-demo", "user_id": "notebook"}},
)

# Stream the answer as it's generated. Text arrives as `response.output_text.delta`
# events; other event types (reasoning, tool steps) are part of the trace. The
# final event carries this run's MLflow trace id in its custom outputs — capture
# it here so the next cell can show the trace without re-running the agent.
print(f"Q: {question}\n\nA: ", end="", flush=True)
trace_id: str | None = None
event: ResponsesAgentStreamEvent
for event in agent.predict_stream(request):
    if event.type == "response.output_text.delta":
        print(event.delta, end="", flush=True)
    custom_outputs: dict[str, Any] | None = getattr(event, "custom_outputs", None)
    if custom_outputs and custom_outputs.get("trace_id"):
        trace_id = custom_outputs["trace_id"]
print()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Look at the trace
# MAGIC
# MAGIC Fetches the trace for the answer above and renders it inline — expand the steps to see
# MAGIC the Genie query and its result. (Traces also show up under **Experiments** for this notebook.)

# COMMAND ----------

# `trace_id` was captured from the streamed answer above (falling back to the
# last trace MLflow recorded). No second agent call — and no second Genie query.
trace_id = trace_id or mlflow.get_last_active_trace_id()

print(f"Trace id: {trace_id}")
if trace_id:
    display(mlflow.get_trace(trace_id))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Deploy it
# MAGIC
# MAGIC Publishes the assistant to wherever you chose in the **`deploy_mode`** widget:
# MAGIC
# MAGIC - **`apps`** — a Databricks App. With `as_mcp` + `with_connection` on (the default), it's
# MAGIC   published as an **MCP server** and registered as a **Unity Catalog connection** so you can
# MAGIC   add it to a Genie One chat. This is the Walmart Pharmacy assistant's normal home.
# MAGIC - **`model_serving`** — a REST endpoint you can call from anywhere.
# MAGIC
# MAGIC This step can take several minutes.

# COMMAND ----------

from dao_ai.config import ServingMode

if deploy_mode == "model_serving":
    # Log the MLflow model first, then create/update the serving endpoint.
    config.create_agent()
    config.deploy_agent(mode=ServingMode.MODEL_SERVING)
    print(f"Deployed to Model Serving endpoint: {config.app.endpoint_name}")
elif deploy_mode == "apps":
    config.deploy_agent(mode=ServingMode.APPS, as_mcp=as_mcp, with_connection=with_connection)
    print(f"Deployed as Databricks App: {config.app.name}  (as_mcp={as_mcp}, with_connection={with_connection})")
else:
    raise ValueError(f"Unknown deploy_mode: {deploy_mode!r} (expected 'apps' or 'model_serving').")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Ask the **live** Model Serving endpoint
# MAGIC
# MAGIC *(Runs only when you deployed to `model_serving`.)*
# MAGIC
# MAGIC Calls the deployed endpoint using the standard OpenAI client and **streams** the answer
# MAGIC back — the same way any application would consume it.

# COMMAND ----------

if deploy_mode == "model_serving":
    from databricks.sdk import WorkspaceClient
    from openai import OpenAI

    w: WorkspaceClient = WorkspaceClient()
    host: str = w.config.host.rstrip("/")
    # `authenticate()` can return None / omit the header; guard like the rest of
    # the codebase before stripping the "Bearer " prefix.
    token: str = (w.config.authenticate() or {}).get("Authorization", "").removeprefix("Bearer ").strip()

    # Databricks serving endpoints speak the OpenAI Responses API.
    client: OpenAI = OpenAI(base_url=f"{host}/serving-endpoints", api_key=token)

    live_question: str = "What is our refill rate this year versus last year?"
    print(f"Q: {live_question}\n\nA: ", end="", flush=True)

    stream = client.responses.create(
        model=config.app.endpoint_name,
        input=[{"role": "user", "content": live_question}],
        stream=True,
    )
    for event in stream:
        if event.type == "response.output_text.delta":
            print(event.delta, end="", flush=True)
    print()
else:
    print("Skipped — deploy_mode is not 'model_serving'.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 10. Ask the **live** MCP app
# MAGIC
# MAGIC *(Runs only when you deployed to `apps` with `as_mcp` on.)*
# MAGIC
# MAGIC The deployed App exposes the assistant as an **MCP tool** (the same surface Genie One
# MAGIC uses). Here we build a tiny helper agent that *connects to that MCP server* and asks it a
# MAGIC question, streaming the answer back — proving the live server works end to end. Auth and
# MAGIC the server URL are resolved for you (the same path the `dao-ai mcp call` command uses).

# COMMAND ----------

if deploy_mode == "apps" and as_mcp:
    from databricks_langchain import ChatDatabricks
    from langchain.agents import create_agent
    from langchain_core.language_models import BaseChatModel
    from langchain_core.tools import BaseTool

    from dao_ai.config import DatabricksAppModel, McpFunctionModel, app_name_for
    from dao_ai.tools.mcp import acreate_mcp_tools

    # The deployed MCP app name (mcp- prefixed) and its tool surface.
    mcp_app_name: str = app_name_for(config.app.name, as_mcp=True)
    mcp_function: McpFunctionModel = McpFunctionModel(app=DatabricksAppModel(name=mcp_app_name))
    print(f"MCP server: {mcp_function.mcp_url}")

    mcp_tools: list[BaseTool] = await acreate_mcp_tools(mcp_function)
    print(f"Tools advertised: {[tool.name for tool in mcp_tools]}")

    # A small *client* agent that calls the live MCP server. Its own reasoning
    # model is just for this demo (independent of the deployed assistant) — here
    # Claude Sonnet 5 via ChatDatabricks. `stream_mode='messages'` yields tokens.
    consumer_model: BaseChatModel = ChatDatabricks(endpoint="databricks-claude-sonnet-5")
    consumer = create_agent(model=consumer_model, tools=mcp_tools)

    live_question: str = "How many active digital pharmacy accounts do we have?"
    print(f"\nQ: {live_question}\n\nA: ", end="", flush=True)

    async for token, _metadata in consumer.astream(
        {"messages": [{"role": "user", "content": live_question}]},
        stream_mode="messages",
    ):
        if getattr(token, "content", None):
            print(token.content, end="", flush=True)
    print()
else:
    print("Skipped — this cell runs only for an 'apps' deployment with as_mcp=true.")
