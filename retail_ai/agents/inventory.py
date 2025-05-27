"""
Inventory Agent

This module contains the inventory agent that handles inventory queries,
stock level checks, and store-specific inventory information.
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

from retail_ai.state import AgentConfig, AgentState
from retail_ai.tools import (
    create_find_inventory_by_sku_tool,
    create_find_inventory_by_upc_tool,
    create_find_store_inventory_by_sku_tool,
    create_find_store_inventory_by_upc_tool,
)
from retail_ai.types import AgentCallable

# Optional imports for guardrails
try:
    from retail_ai.guardrails import reflection_guardrail, with_guardrails
    GUARDRAILS_AVAILABLE = True
except ImportError:
    GUARDRAILS_AVAILABLE = False


def inventory_agent(model_config: ModelConfig) -> AgentCallable:
    """
    Create an inventory agent that handles inventory and stock level queries.

    This agent specializes in inventory-related tasks including stock level checks,
    store-specific inventory queries, and availability information.

    Args:
        model_config: Model configuration containing inventory agent settings

    Returns:
        An agent callable function that handles inventory queries
    """
    model: str = model_config.get("agents").get("inventory").get("model").get("name")
    prompt: str = model_config.get("agents").get("inventory").get("prompt")
    guardrails: Sequence[dict[str, Any]] = (
        model_config.get("agents").get("inventory").get("guardrails") or []
    )

    warehouse_id: str = (
        model_config.get("resources")
        .get("warehouses")
        .get("shared_endpoint_warehouse")
        .get("warehouse_id")
    )

    @mlflow.trace()
    def inventory(state: AgentState, config: AgentConfig) -> dict[str, BaseMessage]:
        """
        Handle inventory-related queries and stock level checks.
        
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

        # Create inventory-specific tools
        tools = [
            create_find_inventory_by_sku_tool(warehouse_id),
            create_find_inventory_by_upc_tool(warehouse_id),
            create_find_store_inventory_by_sku_tool(warehouse_id),
            create_find_store_inventory_by_upc_tool(warehouse_id),
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

        logger.debug("Inventory agent created with tools and guardrails")
        return agent

    return inventory 