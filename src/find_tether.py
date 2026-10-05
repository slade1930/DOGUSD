"""Búsqueda de Tether (USDT) en el broker. Solo consulta."""
import datetime as dt

import MetaTrader5 as mt5

import config
import mt5_client

STALE_SECONDS = 600  # 10 minutos


def main():
    mt5_client.connect()  # aborta si no es demo
    symbols = mt5.symbols_get()
    if not symbols:
        print("Error: mt5.symbols_get() devolvió None/vacío:", mt5.last_error())
        return

    matches = []
    for s in symbols:
        name = s.name or ""
        desc = s.description or ""
        if "USDT" in name.upper() or "USDT" in desc.upper() or "TETHER" in name.upper() or "TETHER" in desc.upper():
            matches.append(s)

    print(f"Símbolos cuyo name/description contienen 'USDT' o 'TETHER': {len(matches)}")
    now_utc = dt.datetime.now(dt.timezone.utc)
    candidates = []
    for s in matches:
        print("-" * 60)
        print(f"name:            {s.name}")
        print(f"description:     {s.description}")
        print(f"path:            {s.path}")
        print(f"currency_base:   {s.currency_base}")
        print(f"currency_profit: {s.currency_profit}")
        print(f"digits:          {s.digits}")
        if not mt5.symbol_select(s.name, True):
            print(f"  (no se pudo seleccionar: {mt5.last_error()})")
            continue
        tick = mt5.symbol_info_tick(s.name)
        if tick is None:
            print(f"  tick: None ({mt5.last_error()})")
            continue
        t = dt.datetime.fromtimestamp(tick.time, tz=dt.timezone.utc)
        print(f"  bid: {tick.bid}  ask: {tick.ask}  hora tick (UTC): {t.isoformat()}")
        age = (now_utc - t).total_seconds()
        if age > STALE_SECONDS:
            print(f"  AVISO: feed congelado o mercado cerrado (tick con {age/60:.1f} min de antigüedad). No se calcula desfase.")
        else:
            print(f"  tick fresco ({age:.0f} s). Desfase servidor-UTC ~ {(t - now_utc).total_seconds()/3600:+.3f} h")
        if 0.90 <= tick.bid <= 1.10:
            candidates.append((s.name, tick.bid))

    print("=" * 60)
    if candidates:
        print("Candidatos reales (tick presente y bid entre 0.90 y 1.10):")
        for name, bid in candidates:
            print(f"  - {name} (bid={bid})")
    else:
        print("No se encontraron candidatos reales de Tether.")
        print("Símbolos del path que contiene 'Crypto':")
        for s in symbols:
            if s.path and "crypto" in s.path.lower():
                print(f"  - name: {s.name} | description: {s.description} | path: {s.path}")
        print("Este broker no ofrece Tether")

    mt5.shutdown()


if __name__ == "__main__":
    main()
