"""
Retail AI Module

A comprehensive AI agent system for retail operations including product discovery,
inventory management, store information, and customer service automation.

This module provides:
- Specialized AI agents for different retail domains
- Tools for product, inventory, and store data access
- State management for conversational workflows
- Integration with Databricks and LangChain ecosystems
"""

from retail_ai.agents import (
    comparison_agent,
    diy_agent,
    general_agent,
    inventory_agent,
    message_validation_agent,
    orders_agent,
    process_images_agent,
    product_agent,
    recommendation_agent,
    router_agent,
)
from retail_ai.models import LanggraphChatModel, create_agent
from retail_ai.state import AgentConfig, AgentState
from retail_ai.tools.factory import ToolFactory
from retail_ai.types import AgentCallable

__version__ = "0.1.0"

__all__ = [
    # Core types
    "AgentState",
    "AgentConfig", 
    "AgentCallable",
    
    # Agents
    "message_validation_agent",
    "router_agent",
    "product_agent",
    "inventory_agent",
    "comparison_agent",
    "diy_agent",
    "general_agent",
    "recommendation_agent",
    "orders_agent",
    "process_images_agent",
    
    # Models
    "LanggraphChatModel",
    "create_agent",
    
    # Tools
    "ToolFactory",
]
