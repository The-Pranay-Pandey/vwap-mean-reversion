import numpy as np
import pandas as pd
from src.config import spread, slip_entry, slip_exit, commission_rt, last_n_trades, pause


def run_backtest(data):
    """Iterative backtest. Returns a DataFrame of trades (pnl is in R multiples)."""
    open, high, low, close = (data[x].to_numpy() for x in ['open', 'high', 'low', 'close'])

    signal = data['entry_signal'].to_numpy()  # already shifted
    stop = data['stop_loss'].to_numpy()       # already shifted
    target = data['target'].to_numpy()        # already shifted
    timestamps = data.index.to_numpy()

    last_bar_before_gap = data['last_bar_before_gap'].to_numpy()
    stop_entry_bar = data['stop_entry_bar'].to_numpy()
    mature_bars = data['mature_bars'].to_numpy()

    entry_i = -1
    position = 0
    trades = []

    exit_price = 0.0
    entry_price = 0.0

    stop_price = 0.0
    target_price = 0.0
    r = 0.0

    n = len(data)

    last_n_results = []
    last_trade_close_time = None
    avoid_time = data.index.to_numpy()[0]

    def close_trade(entry_i, i, entry_price, exit_price, reason, risk):
        nonlocal position, last_trade_close_time, avoid_time
        gross = (exit_price - entry_price) * position
        pnl = (gross - commission_rt) / risk
        last_n_results.append(1 if pnl > 0 else -1)
        if len(last_n_results) > last_n_trades:
            last_n_results.pop(0)
        last_trade_close_time = timestamps[i]
        if 1 not in last_n_results and len(last_n_results) >= last_n_trades:
            avoid_time = last_trade_close_time + pause
            # last_n_results.clear()
        trades.append({'type': 'long' if position == 1 else 'short', 'entry_time': timestamps[entry_i], 'exit_time': timestamps[i],
                       'entry_price': entry_price, 'exit_price': exit_price, 'pnl': pnl, 'reason': reason, "risk": risk})

    for i in range(n):

        if position == 0 and not (stop_entry_bar[i]) and mature_bars[i] and (timestamps[i] > avoid_time):  # Position entry
            if (signal[i] == 1) and not (np.isnan(stop[i]) or np.isnan(target[i])) and (stop[i] < open[i] < target[i]):  # long entry
                fill = open[i] + spread + slip_entry
                if stop[i] < fill < target[i]:
                    entry_price = fill
                    stop_price = stop[i]
                    target_price = target[i]
                    position = 1
                    entry_i = i
                    r = abs(entry_price - stop_price)

            elif (signal[i] == -1) and not (np.isnan(stop[i]) or np.isnan(target[i])) and (target[i] < open[i] < stop[i]):  # short entry
                fill = open[i] - slip_entry
                if target[i] < fill < stop[i]:
                    entry_price = fill
                    stop_price = stop[i]
                    target_price = target[i]
                    position = -1
                    entry_i = i
                    r = abs(entry_price - stop_price)

        if position == 1:  # long exit

            if (open[i] <= stop_price):  # stoploss hit - opened gap down below the sl
                exit_price = open[i] - slip_exit
                close_trade(entry_i, i, entry_price, exit_price, "stop_loss", r)
                position = 0

            elif (low[i] <= stop_price):  # stoploss hit - low crossed the sl
                exit_price = stop_price
                close_trade(entry_i, i, entry_price, exit_price, "stop_loss", r)
                position = 0

            elif (open[i] >= target_price):  # target hit - opened gap up above the tp
                exit_price = open[i] - slip_exit
                close_trade(entry_i, i, entry_price, exit_price, "target_hit", r)
                position = 0

            elif (high[i] >= target_price):  # target hit - high crossed the tp
                exit_price = target_price
                close_trade(entry_i, i, entry_price, exit_price, "target_hit", r)
                position = 0

        elif position == -1:  # short exit
            ask_open = open[i] + spread
            ask_high = high[i] + spread
            ask_low = low[i] + spread
            if (ask_open >= stop_price):  # stoploss hit - opened gap up above the sl
                exit_price = ask_open + slip_exit
                close_trade(entry_i, i, entry_price, exit_price, "stop_loss", r)
                position = 0

            elif (ask_high >= stop_price):  # stoploss hit - high crossed the sl
                exit_price = stop_price
                close_trade(entry_i, i, entry_price, exit_price, "stop_loss", r)
                position = 0

            elif (ask_open <= target_price):  # target hit - opened down below the tp
                exit_price = ask_open + slip_exit
                close_trade(entry_i, i, entry_price, exit_price, "target_hit", r)
                position = 0

            elif (ask_low <= target_price):  # target hit - low crossed the tp
                exit_price = target_price
                close_trade(entry_i, i, entry_price, exit_price, "target_hit", r)
                position = 0

        if position != 0 and (last_bar_before_gap[i] or i == n - 1):
            px = (close[i] - slip_exit) if position == 1 else (close[i] + spread + slip_exit)
            close_trade(entry_i, i, entry_price, px, 'weekend_close' if last_bar_before_gap[i] else 'end_of_data', r)
            position = 0

    if not trades:
        raise SystemExit("No trades were taken")
    return pd.DataFrame(trades)
