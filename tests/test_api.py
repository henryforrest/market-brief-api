import pytest
from fastapi.testclient import TestClient

import main
from get_data import TickerNotFoundError

RESPONSE_KEYS = {
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
    "ai_summary",
}

STOCK_DATA = {
    "ticker": "AAPL",
    "name": "Apple Inc.",
    "price": 341.07,
    "market_cap": 4977636933632,
    "pe_ratio": 39.07,
    "max_drawdown": -0.374,
    "sharpe_ratio": 0.867,
    "annualized_return": 0.25,
    "volatility": 0.297,
    "sector": "Technology",
    "summary": {
        "name": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "summary": "Apple Inc. designs, manufactures, and markets smartphones.",
        "website": "https://www.apple.com",
        "market_cap": 4977636933632,
    },
}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main, "generate_ai_summary", lambda ticker, data: "Summary: steady.")
    return TestClient(main.app)


def test_known_ticker_returns_the_full_document(client, monkeypatch):
    requested = []

    def fake_fetch(ticker):
        requested.append(ticker)
        return dict(STOCK_DATA)

    monkeypatch.setattr(main, "fetch_stock_data", fake_fetch)

    response = client.get("/stock/AAPL")

    assert response.status_code == 200
    assert set(response.json()) == RESPONSE_KEYS
    assert response.json() == {**STOCK_DATA, "ai_summary": "Summary: steady."}
    assert requested == ["AAPL"]


def test_unknown_ticker_returns_404(client, monkeypatch):
    def fake_fetch(ticker):
        raise TickerNotFoundError(ticker.upper())

    monkeypatch.setattr(main, "fetch_stock_data", fake_fetch)

    response = client.get("/stock/zzzz")

    assert response.status_code == 404
    assert response.json() == {"detail": "Unknown ticker: ZZZZ"}


def test_any_other_failure_returns_500_with_the_message(client, monkeypatch):
    def fake_fetch(ticker):
        raise RuntimeError("Yahoo Finance timed out")

    monkeypatch.setattr(main, "fetch_stock_data", fake_fetch)

    response = client.get("/stock/AAPL")

    assert response.status_code == 500
    assert response.json() == {"detail": "Yahoo Finance timed out"}


def test_end_to_end_with_stubbed_yfinance(client, fake_yfinance, ohlc_frame, sample_info):
    fake_yfinance(history=ohlc_frame, info=sample_info)

    response = client.get("/stock/aapl")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == RESPONSE_KEYS
    assert body["ticker"] == "AAPL"
    assert body["name"] == "Apple Inc."
    assert body["max_drawdown"] == pytest.approx(-0.5)  # from Close; Open alone never falls
    assert body["ai_summary"] == "Summary: steady."


def test_end_to_end_unknown_ticker_with_stubbed_yfinance(client, fake_yfinance, ohlc_frame):
    fake_yfinance(history=ohlc_frame.iloc[0:0], info={})

    response = client.get("/stock/zzzz")

    assert response.status_code == 404
    assert response.json() == {"detail": "Unknown ticker: ZZZZ"}
