# Databricks notebook source

import mlflow
from mlflow.models.model import ModelInfo
from mlflow.entities.model_registry.model_version import ModelVersion
from mlflow.models.evaluation import EvaluationResult
from mlflow.models import ModelConfig

import pandas as pd

# COMMAND ----------

# Load configuration
config: ModelConfig = ModelConfig(development_config="model_config.yaml")

# Set up MLflow registry
mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

# Get evaluation configuration
evaluation_table_name: str = config.get("evaluation").get("table_name")
registered_model_name: str = config.get("app").get("registered_model_name")

# Load evaluation data
evaluation_pdf: pd.DataFrame = spark.table(evaluation_table_name).toPandas()

print(f"Loaded {len(evaluation_pdf)} evaluation examples from {evaluation_table_name}")
print(f"Evaluating model: {registered_model_name}")

# COMMAND ----------

# Set up evaluation configuration
global_guidelines = {
    # Add any global guidelines for evaluation here
}

# Use the Champion alias for evaluation
model_uri: str = f"models:/{registered_model_name}@Champion"

print(f"Evaluating model URI: {model_uri}")

# COMMAND ----------

# Run MLflow evaluation
with mlflow.start_run(run_name="agent_evaluation"):
    mlflow.set_tag("type", "evaluation")
    mlflow.set_tag("model_name", registered_model_name)
    mlflow.set_tag("evaluation_table", evaluation_table_name)
    
    eval_results = mlflow.evaluate(
        data=evaluation_pdf,
        model=model_uri,
        model_type="databricks-agent",
        evaluator_config={"databricks-agent": {"global_guidelines": global_guidelines}},
    )
    
    print("Evaluation completed successfully!")
    print(f"Evaluation results: {eval_results}")

# COMMAND ----------
