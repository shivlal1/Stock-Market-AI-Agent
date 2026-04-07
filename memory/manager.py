"""
Mem0 memory manager with three scopes.

This wraps Mem0 to provide the per-user persistent memory that PAHF requires.
Every user gets isolated memory — Alice's preferences never affect Bob's results.
"""
from mem0 import Memory
from config import AGENT_MODEL, EMBEDDING_MODEL, CHROMA_DB_PATH, MEMORY_COLLECTION, MEMORY_SEARCH_LIMIT


class UserMemoryManager:
    """
    Three-scope memory manager implementing PAHF's memory design.

    Why three scopes?
    - Semantic:  "Alice likes growth stocks" (permanent until corrected)
    - Episodic:  "Last session we discussed NVDA earnings" (session summaries)
    - Working:   "Right now Alice is asking about healthcare" (temporary)

    Mem0 handles the hard parts: embedding, deduplication, conflict resolution.
    """

    def __init__(self):
        """Initialize Mem0 with local ChromaDB storage (no cloud needed)."""
        self.memory = Memory.from_config({
            "llm": {
                "provider": "openai",
                "config": {
                    "model": AGENT_MODEL,
                    "temperature": 0.1,
                }
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "model": EMBEDDING_MODEL,
                }
            },
            "vector_store": {
                "provider": "chroma",
                "config": {
                    "collection_name": MEMORY_COLLECTION,
                    "path": CHROMA_DB_PATH,
                }
            },
        })

    # ── WRITE operations ──

    def add_to_semantic(self, user_id: str, info: str):
        """Store a long-term preference fact.

        Examples: "Interested in AI stocks", "Risk tolerance is moderate",
                  "Holds NVDA, MSFT, GOOGL"
        """
        self.memory.add(
            info,
            user_id=user_id,
            metadata={"scope": "semantic"},
        )

    def add_to_episodic(self, user_id: str, session_summary: str):
        """Store a past session summary.

        Example: "2025-03-15: Discussed NVDA earnings, user was bullish on AI"
        """
        self.memory.add(
            session_summary,
            user_id=user_id,
            metadata={"scope": "episodic"},
        )

    def add_to_working(self, user_id: str, context: str):
        """Store current session context (temporary).

        Example: "Currently asking about semiconductor sector news"
        """
        self.memory.add(
            context,
            user_id=user_id,
            metadata={"scope": "working"},
        )

    def update_from_feedback(self, user_id: str, feedback: str, context: str):
        """
        PAHF Step 3: Process post-action feedback into memory.

        This is the critical mechanism. When the user says something like
        "I don't care about crypto" or "I've sold my GOOGL position",
        this extracts and stores that preference.

        Mem0 automatically handles:
        - Deduplication (won't store "likes tech" twice)
        - Conflict resolution (updates "likes tea" → "likes coffee")
        """
        self.memory.add(
            f"User feedback: {feedback}. Context: {context}",
            user_id=user_id,
            metadata={"scope": "semantic", "source": "feedback"},
        )

    # ── READ operations ──

    def retrieve_all_relevant(self, user_id: str, query: str, limit: int = None):
        """Search all memory scopes for info relevant to the query.

        Mem0 uses semantic similarity (not keyword matching), so:
        - Query "semiconductor earnings" will find "User interested in NVDA and AMD"
        - Query "risk" will find "User has moderate risk tolerance"
        """
        if limit is None:
            limit = MEMORY_SEARCH_LIMIT

        results = self.memory.search(
            query=query,
            user_id=user_id,
            limit=limit,
        )
        return results.get("results", [])

    def retrieve_profile(self, user_id: str):
        """Get ALL memories for a user (for display/debugging)."""
        all_memories = self.memory.get_all(user_id=user_id)
        return all_memories.get("results", [])

    def clear_user_memory(self, user_id: str):
        """Delete all memories for a user (useful for evaluation resets)."""
        self.memory.delete_all(user_id=user_id)