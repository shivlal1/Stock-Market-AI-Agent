"""
Gradio web interface for the Stock Watchlist Agent.

Run with: python app.py
Or in Colab: demo.launch(share=True) creates a public URL.
"""
import gradio as gr
from langchain_core.messages import HumanMessage, AIMessage
from agent.graph import build_agent
from memory.manager import UserMemoryManager

agent = build_agent()
memory = UserMemoryManager()


# def chat(message: str, history: list, user_id: str):
#     """Process a chat message through the PAHF agent."""
#     if not user_id.strip():
#         user_id = "demo_user"
#
#     # Convert Gradio history format to LangChain messages
#     messages = []
#     for human_msg, ai_msg in history:
#         messages.append(HumanMessage(content=human_msg))
#         if ai_msg:
#             messages.append(AIMessage(content=ai_msg))
#     messages.append(HumanMessage(content=message))
#
#     # Run the PAHF agent
#     result = agent.invoke({
#         "messages": messages,
#         "user_id": user_id,
#         "memory_context": "",
#         "needs_clarification": False,
#         "action_taken": "",
#         "feedback_received": "",
#         "session_notes": [],
#     })
#
#     return result["messages"][-1].content


def chat(message: str, history: list, user_id: str):
    if not user_id.strip():
        user_id = "demo_user"

    # Convert Gradio 6.x history (list of dicts) to LangChain messages
    messages = []
    for msg in history:
        if isinstance(msg, dict):
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        elif isinstance(msg, (list, tuple)):
            messages.append(HumanMessage(content=msg[0]))
            if msg[1]:
                messages.append(AIMessage(content=msg[1]))
    messages.append(HumanMessage(content=message))

    try:
        result = agent.invoke({
            "messages": messages,
            "user_id": user_id,
            "memory_context": "",
            "needs_clarification": False,
            "action_taken": "",
            "feedback_received": "",
            "session_notes": [],
        })

        # Walk backwards through messages to find the last text response
        for msg in reversed(result["messages"]):
            if hasattr(msg, "content") and msg.content and isinstance(msg.content, str):
                return msg.content

        return "I processed your request but couldn't generate a response. Please try again."

    except Exception as e:
        return f"Error: {str(e)}"


def show_memories(user_id: str):
    """Display all stored memories for a user."""
    if not user_id.strip():
        return "Please enter a User ID first."

    memories = memory.retrieve_profile(user_id.strip())
    if not memories:
        return "No memories stored yet. Start chatting to build your profile!"

    lines = []
    for m in memories:
        scope = m.get("metadata", {}).get("scope", "general")
        lines.append(f"[{scope}] {m['memory']}")
    return "\n".join(lines)


def clear_memories(user_id: str):
    """Clear all memories for a user (useful for testing)."""
    if not user_id.strip():
        return "Please enter a User ID first."
    memory.clear_user_memory(user_id.strip())
    return f"All memories cleared for user '{user_id}'."


# ── Build the Gradio UI ──
with gr.Blocks(title="📈 Personalized Stock Watchlist Agent") as demo:
    gr.Markdown("# 📈 Personalized Stock Watchlist Agent")
    gr.Markdown(
        "*An AI financial assistant that learns your preferences through conversation. "
        "Powered by PAHF (Pre-action + Post-action Human Feedback).*"
    )

    with gr.Row():
        user_id_input = gr.Textbox(
            label="Your User ID",
            value="demo_user",
            placeholder="Enter any unique name",
            scale=2,
        )
        show_mem_btn = gr.Button("📋 Show My Memories", scale=1)
        clear_mem_btn = gr.Button("🗑️ Clear My Memories", scale=1)

    memory_display = gr.Textbox(
        label="Stored Memories (what the agent knows about you)",
        lines=4,
        interactive=False,
    )

    show_mem_btn.click(show_memories, inputs=[user_id_input], outputs=[memory_display])
    clear_mem_btn.click(clear_memories, inputs=[user_id_input], outputs=[memory_display])

    gr.ChatInterface(
        fn=chat,
        additional_inputs=[user_id_input],
        examples=[
            ["What's happening in the market today?"],
            ["How are my holdings doing?"],
            ["Any news about the semiconductor sector?"],
            ["I'm thinking about shifting into healthcare stocks"],
        ],
        title="Chat with your agent",
    )

if __name__ == "__main__":
    demo.launch(share=True)