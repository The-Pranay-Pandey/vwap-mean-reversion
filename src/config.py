import pandas as pd

# Data
instrument = "eurusd"
start = '2022-01-01'
end = '2026-07-01'
timeframe = "m5"

# vwap_signal
std_dev_multiplier = 2
band_touch_window = 2

# volume_fading
look_back_period = 20
volume_factor = 1.5

# momentum_signal
htf_rule = "1h"
htf_lookback = 4

# atr
atr_window = 14

# trading costs in pips
pip = 0.0001
spread = 0.5 * pip
commission_rt = 0.6 * pip
slip_entry = 0.2 * pip
slip_exit = 0.2 * pip

# sl and tp
sl_factor = 1
tp_factor = 2

# trade filters
weekend_gap = pd.Timedelta(hours=24)  # gap that marks the weekend
n_bars = 8                            # no entries in the last n_bars before a gap
k = 4                                 # no entries in the first k bars of a session

# loss-streak pause
last_n_trades = 3
pause = pd.Timedelta(hours=2)

# Monte Carlo
seed = 42
n_sims = 10_000
risk_per_trade = 0.01
ruin_level = 0.1
