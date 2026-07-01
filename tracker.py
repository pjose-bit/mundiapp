"""
tracker.py
Guarda predicciones antes de cada partido y registra el resultado real.
Calcula qué casas de apuestas y fuentes de prensa aciertan más.
"""

import json
import os
from datetime import datetime
from config import BASE_DIR

TRACKER_FILE = os.path.join(BASE_DIR, "datos", "historial_predicciones.json")


# ── Helpers de persistencia ────────────────────────────────────────────────────

def _cargar() -> dict:
    os.makedirs(os.path.dirname(TRACKER_FILE), exist_ok=True)
    if os.path.isfile(TRACKER_FILE):
        with open(TRACKER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"partidos": []}


def _guardar(data: dict):
    os.makedirs(os.path.dirname(TRACKER_FILE), exist_ok=True)
    with open(TRACKER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _id_partido(local: str, visitante: str, fecha: str) -> str:
    return f"{local}_vs_{visitante}_{fecha}".replace(" ", "_")


# ── Guardar predicción antes del partido ──────────────────────────────────────

def guardar_prediccion(partido_apuestas: dict, partido_prensa: dict):
    """
    Llama ANTES del partido para guardar snapshot de predicciones.
    partido_apuestas: dict de analizar_cuotas()
    partido_prensa:   dict de analizar_prensa()
    """
    from scraper_apuestas import estimar_marcadores

    local    = partido_apuestas.get("local", "")
    visita   = partido_apuestas.get("visitante", "")
    fecha    = partido_apuestas.get("fecha", datetime.now().strftime("%Y-%m-%d"))
    pid      = _id_partido(local, visita, fecha)

    # Poisson top-3
    marcadores = estimar_marcadores(partido_apuestas)
    poisson_top = marcadores[0] if marcadores else {}

    # Favorito según apuestas (menor cuota = más probable)
    probs       = partido_apuestas.get("probabilidades", {})
    favorito_bk = max(probs, key=probs.get) if probs else None
    prob_fav_bk = probs.get(favorito_bk, 0) if favorito_bk else 0

    # Favorito según prensa
    puntos = (partido_prensa or {}).get("resumen_editorial", {}).get("puntos_clave", [])
    press_fav = None
    for p in puntos:
        if "Favorito de la prensa:" in p:
            press_fav = p.replace("Favorito de la prensa:", "").strip()
            break
    press_equilib = any("equilibrado" in p.lower() for p in puntos)

    # Bookmakers individuales
    bookmakers_pred = {}
    for fila in partido_apuestas.get("tabla_bookmakers", []):
        nombre = fila.get("Casa", "").replace("★", "").strip()
        c1 = fila.get(f"1 {local}")
        cx = fila.get("X Empate")
        c2 = fila.get(f"2 {visita}")
        if c1 and cx and c2:
            mejor = min([(c1, "local"), (cx, "empate"), (c2, "visita")], key=lambda x: x[0])
            bookmakers_pred[nombre] = {"favorito": mejor[1], "cuota": mejor[0]}

    data = _cargar()

    # Si ya existe snapshot, no sobreescribir
    for p in data["partidos"]:
        if p["id"] == pid:
            return

    # No guardar si el partido ya empezó (cuotas en vivo ≠ predicción pre-partido)
    already_started = bool(partido_apuestas.get("en_vivo"))
    if not already_started:
        commence_str = partido_apuestas.get("commence_time")
        if commence_str:
            try:
                from datetime import timezone
                ct = datetime.fromisoformat(commence_str.replace("Z", "+00:00"))
                already_started = ct <= datetime.now(timezone.utc)
            except Exception:
                pass

    if already_started:
        print(f"  [tracker] Partido ya iniciado, cuotas en vivo — no se guarda snapshot: {local} vs {visita}")
        return

    data["partidos"].append({
        "id":            pid,
        "local":         local,
        "visitante":     visita,
        "fecha":         fecha,
        "resultado_real": None,
        "prediccion_poisson": {
            "marcador":  poisson_top.get("marcador"),
            "prob":      poisson_top.get("prob"),
            "ganador":   poisson_top.get("resultado"),
        },
        "prediccion_apuestas": {
            "favorito":  favorito_bk,
            "prob":      round(prob_fav_bk, 1),
            "ganador":   _nombre_a_resultado(favorito_bk, local, visita),
        },
        "prediccion_prensa": {
            "favorito":   press_fav,
            "equilibrado": press_equilib,
            "ganador":    _nombre_a_resultado(press_fav, local, visita) if press_fav else None,
        },
        "bookmakers_pred": bookmakers_pred,
        "fuentes_prensa":  sorted({
            a.get("fuente", "") for a in (partido_prensa or {}).get("articulos", [])
            if a.get("es_destacada")
        }),
        "timestamp_pred": datetime.now().isoformat(),
    })
    _guardar(data)
    print(f"  [tracker] Predicción guardada: {local} vs {visita} ({fecha})")


# ── Registrar resultado real ───────────────────────────────────────────────────

def registrar_resultado(local: str, visitante: str, fecha: str,
                        goles_local: int, goles_visita: int):
    """Llama después del partido para guardar el resultado real."""
    pid  = _id_partido(local, visitante, fecha)
    data = _cargar()

    ganador = "local" if goles_local > goles_visita else \
              "visita" if goles_visita > goles_local else "empate"

    for p in data["partidos"]:
        if p["id"] == pid:
            p["resultado_real"] = {
                "goles_local":  goles_local,
                "goles_visita": goles_visita,
                "marcador":     f"{goles_local}-{goles_visita}",
                "ganador":      ganador,
            }
            p["timestamp_result"] = datetime.now().isoformat()
            _guardar(data)
            print(f"  [tracker] Resultado guardado: {local} {goles_local}-{goles_visita} {visitante}")
            return

    print(f"  [tracker] Partido no encontrado: {pid}. Guardando con resultado directo.")
    data["partidos"].append({
        "id": pid, "local": local, "visitante": visitante, "fecha": fecha,
        "resultado_real": {"goles_local": goles_local, "goles_visita": goles_visita,
                           "marcador": f"{goles_local}-{goles_visita}", "ganador": ganador},
        "prediccion_poisson": None, "prediccion_apuestas": None,
        "prediccion_prensa": None, "bookmakers_pred": {}, "fuentes_prensa": [],
        "timestamp_result": datetime.now().isoformat(),
    })
    _guardar(data)


# ── Calcular exactitud ─────────────────────────────────────────────────────────

def calcular_exactitud() -> dict:
    """
    Retorna dict con estadísticas de exactitud por fuente.
    Solo considera partidos con resultado_real registrado.
    """
    data = _cargar()
    completados = [p for p in data["partidos"] if p.get("resultado_real")]

    if not completados:
        return {"total": 0, "poisson": {}, "apuestas": {}, "prensa": {}, "bookmakers": {}}

    total = len(completados)

    def _acierto(pred_ganador, real_ganador):
        if pred_ganador is None:
            return None
        return pred_ganador == real_ganador

    # Poisson
    poisson_aciertos = [_acierto(p["prediccion_poisson"]["ganador"],
                                  p["resultado_real"]["ganador"])
                        for p in completados if p.get("prediccion_poisson")]
    poisson_aciertos = [a for a in poisson_aciertos if a is not None]

    # Apuestas (global)
    apuestas_aciertos = [_acierto(p["prediccion_apuestas"]["ganador"],
                                   p["resultado_real"]["ganador"])
                         for p in completados if p.get("prediccion_apuestas")]
    apuestas_aciertos = [a for a in apuestas_aciertos if a is not None]

    # Prensa
    prensa_aciertos = [_acierto(p["prediccion_prensa"]["ganador"],
                                 p["resultado_real"]["ganador"])
                       for p in completados if p.get("prediccion_prensa")]
    prensa_aciertos = [a for a in prensa_aciertos if a is not None]

    # Por casa de apuestas
    bk_stats = {}
    for p in completados:
        real = p["resultado_real"]["ganador"]
        for bk_nombre, bk_pred in (p.get("bookmakers_pred") or {}).items():
            if bk_nombre not in bk_stats:
                bk_stats[bk_nombre] = {"aciertos": 0, "total": 0}
            bk_stats[bk_nombre]["total"] += 1
            if bk_pred["favorito"] == real:
                bk_stats[bk_nombre]["aciertos"] += 1

    bk_resultado = {
        k: {"aciertos": v["aciertos"], "total": v["total"],
            "pct": round(v["aciertos"] / v["total"] * 100, 1)}
        for k, v in sorted(bk_stats.items(), key=lambda x: -x[1]["aciertos"] / max(x[1]["total"], 1))
    }

    def _pct(lista): return round(sum(lista) / len(lista) * 100, 1) if lista else None

    return {
        "total":      total,
        "partidos":   completados,
        "poisson":    {"aciertos": sum(poisson_aciertos),  "total": len(poisson_aciertos),  "pct": _pct(poisson_aciertos)},
        "apuestas":   {"aciertos": sum(apuestas_aciertos), "total": len(apuestas_aciertos), "pct": _pct(apuestas_aciertos)},
        "prensa":     {"aciertos": sum(prensa_aciertos),   "total": len(prensa_aciertos),   "pct": _pct(prensa_aciertos)},
        "bookmakers": bk_resultado,
    }


# ── Helper interno ─────────────────────────────────────────────────────────────

def _nombre_a_resultado(nombre: str, local: str, visita: str) -> str | None:
    if not nombre:
        return None
    n = nombre.lower()
    if n in local.lower() or local.lower() in n:
        return "local"
    if n in visita.lower() or visita.lower() in n:
        return "visita"
    return None


# ── CLI rápido ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 5:
        # python tracker.py "Mexico" "Ecuador" "2026-06-30" "2-0"
        loc, vis, fec, marc = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
        gl, gv = map(int, marc.split("-"))
        registrar_resultado(loc, vis, fec, gl, gv)
    stats = calcular_exactitud()
    print(f"\nPartidos analizados: {stats['total']}")
    print(f"Poisson:   {stats['poisson']}")
    print(f"Apuestas:  {stats['apuestas']}")
    print(f"Prensa:    {stats['prensa']}")
    print("\nCasas de apuestas:")
    for k, v in stats["bookmakers"].items():
        print(f"  {k}: {v['aciertos']}/{v['total']} ({v['pct']}%)")
