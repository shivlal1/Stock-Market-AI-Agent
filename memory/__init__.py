"""
Memory package — persistent per-user preference storage via Mem0.

Implements three memory scopes inspired by cognitive science:
- Semantic: long-term facts (risk tolerance, favorite sectors)
- Episodic: past interaction summaries (what we discussed last time)
- Working: current session context (what we're focused on right now)
"""
from memory.manager import UserMemoryManager

__all__ = ["UserMemoryManager"]