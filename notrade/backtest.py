import event
from strategy import strategy

bars = DataHandler()
strategy = Strategy()
portfolio = Portfolio()
broker = ExecutionHandler()

while True:
    # Update the bars (specific for backtest)
    if bars.continue_backtest:
        bars.update_bars()
    else:
        break

    # Handle the events
    while True:
        try:
            event = events.get(False)
        except Queue.Empty:
            break
        else:
            if event is not None:
                if event.type == 'MARKET':
                    strategy.calculate_signals(event)
                    portfolio.update_timeindex(event)
                elif event.type == 'SIGNAL':
                    portfolio.update_signal(event)
                elif event.type == 'ORDER':
                    broker.execute_order(event)
                elif event.type == 'FILL':
                    port.update_fill(event)
    # 10 min heartbeat
    time.sleep(600)
