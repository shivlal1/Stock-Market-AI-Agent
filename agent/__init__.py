"""
Agent package — contains the PAHF-based LangGraph agent.

This is the brain of the system. It implements the three-step PAHF loop:
1. Retrieve memory + check if clarification needed (pre-action)
2. Reason and act using tools + memory (action)
3. Process user feedback into memory updates (post-action)
"""
from agent.graph import build_agent

__all__ = ["build_agent"]