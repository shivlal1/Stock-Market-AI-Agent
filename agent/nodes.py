"""
Agent node functions — each one is a "step" in the LangGraph.

Each function:
  - Receives the current AgentState
  - Does some work (LLM call, memory lookup, tool use, etc.)
  - Returns a dict of state updates (only the fields that changed)

LangGraph automatically merges these updates into the state.
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from agent.prompts import (
    SYSTEM_PROMPT,
    CLARIFICATION_CHECK_PROMPT,
    CLARIFICATION_QUESTION_PROMPT,
    FEEDBACK_EXTRACTION_PROMPT,
)
from agent.state import AgentState
from memory.manager import UserMemoryManager
from tools import ALL_TOOLS
from config import AGENT_MODEL, TEMPERATURE

# Initialize shared resources (created once, reused across calls)
llm = ChatOpenAI(model=AGENT_MODEL, temperature=TEMPERATURE)
llm_with_tools = llm.bind_tools(ALL_TOOLS)
memory_manager = UserMemoryManager()


def retrieve_memory(state: AgentState) -> dict:
    """
    PAHF PRE-STEP: Read from memory AND extract preferences from current message.

    This runs FIRST on every user message. Two jobs:
    1. Store any preference info from the user's latest message
    2. Retrieve all relevant memories for downstream nodes
    """
    user_id = state["user_id"]
    last_message = state["messages"][-1].content

    # ── STEP A: Extract and store preferences from current message ──
    extraction_prompt = (
        f"Does this message reveal ANY investment-related preference?\n"
        f"Message: '{last_message}'\n\n"
        f"Extract as a concise fact. Be generous — if someone mentions ANY stocks, "
        f"sectors, risk preferences, or investment style, extract it.\n\n"
        f"Examples:\n"
        f"- 'big tech like google meta' → 'User is interested in big tech stocks, specifically GOOGL and META'\n"
        f"- 'I prefer dividends' → 'User prefers dividend-paying stocks'\n"
        f"- 'What is AAPL at?' → 'User is interested in AAPL (Apple)'\n"
        f"- 'hello' → NO_NEW_INFO\n"
        f"- 'thanks that was helpful' → NO_NEW_INFO\n"
        f"- 'how does the market work?' → NO_NEW_INFO\n\n"
        f"Extract:"
    )

    try:
        extraction = llm.invoke([HumanMessage(content=extraction_prompt)])
        extracted = extraction.content.strip()

        if "NO_NEW_INFO" not in extracted and len(extracted) > 10:
            memory_manager.add_to_semantic(user_id, extracted)
    except Exception:
        pass  # Don't let extraction failure break the agent

    # ── STEP B: Retrieve relevant memories ──
    memories = memory_manager.retrieve_all_relevant(user_id, last_message)

    if memories:
        memory_text = "\n".join(
            f"- [{m.get('metadata', {}).get('scope', 'general')}] {m['memory']}"
            for m in memories
        )
    else:
        memory_text = "No stored preferences found. This appears to be a new user."

    return {"memory_context": memory_text}


def check_clarification(state: AgentState) -> dict:
    """
    PAHF STEP 1 (decision): Should we ask the user a question first?

    CRITICAL: If we already asked a clarification question (there's
    conversation history), DON'T ask again — proceed to action.
    The user's answers are already in the message history, and
    reason_and_act will see them.
    """
    messages = state["messages"]
    memory_context = state.get("memory_context", "")

    # Count how many human messages exist in history
    human_messages = [m for m in messages if isinstance(m, HumanMessage)]
    ai_messages = [m for m in messages if isinstance(m, AIMessage)]

    # If there's already back-and-forth (we asked, user answered),
    # DON'T ask again — proceed to reason_and_act
    if len(human_messages) >= 2 and len(ai_messages) >= 1:
        return {"needs_clarification": False}

    # If memory already has useful info, no need to clarify
    if memory_context and "no stored preferences" not in memory_context.lower():
        return {"needs_clarification": False}

    # First message from a new user with no memory — check if it's ambiguous
    last_message = messages[-1].content

    prompt = CLARIFICATION_CHECK_PROMPT.format(
        user_message=last_message,
        memory_context=memory_context,
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    needs_clarification = "CLARIFY" in response.content.upper()

    return {"needs_clarification": needs_clarification}


def ask_clarification(state: AgentState) -> dict:
    """
    PAHF STEP 1 (action): Generate a clarification question.

    Also: store whatever info the user already provided in this message.
    For example if user said "I like big tech", store that even though
    we're asking for more detail.
    """
    user_id = state["user_id"]
    last_message = state["messages"][-1].content
    memory_context = state.get("memory_context", "")

    # IMPORTANT: Store any preference info from the user's current message
    # even though we're going to ask for more detail
    extraction_prompt = (
        f"Does this message contain ANY investment preference info worth storing?\n"
        f"Message: '{last_message}'\n"
        f"If yes, extract it as a concise fact. If no, respond NO_NEW_INFO.\n"
        f"Examples:\n"
        f"- 'big tech' → 'User is interested in big tech stocks'\n"
        f"- 'hello' → NO_NEW_INFO\n"
        f"- 'google meta nvidia' → 'User is interested in GOOGL, META, NVDA'\n"
        f"Extract:"
    )
    extraction = llm.invoke([HumanMessage(content=extraction_prompt)])
    extracted = extraction.content.strip()

    if "NO_NEW_INFO" not in extracted and len(extracted) > 10:
        memory_manager.add_to_semantic(user_id, extracted)

    # Now generate the clarification question
    prompt = CLARIFICATION_QUESTION_PROMPT.format(
        user_message=last_message,
        memory_context=memory_context,
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    return {"messages": [AIMessage(content=response.content)]}


def reason_and_act(state: AgentState) -> dict:
    """
    PAHF STEP 2: Generate a personalized response using memory + tools.

    This is the main "brain" of the agent. It receives:
    - The full conversation history (state["messages"])
    - The user's memory context (injected via system prompt)
    - Access to tools (stock prices, news, sector data)

    The LLM decides whether to call tools or respond directly.
    If it calls a tool, LangGraph routes to the ToolNode, gets the result,
    and comes BACK here to continue reasoning.

    Flow: has enough info → this node reasons → either calls tool (loop)
          or generates final response → process_feedback
    """
    memory_context = state.get("memory_context", "")
    system = SystemMessage(
        content=SYSTEM_PROMPT.format(memory_context=memory_context)
    )

    # Build message list: system prompt + full conversation
    messages = [system] + list(state["messages"])

    # llm_with_tools can either respond normally OR request a tool call
    response = llm_with_tools.invoke(messages)

    # Save what the agent said (for feedback processing later)
    action = response.content if isinstance(response.content, str) else ""

    return {
        "messages": [response],
        "action_taken": action,
    }


def process_feedback(state: AgentState) -> dict:
    """
    PAHF STEP 3: Extract preference info from the conversation and store it.

    After the agent responds, the user might say something revealing:
    - "Thanks!" → no new info, skip
    - "I don't care about crypto" → NEW PREFERENCE, store it!
    - "Actually I sold GOOGL" → PREFERENCE CHANGE, update memory!

    This node analyzes the user's response and updates Mem0 if needed.

    Flow: agent responded → user replied → this extracts preferences →
          updates memory → END
    """
    user_id = state["user_id"]
    messages = state["messages"]
    action_taken = state.get("action_taken", "")

    # Find the last human message (the user's reaction to our recommendation)
    last_human_msg = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_human_msg = msg.content
            break

    if not last_human_msg:
        return {"feedback_received": ""}

    # Ask the LLM to extract any preference info
    prompt = FEEDBACK_EXTRACTION_PROMPT.format(
        feedback=last_human_msg,
        action_taken=action_taken[:300],  # Truncate to save tokens
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    extracted = response.content.strip()

    # If new info was found, store it in memory
    if "NO_NEW_INFO" not in extracted and len(extracted) > 10:
        memory_manager.update_from_feedback(
            user_id=user_id,
            feedback=extracted,
            context=action_taken[:200],
        )
        return {"feedback_received": extracted}

    return {"feedback_received": ""}