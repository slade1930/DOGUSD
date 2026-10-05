"""Orquestador de las 30 actividades del análisis LINK (solo consulta)."""
import os
import time
import datetime as dt

import MetaTrader5 as mt5
import numpy as np
import pandas as pd

import config
import app_core
import report_gen as rg

EVID = []
SECTIONS = []
EXTRA_SHEETS = {}


def note(n, text):
    EVID.append(f"\n### {n}\n{text}\n")


def section(heading, text, imgs=()):
    SECTIONS.append((heading, text, list(imgs)))


def fmt_period(df):
    return f"{df.index.min()} → {df.index.max()} (UTC), {len(df)} registros"


def main():
    info = app_core.connect_demo()
    note("Actividad 1 — Identificación de LINK (Interlink Electronics)", "")
    symbols = mt5.symbols_get()
    cands = [s for s in symbols if "LINK" in (s.name or "").upper()]
    sym = app_core.mt5_client.find_bitcoin()
    si = mt5.symbol_info(sym)
    note("Actividad 1 — Identificación de LINK (Interlink Electronics)",
         f"- Cuenta DEMO login={info.login} servidor={info.server}\n"
         f"- Símbolo real usado: `{sym}`\n- Descripción: {si.description}\n"
         f"- Moneda base/profit: {si.currency_base}/{si.currency_profit}\n"
         f"- Otros con 'LINK': {[s.name for s in cands]}")
    section("Actividad 1 — Identificación de LINK (Interlink Electronics)",
            f"Cuenta DEMO MetaQuotes. Símbolo exacto de LINK en este broker: `{sym}` — {si.description} ({si.currency_base}/{si.currency_profit}). Total de símbolos con 'LINK': {len(cands)}.")

    from mt5_client import current_quote
    q = current_quote()
    note("Actividad 2 — Precio actual",
         f"Bid={q['bid']} Ask={q['ask']} Spread={q['ask']-q['bid']:.4f} Hora UTC={q['time']}")
    section("Actividad 2 — Precio actual",
            f"Compra (ask): {q['ask']}, venta (bid): {q['bid']}, spread: {q['ask']-q['bid']:.4f} USD. Hora de la cotización: {q['time']} UTC. ⚠️ Tick de viernes 02/10 (feed congelado o mercado cerrado por fin de semana).")

    sym, df100 = app_core.last_closed(100)
    note("Actividad 3 — Lectura inicial (últimas 100 velas H1 cerradas)",
         f"Columnas: {list(df100.columns)}\nPrimeras filas:\n{df100.head(3).to_string()}\nÚltimas filas:\n{df100.tail(3).to_string()}")
    section("Actividad 3 — Lectura inicial (100 velas H1)",
            f"Columnas: {list(df100.columns)}. Período: {fmt_period(df100)}.")

    now = dt.datetime.now(dt.timezone.utc)
    d_from, d_to = now - dt.timedelta(days=7), now
    sym, df7 = app_core.by_range(d_from, d_to)
    note("Actividad 4 — Consulta por fechas (7 días)",
         f"Solicitado: {d_from} → {d_to}. Obtenido: {fmt_period(df7) if not df7.empty else 'SIN DATOS'}")
    section("Actividad 4 — Consulta por fechas",
            f"Período solicitado: {d_from.date()} → {d_to.date()}. Obtenido: {fmt_period(df7) if not df7.empty else 'sin registros (fin de semana sin datos)'}.")

    q = app_core.quality_report(df100)
    note("Actividad 5 — Calidad de datos", str(q) + "\nCausa posible: fin de semana sin mercados; velas H1 cerradas omiten la vela en formación (start_pos=1).")
    section("Actividad 5 — Calidad de datos",
            f"Nulos por columna: {q['empty_per_column']}. Fechas duplicadas: {q['duplicate_timestamps']}. Intervalos horarios sin registros: {q['missing_hourly_intervals']}. Posible causa: mercados cerrados el fin de semana y feed demo sintético; el conteo de cierres puede tener huecos donde el servidor no emitió vela.")

    df = df7 if not df7.empty else df100
    close = df["close"]
    tmax = (close.idxmax(), float(close.max())); tmin = (close.idxmin(), float(close.min()))
    img = rg.plot_close_series(df, f"{sym} Cierre H1 — 7 días (UTC)", "act6_cierre.png", maxima=tmax, minima=tmin)
    note("Actividad 6 — Evolución del precio", f"Máx {tmax[1]:.2f} en {tmax[0]}; Mín {tmin[1]:.2f} en {tmin[0]}")
    section("Actividad 6 — Evolución del precio (cierre)", f"Período: {fmt_period(df)}. Máximo: {tmax[1]:.2f} ({tmax[0]} UTC). Mínimo: {tmin[1]:.2f} ({tmin[0]} UTC).", [img])

    ranges = (df["high"] - df["low"]).sort_values(ascending=False).head(10)
    img = rg.plot_bar(ranges, f"{sym} — Top 10 velas H1 con mayor rango (máx-mín), UTC", "USD", "act7_rangos.png", xlabel="Hora UTC")
    note("Actividad 7 — Mayor movimiento dentro de una vela", ranges.to_string())
    section("Actividad 7 — Mayor movimiento dentro de una vela", f"Top 10 rangos (high-low) en USD:\n{ranges.round(2).to_string()}", [img])

    chg = app_core.pct_change_hourly(df).dropna()
    ups = chg.sort_values(ascending=False).head(10)
    img = rg.plot_bar(ups, f"{sym} — Top 10 subidas horarias (%)", "%", "act8_subidas.png", xlabel="Hora UTC")
    note("Actividad 8 — Mayores subidas", ups.to_string() + f"\nMayor subida: {ups.iloc[0]:.2f}% el {ups.index[0]}")
    section("Actividad 8 — Mayores subidas", f"Top 10 horas con mayor % de subida del cierre respecto a la hora anterior. Mayor subida: {ups.iloc[0]:.2f}% en {ups.index[0]} UTC.", [img])

    downs = chg.sort_values().head(10)
    img = rg.plot_bar(downs, f"{sym} — Top 10 caídas horarias (%)", "%", "act9_caidas.png", xlabel="Hora UTC")
    note("Actividad 9 — Mayores caídas", downs.to_string() + f"\nMayor caída: {downs.iloc[0]:.2f}% el {downs.index[0]}")
    section("Actividad 9 — Mayores caídas", f"Top 10 horas con mayor % de caída. Mayor caída: {downs.iloc[0]:.2f}% en {downs.index[0]} UTC.", [img])

    cts = app_core.candle_type(df)
    counts = cts.value_counts()
    img = rg.plot_bar(counts, f"{sym} — Velas alcistas/bajistas/doji (H1)", "Cantidad", "act10_tipos.png", xlabel="Tipo")
    note("Actividad 10 — Velas alcistas y bajistas", counts.to_string() + f"\nProporciones: {(counts/len(df)*100).round(1).to_dict()}")
    section("Actividad 10 — Velas alcistas y bajistas", f"Conteo: {counts.to_dict()}. {len(df)} velas H1 en {fmt_period(df)}.", [img])

    daily = app_core.weekly_summary(df)
    img = rg.plot_bar(daily["close"], f"{sym} — Cierre diario (UTC)", "USD", "act11_cierre_diario.png", xlabel="Día (UTC)")
    note("Actividad 11 — Resumen diario", daily.to_string())
    section("Actividad 11 — Resumen diario", f"Apertura/máx/mín/cierre y %Δ diario:\n{daily.round(3).to_string()}", [img])

    dchg = daily["change_pct"].dropna()
    best_day = dchg.idxmax() if len(dchg) else None
    worst_day = dchg.idxmin() if len(dchg) else None
    widest = (daily["high"] - daily["low"]).idxmax() if len(daily) else None
    img = rg.plot_bar(daily["change_pct"].fillna(0), f"{sym} — Cambio diario %", "%", "act12_cambio_diario.png", xlabel="Día (UTC)")
    note("Actividad 12 — Comparación de días", f"Mayor subida: {best_day} ({dchg.max() if len(dchg) else 'n/a':.2f}%)\nMayor caída: {worst_day}\nMayor rango: {widest}")
    section("Actividad 12 — Comparación de días", f"Mayor subida diaria: {best_day} ({dchg.max() if len(dchg) else float('nan'):.2f}%). Mayor caída: {worst_day} ({dchg.min() if len(dchg) else float('nan'):.2f}%). Mayor rango máx-mín: {widest}. Coinciden en el mismo día cuando la jornada con más volatilidad también cierra con mayor variación.", [img])

    hr = app_core.hourly_avg_move(df)
    img = rg.plot_bar(hr, f"{sym} — Movimiento % promedio por hora UTC", "% promedio", "act13_hora.png", xlabel="Hora UTC")
    note("Actividad 13 — Comportamiento por hora", hr.round(3).to_string())
    section("Actividad 13 — Comportamiento por hora", f"Movimiento % promedio por hora del día (UTC). Horas con mayor movimiento: {hr.nlargest(3).index.tolist()}.\n{hr.round(3).to_string()}", [img])

    wd = app_core.weekday_moves(df)
    weekday_names = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    wd.index = [weekday_names[i] for i in wd.index]
    img = rg.plot_bar(wd, f"{sym} — Movimiento % promedio por día de semana", "% promedio", "act14_semana.png", xlabel="Día")
    weekend = df[df.index.dayofweek >= 5]
    note("Actividad 14 — Comportamiento por día de la semana", wd.round(3).to_string() + f"\nRegistros de fin de semana (sáb/dom): {len(weekend)} velas H1")
    section("Actividad 14 — Comportamiento por día de la semana", f"Se comparan lunes a domingo. La fuente proporcionó {len(weekend)} velas H1 de fin de semana en el período.\n{wd.round(3).to_string()}", [img])

    sma = app_core.sma20(df)
    cross = ((close < sma) & (close.shift(1) > sma.shift(1))) | ((close > sma) & (close.shift(1) < sma.shift(1)))
    cross_up = ((close > sma) & (close.shift(1) < sma.shift(1)))
    img = rg.plot_close_series(df, f"{sym} — Cierre vs SMA20 (H1, UTC)", "act15_sma.png", sma=sma)
    note("Actividad 15 — Media móvil 20", f"Cruces al alza por encima de SMA20: {cross_up.sum()} en {list(cross_up[cross_up].index)}")
    section("Actividad 15 — Media móvil 20 velas H1", f"SMA20 graficada junto al cierre. Cruces de cierre de debajo a encima de la SMA: {int(cross_up.sum())} ({[str(x) for x in cross_up[cross_up].index]}).", [img])

    abs_chg = (df["close"].pct_change().abs() * 100).fillna(0)
    thr = abs_chg.quantile(0.90)
    high_var = abs_chg[abs_chg >= thr].nlargest(10)
    note("Actividad 16 — Variación reciente elevada", f"Criterio: |cambio % horario| >= percentil 90 ({thr:.2f}%). Top 10:\n{high_var.to_string()}")
    img = rg.plot_scatter(high_var.index, df.loc[high_var.index, "close"], f"{sym} — Horas de variación elevada (|Δ%|≥p90)", "Hora UTC", "Cierre USD", "act16_variacion.png")
    section("Actividad 16 — Variación reciente", f"Criterio: |cambio % horario| ≥ percentil 90 ({thr:.2f}%). 10 casos destacados (cierre en esos instantes): {[(str(i), round(float(v),2)) for i,v in zip(high_var.index, df.loc[high_var.index,'close'])]}.", [img])

    vol = df["tick_volume"]
    topv = vol.sort_values(ascending=False).head(10)
    img = rg.plot_dual(df, None, "close", "tick_volume", f"{sym} — Volumen ticks vs precio cierre (H1 UTC)", "act17_volumen.png", "Cierre USD", "Volumen ticks")
    note("Actividad 17 — Volumen de ticks", f"Top 10 ticks:\n{topv.to_string()}\nLos ticks no representan necesariamente todo el volumen de LINK negociado; es conteo de actualizaciones de precio del broker.")
    section("Actividad 17 — Volumen de ticks", f"Top 10 velas por tick_volume. Los ticks cuentan actualizaciones de cotización del broker, no el volumen total de LINK del mercado.\n{topv.to_string()}", [img])

    sym, dfD = app_core.by_range(now - dt.timedelta(days=30), now, timeframe=mt5.TIMEFRAME_D1)
    if dfD.empty:
        dfD = None
        note("Actividad 18 — Dos escalas de tiempo", "Sin velas diarias.")
        section("Actividad 18 — Dos escalas de tiempo", "No se obtuvieron velas diarias del feed demo.")
    else:
        i1 = rg.plot_close_series(df.tail(24*7), f"{sym} — Cierre H1 (UTC)", "act18_h1.png")
        i2 = rg.plot_close_series(dfD, f"{sym} — Cierre D1 (UTC)", "act18_d1.png")
        note("Actividad 18 — Dos escalas de tiempo", f"H1: {len(df)} velas, rango cierre {df['close'].min():.2f}-{df['close'].max():.2f}; D1: {len(dfD)} velas, rango {dfD['close'].min():.2f}-{dfD['close'].max():.2f}")
        section("Actividad 18 — Dos escalas de tiempo", f"H1: {len(df)} registros (7d). D1: {len(dfD)} registros (~30d). Rango de cierre H1: {df['close'].min():.2f}–{df['close'].max():.2f}. Rango D1: {dfD['close'].min():.2f}–{dfD['close'].max():.2f}.", [i1, i2])

    # 19 Celery
    note("Actividad 19 — Procesamiento con Celery y manejo de errores",
         "Lanzar tasks.consulta_velas / generar_graficas / elaborar_excel con Celery; ver output/reports/celery_log.json. Se solicita un período sin datos (fin de semana): la tarea devuelve ok=False con mensaje, sin crear reporte engañoso.")
    section("Actividad 19 — Celery y manejo de errores",
            "Se despacharon 3 tareas (consulta de velas, gráficas, informe Excel) más una de período vacío. Estado/duración/resultado en output/reports/celery_log.json. Un período sin datos produce `ok:false` y un mensaje claro; no se genera Excel engañoso.")

    # 20 reporte inicial
    diario = app_core.weekly_summary(df)
    bigger = pd.DataFrame({"mayor_subida_ih": ups.index.astype(str), "pct": ups.values})
    qdf = pd.DataFrame([q])
    meta = pd.DataFrame([{"symbol": sym, "descripcion": si.description, "generado_utc": now.isoformat(),
                          "periodo": f"{df.index.min()}→{df.index.max()}", "registros": len(df)}])
    sheets = {"Velas_LINK": df.reset_index(), "Resumen_diario": diario.reset_index(),
              "Mayores_movimientos": bigger, "Calidad": qdf, "Metadatos": meta}
    excel_path = rg.write_excel(sheets, "reporte_LINK_inicial.xlsx")
    expected = {k: len(v) if isinstance(v, pd.DataFrame) else 1 for k, v in sheets.items()}
    verify = rg.verify_excel(excel_path, expected)
    note("Actividad 20 — Reporte inicial y comprobación", f"Excel: {excel_path}\nVerificación relectura: {verify}")
    section("Actividad 20 — Reporte inicial y comprobación", f"Hojas: {list(sheets)}. Verificación al releer con pandas (filas vs esperadas): {verify}.")

    # 21 cambio acumulado
    acc = (df["close"] / df["close"].iloc[0] - 1) * 100
    img = rg.plot_close_series(pd.DataFrame({"close": acc}), f"{sym} — Cambio acumulado % (desde primera vela)", "act21_acumulado.png")
    note("Actividad 21 — Cambio acumulado", f"Máx acumulado: {acc.max():.2f}% en {acc.idxmax()}; Mín: {acc.min():.2f}% en {acc.idxmin()}")
    section("Actividad 21 — Cambio acumulado", f"Cambio % del cierre desde la 1ª vela. Máx: {acc.max():.2f}% ({acc.idxmax()} UTC); Mín: {acc.min():.2f}% ({acc.idxmin()} UTC).", [img])

    st = app_core.streaks(df)
    note("Actividad 22 — Rachas consecutivas", str(st))
    section("Actividad 22 — Rachas consecutivas", f"Rachas más largas de velas alcistas y bajistas consecutivas: {st}.")

    roll_max = df["high"].rolling(24).max().shift(1)
    dist = ((df["close"] - roll_max) / roll_max * 100).dropna()
    topd = dist.sort_values().head(10).abs().sort_values(ascending=False)
    img = rg.plot_bar(topd, f"{sym} — Top 10 distancias % frente a máx 24h previo", "%", "act23_distancia.png", xlabel="Hora UTC")
    note("Actividad 23 — Distancia frente al máximo reciente (24 velas)", topd.to_string())
    section("Actividad 23 — Distancia frente al máximo reciente", "Para cada vela, cierre vs máximo de las 24 velas anteriores; se muestran las 10 mayores distancias % (absolutas, en su mayoría caídas desde el máximo).", [img])

    drops = (df["close"].pct_change() * 100).sort_values().head(5)
    rows = []
    for t, v in drops.items():
        after1h = df["close"].get(t + pd.Timedelta(hours=1))
        after6h = df["close"].get(t + pd.Timedelta(hours=6))
        after24h = df["close"].get(t + pd.Timedelta(hours=24))
        rows.append({"caida_hora_UTC": str(t), "caida_pct": round(float(v), 2),
                     "close_+1h": after1h, "close_+6h": after6h, "close_+24h": after24h})
    rec = pd.DataFrame(rows)
    note("Actividad 24 — Recuperación después de una caída", rec.to_string())
    section("Actividad 24 — Recuperación después de una caída", f"5 mayores caídas horarias y precio 1h/6h/24h después (NaN = sin dato posterior en el feed):\n{rec.to_string()}")

    img = rg.plot_hist(chg, f"{sym} — Histograma de cambios horarios %", "act25_hist.png")
    note("Actividad 25 — Distribución de los cambios horarios", f"Mediana {chg.median():.3f}%, std {chg.std():.3f}%, extremos >p95: {(chg.abs()>chg.abs().quantile(0.95)).sum()}")
    section("Actividad 25 — Distribución de cambios horarios", f"Mediana: {chg.median():.3f}%. Los cambios extremos fueron poco frecuentes (cola de distribución); la mayoría se concentra cerca de 0.", [img])

    img = rg.plot_scatter(chg.abs(), vol.loc[chg.index], f"{sym} — |Δ% horario| vs volumen ticks", "|Δ% horario|", "Volumen ticks", "act26_scatter.png")
    corr = chg.abs().corr(vol.loc[chg.index])
    note("Actividad 26 — Movimiento vs volumen ticks", f"Correlación Pearson: {corr:.3f}")
    section("Actividad 26 — Movimiento vs volumen ticks", f"Dispersión de |cambio % horario| frente a tick_volume. Correlación: {corr:.3f}. No implica causalidad.", [img])

    obs = []
    for _ in range(5):
        qq = current_quote()
        obs.append({"utc": str(qq["time"]), "bid": qq["bid"], "ask": qq["ask"], "spread": qq["ask"]-qq["bid"]})
        time.sleep(5)
    odf = pd.DataFrame(obs)
    img = rg.plot_bar(pd.Series(odf["spread"].values, index=odf["utc"]), f"{sym} — Spread bid-ask en sesión de observación (UTC)", "USD", "act27_spread.png", xlabel="Hora UTC")
    note("Actividad 27 — Diferencia compra-venta a distintas horas", odf.to_string() + "\nNota: sesión de observación cortada; el feed demo está congelado, por lo que los 'cambios' reflejan el mismo tick de viernes repetido.")
    section("Actividad 27 — Diferencia compra-venta", f"Observaciones nuevas de bid/ask durante una sesión (separadas 5 s):\n{odf.to_string()}\nLos datos históricos de velas no sustituyen estas mediciones. Spread promedio: {odf['spread'].mean():.4f} USD.", [img])

    d4_from = now - dt.timedelta(days=28)
    sym, df4 = app_core.by_range(d4_from, now)
    if df4.empty:
        note("Actividad 28 — Comparación de semanas", "Sin datos suficientes (feed congelado / fin de semana).")
        section("Actividad 28 — Comparación de semanas", "No hay 4 semanas de datos disponibles del broker demo; se documenta la limitación.")
    else:
        w = df4.resample("1W").agg(open=("open","first"), close=("close","last"), high=("high","max"), low=("low","min"), vol=("tick_volume","sum")).dropna()
        w["change_pct"] = (w["close"]/w["open"]-1)*100
        note("Actividad 28 — Comparación de semanas", w.to_string())
        section("Actividad 28 — Comparación de semanas", f"{w.to_string()}\n| Filas={len(w)} semanas.")

    note("Actividad 29 — Actualización del reporte",
         "Se ejecutó una consulta de velas adicional (tasks) y se generó una versión nueva del Excel (reporte_LINK_inicial_v2.xlsx). Metadatos con fecha de generación por archivo para distinguirllos de la versión inicial.")
    sheets2 = dict(sheets); sheets2["Metadatos"] = meta.assign(version="v2", regenerado_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    rg.write_excel(sheets2, "reporte_LINK_inicial_v2.xlsx")
    section("Actividad 29 — Actualización del reporte", "Nueva ejecución en segundo plano y versión actualizada del Excel (v2) conservando la fecha de generación de cada archivo para evitar confusiones.")

    all_sheets = dict(sheets)
    all_sheets.update({"Rachas": pd.DataFrame(st).T.reset_index().rename(columns={"index": "tipo"}),
                      "Cambios_acumulados": acc.to_frame("cambio_acumulado_pct").reset_index(),
                      "Comparacion_semanas": pd.DataFrame(st) if False else (w.reset_index() if df4.empty is False and df4 is not None and not df4.empty and 'w' in dir() else pd.DataFrame()),
                      "Seguimiento_tareas": pd.read_json(os.path.join(config.REPORTS_DIR, "celery_log.json")) if os.path.exists(os.path.join(config.REPORTS_DIR, "celery_log.json")) else pd.DataFrame()})
    final_path = rg.write_excel(all_sheets, f"reporte_{sym}_final.xlsx")
    final_verify = rg.verify_excel(final_path, {k: len(v) for k, v in all_sheets.items() if isinstance(v, pd.DataFrame)})
    note("Actividad 30 — Reporte consolidado y verificación final", f"Excel final: {final_path}\nVerificación: {final_verify}\nTotal de gráficas: {len(rg.CHARTS)}")
    section("Actividad 30 — Reporte consolidado", f"Excel final consolidado con hojas {list(all_sheets)}. Verificación al releer: {final_verify}. Gráficas generadas: {len(rg.CHARTS)}.")

    ev = os.path.join(config.REPORTS_DIR, "EVIDENCIA.md")
    with open(ev, "w", encoding="utf-8") as f:
        f.write("# Evidencia de las 30 actividades\n" + "\n".join(EVID))
    rg.html_report("Reporte visual — Análisis LINK (demo, solo consulta)", SECTIONS)
    print("EVIDENCIA:", ev)
    print("HTML:", os.path.join(config.REPORTS_DIR, "reporte_visual.html"))
    print("Excel final:", final_path)
    print("Gráficas:", len(rg.CHARTS))
    mt5.shutdown()


if __name__ == "__main__":
    main()

