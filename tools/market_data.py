"""Stock market data tools using yfinance (free, no API key needed)."""
import yfinance as yf
from langchain_core.tools import tool


@tool
def get_stock_price(symbol: str) -> str:
    """Get current stock price and key metrics for a ticker symbol.

    Args:
        symbol: Stock ticker like AAPL, MSFT, NVDA
    """
    try:
        ticker = yf.Ticker(symbol.upper().strip())
        info = ticker.info
        hist = ticker.history(period="5d")

        if hist.empty:
            return f"No data found for {symbol}"

        current = hist["Close"].iloc[-1]
        prev = hist["Close"].iloc[-2] if len(hist) > 1 else current
        change_pct = ((current - prev) / prev) * 100

        return (
            f"{symbol.upper()}: ${current:.2f} ({change_pct:+.2f}% today)\n"
            f"52-Week High: ${info.get('fiftyTwoWeekHigh', 'N/A')}\n"
            f"52-Week Low: ${info.get('fiftyTwoWeekLow', 'N/A')}\n"
            f"Market Cap: ${info.get('marketCap', 0) / 1e9:.1f}B\n"
            f"P/E Ratio: {info.get('trailingPE', 'N/A')}\n"
            f"Sector: {info.get('sector', 'N/A')}"
        )
    except Exception as e:
        return f"Error fetching data for {symbol}: {str(e)}"


@tool
def get_portfolio_summary(symbols: str) -> str:
    """Get a quick price summary for multiple stocks at once.

    Args:
        symbols: Comma-separated ticker symbols like 'AAPL,MSFT,NVDA'
    """
    tickers = [s.strip().upper() for s in symbols.split(",")]
    results = []

    for sym in tickers[:10]:  # Cap at 10 to avoid slow responses
        try:
            hist = yf.Ticker(sym).history(period="5d")
            if not hist.empty:
                current = hist["Close"].iloc[-1]
                prev = hist["Close"].iloc[-2] if len(hist) > 1 else current
                change = ((current - prev) / prev) * 100
                results.append(f"  {sym}: ${current:.2f} ({change:+.2f}%)")
            else:
                results.append(f"  {sym}: no data available")
        except Exception:
            results.append(f"  {sym}: error fetching data")

    return "Portfolio Summary:\n" + "\n".join(results)