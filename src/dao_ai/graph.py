from typing import Callable, Sequence

from langchain_core.language_models import LanguageModelLike
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.store.base import BaseStore
from langgraph_supervisor import create_handoff_tool as supervisor_handoff_tool
from langgraph_supervisor import create_supervisor
from langgraph_swarm import create_handoff_tool as swarm_handoff_tool
from langgraph_swarm import create_swarm
from langmem import create_manage_memory_tool, create_search_memory_tool
from loguru import logger

from dao_ai.config import (
    AgentModel,
    AppConfig,
    OrchestrationModel,
    SupervisorModel,
    SwarmModel,
)
from dao_ai.nodes import (
    create_agent_node,
    message_hook_node,
)
from dao_ai.state import AgentConfig, AgentState


def route_message_hook(on_success: str) -> Callable:
    def route_message(state: AgentState) -> str:
        if not state["is_valid"]:
            return END
        return on_success

    return route_message


def _handoffs_for_agent(agent: AgentModel, config: AppConfig) -> Sequence[BaseTool]:
    handoff_tools: list[BaseTool] = []

    handoffs: dict[str, Sequence[AgentModel | str]] = (
        config.app.orchestration.swarm.handoffs or {}
    )
    agent_handoffs: Sequence[AgentModel | str] = handoffs.get(agent.name)
    if agent_handoffs is None:
        agent_handoffs = config.app.agents

    for handoff_to_agent in agent_handoffs:
        if isinstance(handoff_to_agent, str):
            handoff_to_agent = next(
                iter(config.find_agents(lambda a: a.name == handoff_to_agent)), None
            )

        if handoff_to_agent is None:
            logger.warning(
                f"Handoff agent {handoff_to_agent} not found in configuration for agent {agent.name}"
            )
            continue
        if agent.name == handoff_to_agent.name:
            continue
        logger.debug(
            f"Creating handoff tool from agent {agent.name} to {handoff_to_agent.name}"
        )
        handoff_tools.append(
            swarm_handoff_tool(
                agent_name=handoff_to_agent.name,
                description=f"Ask {handoff_to_agent.name} for help with: "
                + handoff_to_agent.handoff_prompt,
            )
        )
    return handoff_tools


def _create_supervisor_graph(config: AppConfig) -> CompiledStateGraph:
    logger.debug("Creating supervisor graph")
    agents: list[CompiledStateGraph] = []
    tools: Sequence[BaseTool] = []
    for registered_agent in config.app.agents:
        agents.append(create_agent_node(agent=registered_agent, additional_tools=[]))
        tools.append(
            supervisor_handoff_tool(
                agent_name=registered_agent.name,
                description=registered_agent.handoff_prompt,
            )
        )

    supervisor: SupervisorModel = config.app.orchestration.supervisor

    store: BaseStore = None
    if supervisor.memory and supervisor.memory.store:
        store = supervisor.memory.store.as_store()
        logger.debug(f"Using memory store: {store}")
        namespace: tuple[str, ...] = ("memory",)

        if supervisor.memory.store.namespace:
            namespace = namespace + (supervisor.memory.store.namespace,)
            logger.debug(f"Memory store namespace: {namespace}")
            tools += [
                create_manage_memory_tool(namespace=namespace, store=store),
                create_search_memory_tool(namespace=namespace, store=store),
            ]

    checkpointer: BaseCheckpointSaver = None
    if supervisor.memory and supervisor.memory.checkpointer:
        checkpointer = supervisor.memory.checkpointer.as_checkpointer()

    model: LanguageModelLike = supervisor.model.as_chat_model()
    supervisor_workflow: StateGraph = create_supervisor(
        supervisor_name="triage",
        agents=agents,
        model=model,
        tools=tools,
        state_schema=AgentState,
        config_schema=AgentConfig,
    )

    supervisor_node: CompiledStateGraph = supervisor_workflow.compile(
        checkpointer=checkpointer, store=store
    )

    workflow: StateGraph = StateGraph(AgentState, config_schema=AgentConfig)

    workflow.add_node("message_hook", message_hook_node(config=config))
    workflow.add_node("supervisor", supervisor_node)

    workflow.add_conditional_edges(
        "message_hook",
        route_message_hook("supervisor"),
        {
            "supervisor": "supervisor",
            END: END,
        },
    )

    workflow.set_entry_point("message_hook")

    return workflow.compile()


def _create_swarm_graph(config: AppConfig) -> CompiledStateGraph:
    logger.debug("Creating swarm graph")
    agents: list[CompiledStateGraph] = []
    for registered_agent in config.app.agents:
        handoff_tools: Sequence[BaseTool] = _handoffs_for_agent(
            agent=registered_agent, config=config
        )
        agents.append(
            create_agent_node(agent=registered_agent, additional_tools=handoff_tools)
        )

    swarm: SwarmModel = config.app.orchestration.swarm

    default_agent: AgentModel = swarm.default_agent
    if isinstance(default_agent, AgentModel):
        default_agent = default_agent.name

    swarm_workflow: StateGraph = create_swarm(
        agents=agents,
        default_active_agent=default_agent,
        state_schema=AgentState,
        config_schema=AgentConfig,
    )

    store: BaseStore = None
    if swarm.memory and swarm.memory.store:
        store = swarm.memory.store.as_store()

    checkpointer: BaseCheckpointSaver = None
    if swarm.memory and swarm.memory.checkpointer:
        checkpointer = swarm.memory.checkpointer()

    swarm_node: CompiledStateGraph = swarm_workflow.compile(
        checkpointer=checkpointer, store=store
    )

    workflow: StateGraph = StateGraph(AgentState, config_schema=AgentConfig)

    workflow.add_node("message_hook", message_hook_node(config=config))
    workflow.add_node("swarm", swarm_node)

    workflow.add_conditional_edges(
        "message_hook",
        route_message_hook("swarm"),
        {
            "swarm": "swarm",
            END: END,
        },
    )

    workflow.add_edge("message_hook", "swarm")

    workflow.set_entry_point("message_hook")

    return workflow.compile()


def create_dao_ai_graph(config: AppConfig) -> CompiledStateGraph:
    orchestration: OrchestrationModel = config.app.orchestration
    if orchestration.supervisor:
        return _create_supervisor_graph(config)

    if orchestration.swarm:
        return _create_swarm_graph(config)

    raise ValueError("No valid orchestration model found in the configuration.")
