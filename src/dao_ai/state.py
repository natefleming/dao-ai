from typing import Sequence, TypedDict

from langchain_core.documents.base import Document
from langgraph.graph import MessagesState
from langgraph.managed import RemainingSteps


class AgentConfig(TypedDict):
    """
    Configuration parameters for the DAO AI agent.

    This TypedDict defines external configuration parameters that can be passed
    to the agent during invocation. It allows for runtime customization of the
    agent's behavior without changing the agent's code.

    Example configurations might include:
    - user_id: Identifier for the current user
    - store_id: Identifier for the relevant DAO store location
    - thread_id: Conversation thread identifier for stateful conversations
    - product_categories: Categories to filter for in product searches
    """

    ...  # Fields are defined at runtime based on invocation parameters


class AgentState(MessagesState):
    """
    State representation for the DAO AI agent conversation workflow.

    Extends LangGraph's MessagesState to maintain the conversation history while
    adding additional state fields specific to the DAO domain. This state is
    passed between nodes in the agent graph and modified during execution.

    Attributes:
        documents: Retrieved documents providing relevant product/inventory information
        route: The current routing decision (which specialized agent to use)
        remaining_steps: Counter to limit reasoning steps and prevent infinite loops
    """

    documents: Sequence[Document]  # Documents retrieved from vector search
    context: str
    route: str
    active_agent: str

    remaining_steps: RemainingSteps
    is_valid: bool
    message_error: str
