# Databricks notebook source
# MAGIC %pip install --quiet uv
# MAGIC
# MAGIC import os
# MAGIC os.environ["UV_PROJECT_ENVIRONMENT"] = os.environ["VIRTUAL_ENV"]

# COMMAND ----------

# MAGIC %sh uv --project ../ sync

# COMMAND ----------

# MAGIC %restart_python

# COMMAND ----------

import logging
logging.getLogger("py4j").setLevel(logging.WARNING)

# COMMAND ----------

import sys

sys.path.insert(0, "..")

# COMMAND ----------

from dotenv import find_dotenv, load_dotenv

_ = load_dotenv(find_dotenv())

# COMMAND ----------

dbutils.widgets.text(name="config-path", defaultValue="../config/model_config_dais.yaml")
config_path: str = dbutils.widgets.get("config-path")
print(config_path)

# COMMAND ----------

from typing import Sequence
from importlib.metadata import version

pip_requirements: Sequence[str] = (
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
)

print("\n".join(pip_requirements))

# COMMAND ----------

# MAGIC %load_ext autoreload
# MAGIC %autoreload 2

# COMMAND ----------

from typing import Any
import yaml
from pathlib import Path

dais_examples_path: Path = Path.cwd().parent / "examples" / "dais-examples.yaml"
dais_examples: dict[str, Any] = yaml.safe_load(dais_examples_path.read_text())

# COMMAND ----------

import sys

import mlflow
from mlflow.models import ModelConfig

from langgraph.graph.state import CompiledStateGraph
from mlflow.pyfunc import ChatModel
from retail_ai.graph import create_retail_ai_graph
from retail_ai.models import create_agent 
from retail_ai.config import AppConfig

from loguru import logger

mlflow.langchain.autolog()

model_config_path: str = config_path
model_config: ModelConfig = ModelConfig(development_config=model_config_path)
config: AppConfig = AppConfig(**model_config.to_dict())

log_level: str = config.app.log_level

logger.add(sys.stderr, level=log_level)

graph: CompiledStateGraph = create_retail_ai_graph(config=config)

app: ChatModel = create_agent(graph)

# COMMAND ----------

# MAGIC %md
# MAGIC # DAIS Examples - Retail AI Agent System
# MAGIC
# MAGIC This notebook demonstrates the various agent interactions and use cases for the DAIS retail demo.
# MAGIC The examples are organized by functional categories:
# MAGIC
# MAGIC 1. **Demo Script Examples** - Core demo scenarios for live presentations
# MAGIC 2. **Customer Profile Intelligence and Styling** - Personal styling and customer insights  
# MAGIC 3. **Product Information** - Product details, SKU lookups, and specifications
# MAGIC 4. **Inventory Management** - Stock levels, availability, and cross-store checks
# MAGIC 5. **Store Information** - Store details, hours, locations, and comparisons
# MAGIC 6. **Employee Management** - Staff performance, assignments, and tasks
# MAGIC 7. **Customer Service** - Appointments, VIP customers, and service workflows
# MAGIC 8. **Recommendation** - Product suggestions and alternatives
# MAGIC 9. **Comparison** - Product comparisons and side-by-side analysis
# MAGIC 10. **Brand Representative Training** - Nike/Adidas brand education scenarios
# MAGIC 11. **Local San Francisco Context** - Geography-specific recommendations

# COMMAND ----------

from typing import Any
from rich import print as pprint
from retail_ai.models import process_messages

# Helper function to run examples
def run_example(example_name: str, stream: bool = False) -> None:
    examples: dict[str, Any] = dais_examples.get("examples")
    input_example: dict[str, Any] = examples.get(example_name)
    
    if not input_example:
        print(f"❌ Example '{example_name}' not found in dais-examples.yaml")
        return
    
    print(f"🔍 Running example: {example_name}")
    pprint(input_example)
    print("\n" + "="*80 + "\n")
    
    if stream:
        from retail_ai.models import process_messages_stream
        for event in process_messages_stream(app=app, **input_example):
            print(event.choices[0].delta.content, end="", flush=True)
        print("\n")
    else:
        response = process_messages(app=app, **input_example)
        pprint(response)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Demo Script Examples
# MAGIC
# MAGIC These are the core examples designed for live demonstrations and showcase the main capabilities of the retail AI assistant.

# COMMAND ----------

run_example("demo_initial_inventory_check")

# COMMAND ----------

run_example("demo_recommendation_request", stream=True)

# COMMAND ----------

run_example("demo_cross_store_check")

# COMMAND ----------

run_example("demo_hold_request")

# COMMAND ----------

run_example("demo_directions_notifications")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Customer Profile Intelligence and Styling Examples
# MAGIC
# MAGIC These examples demonstrate personal styling capabilities and customer intelligence features for high-touch retail experiences.

# COMMAND ----------

run_example("customer_profile_intelligence_example")

# COMMAND ----------

run_example("styling_appointment_prep_example", stream=True)

# COMMAND ----------

run_example("stylist_notification_example")

# COMMAND ----------

run_example("real_time_styling_example")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Product Information Examples
# MAGIC
# MAGIC Examples showing product lookup, SKU queries, and product specification retrieval.

# COMMAND ----------

run_example("product_by_sku_example")

# COMMAND ----------

run_example("specific_sku_lookup_example")

# COMMAND ----------

# Handle image example separately since it requires special processing
from typing import Any, Sequence
from rich import print as pprint
from pathlib import Path
from langchain_core.messages import HumanMessage
from retail_ai.models import process_messages
from retail_ai.messages import convert_to_langchain_messages

examples: dict[str, Any] = dais_examples.get("examples")
input_example: dict[str, Any] = examples.get("product_image_example")
print("🔍 Running example: product_image_example")
pprint(input_example)
print("\n" + "="*80 + "\n")

if input_example and "image_paths" in input_example["messages"][0]:
    messages: Sequence[HumanMessage] = convert_to_langchain_messages(input_example["messages"])
    custom_inputs = input_example["custom_inputs"]
    
    response = process_messages(
        app=app, 
        messages=messages, 
        custom_inputs=custom_inputs
    )
    pprint(response)
else:
    run_example("product_image_example")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Inventory Management Examples
# MAGIC
# MAGIC Examples demonstrating inventory checking, stock levels, and availability across stores.

# COMMAND ----------

run_example("inventory_by_sku_example")

# COMMAND ----------

run_example("store_inventory_by_sku_example", stream=True)

# COMMAND ----------

run_example("cross_store_inventory_example")

# COMMAND ----------

run_example("out_of_stock_example")

# COMMAND ----------

run_example("size_availability_example")

# COMMAND ----------

run_example("color_availability_example")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Store Information Examples
# MAGIC
# MAGIC Examples showing store details, hours, locations, and store comparisons.

# COMMAND ----------

run_example("store_by_number_example")

# COMMAND ----------

run_example("store_hours_example")

# COMMAND ----------

run_example("store_location_search_example", stream=True)

# COMMAND ----------

run_example("store_comparison_example")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Employee Management Examples
# MAGIC
# MAGIC Examples demonstrating employee performance tracking, task assignments, and staff management.

# COMMAND ----------

run_example("top_employees_example")

# COMMAND ----------

run_example("personal_shopping_associates_example")

# COMMAND ----------

run_example("employee_manager_example")

# COMMAND ----------

run_example("task_assignment_example")

# COMMAND ----------

run_example("department_performance_example", stream=True)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Customer Service Examples
# MAGIC
# MAGIC Examples showing customer appointment management, VIP customer handling, and service workflows.

# COMMAND ----------

run_example("customer_appointments_example")

# COMMAND ----------

run_example("customer_details_example")

# COMMAND ----------

run_example("customer_preparation_example", stream=True)

# COMMAND ----------

run_example("vip_customer_example")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Recommendation Examples
# MAGIC
# MAGIC Examples demonstrating product recommendation and alternative suggestion capabilities.

# COMMAND ----------

run_example("recommendation_example")

# COMMAND ----------

run_example("alternative_recommendation_example", stream=True)

# COMMAND ----------

run_example("style_consultation_example")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Comparison Examples
# MAGIC
# MAGIC Examples showing product comparison capabilities, including image-based comparisons.

# COMMAND ----------

run_example("comparison_example")

# COMMAND ----------

# Handle image comparison example separately
examples: dict[str, Any] = dais_examples.get("examples")
input_example: dict[str, Any] = examples.get("comparison_image_example")
print("🔍 Running example: comparison_image_example")
pprint(input_example)
print("\n" + "="*80 + "\n")

if input_example and "image_paths" in input_example["messages"][0]:
    messages: Sequence[HumanMessage] = convert_to_langchain_messages(input_example["messages"])
    custom_inputs = input_example["custom_inputs"]
    
    response = process_messages(
        app=app, 
        messages=messages, 
        custom_inputs=custom_inputs
    )
    pprint(response)
else:
    run_example("comparison_image_example")

# COMMAND ----------

# MAGIC %md
# MAGIC ## General Store Information, DIY, and Orders Examples
# MAGIC
# MAGIC Examples showing general store information, DIY guidance, and order tracking.

# COMMAND ----------

run_example("general_example")

# COMMAND ----------

run_example("diy_example", stream=True)

# COMMAND ----------

run_example("orders_example")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Brand Representative Training Examples
# MAGIC
# MAGIC Examples designed for brand representative training sessions, focusing on Nike and Adidas product education.

# COMMAND ----------

run_example("brand_rep_nike_customers")

# COMMAND ----------

run_example("brand_rep_product_performance", stream=True)

# COMMAND ----------

run_example("brand_rep_competitive_analysis")

# COMMAND ----------

run_example("brand_rep_product_comparison")

# COMMAND ----------

run_example("brand_rep_positioning", stream=True)

# COMMAND ----------

run_example("brand_rep_objection_handling")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Local San Francisco Context Examples
# MAGIC
# MAGIC Examples incorporating local San Francisco geography, weather, and terrain considerations.

# COMMAND ----------

run_example("sf_weather_styling_example", stream=True)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Custom Example Testing
# MAGIC
# MAGIC Use this section to test custom scenarios or debug specific examples.

# COMMAND ----------

# Test any specific example by name
# run_example("your_example_name_here", stream=False)

# List all available examples
examples: dict[str, Any] = dais_examples.get("examples")
print("📋 Available DAIS Examples:")
print("="*50)
for i, example_name in enumerate(examples.keys(), 1):
    print(f"{i:2d}. {example_name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC This notebook demonstrates **49 different examples** from the DAIS retail AI system, organized into functional categories:
# MAGIC
# MAGIC - **Demo Script Examples (8)**: Core presentation scenarios
# MAGIC - **Customer Profile Intelligence and Styling (4)**: Personal styling capabilities  
# MAGIC - **Product Information (3)**: Product details and specifications
# MAGIC - **Inventory Management (6)**: Stock levels and availability
# MAGIC - **Store Information (4)**: Store details and comparisons
# MAGIC - **Employee Management (5)**: Staff performance and task management
# MAGIC - **Customer Service (4)**: Appointment and VIP customer management
# MAGIC - **Recommendation (3)**: Product suggestions and alternatives
# MAGIC - **Comparison (2)**: Product comparisons including image analysis
# MAGIC - **General Store Information, DIY, and Orders (3)**: Misc store operations
# MAGIC - **Brand Representative Training (6)**: Nike/Adidas education scenarios
# MAGIC - **Local San Francisco Context (1)**: Geography-specific recommendations
# MAGIC
# MAGIC All examples use San Francisco store locations (101: Downtown Market, 102: Marina Market, 103: Mission Market) and feature Adidas sneaker products as the primary focus for the DAIS demonstration.
