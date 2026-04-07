"""
LangGraph wiring — connects all nodes into the PAHF agent.

This file defines the FLOW: which node runs first, what happens next,
and what conditions determine the path through the graph.

Think of this as the "flowchart definition" file.
"""
from typing import Literal

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from agent.state import AgentState
from agent.nodes import (
    retrieve_memory,
    check_clarification,
    ask_clarification,
    reason_and_act,
    process_feedback,
)
from tools import ALL_TOOLS


# ── Routing functions (the "diamond" decision boxes in a flowchart) ──

def route_after_clarification_check(
        state: AgentState,
) -> Literal["ask_clarification", "reason_and_act"]:
    """
    After checking if clarification is needed, go to either:
    - ask_clarification: generate a question for the user
    - reason_and_act: proceed to answer with tools + memory
    """
    if state.get("needs_clarification", False):
        return "ask_clarification"
    return "reason_and_act"


def route_after_reasoning(
        state: AgentState,
) -> Literal["tools", "process_feedback"]:
    """
    After the agent reasons, check if it wants to call a tool:
    - tools: execute the tool call, then loop back to reason_and_act
    - process_feedback: no tool needed, proceed to feedback processing
    """
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "process_feedback"


# ── Build the graph ──

def build_agent():
    """
    Construct and compile the PAHF agent graph.

    Returns a compiled graph that you can call with:
        result = agent.invoke({"messages": [...], "user_id": "alice", ...})
    """
    graph = StateGraph(AgentState)

    # Register all nodes (steps)
    graph.add_node("retrieve_memory", retrieve_memory)
    graph.add_node("check_clarification", check_clarification)
    graph.add_node("ask_clarification", ask_clarification)
    graph.add_node("reason_and_act", reason_and_act)
    graph.add_node("tools", ToolNode(tools=ALL_TOOLS))
    graph.add_node("process_feedback", process_feedback)

    # Wire the edges (flow)
    graph.add_edge(START, "retrieve_memory")
    graph.add_edge("retrieve_memory", "check_clarification")

    graph.add_conditional_edges(
        "check_clarification",
        route_after_clarification_check,
    )

    graph.add_edge("ask_clarification", END)  # Wait for user's answer

    graph.add_conditional_edges(
        "reason_and_act",
        route_after_reasoning,
    )

    graph.add_edge("tools", "reason_and_act")  # After tool → reason again
    graph.add_edge("process_feedback", END)  # Done

    return graph.compile()