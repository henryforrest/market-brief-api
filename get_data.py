import yfinance as yf


def get_stock_data(ticker, start_date="2015-01-01"):
    ticker = ticker.upper()
    stock = yf.Ticker(ticker)
    df = stock.history(start=start_date)

    if df.empty:
        raise ValueError(f"No data found for ticker: {ticker}")

    return df

def get_prices(df):
    """Return the price series the metrics use: the adjusted close if present, otherwise the close."""
    if "Adj Close" in df.columns:
        return df["Adj Close"]
    elif "Close" in df.columns:
        return df["Close"]
    else:
        raise KeyError("Price column not found in data")



def get_volume(df):
    return df["Volume"]
