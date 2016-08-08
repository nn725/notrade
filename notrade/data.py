import datetime
import os, os.path
import pandas as pd

from abc import ABCMeta, abstractmethod

from .event import MarketEvent

class DataHandler(object):
    """ DataHandler is an abstract base class for handling market data. """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_bars(self, symbol, N=1):
        """
        Returns the last N bars from the latest_symbol list, or fewer if
        less bars are available.
        """
        raise NotImplementedError('get_bars not implemented.')

    @absractmethod
    def update_bars(self):
        """
        Pushes the latest bar to the latest symbol structure for all
        symbols in the symbol list.
        """
        raise NotImplementedError('update_bars not implemented.')

class HistoricCSVDataHandler(DataHandler):
    """ HistoricCSVDataHanlder handles data in CSV files. """

    def __init__(self, events, csv_dir, symbol_list):
        """
        Initializes the data handler. All files are of the form
        '{symbol}.csv'.

        Parameters:
        events - the Event queue
        csv_dir - absolute path to data
        symbol_list - a list of symbol strings
        """
        self.events = events
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list

        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.continue_backtest = True

        self._open_convert_csv_files()

    def _open_convert_csv_files(self):
        """
        Opens the CSV files from the data directory, converting them
        into pandas DataFrames within a symbol directory. The format
        is assumed to be the DTN IQFeed.
        """
        comb_index = None
        for s in self.symbol_list:
            self.symbol_data[s] = pd.io.parsers.read_csv(
                    os.path.join(self.csv_dir, '%s.csv' % s),
                    header=0, index_col=0,
                    names=['datetime', 'open', 'low', 'high', 'close'])
            if comb_index is None:
                comb_index = self.symbol_data[s].index
            else:
                comb_index.union(self.symbol_data[s].index)

            self.latest_symbol_data[s] = []

        for s in self.symbol_list:
            self.symbol_data[s] = self.symbol_data[s].reindex(
                    index=comb_index, method='pad').iterrows()

    def _get_new_bar(self, symbol):
        """
        Returns the latest bar from the data feed as a tuple of
        (symbol, datetime, open, low, high, close, volume).
        """
        for b in self.symbol_data[symbol]:
            yield tuple([symbol, datetime.datetime.strptime(
                b[0], '%Y-%m-%d %H:%M:%S'), b[1][0], b[1][1],
                b[1][2], b[1][3], b[1][4]])

    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars from the latest_symbol list
        or less if unavailable.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print('{} is not available in the data set.'.format(symbol))
        else:
            return bars_list[-N:]

    def update_bars(self):
        """
        Pushes the latest bar to the latest_symbol_data structure.
        """
        for s in self.symbol_list:
            try:
                bar = self._get_new_bars(s).next()
            except StopIteration:
                self.continue_backtest = False
            else:
                if bar is not None:
                    self.latest_symbol_data[s].append(bar)
        self.events.put(MarketEvent())
