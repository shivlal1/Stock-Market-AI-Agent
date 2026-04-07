"""
LLM-based human simulator for automated evaluation.

Instead of testing with real humans (expensive, slow), we use GPT-4o-mini
to role-play as each investor persona. This is the same approach the
PAHF paper uses (they call it "simulating human behavior by employing
another LLM with specific persona").
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from config import AGENT_MODEL


class SimulatedUser:
    """Simulates a human user with a specific investor persona."""

    def __init__(self, persona_config: dict):
        self.persona = persona_config
        self.llm = ChatOpenAI(model=AGENT_MODEL, temperature=0.3)
        self.system_msg = SystemMessage(content=persona_config["persona_prompt"])

    def respond_to_clarification(self, agent_question: str) -> str:
        """Answer the agent's pre-action clarification question."""
        response = self.llm.invoke([
            self.system_msg,
            HumanMessage(
                content=(
                    f"A financial assistant asks you: '{agent_question}'\n"
                    f"Answer briefly and naturally as yourself. 1-2 sentences max."
                )
            ),
        ])
        return response.content

    def give_post_feedback(self, agent_response: str) -> str:
        """React to the agent's recommendation (PAHF Step 3 trigger)."""
        response = self.llm.invoke([
            self.system_msg,
            HumanMessage(
                content=(
                    f"A financial assistant just gave you this update:\n"
                    f"---\n{agent_response[:500]}\n---\n\n"
                    f"Give brief, natural feedback (1-3 sentences). "
                    f"If it matches your interests, say so briefly. "
                    f"If it doesn't match your CURRENT preferences, "
                    f"explain what you'd actually prefer."
                )
            ),
        ])
        return response.content