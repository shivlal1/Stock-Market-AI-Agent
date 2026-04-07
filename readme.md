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
| Evaluation | Custom PAHF 4-phase protocol | Automated testing with simulated users |

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
│
└── evaluation/                   # PAHF 4-phase testing
    ├── __init__.py
    ├── scenarios.py              # Test queries
    ├── metrics.py                # SR, FF, ACPE calculations
    └── run_eval.py               # Full evaluation runner
```

---

##  Quick Start

### Prerequisites

- Python 3.10+
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))

### Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/stock-watchlist-agent.git
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

### Run Evaluation (Optional)

```bash
python -m evaluation.run_eval
```

Runs the full PAHF 4-phase protocol with 5 synthetic investor personas across 15 scenarios each.

---

## 🧠 How the PAHF Framework Works

This project implements the [PAHF paper](https://arxiv.org/abs/2602.16173) (Meta, Feb 2026) which introduced a three-step loop for continual personalization:

### The Three-Step Loop

1. **Pre-Action Clarification**: Before responding, the agent checks its memory. If it doesn't have enough info about the user, it asks a targeted question first. This prevents bad guesses for new users.

2. **Memory-Grounded Action**: The agent retrieves relevant preferences from Mem0 and injects them into the system prompt, ensuring every response is personalized to THIS specific user.

3. **Post-Action Feedback Integration**: After responding, the agent analyzes the user's reply for new preference signals ("I don't care about crypto", "I sold GOOGL") and stores them in memory automatically.

### Why Both Feedback Channels Matter

| Channel | Solves | Example |
|---------|--------|---------|
| Pre-action (asking first) | Cold start — new user with no data | "Which sectors interest you?" |
| Post-action (learning from reactions) | Preference drift — outdated memory | User: "Actually I'm into biotech now" |

The PAHF paper proves mathematically that **both channels together** outperform either alone.

### 4-Phase Evaluation Protocol

| Phase | Personas | Feedback | Tests |
|-------|----------|----------|-------|
| Phase 1 | Original | ON | Can the agent learn from scratch? |
| Phase 2 | Original | OFF | Can it use what it learned on new scenarios? |
| Phase 3 | Evolved (shifted) | ON | Can it detect and adapt to preference changes? |
| Phase 4 | Evolved (shifted) | OFF | Did it actually update its memory correctly? |

---

## 💰 Cost

| Component | Cost |
|-----------|------|
| GPT-4o-mini (reasoning + memory) | ~$0.15/1M input, $0.60/1M output tokens |
| yfinance | Free |
| RSS news feeds | Free |
| Mem0 open-source | Free |
| ChromaDB | Free |
| **Typical dev session** | **~$0.05 - $0.20** |
| **Full evaluation run** | **~$8 - $15** |

---

##  Metrics

Following the PAHF paper, we track three metrics:

- **Success Rate (SR)**: Fraction of responses that were relevant to the user's actual preferences
- **Feedback Frequency (FF)**: How often feedback was needed (should decrease as agent learns)
- **ACPE (Average Cumulative Personalization Error)**: Tracks learning speed over iterations — a steeply declining ACPE means the agent is learning fast

---

## 🔧 Configuration

Edit `config.py` to customize:

```python
AGENT_MODEL = "gpt-4o-mini"       # LLM for reasoning (swap for gpt-4o for better quality)
TEMPERATURE = 0.2                  # Lower = more deterministic
MEMORY_SEARCH_LIMIT = 8           # Max memories retrieved per query
LEARNING_ITERATIONS = 3           # Evaluation iterations per phase
MAX_PERSONAS_FOR_EVAL = 5         # Number of test personas
```

---

##  Roadmap

- [ ] Add more investor personas (target: 20) for robust evaluation
- [ ] Implement drift detection using change-point algorithms on memory embeddings
- [ ] Add layered memory (working/episodic/semantic) with proper scope management
- [ ] Build SEC EDGAR integration for earnings and filing alerts
- [ ] Add portfolio tracking with performance attribution
- [ ] Human evaluation study via Gradio
- [ ] Publish evaluation results and benchmark

---

## 📚 References

- **PAHF Paper**: Liang et al., "Learning Personalized Agents from Human Feedback", arXiv:2602.16173, Feb 2026. [Paper](https://arxiv.org/abs/2602.16173) | [Code](https://github.com/facebookresearch/PAHF) | [Project Page](https://personalized-ai.github.io/)
- **Mem0**: Chhikara et al., "Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory", arXiv:2504.19413, 2025. [GitHub](https://github.com/mem0ai/mem0)
- **LangGraph**: LangChain's agent orchestration framework. [Docs](https://www.langchain.com/langgraph)
- **ReAct**: Yao et al., "ReAct: Synergizing Reasoning and Acting in Language Models", ICLR 2023.

---

## 🙏 Acknowledgments

- Meta's PAHF team for the continual personalization framework
- Mem0 team for the open-source memory layer
- LangChain team for LangGraph
- yfinance for free market data access# 📈 Personalized Stock Watchlist Agent

A conversational AI financial research assistant that **learns your investment preferences through conversation** and delivers personalized market updates, news, and portfolio insights — improving over every interaction.

Built on Meta's PAHF framework, combining LLM-based agents, persistent per-user memory, and dual feedback channels for continual personalization.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-green)
![Mem0](https://img.shields.io/badge/Mem0-1.0+-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## What It Does

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
          │ Process Feedback │ ← Extract new preferences, update Mem0
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
| Evaluation | Custom PAHF 4-phase protocol | Automated testing with simulated users |

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
│
└── evaluation/                   # PAHF 4-phase testing
    ├── __init__.py
    ├── scenarios.py              # Test queries
    ├── metrics.py                # SR, FF, ACPE calculations
    └── run_eval.py               # Full evaluation runner
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))

### Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/stock-watchlist-agent.git
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

---

## 🧠 How the PAHF Framework Works

This project implements the Meta PAHF paper which introduced a three-step loop for continual personalization:

### The Three-Step Loop

1. **Pre-Action Clarification**: Before responding, the agent checks its memory. If it doesn't have enough info about the user, it asks a targeted question first. This prevents bad guesses for new users.

2. **Memory-Grounded Action**: The agent retrieves relevant preferences from Mem0 and injects them into the system prompt, ensuring every response is personalized to THIS specific user.

3. **Post-Action Feedback Integration**: After responding, the agent analyzes the user's reply for new preference signals ("I don't care about crypto", "I sold GOOGL") and stores them in memory automatically.

### Why Both Feedback Channels Matter

| Channel | Solves | Example |
|---------|--------|---------|
| Pre-action (asking first) | Cold start — new user with no data | "Which sectors interest you?" |
| Post-action (learning from reactions) | Preference drift — outdated memory | User: "Actually I'm into biotech now" |

---

##  Cost

| Component | Cost |
|-----------|------|
| GPT-4o-mini (reasoning + memory) | ~$0.15/1M input, $0.60/1M output tokens |
| yfinance | Free |
| RSS news feeds | Free |
| Mem0 open-source | Free |
| ChromaDB | Free |
| **Typical dev session** | **~$0.05 - $0.20** |
| **Full evaluation run** | **~$8 - $15** |


## 🔧 Configuration

Edit `config.py` to customize:

```python
AGENT_MODEL = "gpt-4o-mini"       # LLM for reasoning (swap for gpt-4o for better quality)
TEMPERATURE = 0.2                  # Lower = more deterministic
MEMORY_SEARCH_LIMIT = 8           # Max memories retrieved per query
LEARNING_ITERATIONS = 3           # Evaluation iterations per phase
MAX_PERSONAS_FOR_EVAL = 5         # Number of test personas
```

---

## 📚 References

- **PAHF Paper**: Liang et al., "Learning Personalized Agents from Human Feedback", arXiv:2602.16173, Feb 2026. [Paper](https://arxiv.org/abs/2602.16173)
- **Mem0**: Chhikara et al., "Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory", arXiv:2504.19413, 2025. [GitHub](https://github.com/mem0ai/mem0)
- **LangGraph**: LangChain's agent orchestration framework. [Docs](https://www.langchain.com/langgraph)
- **ReAct**: Yao et al., "ReAct: Synergizing Reasoning and Acting in Language Models", ICLR 2023.

---

##  Acknowledgments

- Meta's PAHF team for the continual personalization framework
- Mem0 team for the open-source memory layer
- LangChain team for LangGraph
- yfinance for free market data access# Stock-Market-AI-Agent
