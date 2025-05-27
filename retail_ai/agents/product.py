"""
Product Agent

This module contains the product agent that handles product discovery,
SKU/UPC lookups, and product information queries.
"""

from typing import Any, Sequence

import mlflow
from databricks_langchain import ChatDatabricks
from langchain.prompts import PromptTemplate
from langchain_core.language_models import LanguageModelLike
from langchain_core.messages import BaseMessage
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent
from loguru import logger
from mlflow.models import ModelConfig

# Optional imports for guardrails
try:
    from retail_ai.guardrails import reflection_guardrail, with_guardrails
    GUARDRAILS_AVAILABLE = True
except ImportError:
    GUARDRAILS_AVAILABLE = False

from retail_ai.state import AgentConfig, AgentState
from retail_ai.tools import (
    create_find_product_by_sku_tool,
    create_find_product_by_upc_tool,
    find_product_details_by_description_tool,
)
from retail_ai.types import AgentCallable


def product_agent(model_config: ModelConfig) -> AgentCallable:
    """
    Create a product agent that handles product discovery and information queries.

    This agent specializes in product-related tasks including SKU/UPC lookups,
    semantic product search, and product information retrieval.

    Args:
        model_config: Model configuration containing product agent settings

    Returns:
        An agent callable function that handles product queries
    """
    model: str = model_config.get("agents").get("product").get("model").get("name")
    prompt: str = model_config.get("agents").get("product").get("prompt")
    guardrails: Sequence[dict[str, Any]] = (
        model_config.get("agents").get("product").get("guardrails") or []
    )

    retriever_config: dict[str, Any] = model_config.get("retrievers").get(
        "products_retriever"
    )
    index_name: str = retriever_config.get("vector_store").get("index_name")
    endpoint_name: str = retriever_config.get("vector_store").get("endpoint_name")
    columns: Sequence[str] = retriever_config.get("columns")
    search_parameters: dict[str, Any] = retriever_config.get("search_parameters", {})
    num_results: int = search_parameters.get("num_results", 10)

    warehouse_id: str = (
        model_config.get("resources")
        .get("warehouses")
        .get("shared_endpoint_warehouse")
        .get("warehouse_id")
    )

    @mlflow.trace()
    def product(state: AgentState, config: AgentConfig) -> dict[str, BaseMessage]:
        """
        Handle product-related queries and information requests.
        
        Args:
            state: Current agent state containing messages and context
            config: Agent configuration parameters
            
        Returns:
            Dictionary with updated agent state
        """
        llm: LanguageModelLike = ChatDatabricks(model=model, temperature=0.1)

        prompt_template: PromptTemplate = PromptTemplate.from_template(prompt)
        configurable: dict[str, Any] = {
            "user_id": state["user_id"],
            "store_num": state["store_num"],
        }
        system_prompt: str = prompt_template.format(**configurable)

        # Create product-specific tools
        tools = [
            find_product_details_by_description_tool(
                endpoint_name=endpoint_name,
                index_name=index_name,
                columns=columns,
                k=num_results,
            ),
            create_find_product_by_sku_tool(warehouse_id),
            create_find_product_by_upc_tool(warehouse_id),
        ]

        # Create the agent with tools
        agent: CompiledStateGraph = create_react_agent(
            model=llm,
            prompt=system_prompt,
            tools=tools,
        )

        # Apply guardrails if configured and available
        if GUARDRAILS_AVAILABLE:
            for guardrail_definition in guardrails:
                guardrail: CompiledStateGraph = reflection_guardrail(guardrail_definition)
                agent = with_guardrails(agent, guardrail)
        elif guardrails:
            logger.warning("Guardrails configured but guardrails module not available")

        logger.debug("Product agent created with tools and guardrails")
        return agent

    return product 