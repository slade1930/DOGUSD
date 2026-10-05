"""Fase 1: conexión, detección de símbolo Bitcoin y series de datos (solo lectura)."""
import datetime as dt

import MetaTrader5 as mt5

import config
import mt5_client


def _fmt_rates(rates):
    lines = []
    for r in rates:
        t = dt.datetime.fromtimestamp(r["time"], tz=dt.timezone.utc)
        lines.append(
            f"  {t.isoformat()}  O={r['open']:.2f} H={r['high']:.2f} "
            f"L={r['low']:.2f} C={r['close']:.2f} V={r['tick_volume']}"
        )
    return lines


def main():
    print("=" * 70)
    print("ACTIVIDAD 1: Conexión a MetaTrader 5 y verificación de cuenta DEMO")
    print("=" * 70)
    info = mt5_client.connect()
    print(f"Cuenta: {info.login}")
    print(f"Servidor: {info.server}")
    print(f"Trade mode: {info.trade_mode} (0 = DEMO)")
    print(f"Balance: {info.balance} {info.currency}")
    print(f"Apalancamiento: {info.leverage}")

    print()
    print("=" * 70)
    print("ACTIVIDAD 2: Detección del símbolo de Bitcoin")
    print("=" * 70)
    symbols = mt5.symbols_get()
    all_names = [s.name for s in symbols]
    btc_like = sorted(n for n in all_names if "BTC" in n.upper())
    print(f"Símbolos que contienen 'BTC' ({len(btc_like)}):")
    for n in btc_like:
        print(f"  - {n}")
    has_btcusdt = any(n.upper().startswith("BTCUSDT") for n in all_names)
    has_btcusd = any(n.upper().startswith("BTCUSD") and not n.upper().startswith("BTCUSDT") for n in all_names)
    print(f"¿Existe BTCUSDT?: {has_btcusdt}")
    print(f"¿Existe BTCUSD?: {has_btcusd}")
    exact = mt5_client.find_bitcoin()
    print(f"Símbolo exacto de Bitcoin seleccionado: {exact}")

    print()
    print("=" * 70)
    print("ACTIVIDAD 3: Desfase servidor-UTC, cita actual y velas")
    print("=" * 70)
    offset, server_time, utc_now = mt5_client.server_offset_hours()
    print(f"Hora servidor (UTC-stamped): {server_time.isoformat()}")
    print(f"Hora UTC local:             {utc_now.isoformat()}")
    print(f"Desfase servidor-UTC:       {offset:+.2f} horas")

    quote = mt5_client.current_quote()
    print(f"Cita actual de {quote['symbol']}:")
    print(f"  Tiempo: {quote['time'].isoformat()}")
    print(f"  Bid: {quote['bid']}  Ask: {quote['ask']}  Last: {quote['last']}  Vol: {quote['volume']}")

    print("Últimas 5 velas H1 cerradas (start_pos=1, se omite la vela en formación):")
    for line in _fmt_rates(mt5_client.last_closed_candles(exact, mt5.TIMEFRAME_H1, 5)):
        print(line)

    date_to = dt.datetime.now(dt.timezone.utc)
    date_from = date_to - dt.timedelta(days=2)
    print(f"Velas por rango ({date_from.date()} -> {date_to.date()}, H1):")
    rates = mt5_client.candles_by_range(exact, mt5.TIMEFRAME_H1, date_from, date_to)
    print(f"  Total de velas: {len(rates)}")
    for line in _fmt_rates(rates[-5:]):
        print(line)

    mt5.shutdown()
    print()
    print("mt5.shutdown() OK. Fase 1 completada.")


if __name__ == "__main__":
    main()
