# Databricks notebook source
# ruff: noqa: E402, F821 -- Databricks notebook: dbutils/spark are runtime globals
# Express-deployment spike: which CPU architecture does serverless compute run on?
# MLflow >=3.16 silently drops ``env_pack`` when DATABRICKS_CPU_ARCH is arm64/aarch64.
import os
import platform

dbutils.notebook.exit(
    f"arch={os.environ.get('DATABRICKS_CPU_ARCH')} machine={platform.machine()} "
    f"runtime={os.environ.get('DATABRICKS_RUNTIME_VERSION')}"
)
