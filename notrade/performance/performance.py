import numpy as np
import pandas as pd

def calculate_sharpe_ratio(returns, periods=252):
    """
    Calculates the Sharpe ratio for the strategy, based on
    a benchmark of zero (i.e. no risk-free rate information).

    Parameters:
    returns - a pandas Series representing period percentage returns
    periods - Daily (252), Hourly (252 * 6.5), Minutely(252 * 6.5 * 60), etc
    """
    return np.sqrt(periods) * np.mean(returns) / np.std(returns)

def calculate_drawdowns(equity_curve):
    """
    Calculate the largest peak-to-trough drawdown of the PnL curve
    as well as the duration of the drawdown. Requires that the
    equity_curve is a pandas Series.

    Parameters:
    equity_curve - a pandas Series representing period percentage returns

    Returns:
    drawdown, duration - highes peak-to-trough drawdown and duration
    """
    hwm = [0]

    # create the drawdown and duration series
    eq_idx = equity_curve.index
    drawdown = pd.Series(index=eq_idx)
    duration = pd.Series(index=eq_idx)

    for t in range(1, len(eq_idx)):
        cur_hwm = max(hwm[t-1], equity_curve[t])
        hwm.append(cur_hwm)
        drawdown[t] = hwm[t] - equity_curve[t]
        duration[t] = 0 if drawdown[t] == 0 else duration[t-1] + 1
    return drawdown.max(), duration.max()
