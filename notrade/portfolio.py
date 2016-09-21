from .position import Position

class Portfolio(object):
    def __init_(self, price_handler, cash):
        """
        On creation, the Portfolio object contains
        no positions and all values are set to initial
        cash, with no PnL.
        """
        self.price_handler = price_handler
        self.init_cash = cash
        self.equity = cash
        self.cur_cash = cash
        self.positions = {}
        self.closed_positions = {}
        self.realized_pnl = 0

    def update_portfolio(self):
        """
        Updates the value of all positions that are currently
        open. Value of closed positions is tallied as
        self.realized_pnl.
        """
        self.unrealized_pnl = 0
        self.equity += self.realized_pnl
        self.equity += self.init_cash

        for ticker in self.positions:
            pt = self.positions[ticker]
            if self.price_handler.istick():
                bid, ask = self.price_handler.get_best_bid_ask(ticker)
            else:
                close_price = self.price_handler.get_last_close(ticker)
                bid = close_price
                ask = close_price
            pt.update_market_value(bid, ask)
            self.unrealized_pnl += pt.unrealized_pnl
            pnl_diff = pt.realized_pnl - pt.unrealized_pnl
            self.equity += pt.market_value - pt.cost_basis + pnl_diff

    def _add_position(self, action, ticker, quantity, price, commission):
        """ Adds a new Position object to the Portfolio. """
        if ticker not in self.positions:
            if self.price_handler.istick():
                bid, ask = self.price_handler.get_best_bid_ask(ticker)
            else:
                close_price = self.price_handler.get_last_close(ticker)
                bid, ask = close_price, close_price
            position = Position(action, ticker, quantity, price, commission, bid, ask)
            self.positions[ticker] = position
            self.update_portfolio()
        else:
            print('%s is already in the positions list.'.format(ticker))

   def _modify_position(self, action, ticker, quantity, price, commission):
       """
       Modifies a current Position oject to the Portfolio. This requires
       getting the bid/ask price from the price handler.
       """
       if ticker in self.positions:
           self.positions[ticker].transact_shares(action, quantity, price, commission)
           if self.price_handler.istick():
               bid, ask = self.price_handler.get_best_bid_ask(ticker)
           else:
               close_price = self.price_handler.get_last_close(ticker)
               bid, ask = close_price, close_price
           self.positions[ticker].update_market_value(bid, ask)

           if self.positions[ticker].quantity == 0:
               closed = self.positions.pop(ticker)
               self.realized_pnl += closed.realized_pnl
               self.closed_positions.append(closed)

           self.update_portfolio()
       else:
           print('%s not in current position list.'.format(ticker))

    def transact_position(self, action, ticker, quantity, price, commission):
        """
        Handles any new position or modification to a current position,
        by calling the respective _add_position and _modify_position
        methods.
        """
        if action == 'BOT':
            self.cur_cash -= ((quantity * price) + commission)
        elif action == 'SLD':
            self.cur_cash += ((quantity * price) - commission)

        if ticker not in self.positions:
            self._add_position(action, ticker, quantity, price, commission)
        else:
            self._modify_position(action, ticker, quantity, price, commission)

