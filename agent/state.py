"""
Agent state definition.

In LangGraph, "state" is a dictionary that flows between every node.
Think of it as a shared notepad. Each node reads from it and writes to it.

When the agent starts, the state has the user's message.
As it flows through nodes, memories get added, tools get called,
and by the end the state contains the full response.
"""
from typing import Annotated, Sequence, TypedDict, Optional, List
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class AgentState(TypedDict):
    # The conversation history — grows as user and agent exchange messages.
    # add_messages is a "reducer": it APPENDS new messages instead of replacing.
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Which user we're talking to (for per-user memory isolation)
    user_id: str

    # Memories retrieved from Mem0 (filled by retrieve_memory node)
    memory_context: str

    # Did the clarification checker decide we need to ask the user?
    needs_clarification: bool

    # What the agent actually recommended (for feedback processing)
    action_taken: str

    # What preference info was extracted from feedback
    feedback_received: str

    # Notes accumulated during this session (saved to episodic memory at end)
    session_notes: List[str]