import yfinance as yf
from get_metrics import calculate_returns
from get_data import get_stock_data, get_prices
from get_metrics import calculate_all_metrics
from company import get_company_summary 

def fetch_stock_data(ticker: str):
    ticker = ticker.upper()

    # Fetch the price history first: get_stock_data raises TickerNotFoundError when
    # Yahoo has no rows for the ticker, so an unknown ticker fails here, before any
    # fundamentals are requested.
    history = get_stock_data(ticker)
    prices = get_prices(history)
    returns = calculate_returns(prices)

    metrics = calculate_all_metrics(prices, returns)

    stock = yf.Ticker(ticker)
    info = stock.info
    if info is None or "shortName" not in info:
        raise ValueError(f"No company data found for ticker: {ticker}")

    summary = get_company_summary(ticker)

    return {
        "ticker": ticker,
        "name": info.get("shortName"),
        "price": info.get("currentPrice"),
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "max_drawdown": metrics["max_drawdown"],
        "sharpe_ratio": metrics["sharpe_ratio"],
        "annualized_return": metrics["annualized_return"],
        "volatility": metrics["volatility"],
        "sector": info.get("sector"),
        "summary": summary,
    }


