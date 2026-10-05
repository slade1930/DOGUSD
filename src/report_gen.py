"""Generación de gráficas, Excel y reporte visual (solo análisis)."""
import os
import datetime as dt

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import config

CHARTS = []


def _save(fig, name):
    path = os.path.join(config.CHARTS_DIR, name)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    CHARTS.append(path)
    return path


def plot_close_series(df, title, filename, sma=None, maxima=None, minima=None):
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(df.index, df["close"], label="Cierre", color="steelblue")
    if sma is not None:
        ax.plot(df.index, sma, label="SMA 20", color="orange")
    if maxima is not None:
        ax.scatter([maxima[0]], [maxima[1]], color="green", zorder=5, label=f"Máx {maxima[1]:.2f}")
    if minima is not None:
        ax.scatter([minima[0]], [minima[1]], color="red", zorder=5, label=f"Mín {minima[1]:.2f}")
    ax.set_title(title)
    ax.set_xlabel("Fecha/hora (UTC)")
    ax.set_ylabel("USD por BTC")
    ax.legend(); ax.grid(True, alpha=0.3)
    return _save(fig, filename)


def plot_bar(series, title, ylabel, filename, xlabel="Período"):
    fig, ax = plt.subplots(figsize=(11, 5))
    series.plot(kind="bar", ax=ax, color="steelblue")
    ax.set_title(title); ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.grid(True, axis="y", alpha=0.3)
    return _save(fig, filename)


def plot_scatter(x, y, title, xlabel, ylabel, filename):
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.scatter(x, y, alpha=0.6)
    ax.set_title(title); ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    return _save(fig, filename)


def plot_dual(df, x_col, y1, y2, title, filename, y1label, y2label):
    fig, ax1 = plt.subplots(figsize=(11, 5))
    ax1.plot(df.index if x_col is None else df[x_col], df[y1], color="steelblue", label=y1label)
    ax1.set_ylabel(y1label, color="steelblue")
    ax2 = ax1.twinx()
    ax2.plot(df.index if x_col is None else df[x_col], df[y2], color="darkorange", label=y2label)
    ax2.set_ylabel(y2label, color="darkorange")
    ax1.set_title(title); ax1.set_xlabel("Fecha/hora (UTC)")
    return _save(fig, filename)


def plot_hist(series, title, filename, median_line=True):
    fig, ax = plt.subplots(figsize=(9, 5))
    series.hist(bins=20, ax=ax, color="steelblue", edgecolor="white")
    if median_line:
        ax.axvline(series.median(), color="red", linestyle="--", label=f"Mediana {series.median():.3f}%")
        ax.legend()
    ax.set_title(title); ax.set_xlabel("Cambio %"); ax.set_ylabel("Frecuencia")
    return _save(fig, filename)


def write_excel(sheets: dict, filename):
    path = os.path.join(config.REPORTS_DIR, filename)
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        for name, df in sheets.items():
            if isinstance(df, pd.DataFrame):
                df2 = df.copy()
                for c in df2.columns:
                    if pd.api.types.is_datetime64_any_dtype(df2[c]):
                        try:
                            df2[c] = df2[c].dt.tz_convert(None) if getattr(df2[c].dt, "tz", None) else df2[c]
                        except Exception:
                            pass
                        if getattr(df2[c].dt, "tz", None) is not None:
                            df2[c] = df2[c].dt.tz_localize(None)
                    if df2[c].dtype == object:
                        df2[c] = df2[c].astype(str)
                if isinstance(df2.index, pd.DatetimeIndex):
                    df2.index = df2.index.tz_convert(None) if df2.index.tz else df2.index
                df2.to_excel(w, sheet_name=name)
            else:
                pd.DataFrame([df]).to_excel(w, sheet_name=name, index=False)
    return path


def verify_excel(path, expected: dict):
    """Lee el Excel y comprueba hojas y cantidades de registros."""
    with pd.ExcelFile(path, engine="openpyxl") as x:
        result = {}
        for sheet in x.sheet_names:
            df = pd.read_excel(x, sheet_name=sheet)
            exp = expected.get(sheet)
            result[sheet] = {"rows": len(df), "expected": exp, "ok": (exp is None or len(df) == exp)}
        extra = set(x.sheet_names) - set(expected)
        missing = set(expected) - set(x.sheet_names)
        result["_extra_sheets"] = sorted(extra)
        result["_missing_sheets"] = sorted(missing)
        return result


def html_report(title, sections):
    """sections: lista de (heading, text, [imgs])"""
    css = """
    <style>
      :root { --bg:#0f172a; --card:#ffffff; --accent:#2563eb; --accent2:#16a34a; --text:#1e293b; --muted:#64748b; }
      * { box-sizing:border-box; }
      body { margin:0; background:linear-gradient(135deg,#e0e7ff 0%,#f8fafc 40%,#ecfeff 100%); font-family:'Segoe UI',Roboto,Arial,sans-serif; color:var(--text); }
      .wrap { max-width:1100px; margin:0 auto; padding:32px 20px 64px; }
      header { background:linear-gradient(90deg,#1e3a8a,#2563eb); color:white; padding:28px 32px; border-radius:16px; box-shadow:0 10px 24px rgba(37,99,235,.25); margin-bottom:28px; }
      header h1 { margin:0 0 6px; font-size:1.8rem; }
      header p { margin:0; opacity:.85; }
      .card { background:var(--card); border-radius:14px; padding:22px 26px; margin:0 0 22px; box-shadow:0 4px 14px rgba(15,23,42,.08); border:1px solid #e2e8f0; }
      .card h2 { margin-top:0; color:var(--accent); border-bottom:2px solid #e0e7ff; padding-bottom:8px; }
      .card p { line-height:1.55; }
      .card img { width:100%; max-width:900px; border:1px solid #e2e8f0; border-radius:10px; margin:12px 0 4px; box-shadow:0 4px 10px rgba(0,0,0,.06); }
      table { border-collapse:collapse; width:100%; margin:10px 0; font-size:.9rem; }
      th,td { border:1px solid #e2e8f0; padding:8px 10px; text-align:left; }
      th { background:#eff6ff; }
      .badge { display:inline-block; background:#dcfce7; color:#166534; padding:2px 10px; border-radius:999px; font-size:.75rem; font-weight:600; }
      footer { text-align:center; color:var(--muted); margin-top:40px; font-size:.85rem; }
    </style>
    """
    parts = [f"<html><head><meta charset='utf-8'><title>{title}</title>{css}</head><body><div class='wrap'>",
             f"<header><h1>{title}</h1>", f"<p>Generado: {dt.datetime.now(dt.timezone.utc).isoformat()} UTC</p></header>"]
    for heading, text, imgs in sections:
        parts.append("<div class='card'>")
        parts.append(f"<h2>{heading}</h2>")
        for line in text.split("\n"):
            parts.append(f"<p>{line}</p>")
        for img in imgs:
            rel = os.path.relpath(img, config.REPORTS_DIR).replace("\\", "/")
            parts.append(f"<img src='{rel}' width='900'><br>")
        parts.append("</div>")
    parts.append("<footer>Informe de consulta y análisis · MetaTrader5 · pandas · Celery · Matplotlib. Proyecto de solo lectura — sin compras ni ventas.</footer>")
    parts.append("</div></body></html>")
    path = os.path.join(config.REPORTS_DIR, "reporte_visual.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    return path
