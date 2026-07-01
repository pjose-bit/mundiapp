"""
api/index.py — Flask app para Vercel.
Sirve el dashboard con datos en tiempo real.
Las noticias se omiten en Vercel para evitar timeouts; se muestra enlace a Google News.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, Response, abort

app = Flask(__name__)


def _prensa_vacia(local: str, visitante: str) -> dict:
    return {
        "partido": f"{local} vs {visitante}",
        "equipo1": local,
        "equipo2": visitante,
        "total_articulos": 0,
        "articulos": [],
    }


def _todas_prensas_con_timeout(todos: list, timeout: int = 24) -> dict:
    """Busca noticias para todos los partidos en paralelo con timeout global."""
    import concurrent.futures
    from scraper_prensa import analizar_prensa_todos
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(analizar_prensa_todos, todos, 4)
        try:
            return future.result(timeout=timeout)
        except Exception:
            return {}


def _generar_dashboard(nombre_partido: str = None) -> str:
    from scraper_apuestas import obtener_partidos_con_estado
    from generar_reporte import construir_html

    todos = obtener_partidos_con_estado()
    if not todos:
        abort(503, "No hay partidos disponibles. Verifica la API key.")

    partido = todos[0]
    if nombre_partido:
        slug = nombre_partido.lower()
        for p in todos:
            if p["partido"].lower().replace(" ", "-").replace("&", "and") == slug:
                partido = p
                break

    todas_prensas = _todas_prensas_con_timeout(todos)
    prensa = todas_prensas.get(partido["partido"]) or _prensa_vacia(partido["local"], partido["visitante"])

    # Guardar predicciones automáticamente para tracking futuro
    try:
        from tracker import guardar_prediccion
        for p in todos:
            pr = todas_prensas.get(p["partido"]) or _prensa_vacia(p["local"], p["visitante"])
            guardar_prediccion(p, pr)
    except Exception:
        pass

    return construir_html(partido, prensa, todos, todas_prensas=todas_prensas)


@app.route("/")
def index():
    return Response(_generar_dashboard(), mimetype="text/html; charset=utf-8")


@app.route("/partido/<path:nombre>")
def partido(nombre):
    return Response(_generar_dashboard(nombre), mimetype="text/html; charset=utf-8")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
