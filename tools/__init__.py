"""
Tools package — external capabilities the agent can use.

Each tool is a Python function decorated with @tool from LangChain.
The agent sees the function name and docstring, and decides when to call it.

ALL_TOOLS is the master list that gets bound to the LLM.
"""
from tools.market_data import get_stock_price, get_portfolio_summary
from tools.news import fetch_financial_news, get_sector_overview

# Master list of all tools available to the agent
ALL_TOOLS = [
    get_stock_price,
    get_portfolio_summary,
    fetch_financial_news,
    get_sector_overview,
]

__all__ = ["ALL_TOOLS", "get_stock_price", "get_portfolio_summary",
           "fetch_financial_news", "get_sector_overview"]