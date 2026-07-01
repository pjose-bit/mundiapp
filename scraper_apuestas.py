"""
Módulo: scraper_apuestas.py
Obtiene cuotas de casas de apuestas para partidos del Mundial usando The Odds API.
Resalta los resultados más probables (cuota más baja).
"""

import requests
import pandas as pd
import os
import json
import time
from datetime import datetime, date
from config import (ODDS_API_KEY, SPORT_KEY, ODDS_REGIONS,
                    ODDS_MARKETS, ODDS_FORMAT, DATOS_DIR,
                    BOOKMAKERS_PREFERIDOS)

# Lee límites del config (con defaults por si config viejo no los tiene)
try:
    from config import CACHE_TTL_MINUTOS, MAX_CONSULTAS_DIA
except ImportError:
    CACHE_TTL_MINUTOS = 30
    MAX_CONSULTAS_DIA = 15

API_BASE = "https://api.the-odds-api.com/v4"

# ── Caché en memoria (persiste mientras el proceso está vivo) ─────────────────
_MEM_CACHE = {}          # key → {"data": ..., "ts": float}

# Uso de API — se actualiza con cada llamada
_api_uso = {"usadas": None, "restantes": None}


def _dir_cache() -> str:
    """Directorio escribible para caché: datos/ localmente, /tmp en Vercel."""
    if os.path.isdir(DATOS_DIR):
        return DATOS_DIR
    tmp = "/tmp/mundiapp"
    os.makedirs(tmp, exist_ok=True)
    return tmp


def _leer_cache(key: str, ttl: float):
    """Devuelve datos en caché si son frescos, o None si vencieron."""
    # 1. Memoria (más rápido)
    entry = _MEM_CACHE.get(key)
    if entry and (time.time() - entry["ts"]) < ttl:
        return entry["data"]

    # 2. Disco
    try:
        ruta = os.path.join(_dir_cache(), f"cache_{key}.json")
        if os.path.isfile(ruta):
            with open(ruta, "r", encoding="utf-8") as f:
                entry = json.load(f)
            if (time.time() - entry["ts"]) < ttl:
                _MEM_CACHE[key] = entry   # promover a memoria
                return entry["data"]
    except Exception:
        pass
    return None


def _guardar_cache(key: str, data):
    """Guarda datos en memoria y disco."""
    entry = {"data": data, "ts": time.time()}
    _MEM_CACHE[key] = entry
    try:
        ruta = os.path.join(_dir_cache(), f"cache_{key}.json")
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False)
    except Exception:
        pass


def _leer_cache_cualquier_edad(key: str):
    """Devuelve el último valor en caché sin importar cuándo fue guardado."""
    if key in _MEM_CACHE:
        return _MEM_CACHE[key]["data"]
    try:
        ruta = os.path.join(_dir_cache(), f"cache_{key}.json")
        if os.path.isfile(ruta):
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)["data"]
    except Exception:
        pass
    return None


# ── Contador diario ────────────────────────────────────────────────────────────

def _consultas_hoy() -> int:
    try:
        ruta = os.path.join(_dir_cache(), "api_diario.json")
        if os.path.isfile(ruta):
            with open(ruta, "r") as f:
                d = json.load(f)
            if d.get("fecha") == str(date.today()):
                return d.get("consultas", 0)
    except Exception:
        pass
    return 0


def _incrementar_consultas():
    try:
        hoy = str(date.today())
        consultas = _consultas_hoy() + 1
        ruta = os.path.join(_dir_cache(), "api_diario.json")
        with open(ruta, "w") as f:
            json.dump({"fecha": hoy, "consultas": consultas}, f)
    except Exception:
        pass


# ── Helpers de uso ─────────────────────────────────────────────────────────────

def _registrar_uso(resp):
    """Lee los headers de cuota y guarda los valores globalmente."""
    try:
        usadas    = resp.headers.get("x-requests-used")
        restantes = resp.headers.get("x-requests-remaining")
        if usadas is not None:
            _api_uso["usadas"]    = int(usadas)
            _api_uso["restantes"] = int(restantes) if restantes else None
    except Exception:
        pass


def get_api_uso() -> dict:
    """Retorna dict con usadas/restantes de la API este mes."""
    return _api_uso.copy()


# ── Funciones de acceso a la API ───────────────────────────────────────────────

def obtener_partidos_disponibles():
    """Retorna la lista de partidos del Mundial con cuotas disponibles."""
    if not ODDS_API_KEY:
        print("  [!] Falta ODDS_API_KEY en config.py")
        return []

    ttl = CACHE_TTL_MINUTOS * 60

    # 1. Usar caché si está fresca
    cached = _leer_cache("partidos", ttl)
    if cached is not None:
        print(f"  [cache] Cuotas en caché (válida {CACHE_TTL_MINUTOS} min). Sin nueva consulta.")
        return cached

    # 2. Verificar límite diario
    consultas = _consultas_hoy()
    if consultas >= MAX_CONSULTAS_DIA:
        print(f"  [limite] Límite diario de {MAX_CONSULTAS_DIA} consultas alcanzado.")
        print("  [limite] Usando datos anteriores en caché.")
        viejo = _leer_cache_cualquier_edad("partidos")
        return viejo if viejo is not None else []

    # 3. Llamar a la API
    url = f"{API_BASE}/sports/{SPORT_KEY}/odds/"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": ODDS_REGIONS,
        "markets": ODDS_MARKETS,
        "oddsFormat": ODDS_FORMAT,
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    _registrar_uso(resp)
    _incrementar_consultas()
    datos = resp.json()
    _guardar_cache("partidos", datos)
    print(f"  [api] Cuotas actualizadas. Consultas hoy: {consultas + 1}/{MAX_CONSULTAS_DIA}")
    return datos


def analizar_cuotas(partido: dict) -> dict:
    """
    Dado un objeto de partido de la API, calcula:
    - Promedio de cuotas para 1 / X / 2
    - Probabilidad implícita de cada resultado
    - Resultado más probable (cuota mínima)
    """
    local    = partido["home_team"]
    visitante = partido["away_team"]
    fecha    = partido["commence_time"][:10]

    cuotas_1, cuotas_x, cuotas_2 = [], [], []
    filas = []

    for bk in partido.get("bookmakers", []):
        nombre = bk["key"]
        for market in bk.get("markets", []):
            if market["key"] != "h2h":
                continue
            odds = {o["name"]: o["price"] for o in market["outcomes"]}
            c1 = odds.get(local)
            cx = odds.get("Draw")
            c2 = odds.get(visitante)
            if c1 and cx and c2:
                cuotas_1.append(c1)
                cuotas_x.append(cx)
                cuotas_2.append(c2)
                preferido = "★" if nombre in BOOKMAKERS_PREFERIDOS else ""
                filas.append({
                    "Casa": nombre + preferido,
                    f"1 {local}": c1,
                    "X Empate": cx,
                    f"2 {visitante}": c2,
                })

    if not filas:
        return {"partido": f"{local} vs {visitante}", "fecha": fecha, "datos": None}

    prom_1 = round(sum(cuotas_1) / len(cuotas_1), 2)
    prom_x = round(sum(cuotas_x) / len(cuotas_x), 2)
    prom_2 = round(sum(cuotas_2) / len(cuotas_2), 2)

    # Probabilidad implícita = 1 / cuota
    prob_1 = round(1 / prom_1 * 100, 1)
    prob_x = round(1 / prom_x * 100, 1)
    prob_2 = round(1 / prom_2 * 100, 1)

    resultados = {local: prom_1, "Empate": prom_x, visitante: prom_2}
    mas_probable = min(resultados, key=resultados.get)

    return {
        "partido": f"{local} vs {visitante}",
        "local": local,
        "visitante": visitante,
        "fecha": fecha,
        "tabla_bookmakers": filas,
        "promedios": {"1": prom_1, "X": prom_x, "2": prom_2},
        "probabilidades": {local: prob_1, "Empate": prob_x, visitante: prob_2},
        "mas_probable": mas_probable,
        "cuota_mas_probable": resultados[mas_probable],
    }


def guardar_csv(resultado: dict):
    """Guarda la tabla de cuotas en un CSV dentro de /datos."""
    if resultado.get("datos") is None and not resultado.get("tabla_bookmakers"):
        return
    nombre = resultado["partido"].replace(" ", "_").replace("/", "-")
    ruta = os.path.join(DATOS_DIR, f"cuotas_{nombre}_{resultado['fecha']}.csv")
    df = pd.DataFrame(resultado["tabla_bookmakers"])
    df.to_csv(ruta, index=False, encoding="utf-8-sig")
    print(f"  [✓] CSV guardado: {ruta}")


def buscar_partido(equipo1: str, equipo2: str) -> dict | None:
    """Busca un partido específico por nombre de equipos (búsqueda flexible)."""
    partidos = obtener_partidos_disponibles()
    e1 = equipo1.lower()
    e2 = equipo2.lower()
    for p in partidos:
        h = p["home_team"].lower()
        a = p["away_team"].lower()
        if (e1 in h or e1 in a) and (e2 in h or e2 in a):
            return analizar_cuotas(p)
    return None


def listar_partidos():
    """Imprime todos los partidos disponibles con sus cuotas resumidas."""
    partidos = obtener_partidos_disponibles()
    if not partidos:
        print("No hay partidos disponibles o falta API key.")
        return

    print(f"\n{'='*60}")
    print(f"  PARTIDOS DISPONIBLES ({len(partidos)} encontrados)")
    print(f"{'='*60}")
    for p in partidos:
        r = analizar_cuotas(p)
        if not r.get("tabla_bookmakers"):
            continue
        pr = r["promedios"]
        print(f"\n  {r['partido']}  [{r['fecha']}]")
        print(f"    Cuotas promedio → 1:{pr['1']}  X:{pr['X']}  2:{pr['2']}")
        print(f"    Más probable    → {r['mas_probable']} (cuota {r['cuota_mas_probable']})")


def obtener_en_vivo() -> set:
    """Retorna set de IDs de partidos actualmente en vivo (con caché)."""
    if not ODDS_API_KEY:
        return set()

    ttl = CACHE_TTL_MINUTOS * 60
    cached = _leer_cache("en_vivo", ttl)
    if cached is not None:
        return set(cached)

    consultas = _consultas_hoy()
    if consultas >= MAX_CONSULTAS_DIA:
        viejo = _leer_cache_cualquier_edad("en_vivo")
        return set(viejo) if viejo else set()

    try:
        url = f"{API_BASE}/sports/{SPORT_KEY}/scores/"
        params = {"apiKey": ODDS_API_KEY, "daysFrom": 1}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            _registrar_uso(resp)
            _incrementar_consultas()
            ids_vivo = [
                p["id"] for p in resp.json()
                if not p.get("completed") and p.get("scores")
            ]
            _guardar_cache("en_vivo", ids_vivo)
            return set(ids_vivo)
    except Exception:
        pass
    return set()


def obtener_partidos_con_estado() -> list:
    """Retorna partidos con campo 'en_vivo' incluido."""
    partidos_raw = obtener_partidos_disponibles()
    en_vivo_ids  = obtener_en_vivo()
    resultado = []
    for p in partidos_raw:
        analizado = analizar_cuotas(p)
        if analizado.get("tabla_bookmakers"):
            analizado["en_vivo"] = p.get("id", "") in en_vivo_ids
            analizado["id"]      = p.get("id", "")
            resultado.append(analizado)
    # Ordenar: en vivo primero
    resultado.sort(key=lambda x: (not x["en_vivo"], x["fecha"]))
    return resultado


# ── Marcador exacto via distribución de Poisson ──────────────────────────────

import math

def _poisson(lam: float, k: int) -> float:
    return (math.exp(-lam) * (lam ** k)) / math.factorial(k)


def estimar_marcadores(partido_apuestas: dict, max_goles: int = 5) -> list:
    """
    Estima probabilidades de marcadores exactos usando distribución de Poisson.
    Calibra los goles esperados de cada equipo a partir de las cuotas 1X2.
    """
    pb     = partido_apuestas.get("probabilidades", {})
    local  = partido_apuestas["local"]
    visita = partido_apuestas["visitante"]

    ph = max(pb.get(local,  33) / 100, 0.01)
    pa = max(pb.get(visita, 33) / 100, 0.01)

    # Promedio histórico de goles por partido en Mundiales (fase de grupos ≈ 2.6, KO ≈ 2.2)
    total_goles = 2.4
    ratio       = math.sqrt(ph / pa)
    lambda_h    = total_goles * ratio / (1 + ratio)
    lambda_a    = total_goles          / (1 + ratio)

    scores = []
    for g_h in range(max_goles + 1):
        for g_a in range(max_goles + 1):
            prob = _poisson(lambda_h, g_h) * _poisson(lambda_a, g_a) * 100
            if prob >= 0.4:
                if   g_h > g_a: resultado = "local"
                elif g_h == g_a: resultado = "empate"
                else:            resultado = "visita"
                scores.append({
                    "marcador":     f"{g_h}-{g_a}",
                    "goles_local":  g_h,
                    "goles_visita": g_a,
                    "prob":         round(prob, 1),
                    "resultado":    resultado,
                })

    scores.sort(key=lambda x: x["prob"], reverse=True)
    return scores[:15]


if __name__ == "__main__":
    listar_partidos()
