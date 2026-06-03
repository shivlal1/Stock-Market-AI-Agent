# 📈 Personalized Stock Watchlist Agent

A conversational AI financial research assistant that **learns your investment preferences through conversation** and delivers personalized market updates, news, and portfolio insights - improving over every interaction.

Built on Meta's PAHF framework, combining LLM-based agents, persistent per-user memory, and dual feedback channels for continual personalization.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-green)
![Mem0](https://img.shields.io/badge/Mem0-1.0+-purple)

---

## 🎯 What It Does

- **Remembers you**: Stores your investment interests, holdings, risk tolerance, and sector preferences across sessions using Mem0 persistent memory
- **Learns gradually**: Extracts preferences from natural conversation — no forms or setup wizards
- **Adapts to change**: Detects when your preferences shift ("I sold my GOOGL position") and updates accordingly
- **Fetches real data**: Pulls live stock prices via yfinance and financial news via RSS feeds
- **Personalizes everything**: Ranks and filters information based on what YOU care about, not generic market summaries

### Example Interaction

```
Session 1:
  You:   "What's happening in the market today?"
  Agent: "What sectors or stocks are you interested in?"
  You:   "Big tech — Google, Meta, Nvidia"
  Agent: [fetches GOOGL, META, NVDA prices + tech sector data]
         "Here's your tech portfolio update: NVDA is up 2.1%..."
         → Mem0 stores: "User interested in GOOGL, META, NVDA"

Session 2 (next day):
  You:   "How are my stocks doing?"
  Agent: [remembers your holdings, fetches prices immediately]
         "Your portfolio: NVDA $142.50 (+1.3%), META $585.20 (+0.7%)..."
         → No clarification needed — agent already knows you
```

---

##  Architecture

The agent implements a **three-step PAHF loop** as a LangGraph state machine:

```
User Message
     │
     ▼
┌──────────────────┐
│  Retrieve Memory  │ ← Read Mem0 + extract preferences from message
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│    Check if       │
│  Clarification    │ ← "Do I know enough about this user?"
│    Needed         │
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
  YES        NO
    │         │
    ▼         ▼
┌────────┐ ┌─────────────┐
│  Ask   │ │ Reason &    │◄──────┐
│  User  │ │ Act (ReAct) │       │
└───┬────┘ └──────┬──────┘       │
    │             │              │
    ▼        Tool call?          │
  [END]      │       │           │
  (wait)   YES      NO           │
             │       │           │
             ▼       │           │
          ┌──────┐   │           │
          │Tools │───┘ (loop)    │
          └──────┘               │
                   │
                   ▼
          ┌──────────────────┐
          │ Process Feedback  │ ← Extract new preferences, update Mem0
          └────────┬─────────┘
                   │
                   ▼
                 [END]
```

### Key Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Agent Brain | LangGraph + GPT-4o-mini | ReAct reasoning, tool selection, personalization |
| Memory | Mem0 + ChromaDB | Per-user persistent preference storage |
| Stock Data | yfinance | Real-time prices, fundamentals, sector ETFs |
| News | RSS feeds (Reuters, MarketWatch, CNBC) | Financial news headlines |
| UI | Gradio | Chat interface with memory inspector |

---

##  Project Structure

```
stock-watchlist-agent/
│
├── .env                          # API keys (OPENAI_API_KEY)
├── config.py                     # Central configuration
├── requirements.txt              # Dependencies
├── app.py                        # Gradio web interface
│
├── agent/                        # PAHF agent (the brain)
│   ├── __init__.py
│   ├── state.py                  # LangGraph state schema
│   ├── prompts.py                # All prompt templates
│   ├── nodes.py                  # Node functions (clarify, act, feedback)
│   └── graph.py                  # Wires nodes into LangGraph
│
├── memory/                       # Persistent per-user memory
│   ├── __init__.py
│   └── manager.py                # Mem0 wrapper (semantic/episodic/working scopes)
│
├── tools/                        # External data tools
│   ├── __init__.py
│   ├── market_data.py            # Stock prices (yfinance)
│   └── news.py                   # Financial news (RSS)
│
├── personas/                     # Synthetic users (evaluation only)
│   ├── __init__.py
│   ├── profiles.py               # 5 investor personas + evolved versions
│   └── simulator.py              # LLM-based human simulator
```

---

##  Quick Start

### Prerequisites

- Python 3.10+
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))

### Installation

```bash
# Clone the repo
git clone https://github.com/shivlal1/Stock-Market-AI-Agent/tree/main
cd stock-watchlist-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

### Run the App

```bash
python app.py
```

Opens a Gradio chat interface at `http://localhost:7860`. Start chatting — the agent will learn your preferences automatically.

```

Runs the full PAHF 4-phase protocol with 5 synthetic investor personas across 15 scenarios each.

---

## 🧠 How the PAHF Framework Works

This project implements the [PAHF paper](https://arxiv.org/abs/2602.16173) (Meta, Feb 2026) which introduced a three-step loop for continual personalization:

### The Three-Step Loop

1. **Pre-Action Clarification**: Before responding, the agent checks its memory. If it doesn't have enough info about the user, it asks a targeted question first. This prevents bad guesses for new users.

2. **Memory-Grounded Action**: The agent retrieves relevant preferences from Mem0 and injects them into the system prompt, ensuring every response is personalized to THIS specific user.

3. **Post-Action Feedback Integration**: After responding, the agent analyzes the user's reply for new preference signals ("I don't care about crypto", "I sold GOOGL") and stores them in memory automatically.



---
