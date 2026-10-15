import numpy as np
import pandas as pd
from src.config import (
    std_dev_multiplier, band_touch_window, look_back_period, volume_factor,
    htf_rule, htf_lookback, atr_window, spread, slip_entry, sl_factor,
    tp_factor, weekend_gap, n_bars, k,
)


def add_vwap_bands(data):
    ny = data.index.tz_convert("America/New_York").tz_localize(None)
    data["vwap_day"] = (ny - pd.Timedelta(hours=17)).date

    data['tp'] = (data['high'] + data['low'] + data['close']) / 3
    data['tpv'] = data['tp'] * data['volume']
    data["cum_tpv"] = data.groupby('vwap_day')['tpv'].cumsum()
    data["cum_vol"] = data.groupby('vwap_day')['volume'].cumsum()
    data["vwap"] = data["cum_tpv"] / data["cum_vol"]
    data['tp2v'] = (data['tp'] ** 2) * data['volume']
    data['cum_tp2v'] = data.groupby('vwap_day')['tp2v'].cumsum()

    data['variance'] = data["cum_tp2v"] / data["cum_vol"] - data["vwap"] ** 2
    data['std_dev'] = np.sqrt(data["variance"].clip(lower=0))

    data[f"upper_{std_dev_multiplier}_std"] = data["vwap"] + std_dev_multiplier * data["std_dev"]
    data[f"lower_{std_dev_multiplier}_std"] = data["vwap"] - std_dev_multiplier * data["std_dev"]

    data.drop(columns=['tp', 'tpv', 'cum_tpv', 'cum_vol', 'tp2v', 'cum_tp2v', 'variance', 'std_dev'], inplace=True)
    return data


def add_touch_signals(data):
    data['touched_upper'] = (data["high"] > data[f"upper_{std_dev_multiplier}_std"]).rolling(band_touch_window).max().fillna(0).astype(int)
    data['touched_lower'] = (data["low"] < data[f"lower_{std_dev_multiplier}_std"]).rolling(band_touch_window).max().fillna(0).astype(int)
    return data


def add_volume_fade_signal(data):
    volume = data['volume'].to_numpy()
    close = data['close'].to_numpy()
    n = len(data)
    signal = np.zeros(n, dtype=np.int8)

    if n >= look_back_period:
        volume_windows = np.lib.stride_tricks.sliding_window_view(volume, look_back_period)

        max_vol_pos = np.arange(n - look_back_period + 1) + volume_windows.argmax(axis=1)

        max_vol = volume[max_vol_pos]
        max_vol_close = close[max_vol_pos]

        v = volume[look_back_period - 1:]  # bar at the end of each window - current bar
        c = close[look_back_period - 1:]

        faded = max_vol > volume_factor * v
        signal[look_back_period - 1:] = np.where(faded & (c < max_vol_close), 1, 0)
        signal[look_back_period - 1:] = np.where(faded & (c > max_vol_close), -1, signal[look_back_period - 1:])

    data['volume_faded_signal'] = signal
    return data


def add_momentum_signal(data):
    htf_close = data["close"].tz_convert("UTC").resample(htf_rule).last().dropna()
    htf_trend = np.sign(htf_close.diff(htf_lookback))
    htf_trend = htf_trend.shift(1)
    data["momentum_signal"] = htf_trend.reindex(data.index, method="ffill").fillna(0).astype(int)
    return data


def add_atr(data):
    prev_close = data['close'].shift(1)
    tr = pd.concat([
        data['high'] - data['low'],
        (data['high'] - prev_close).abs(),
        (data['low'] - prev_close).abs()],
        axis=1).max(axis=1)

    data['atr'] = tr.ewm(alpha=1 / atr_window, adjust=False, min_periods=atr_window).mean()
    data['atr'] = data['atr'].shift(1)
    return data


def add_entry_signals(data):
    long_entry = (
        (data["momentum_signal"] == 1) &
        (data['touched_lower'] == 1) &
        (data["volume_faded_signal"] == 1) &
        # (data['close'] > data['close'].shift(1))
        (data['close'].shift(1) >= data['vwap'].shift(1))
    )
    short_entry = (
        (data["momentum_signal"] == -1) &
        (data['touched_upper'] == 1) &
        (data["volume_faded_signal"] == -1) &
        # (data['close'] < data['close'].shift(1))
        (data['close'].shift(1) <= data['vwap'].shift(1))
    )

    data["entry_signal"] = np.select([long_entry, short_entry], [1, -1], default=0)
    data["entry_signal"] = data['entry_signal'].shift(1).fillna(0).astype(int)
    return data


def add_exit_levels(data):
    data['prev_high'] = data['high'].shift(1)
    data['prev_low'] = data['low'].shift(1)

    data['stop_loss'] = np.select(
        [data['entry_signal'] == -1, data['entry_signal'] == 1],
        [data['prev_high'] + sl_factor * data['atr'] + spread, data['prev_low'] - sl_factor * data['atr']],
        default=np.nan)
    fill_long = data['open'] + spread + slip_entry
    fill_short = data['open'] - slip_entry
    risk = np.select(
        [data['entry_signal'] == -1, data['entry_signal'] == 1],
        [data['stop_loss'] - fill_short, fill_long - data['stop_loss']])
    data['target'] = np.select(
        [data['entry_signal'] == -1, data['entry_signal'] == 1],
        [fill_short - tp_factor * risk, fill_long + tp_factor * risk],
        default=np.nan)
    return data


def add_trade_filters(data):
    idx = data.index.to_series()
    # prevent weekend holding
    data['last_bar_before_gap'] = ((idx.shift(-1) - idx) > weekend_gap).to_numpy()
    # prevent taking trades in last n_bars
    data['stop_entry_bar'] = ((idx.shift(-n_bars) - idx) > weekend_gap).to_numpy()
    # prevent entry in first k session bars
    data['bars_in_session'] = data.groupby('vwap_day').cumcount()
    data['mature_bars'] = (data['bars_in_session'] >= k).to_numpy()
    return data


def build_features(data):
    """Run the full indicator / signal pipeline in order."""
    data = add_vwap_bands(data)
    data = add_touch_signals(data)
    data = add_volume_fade_signal(data)
    data = add_momentum_signal(data)
    data = add_atr(data)
    data = add_entry_signals(data)
    data = add_exit_levels(data)
    data = add_trade_filters(data)
    return data
