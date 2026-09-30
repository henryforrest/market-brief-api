import yfinance as yf
from get_metrics import calculate_returns
from get_data import get_stock_data, get_prices
from get_metrics import calculate_all_metrics
from company import get_company_summary 

def fetch_stock_data(ticker: str):
    ticker = ticker.upper()
    stock = yf.Ticker(ticker)
    info = stock.info

    history = get_stock_data(ticker)
    prices = get_prices(history)
    returns = calculate_returns(prices)

    metrics = calculate_all_metrics(prices, returns)
    summary = get_company_summary(ticker)

    if info is None or "shortName" not in info:
        raise ValueError("Invalid ticker")

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


