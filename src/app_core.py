"""Núcleo de consultas: conexión, datos y análisis con pandas (solo consulta)."""
import datetime as dt

import MetaTrader5 as mt5
import numpy as np
import pandas as pd

import config
import mt5_client


def connect_demo():
    """Conecta y aborta si la cuenta no es demo."""
    return mt5_client.connect()


def rates_to_df(rates):
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    return df.set_index("time")


def last_closed(count=100, timeframe=mt5.TIMEFRAME_H1):
    symbol = mt5_client.find_bitcoin()
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 1, count)
    if rates is None or len(rates) == 0:
        raise RuntimeError(f"Sin velas cerradas para {symbol}: {mt5.last_error()}")
    return symbol, rates_to_df(rates)


def by_range(date_from, date_to, timeframe=mt5.TIMEFRAME_H1):
    symbol = mt5_client.find_bitcoin()
    rates = mt5.copy_rates_range(symbol, timeframe, date_from, date_to)
    if rates is None or len(rates) == 0:
        return symbol, pd.DataFrame()
    return symbol, rates_to_df(rates)


def weekly_summary(df):
    d = df.resample("1D").agg(open=("open", "first"), high=("high", "max"),
                              low=("low", "min"), close=("close", "last"),
                              tick_volume=("tick_volume", "sum")).dropna()
    d["change_pct"] = d["close"].pct_change() * 100
    return d


def quality_report(df):
    empty = df.isna().sum().to_dict()
    dups = df.index.duplicated().sum()
    if isinstance(df.index, pd.DatetimeIndex) and len(df) > 1:
        expected = pd.date_range(df.index.min(), df.index.max(), freq="1h", tz="UTC")
        missing = expected.difference(df.index)
    else:
        missing = []
    return {"empty_per_column": empty, "duplicate_timestamps": int(dups),
            "missing_hourly_intervals": len(missing), "missing_timestamps": [str(x) for x in missing][:50]}


def pct_change_hourly(df):
    return df["close"].pct_change() * 100


def candle_type(df):
    out = pd.Series(np.where(df["close"] > df["open"], "alcista",
                             np.where(df["close"] < df["open"], "bajista", "doji")),
                    index=df.index)
    return out


def hourly_avg_move(df):
    mv = df["close"].pct_change().abs() * 100
    return mv.groupby(df.index.hour).mean()


def weekday_moves(df):
    mv = df["close"].pct_change().abs() * 100
    return mv.groupby(df.index.dayofweek).mean()


def sma20(df):
    return df["close"].rolling(20).mean()


def streaks(df):
    types = candle_type(df)
    best = {"alcista": (0, None, None), "bajista": (0, None, None)}
    cur, start = None, None
    for t, ty in types.items():
        if ty in ("alcista", "bajista"):
            if ty == cur:
                pass
            else:
                if cur is not None:
                    n = len(types.loc[start:t]) - 1
                cur, start = ty, t
        else:
            cur, start = None, None
    # versión simple y robusta
    results = {}
    for target in ("alcista", "bajista"):
        seq = (types == target).astype(int)
        max_len, cur_len = 0, 0
        end_idx = None
        for i, v in seq.items():
            cur_len = cur_len + 1 if v else 0
            if cur_len > max_len:
                max_len, end_idx = cur_len, i
        if end_idx is not None and max_len > 0:
            start_idx = types.index[types.index.get_loc(end_idx) - max_len + 1]
            price_change = (df.loc[end_idx, "close"] / df.loc[start_idx, "open"] - 1) * 100
            results[target] = {"hours": int(max_len), "start": str(start_idx), "end": str(end_idx),
                               "price_change_pct": round(float(price_change), 3)}
    return results
