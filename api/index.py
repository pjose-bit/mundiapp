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
    """Devuelve estructura de prensa vacía para no depender del scraper en Vercel."""
    return {
        "partido": f"{local} vs {visitante}",
        "equipo1": local,
        "equipo2": visitante,
        "total_articulos": 0,
        "articulos": [],
    }


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

    prensa = _prensa_vacia(partido["local"], partido["visitante"])
    return construir_html(partido, prensa, todos)


@app.route("/")
def index():
    return Response(_generar_dashboard(), mimetype="text/html; charset=utf-8")


@app.route("/partido/<path:nombre>")
def partido(nombre):
    return Response(_generar_dashboard(nombre), mimetype="text/html; charset=utf-8")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
