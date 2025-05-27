"""
General Agent

This module contains the general agent that handles general customer service
queries and fallback scenarios.
"""

from typing import Any

from mlflow.models import ModelConfig

from retail_ai.state import AgentConfig, AgentState
from retail_ai.types import AgentCallable


def general_agent(model_config: ModelConfig) -> AgentCallable:
    """
    Create a general agent that handles general customer service queries.

    Args:
        model_config: Model configuration containing general agent settings

    Returns:
        An agent callable function that handles general queries
    """
    # TODO: Implement general agent logic
    def general(state: AgentState, config: AgentConfig) -> dict[str, Any]:
        return {}
    
    return general 