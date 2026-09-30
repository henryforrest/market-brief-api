import os
import sys
from pathlib import Path

# ai_summary.py reads HF_TOKEN when it is imported, so it must exist before main is loaded.
os.environ.setdefault("HF_TOKEN", "test-token")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402
import pytest  # noqa: E402
import yfinance  # noqa: E402


@pytest.fixture
def ohlc_frame():
    """Ten days of prices where Open only ever rises but Close peaks at 200 and halves.

    Metrics computed from the two columns therefore differ: Open gives a drawdown of 0,
    Close gives -0.5.
    """
    return pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0],
            "High": [105.0, 125.0, 155.0, 205.0, 110.0, 125.0, 135.0, 145.0, 155.0, 165.0],
            "Low": [95.0, 100.0, 101.0, 102.0, 95.0, 100.0, 105.0, 106.0, 107.0, 108.0],
            "Close": [100.0, 120.0, 150.0, 200.0, 100.0, 120.0, 130.0, 140.0, 150.0, 160.0],
            "Volume": [1000] * 10,
        },
        index=pd.bdate_range("2024-01-01", periods=10),
    )


@pytest.fixture
def sample_info():
    return {
        "shortName": "Apple Inc.",
        "currentPrice": 341.07,
        "marketCap": 4977636933632,
        "trailingPE": 39.07,
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "longBusinessSummary": "Apple Inc. designs, manufactures, and markets smartphones.",
        "website": "https://www.apple.com",
    }


@pytest.fixture
def fake_yfinance(monkeypatch):
    """Replace yfinance.Ticker with a stub serving canned data, so no test touches the network.

    Returns an installer: call it with the history frame and info dict to serve. The
    installer returns a list that records every (method, symbol) call made on the stub.
    """

    def install(history, info=None):
        calls = []

        class FakeTicker:
            def __init__(self, symbol):
                self.symbol = symbol

            def history(self, start=None, **kwargs):
                calls.append(("history", self.symbol))
                return history.copy()

            @property
            def info(self):
                calls.append(("info", self.symbol))
                return info

        monkeypatch.setattr(yfinance, "Ticker", FakeTicker)
        return calls

    return install
