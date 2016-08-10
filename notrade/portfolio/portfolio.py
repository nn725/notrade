import datetime
import numpy as np
import pandas as pd
import queue

from abc import ABCMeta, abstractmethod
from math import floor

from ..event import FillEvent, OrderEvent
from ..performance import calculate_sharpe_ratio, calculate_drawdowns

class Portfolio(object):
    """
    The Portfolio class handles the positions and market
    value of all instruments at a resolution of a bar.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def update_signal(self, event):
        """
        Acts on a SignalEvent to generate new orders
        based on the portfolio logic.
        """
        raise NotImplementedError('udate_signal() not implemented')

    @abstractmethod
    def update_fill(self, event):
        """
        Updates the portfolio current positions and holdings
        from a FillEvent.
        """
        raise NotImplementedError('update_fill() not implemented')

class SimplePortfolio(Portfolio):
    """
    The SimplePortfolio is designed to send orders to a brokerage
    object with a constant quantity size without any risk management
    or position sizing. It is used to test simple strategies.
    """

    def __init__(self, bars, events, start_date, initial_capital=100000.0):
        """
        Initializes the portfolio.

        Parameters:
        bars - the DataHandler object with current market data
        events - the Event Queue
        start_date - the start date (bar) of the portfolio
        initial_capital - the starting capital in USD
        """
        self.bars = bars
        self.events = events
        self.symbol_list = self.bars.symbol_list
        self.start_date = start_date
        self.initial_capital = initial_capital

        self.all_positions = self.construct_positions()
        self.current_positions = self._create_symbol_dict()
        self.all_holdings = self.construct_all_holdings()
        self.current_holdings = self.construct_current_holdings()

    def construct_positions(self):
        """
        Constructs the positions list using the start_date
        to determine when the time index will begin.
        """
        d = self._create_symbol_dict()
        d['datetime'] = self.start_date
        return [d]

    def construct_all_holdings(self):
        """
        Constructs the holdings list using the start_date
        to determine when the time index will begin.
        """
        d = _create_symbol_dict()
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return d

    def update_timeindex(self, event):
        """
        Adds a new record to the positions dict for the
        current market data bar. This reflects the
        previous bar. Uses a MarketEvent from the
        events queue.
        """
        bars = {sym: self.bars.get_latest_bars(sym, N=1)
                for sym in self.symbol_list}

        # Update positions
        dp = self._create_symbol_dict()
        dp['datetime'] = bars[self.symbol_list[0]][0][1] # time of latest bar of some symbol

        dp.update(self.current_positions)

        # Append the current positions
        self.all_positions.append(dp)

        # Update holdings
        dh = self._create_symbol_dict()
        dh['datetime'] = bars[self.symbol_list[0]][0][1]
        dh['cash'] = self.current_holdings['cash']
        dh['commission'] = self.current_holdings['commission']
        dh['total'] = self.current_holdings['cash']

        for s in self.symbol_list:
            # Approximation for actual value, good for intra day
            market_value = self.current_positions[s] * bars[s][0][5]
            dh[s] = market_value
            dh['total'] += market_value

        # Append the current holdings
        self.all_holdings.append(dh)

    def update_positions_from_fill(self, fill):
        """
        Takes a FillEvent and updates the position to reflect the new
        position.

        Parameters:
        fill - the FillEvent
        """
        fill_dir = 1 if fill.direction == 'BUY' else -1
        self.current_positions[fill.symbol] += fill_dir * fill.quantity

    def update_holdings_from_fill(self, fill):
        """
        Takes a FillEvent and updates the holdings to reflect the
        holdings value.

        Parameters:
        fill - the FillEvent object
        """
        fill_dir = 1 if fill.direction == 'BUY' else -1

        fill_cost = self.bars.get_latest_bars(fill.symbol)[0][5] # close price
        cost = fill_dir * fill_cost * fill.quantity
        self.current_holdings[fill.symbol] += cost
        self.current_holdings['commission'] += fill.commission
        self.current_holdings['cash'] -= cost + fill.commission
        self.current_holdings['total'] -= cost + fill.commission

    def update_fill(self, event):
        """
        Updates the portfolios current positions and holdings from
        an Event.

        Parameters:
        event - the Event object
        """
        if event.type == 'FILL':
            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)

    def create_equity_curve(self):
        """
        Creates a pandas DataFrame from the all_holdings list of
        dictionaries.
        """
        curve = pd.DataFrame(self.all_holdings)
        curve.set_index('datetime', inplace=True)
        curve['returns'] = curve['total'].pct_change()
        curve['equity_curve'] = (1.0 + curve['returns']).cumprod()
        self.equity_curve = curve

    def output_summary_stats(self):
        """
        Creates a list of summary statistics for the portfolio such
        as Sharpe ratio and drawdown information.
        """
        total_return = self.equity_curve['equity_curve'][-1]
        returns = self.equity_curve['returns']
        pnl = self.equity_curve['equity_curve']

        sharpe_ratio = calculate_sharpe_ratio(returns)
        max_dd, dd_duration = calculate_drawdowns(pnl)

        stats = [('Total Return', '%0.2f%%'.format((total_return - 1.0) * 100.0)),
                 ('Sharpe ratio', '%0.2f'.format(sharpe_ratio)),
                 ('Max Drawdown', '%0.2f%%'.format(max_dd * 100.0)),
                 ('Drawdown duration', '%d'.format(dd_duration))]
        return stats

    def _create_symbol_dict(self):
        """
        Constructs a dictionary that maps each symbol in symbol_list
        to 0.
        """
        return {sym: pos for sym, pos in ((s, 0) for s in self.symbol_list)}
