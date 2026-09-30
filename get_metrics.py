import pandas as pd
import numpy as np
from get_data import get_prices

def calculate_returns(prices):
    if isinstance(prices, pd.DataFrame):
        prices = get_prices(prices)

    returns = prices.pct_change().dropna()
    return returns


def calculate_max_drawdown(prices):
    if isinstance(prices, pd.DataFrame):
        prices = get_prices(prices)

    equity = prices / prices.iloc[0]
    drawdown = equity / equity.cummax() - 1
    return drawdown.min()


def calculate_sharpe_ratio(returns, risk_free_rate=0.01):
    if isinstance(returns, pd.DataFrame):
        returns = returns.iloc[:, 0]

    excess_returns = returns - risk_free_rate / 252
    std = excess_returns.std()

    if isinstance(std, pd.Series):
        std = std.mean()

    if std == 0 or not np.isfinite(std):
        return 0.0

    mean = excess_returns.mean()
    if not np.isfinite(mean):
        return 0.0

    return (mean / std) * (252 ** 0.5)



def calculate_annualized_return(returns):
    if isinstance(returns, pd.DataFrame):
        returns = returns.iloc[:, 0]

    if len(returns) == 0:
        return 0.0

    n_years = len(returns) / 252
    if n_years == 0:
        return 0.0

    compounded_growth = (1 + returns).prod()

    if not np.isfinite(compounded_growth):
        return 0.0

    return compounded_growth ** (1 / n_years) - 1



def calculate_volatility(returns):
    return returns.std() * (252 ** 0.5)

def calculate_all_metrics(prices, returns):
    metrics = {
        "max_drawdown": float(calculate_max_drawdown(prices)),
        "sharpe_ratio": float(calculate_sharpe_ratio(returns)),
        "annualized_return": float(calculate_annualized_return(returns)),
        "volatility": float(calculate_volatility(returns)),
    }
    return metrics





