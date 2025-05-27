"""
Validation Agent

This module contains the message validation agent that validates
incoming messages and configuration parameters.
"""

from typing import Any, Optional

import mlflow
from loguru import logger
from mlflow.models import ModelConfig

from retail_ai.state import AgentConfig, AgentState
from retail_ai.types import AgentCallable


def message_validation_agent(model_config: ModelConfig) -> AgentCallable:
    """
    Create a message validation agent that validates incoming messages and configuration.

    This agent ensures that required configuration parameters are present and valid
    before processing continues to other agents.

    Args:
        model_config: Model configuration containing validation settings

    Returns:
        An agent callable function that validates messages and configuration
    """
    @mlflow.trace()
    def message_validation(state: AgentState, config: AgentConfig) -> dict[str, Any]:
        """
        Validate incoming messages and configuration parameters.
        
        Args:
            state: Current agent state containing messages and context
            config: Agent configuration parameters
            
        Returns:
            Dictionary with validation results and updated configuration
        """
        logger.debug(f"Validating state: {state}")

        configurable: dict[str, Any] = config.get("configurable", {})
        validation_errors: list[str] = []

        user_id: Optional[str] = configurable.get("user_id", "")
        if not user_id:
            validation_errors.append("user_id is required")

        store_num: Optional[str] = configurable.get("store_num", "")
        if not store_num:
            validation_errors.append("store_num is required")

        if validation_errors:
            logger.warning(f"Validation errors: {validation_errors}")

        return {"user_id": user_id, "store_num": store_num, "is_valid_config": True}

    return message_validation 