"""
Router Agent

This module contains the router agent that determines which specialized agent
should handle a given customer query based on content analysis.
"""

from typing import Literal, Sequence

import mlflow
from databricks_langchain import ChatDatabricks
from langchain_core.language_models import LanguageModelLike
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableSequence
from loguru import logger
from mlflow.models import ModelConfig
from pydantic import BaseModel, Field

from retail_ai.messages import last_human_message
from retail_ai.state import AgentConfig, AgentState
from retail_ai.types import AgentCallable


def router_agent(model_config: ModelConfig) -> AgentCallable:
    """
    Create a router agent that routes questions to the appropriate specialized agent.

    This factory function returns a callable that uses a language model to analyze
    the latest user message and determine which agent should handle it based on content.
    The routing decision is structured through the Router Pydantic model.

    Args:
        model_config: Model configuration containing router settings

    Returns:
        An agent callable function that updates the state with the routing decision
    """
    model: str = model_config.get("agents").get("router").get("model").get("name")
    prompt: str = model_config.get("agents").get("router").get("prompt")
    allowed_routes: Sequence[str] = (
        model_config.get("agents").get("router").get("allowed_routes")
    )
    default_route: str = model_config.get("agents").get("router").get("default_route")

    @mlflow.trace()
    def router(state: AgentState, config: AgentConfig) -> dict[str, str]:
        """
        Route customer queries to the appropriate specialized agent.
        
        Args:
            state: Current agent state containing messages and context
            config: Agent configuration parameters
            
        Returns:
            Dictionary with the routing decision
        """
        llm: LanguageModelLike = ChatDatabricks(model=model, temperature=0.1)

        class Router(BaseModel):
            route: Literal[tuple(allowed_routes)] = Field(
                default=default_route,
                description=f"The route to take. Must be one of {allowed_routes}",
            )

        Router.__doc__ = prompt

        chain: RunnableSequence = llm.with_structured_output(Router)

        # Extract all messages from the current state
        messages: Sequence[BaseMessage] = state["messages"]

        # Get the most recent message from the human user
        last_message: BaseMessage = last_human_message(messages)

        # Invoke the chain to determine the appropriate route
        response = chain.invoke([last_message])

        logger.debug(f"Router decision: {response.route}")

        # Return the route decision to update the agent state
        return {"route": response.route}

    return router 