"""Tareas Celery de consulta/análisis (sin trading)."""
import datetime as dt
import json

import MetaTrader5 as mt5
import pandas as pd
from celery import Celery

import config
import app_core
import report_gen

celery_app = Celery("link_tasks", broker="redis://127.0.0.1:6379/0", backend="redis://127.0.0.1:6379/1")
celery_app.conf.update(task_track_started=True)


@celery_app.task(bind=True, name="tasks.consulta_velas")
def consulta_velas(self, date_from_iso=None, date_to_iso=None):
    self.update_state(state="PROGRESS", meta={"msg": "descargando velas"})
    app_core.connect_demo()
    symbol = app_core.mt5_client.find_bitcoin()
    now = dt.datetime.now(dt.timezone.utc)
    date_to = dt.datetime.fromisoformat(date_to_iso) if date_to_iso else now
    date_from = dt.datetime.fromisoformat(date_from_iso) if date_from_iso else now - dt.timedelta(days=7)
    symbol, df = app_core.by_range(date_from, date_to)
    if df.empty:
        return {"ok": False, "symbol": symbol, "periodo": [str(date_from), str(date_to)],
                "mensaje": "Sin datos para el período solicitado: terminal sin mercado (fin de semana/feed congelado) o símbolo sin historial."}
    return {"ok": True, "symbol": symbol, "registros": int(len(df)),
            "periodo_real": [str(df.index.min()), str(df.index.max())]}


@celery_app.task(bind=True, name="tasks.generar_graficas")
def generar_graficas(self):
    symbol_info = None
    app_core.connect_demo()
    symbol, df = app_core.last_closed(100)
    if df.empty:
        return {"ok": False, "mensaje": "No hay velas cerradas disponibles; no se generan gráficas."}
    paths = [report_gen.plot_close_series(
        df, f"{symbol} - Cierre H1 (últimas {len(df)} velas, UTC)", f"{symbol.lower()}_cierre_h1.png")]
    return {"ok": True, "symbol": symbol, "graficas": paths}


@celery_app.task(bind=True, name="tasks.elaborar_excel")
def elaborar_excel(self):
    app_core.connect_demo()
    symbol, df = app_core.last_closed(100)
    if df.empty:
        return {"ok": False, "mensaje": "No se elaboró reporte: sin datos de velas."}
    diario = app_core.weekly_summary(df)
    sheets = {
        f"Velas_{symbol.lower()}": df.reset_index(),
        "Resumen_diario": diario.reset_index(),
        "Calidad": pd.DataFrame([app_core.quality_report(df)]),
        "Metadatos": pd.DataFrame([{"symbol": symbol, "generado_utc": dt.datetime.now(dt.timezone.utc).isoformat()}]),
    }
    path = report_gen.write_excel(sheets, f"reporte_{symbol.lower()}.xlsx")
    return {"ok": True, "excel": path, "hojas": list(sheets)}


