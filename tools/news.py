"""Financial news tools using free RSS feeds (no API key needed)."""
import feedparser
from langchain_core.tools import tool

# Free financial news RSS feeds
NEWS_FEEDS = {
    "Reuters Business": "https://feeds.reuters.com/reuters/businessNews",
    "MarketWatch Top": "http://feeds.marketwatch.com/marketwatch/topstories/",
    "CNBC Top News": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
}


@tool
def fetch_financial_news(topic: str) -> str:
    """Fetch recent financial news headlines related to a topic.

    Args:
        topic: A search topic like 'NVIDIA earnings', 'semiconductor sector',
               'Federal Reserve', 'tech stocks'
    """
    all_articles = []
    topic_words = topic.lower().split()

    for source_name, feed_url in NEWS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:25]:
                title = entry.get("title", "")
                summary = entry.get("summary", entry.get("description", ""))
                searchable = f"{title} {summary}".lower()

                # Basic keyword matching — the LLM will do deeper relevance filtering
                if any(word in searchable for word in topic_words):
                    all_articles.append({
                        "title": title,
                        "summary": summary[:200],
                        "source": source_name,
                        "link": entry.get("link", ""),
                    })
        except Exception:
            continue  # Skip broken feeds silently

    if not all_articles:
        return (
            f"No recent news found matching '{topic}'. "
            f"Try broader terms (e.g., 'technology' instead of a specific stock)."
        )

    output = f"Recent news related to '{topic}':\n\n"
    for i, article in enumerate(all_articles[:6], 1):
        output += f"{i}. [{article['source']}] {article['title']}\n"
        if article["summary"]:
            output += f"   {article['summary'][:150]}...\n"
        output += "\n"

    return output


@tool
def get_sector_overview(sector: str) -> str:
    """Get performance overview of a market sector using sector ETFs.

    Args:
        sector: Sector name — one of: technology, healthcare, financial,
                energy, consumer, industrial, materials, utilities,
                real_estate, communication
    """
    import yfinance as yf

    sector_etfs = {
        "technology": ("XLK", "Technology"),
        "healthcare": ("XLV", "Healthcare"),
        "financial": ("XLF", "Financials"),
        "energy": ("XLE", "Energy"),
        "consumer": ("XLY", "Consumer Discretionary"),
        "industrial": ("XLI", "Industrials"),
        "materials": ("XLB", "Materials"),
        "utilities": ("XLU", "Utilities"),
        "real_estate": ("XLRE", "Real Estate"),
        "communication": ("XLC", "Communication Services"),
    }

    lookup = sector.lower().replace(" ", "_")
    match = sector_etfs.get(lookup)

    if not match:
        available = ", ".join(sector_etfs.keys())
        return f"Unknown sector '{sector}'. Available sectors: {available}"

    etf_symbol, full_name = match

    try:
        hist = yf.Ticker(etf_symbol).history(period="1mo")
        if hist.empty:
            return f"No data available for {full_name} sector"

        current = hist["Close"].iloc[-1]
        month_start = hist["Close"].iloc[0]
        change_1m = ((current - month_start) / month_start) * 100

        week_idx = min(5, len(hist) - 1)
        week_start = hist["Close"].iloc[-week_idx]
        change_1w = ((current - week_start) / week_start) * 100

        return (
            f"{full_name} Sector ({etf_symbol}):\n"
            f"  Current Price: ${current:.2f}\n"
            f"  1-Week Change: {change_1w:+.2f}%\n"
            f"  1-Month Change: {change_1m:+.2f}%"
        )
    except Exception as e:
        return f"Error fetching sector data: {str(e)}"