"""Cliente de solo consulta/análisis para MetaTrader 5. Nunca envía órdenes."""
import datetime as dt

import MetaTrader5 as mt5

import config


def connect():
    if not mt5.initialize():
        err = mt5.last_error()
        raise RuntimeError(f"mt5.initialize() falló: {err}")
    info = mt5.account_info()
    if info is None:
        raise RuntimeError(f"No hay cuenta iniciada en el terminal: {mt5.last_error()}")
    # trade_mode 0 = demo
    if info.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO:
        mt5.shutdown()
        raise RuntimeError(
            f"La cuenta no es DEMO (trade_mode={info.trade_mode}). Abortando."
        )
    return info


def find_bitcoin():
    symbols = mt5.symbols_get()
    if not symbols:
        raise RuntimeError(f"No se pudo listar símbolos: {mt5.last_error()}")
    all_names = [s.name for s in symbols]
    exact = None
    for cand in config.SYMBOL_CANDIDATES:
        for name in all_names:
            if name.upper() == cand.upper():
                exact = name
                break
        if exact:
            break
    if exact is None:
        # Fallback: cualquier nombre que empiece con el símbolo objetivo
        target = config.SYMBOL.upper()
        starts = [n for n in all_names if n.upper().startswith(target)]
        if starts:
            exact = sorted(starts, key=len)[0]
        else:
            raise RuntimeError(f"No se encontró el símbolo '{config.SYMBOL}' en el terminal.")
    if not mt5.symbol_select(exact, True):
        raise RuntimeError(f"No se pudo seleccionar el símbolo {exact}: {mt5.last_error()}")
    return exact


def server_offset_hours():
    symbol = find_bitcoin()
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        raise RuntimeError(f"Sin tick para {symbol}: {mt5.last_error()}")
    server_time = dt.datetime.fromtimestamp(tick.time, tz=dt.timezone.utc)
    utc_now = dt.datetime.now(dt.timezone.utc)
    offset = (server_time - utc_now).total_seconds() / 3600.0
    return offset, server_time, utc_now


def current_quote():
    symbol = find_bitcoin()
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        raise RuntimeError(f"Sin tick para {symbol}: {mt5.last_error()}")
    return {
        "symbol": symbol,
        "time": dt.datetime.fromtimestamp(tick.time, tz=dt.timezone.utc),
        "bid": tick.bid,
        "ask": tick.ask,
        "last": tick.last,
        "volume": tick.volume,
    }


def last_closed_candles(symbol=None, timeframe=mt5.TIMEFRAME_H1, count=10):
    if symbol is None:
        symbol = find_bitcoin()
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 1, count)
    if rates is None or len(rates) == 0:
        raise RuntimeError(f"copy_rates_from_pos sin datos para {symbol}: {mt5.last_error()}")
    return rates


def candles_by_range(symbol=None, timeframe=mt5.TIMEFRAME_H1, date_from=None, date_to=None):
    if symbol is None:
        symbol = find_bitcoin()
    if date_from is None:
        date_to = date_to or dt.datetime.now(dt.timezone.utc)
        date_from = date_to - dt.timedelta(days=7)
    rates = mt5.copy_rates_range(symbol, timeframe, date_from, date_to)
    if rates is None or len(rates) == 0:
        raise RuntimeError(f"copy_rates_range sin datos para {symbol}: {mt5.last_error()}")
    return rates
