"""Test scenarios for evaluation — the 'tasks' each persona faces."""

SCENARIOS = [
    # ── Ambiguous queries (typically trigger clarification for new users) ──
    {"query": "What should I be watching today?", "type": "ambiguous"},
    {"query": "Give me a market update", "type": "ambiguous"},
    {"query": "Any good opportunities right now?", "type": "ambiguous"},
    {"query": "What do you think about the market?", "type": "ambiguous"},

    # ── Portfolio-specific (need memory of user's holdings) ──
    {"query": "How are my holdings doing?", "type": "portfolio"},
    {"query": "Any news about my stocks?", "type": "portfolio"},
    {"query": "Should I be worried about my portfolio?", "type": "portfolio"},
    {"query": "Give me a quick portfolio checkup", "type": "portfolio"},

    # ── Sector queries (need memory of user's sector interests) ──
    {"query": "What's happening in my favorite sectors?", "type": "sector"},
    {"query": "Any sector rotation I should know about?", "type": "sector"},
    {"query": "How is the sector I'm most invested in performing?", "type": "sector"},

    # ── Specific/factual (less personalization needed) ──
    {"query": "What's AAPL trading at?", "type": "factual"},
    {"query": "How did the S&P 500 do today?", "type": "factual"},

    # ── Preference-revealing (user volunteers new info) ──
    {"query": "I've been thinking about getting into renewable energy", "type": "preference_reveal"},
    {"query": "I'm getting more risk-averse lately", "type": "preference_reveal"},
]