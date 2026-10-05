"""Demo Celery: envía tareas y registra id/estado/duración/resultado."""
import json
import os
import time

import tasks
import config

log = []
if __name__ == "__main__":
    casos = [
        ("consulta_velas_7d", lambda: tasks.consulta_velas.delay()),
        ("consulta_velas_sin_datos", lambda: tasks.consulta_velas.delay("2025-01-01T00:00:00+00:00", "2025-01-02T00:00:00+00:00")),
        ("generar_graficas", lambda: tasks.generar_graficas.delay()),
        ("elaborar_excel", lambda: tasks.elaborar_excel.delay()),
    ]
    for nombre, fn in casos:
        t0 = time.time()
        res = fn()
        while res.state == "PENDING":
            time.sleep(0.5)
        dur = time.time() - t0
        try:
            resultado = res.get(timeout=120)
        except Exception as e:
            resultado = {"error": str(e)}
        log.append({"tarea": nombre, "id": res.id, "estado": res.state,
                    "duracion_s": round(dur, 2), "resultado": resultado})
        print(nombre, res.state, round(dur, 2), "s ->", resultado)
    p = os.path.join(config.REPORTS_DIR, "celery_log.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    print("Log:", p)
