"""Central configuration for the Stock Watchlist Agent."""
import os
from dotenv import load_dotenv

load_dotenv()  # Reads .env file and sets environment variables

# ── LLM Settings ──
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AGENT_MODEL = "gpt-4o-mini"       # Main reasoning model
EMBEDDING_MODEL = "text-embedding-3-small"  # For memory search
TEMPERATURE = 0.2                  # Lower = more deterministic

# ── Memory Settings ──
CHROMA_DB_PATH = "./chroma_db"     # Where vector DB is stored on disk
MEMORY_COLLECTION = "stock_watchlist"
MEMORY_SEARCH_LIMIT = 8           # Max memories to retrieve per query

# ── Evaluation Settings ──
LEARNING_ITERATIONS = 3           # How many times to loop Phase 1 and 3
MAX_PERSONAS_FOR_EVAL = 5         # Start small, scale up later