import pytest

from get_data import TickerNotFoundError, get_stock_data
from get_metrics import calculate_all_metrics, calculate_returns
from market_data import fetch_stock_data

STOCK_DATA_KEYS = {
    "ticker",
    "name",
    "price",
    "market_cap",
    "pe_ratio",
    "max_drawdown",
    "sharpe_ratio",
    "annualized_return",
    "volatility",
    "sector",
    "summary",
}


def test_get_stock_data_raises_when_yahoo_has_no_rows(fake_yfinance, ohlc_frame):
    fake_yfinance(history=ohlc_frame.iloc[0:0])

    with pytest.raises(TickerNotFoundError) as excinfo:
        get_stock_data("zzzz")

    assert excinfo.value.ticker == "ZZZZ"
    assert str(excinfo.value) == "No data found for ticker: ZZZZ"
    assert isinstance(excinfo.value, ValueError)


def test_fetch_stock_data_stops_before_reading_fundamentals_for_an_unknown_ticker(
    fake_yfinance, ohlc_frame
):
    calls = fake_yfinance(history=ohlc_frame.iloc[0:0], info={})

    with pytest.raises(TickerNotFoundError):
        fetch_stock_data("zzzz")

    assert calls == [("history", "ZZZZ")]


def test_fetch_stock_data_upper_cases_the_ticker_and_uses_closing_prices(
    fake_yfinance, ohlc_frame, sample_info
):
    calls = fake_yfinance(history=ohlc_frame, info=sample_info)

    data = fetch_stock_data("aapl")

    assert data["ticker"] == "AAPL"
    assert calls[0] == ("history", "AAPL")
    assert set(data) == STOCK_DATA_KEYS

    close = ohlc_frame["Close"]
    expected = calculate_all_metrics(close, calculate_returns(close))
    assert {key: data[key] for key in expected} == expected
    assert data["max_drawdown"] == pytest.approx(-0.5)

    assert data["name"] == "Apple Inc."
    assert data["price"] == 341.07
    assert data["summary"]["industry"] == "Consumer Electronics"
