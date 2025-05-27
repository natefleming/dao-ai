from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from mlflow.models import ModelConfig

from retail_ai.messages import has_image
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
from retail_ai.state import AgentConfig, AgentState


def route_message_validation(state: AgentState) -> str:
    if not state["is_valid_config"]:
        return END
    if has_image(state["messages"]):
        return "process_images"
    return "router"


def create_retail_ai_graph(model_config: ModelConfig) -> CompiledStateGraph:
    workflow: StateGraph = StateGraph(AgentState, config_schema=AgentConfig)

    workflow.add_node(
        "message_validation", message_validation_agent(model_config=model_config)
    )
    workflow.add_node("process_images", process_images_agent(model_config=model_config))
    workflow.add_node("router", router_agent(model_config=model_config))
    workflow.add_node("general", general_agent(model_config=model_config))
    workflow.add_node("recommendation", recommendation_agent(model_config=model_config))
    workflow.add_node("inventory", inventory_agent(model_config=model_config))
    workflow.add_node("product", product_agent(model_config=model_config))
    workflow.add_node("orders", orders_agent(model_config=model_config))
    workflow.add_node("diy", diy_agent(model_config=model_config))
    workflow.add_node("comparison", comparison_agent(model_config=model_config))

    workflow.add_conditional_edges(
        "message_validation",
        route_message_validation,
        {
            "router": "router",
            "process_images": "process_images",
            END: END,
        },
    )

    workflow.add_edge("process_images", "router")

    workflow.add_conditional_edges(
        "router",
        lambda state: state["route"],
        {
            "general": "general",
            "recommendation": "recommendation",
            "inventory": "inventory",
            "product": "product",
            "orders": "orders",
            "diy": "diy",
            "comparison": "comparison",
        },
    )

    workflow.set_entry_point("message_validation")

    return workflow.compile()
