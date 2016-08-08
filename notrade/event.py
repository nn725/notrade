class Event(object):
    """ Base class for events. """
    pass

class MarketEvent(Event):
    """ Handles market update event. """
    def __init__(self):
        self.type = 'Market'

class SignalEvent(Event):
    """ Handles event of sending a strategy signal. """
    def __init__(self, symbol, datetime, signal_type):
        """
        Initializes a SignalEvent.

        Parameters:
        symbol - the ticker symbol
        datetime- the timestamp when the signal was generated
        signal_type - 'LONG' or 'SHORT'
        """
        self.type = 'SIGNAL'
        self.symbol = symbol
        self.datetime = datetime
        self.signal_type = signal_type

class OrderEvent(Event):
    """ Handles sending an order to execution system. """
    def __init__(self, symbol, order_type, quantity, direction):
        """
        Initializes a SignalEvent.

        Parameters:
        symbol - the instrument to trade
        order_type - 'MKT' or 'LMT' for Market or Limit
        quantity - non-negative integer for quantity
        direction - 'BUY' or 'SELL' for long or short
        """
        self.type = 'ORDER'
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.direction = direction

    def __str__(self):
        return 'ORDER {} {} ${} {}'.format(self.symbol, 
                self.order_type, self.quantity, self.directioni)

class FillEvent(Event):
    """
    Simulates event of a filled order, as returned by
    brokerage. Stores quantity, price and fees.
    """
    def __init__(self, timeindex, symbol, exchange, quantity,
            direction, fill_cost, commission=None):
        """
        Initializes a FillEvent. If commission is not provided,
        it will be calculated based on IB fees.

        Parameters:
        timeindex - bar-resolution when the order was filled
        symbol - the exchange
        quantity - quantity of fill
        direction - direction of fill
        fill_cost - the holdings value in dollars
        commission - commission of fill
        """
        self.type = 'FILL';
        self.timeindex = timeindex
        self.symbol = symbol
        self.exchange = exchange
        self.quantity = quantity
        self.direction = direction
        self.fill_cost = fill_cost

        self.commission = self.calculate_commission() if commission is None \
                                                      else commission

def calculate_commission(self):
    """
    Calculates the fees of trading based on IB fee structure
    for API in USD. Does not include exchange or ECN fees.

    Source:
    https://www.interactivebrokers.com/en/index.php?f=commission&p=stocks2
    """
    full_cost = 1.3
    if self.quantity <= 500:
        full_cost = max(1.3, 0.013 * self.quantity)
    else:
        full_cost = max(1.3, 0.008 * self.quantity)
    full_cost = min(fill_cost, 0.5 / 100.0 * self.quantity * self.fill_cost)
    return full_cost
