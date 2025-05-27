# Databricks notebook source

from typing import Any
from rich import print as pprint
from agent_as_code import app, config
from retail_ai.models import process_messages

# store num
input_example: dict[str, Any] = {
  'messages': [
    {
      'role': 'user',
      'content': 'Hi, do you have the Starbucks Pike Place coffee pods in stock?'
    }
  ],
  'custom_inputs': {
      'configurable': {
        'thread_id': '1',
        'user_id': 'nate.fleming',
        'store_num': "SF-DOWNTOWN"
      }
    }
  }
pprint(input_example)

response = process_messages(app=app, **input_example)
pprint(response)

# COMMAND ----------

from typing import Any
from rich import print as pprint
from agent_as_code import app, config
from retail_ai.models import process_messages

# store num
input_example: dict[str, Any] = {
  'messages': [
    {
      'role': 'user',
      'content': '"What would you recommend that\'s similar?"'
    }
  ],
  'custom_inputs': {
      'configurable': {
        'thread_id': '1',
        'user_id': 'nate.fleming',
        'store_num': 35048
      }
    }
  }
pprint(input_example)

response = process_messages(app=app, **input_example)
pprint(response)

# COMMAND ----------

from typing import Any
from rich import print as pprint
from agent_as_code import app, config
from retail_ai.models import process_messages

# store num
input_example: dict[str, Any] = {
  'messages': [
    {
      'role': 'user',
      'content': 'Can you tell me about 0017627748017?'
    }
  ],
  'custom_inputs': {
      'configurable': {
        'thread_id': '1',
        'user_id': 'nate.fleming',
        'store_num': 123
      }
    }
  }
pprint(input_example)

response = process_messages(app=app, **input_example)
pprint(response)

# COMMAND ----------

from typing import Any
from rich import print as pprint
from agent_as_code import app, config
from retail_ai.models import process_messages

# store num
input_example: dict[str, Any] = {
  'messages': [
    {
      'role': 'user',
      'content': 'Can you tell me about sku 00176279?'
    }
  ],
  'custom_inputs': {
      'configurable': {
        'thread_id': '1',
        'user_id': 'nate.fleming',
        'store_num': 123
      }
    }
  }
pprint(input_example)

response = process_messages(app=app, **input_example)
pprint(response)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Recommendation

# COMMAND ----------

from typing import Any
from rich import print as pprint
from agent_as_code import app, config
from retail_ai.models import process_messages

examples: dict[str, Any] = config.get("app").get("examples")
input_example: dict[str, Any] = examples.get("recommendation_example")
pprint(input_example)

response = process_messages(app=app, **input_example)
pprint(response)

# COMMAND ----------



# COMMAND ----------

from typing import Any
from agent_as_code import app, config
from retail_ai.models import process_messages_stream

examples: dict[str, Any] = config.get("app").get("examples")
input_example: dict[str, Any] = examples.get("recommendation_example")
pprint(input_example)

for event in process_messages_stream(app=app, **input_example):
  print(event.choices[0].delta.content, end="", flush=True)


# COMMAND ----------

# MAGIC %md
# MAGIC ## Inventory

# COMMAND ----------

from typing import Any
from rich import print as pprint
from agent_as_code import app, config
from retail_ai.models import process_messages

examples: dict[str, Any] = config.get("app").get("examples")
input_example: dict[str, Any] = examples.get("inventory_example")
pprint(input_example)

response = process_messages(app=app, **input_example)
pprint(response)

# COMMAND ----------

from typing import Any
from agent_as_code import app, config
from retail_ai.models import process_messages_stream

examples: dict[str, Any] = config.get("app").get("examples")
input_example: dict[str, Any] = examples.get("inventory_example")
pprint(input_example)

for event in process_messages_stream(app=app, **input_example):
  print(event.choices[0].delta.content, end="", flush=True)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Comparison

# COMMAND ----------

from typing import Any
from rich import print as pprint
from agent_as_code import app, config
from retail_ai.models import process_messages

examples: dict[str, Any] = config.get("app").get("examples")
input_example: dict[str, Any] = examples.get("comparison_example")
pprint(input_example)

response = process_messages(app=app, **input_example)
pprint(response)

# COMMAND ----------

from typing import Any
from agent_as_code import app, config
from retail_ai.models import process_messages_stream

examples: dict[str, Any] = config.get("app").get("examples")
input_example: dict[str, Any] = examples.get("comparison_example")
pprint(input_example)

for event in process_messages_stream(app=app, **input_example):
  print(event.choices[0].delta.content, end="", flush=True)

# COMMAND ----------

from typing import Any, Sequence
from rich import print as pprint

from pathlib import Path
from langchain_core.messages import HumanMessage, convert_to_messages
from agent_as_code import app, config
from retail_ai.models import process_messages
from retail_ai.messages import convert_to_langchain_messages


examples: dict[str, Any] = config.get("app").get("examples")
input_example: dict[str, Any] = examples.get("comparison_image_example")
pprint(input_example)

messages: Sequence[HumanMessage] = convert_to_langchain_messages(input_example["messages"])
custom_inputs = input_example["custom_inputs"]

process_messages(
  app=app, 
  messages=messages, 
  custom_inputs=custom_inputs
)


# COMMAND ----------

# MAGIC %md
# MAGIC ## General

# COMMAND ----------

from typing import Any
from rich import print as pprint
from agent_as_code import app, config
from retail_ai.models import process_messages

examples: dict[str, Any] = config.get("app").get("examples")
input_example: dict[str, Any] = examples.get("general_example")
pprint(input_example)

response = process_messages(app=app, **input_example)
pprint(response)

# COMMAND ----------

from typing import Any
from agent_as_code import app, config
from retail_ai.models import process_messages_stream

examples: dict[str, Any] = config.get("app").get("examples")
input_example: dict[str, Any] = examples.get("general_example")
pprint(input_example)

for event in process_messages_stream(app=app, **input_example):
  print(event.choices[0].delta.content, end="", flush=True)

# COMMAND ----------

# MAGIC %md
# MAGIC ## DIY

# COMMAND ----------

# MAGIC %restart_python

# COMMAND ----------

from typing import Any
from rich import print as pprint
from agent_as_code import app, config
from retail_ai.models import process_messages

examples: dict[str, Any] = config.get("app").get("examples")
input_example: dict[str, Any] = examples.get("diy_example")
pprint(input_example)

response = process_messages(app=app, **input_example)
pprint(response)

# COMMAND ----------

from typing import Any
from agent_as_code import app, config
from retail_ai.models import process_messages_stream

examples: dict[str, Any] = config.get("app").get("examples")
input_example: dict[str, Any] = examples.get("diy_example")
pprint(input_example)

for event in process_messages_stream(app=app, **input_example):
  print(event.choices[0].delta.content, end="", flush=True)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Orders

# COMMAND ----------

from typing import Any
from rich import print as pprint
from agent_as_code import app, config
from retail_ai.models import process_messages

examples: dict[str, Any] = config.get("app").get("examples")
input_example: dict[str, Any] = examples.get("orders_example")
pprint(input_example)

response = process_messages(app=app, **input_example)
pprint(response)

# COMMAND ----------

from typing import Any
from agent_as_code import app, config
from retail_ai.models import process_messages_stream

examples: dict[str, Any] = config.get("app").get("examples")
input_example: dict[str, Any] = examples.get("orders_example")
pprint(input_example)

for event in process_messages_stream(app=app, **input_example):
  print(event.choices[0].delta.content, end="", flush=True)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Product

# COMMAND ----------

# MAGIC %restart_python

# COMMAND ----------

from typing import Any
from rich import print as pprint
from agent_as_code import app, config
from retail_ai.models import process_messages

examples: dict[str, Any] = config.get("app").get("examples")
input_example: dict[str, Any] = examples.get("product_example")
pprint(input_example)

response = process_messages(app=app, **input_example)
pprint(response)

# COMMAND ----------

from typing import Any
from rich import print as pprint
from agent_as_code import app, config
from retail_ai.models import process_messages_stream

examples: dict[str, Any] = config.get("app").get("examples")
input_example: dict[str, Any] = examples.get("product_example")

pprint(input_example)

for event in process_messages_stream(app=app, **input_example):
  print(event.choices[0].delta.content, end="", flush=True)

# COMMAND ----------

from typing import Any, Sequence
from rich import print as pprint

from pathlib import Path
from langchain_core.messages import HumanMessage, convert_to_messages
from agent_as_code import app, config
from retail_ai.models import process_messages
from retail_ai.messages import convert_to_langchain_messages


examples: dict[str, Any] = config.get("app").get("examples")
input_example: dict[str, Any] = examples.get("product_image_example")
pprint(input_example)

messages: Sequence[HumanMessage] = convert_to_langchain_messages(input_example["messages"])
custom_inputs = input_example["custom_inputs"]

process_messages(
  app=app, 
  messages=messages, 
  custom_inputs=custom_inputs
)

