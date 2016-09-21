from .portfolio import Portfolio

class PortfolioHandler(object):
    def __init__(self, initial_cash, events_queue, price_handler
                 position_sizer, risk_manager):
        """
        The PortfolioHandler exposes two methods, on_signal
        and on_fill, which handle how SignalEvent and FillEvent
        objects are dealt with.

        The Portfolio takes handles to a PositionSizer, which
        determines a mechanism as to how to size the new Order,
        and a RiskManager, which is used to modify any generated
        Orders to remain in line with risk parameters.
        """
        self.initial_cash = initial_cash
        self.events_queue = events_queue
        self.price_handler = price_handler
        self.position_sizer = position_sizer
        self.risk_manager = risk_manager
        self.portfolio = Portfolio(price_handler, initial_cash)

    def _create_order_from_signal(self, signal_event):
        """
        Take a SignalEvent and use it to form a SuggestedOrder object,
        which can then be sent to a RiskManager to get an OrderEvent.
        """
        return SuggestedOrder(signal_event.ticker, signal_event.action)

    def _place_orders(self, order_list):
        """
        Once the RiskManager has done its work on the orders, they
        are placed into the events queue.
        """
        for order_event in order_list:
            self.events_queue.put(order_event)

    def _update_portfolio_from_fill(self, fill_event):
        """
        Converts the FillEvent into a transaction that is stored
        in the Portfolio object. This ensures the broker and
        local Portfolio are in sync/

        For backtesting purposes, the portfolio value can be
        reasonably estimated by modifying how the ExecutionHandler
        handles slippage, transaction costs, liquidity and market
        impact.
        """
        action = fill_event.action
        ticker = fill_event.ticker
        quantity = fill_event.quantity
        price = fill_event.price
        commission = fill_event.commission
        self.portfolio.transact_position(action, ticker, quantity,
                price, commission)

    def on_signal(self, signal_event):
        """
        Handles signal events produced in the event queue and
        forms SuggestedOrders from the SignalEvent after running
        it through the PosiionSizer. The event is then sent to
        the RiskManager.
        """
        initial_order = self._create_order_from_signal(signal_event)
        sized_order = self.position_sizer.size_order(self.portfolio,
                initial_order)
        order_events = self.risk_manager.refine_orders(
                self.portfolio, sized_order)
        self._place_orders(order_events)

    def on_fill(self, fill_event):
        """
        Handles fill events by updating the Portfolio object.

        In backtesting, the FillEvents will be simulated by a
        model representing the execution.
        """
        self.update_portfolio_from_fill(fill_event)

    def update_portfolio_value(self):
        """
        Update the portfolio to reflect current market
        value as based on last bid/ask of each ticker.
        """
        self.portfolio._update_portfolio()

class SuggestedOrder(object):
    """
    A helper class to make sure signal events are not converted
    to order events before going through the PositionSizer and
    RiskManager.
    """
    def __init__(self, ticker, action, quantity=0):
        """ Initializes the SuggestedOrder. """
        self.ticker = ticker
        self.action = action
        self.quantity = quantity
