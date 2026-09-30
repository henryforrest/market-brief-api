import numpy as np
import pandas as pd
import pytest

from get_data import get_prices
from get_metrics import (
    calculate_all_metrics,
    calculate_annualized_return,
    calculate_max_drawdown,
    calculate_returns,
    calculate_sharpe_ratio,
    calculate_volatility,
)


def metrics_for(prices):
    return calculate_all_metrics(prices, calculate_returns(prices))


def test_constant_prices_give_zero_for_every_metric():
    metrics = metrics_for(pd.Series([100.0] * 30))

    assert metrics["volatility"] == pytest.approx(0.0, abs=1e-12)
    assert metrics["sharpe_ratio"] == 0.0  # std is zero, so the code short-circuits to 0.0
    assert metrics["max_drawdown"] == pytest.approx(0.0, abs=1e-12)
    assert metrics["annualized_return"] == pytest.approx(0.0, abs=1e-12)


def test_max_drawdown_is_the_worst_fall_from_the_running_peak():
    prices = pd.Series([100.0, 120.0, 150.0, 200.0, 100.0, 120.0])

    assert calculate_max_drawdown(prices) == pytest.approx(-0.5)


def test_annualised_return_of_constant_daily_growth_over_one_year():
    r = 0.001
    prices = pd.Series(100.0 * (1 + r) ** np.arange(253))  # 253 prices, 252 daily returns
    returns = calculate_returns(prices)

    assert len(returns) == 252
    assert calculate_annualized_return(returns) == pytest.approx((1 + r) ** 252 - 1, abs=1e-6)


def test_sharpe_and_volatility_use_a_one_percent_rate_and_a_252_day_year():
    returns = pd.Series([0.01, -0.01, 0.02, -0.005, 0.015])
    excess = returns - 0.01 / 252

    assert calculate_volatility(returns) == pytest.approx(returns.std() * 252**0.5)
    assert calculate_sharpe_ratio(returns) == pytest.approx(excess.mean() / excess.std() * 252**0.5)


def test_metrics_follow_close_not_open(ohlc_frame):
    from_frame = metrics_for(ohlc_frame)

    assert calculate_returns(ohlc_frame).equals(ohlc_frame["Close"].pct_change().dropna())
    assert from_frame == metrics_for(ohlc_frame["Close"])
    assert from_frame != metrics_for(ohlc_frame["Open"])
    assert from_frame["max_drawdown"] == pytest.approx(-0.5)  # Open alone never falls


def test_returns_never_fall_back_to_the_first_column():
    with pytest.raises(KeyError):
        calculate_returns(pd.DataFrame({"Open": [1.0, 2.0, 3.0]}))


def test_get_prices_prefers_adjusted_close():
    df = pd.DataFrame({"Open": [1.0, 2.0], "Close": [10.0, 20.0], "Adj Close": [9.0, 18.0]})

    assert get_prices(df).equals(df["Adj Close"])


def test_get_prices_falls_back_to_close():
    df = pd.DataFrame({"Open": [1.0, 2.0], "Close": [10.0, 20.0]})

    assert get_prices(df).equals(df["Close"])


def test_get_prices_rejects_a_frame_without_a_price_column():
    with pytest.raises(KeyError):
        get_prices(pd.DataFrame({"Open": [1.0, 2.0]}))
