import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Activo objetivo actual del proyecto (se corrió BTC, luego LINK/Interlink)
SYMBOL = "DOGUSD"
SYMBOL_CANDIDATES = [SYMBOL]

OUTPUT_DIR = BASE_DIR  # BASE_DIR ya apunta a DOGUSD (src está dentro de DOGUSD)
CHARTS_DIR = os.path.join(OUTPUT_DIR, "charts")
REPORTS_DIR = os.path.join(OUTPUT_DIR, "reports")

for _d in (OUTPUT_DIR, CHARTS_DIR, REPORTS_DIR):
    os.makedirs(_d, exist_ok=True)

SERVER_UTC_OFFSET_HOURS = None
