"""
Módulo: scraper_prensa.py
Busca predicciones y noticias de prensa deportiva sobre un partido del Mundial.
Usa feeds RSS de Google News (sin API key requerida).
"""

import feedparser
import requests
from bs4 import BeautifulSoup
import os
import unicodedata
from datetime import datetime
from config import NEWS_LANG, NEWS_COUNTRY, MAX_ARTICULOS, DATOS_DIR


def _sin_acentos(texto: str) -> str:
    """Elimina acentos para comparación robusta: México → mexico, etc."""
    return unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf-8').lower()


GOOGLE_NEWS_RSS = (
    "https://news.google.com/rss/search"
    "?q={query}&hl={lang}&gl={country}&ceid={country}:{lang}"
)

# Nombres alternativos en español para búsqueda en artículos
NOMBRES_ES = {
    "england": "inglaterra",
    "germany": "alemania",
    "france": "francia",
    "netherlands": "países bajos",
    "holland": "holanda",
    "switzerland": "suiza",
    "united states": "estados unidos",
    "usa": "estados unidos",
    "south korea": "corea del sur",
    "morocco": "marruecos",
    "ivory coast": "costa de marfil",
    "sweden": "suecia",
    "denmark": "dinamarca",
    "croatia": "croacia",
    "poland": "polonia",
    "portugal": "portugal",
    "spain": "españa",
    "brazil": "brasil",
    "japan": "japón",
    "cameroon": "camerún",
    "norway": "noruega",
    "austria": "austria",
    "serbia": "serbia",
    "tunisia": "túnez",
    "new zealand": "nueva zelanda",
    "saudi arabia": "arabia saudita",
    "czech republic": "república checa",
    "mali": "malí",
}

TERMINOS_BUSQUEDA = [
    "{e1} vs {e2} prediccion mundial 2026",
    "{e1} {e2} previa partido",
    "{e1} lesionados mundial 2026",
    "{e2} lesionados mundial 2026",
    "{e1} {e2} pronostico",
    # Medios especializados
    "{e1} {e2} site:marca.com",
    "{e1} {e2} site:as.com",
    "{e1} vs {e2} world cup site:espn.com",
    "{e1} vs {e2} world cup prediction site:si.com",
    "{e1} vs {e2} site:fifa.com",
    # Predicciones de inteligencia artificial
    "{e1} {e2} prediccion inteligencia artificial mundial 2026",
]

FUENTES_DESTACADAS = {"marca", "as", "espn", "sports illustrated", "si", "fifa", "diario as"}


def _buscar_rss(query: str, max_items: int = MAX_ARTICULOS) -> list[dict]:
    """Obtiene artículos de Google News RSS para una búsqueda dada."""
    url = GOOGLE_NEWS_RSS.format(
        query=requests.utils.quote(query),
        lang=NEWS_LANG,
        country=NEWS_COUNTRY,
    )
    feed = feedparser.parse(url)
    articulos = []
    for entry in feed.entries[:max_items]:
        articulos.append({
            "titulo": entry.get("title", "Sin título"),
            "fuente": entry.get("source", {}).get("title", "Desconocida"),
            "fecha": entry.get("published", "")[:16],
            "link": entry.get("link", ""),
            "resumen": _limpiar_html(entry.get("summary", "")),
        })
    return articulos


def _limpiar_html(texto: str) -> str:
    """Elimina etiquetas HTML de un texto."""
    return BeautifulSoup(texto, "lxml").get_text(separator=" ").strip()


def _intentar_leer_articulo(url: str) -> str:
    """Intenta obtener el texto principal de un artículo (best-effort)."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; WorldCupBot/1.0)"}
        resp = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(resp.text, "lxml")
        # Eliminar scripts y estilos
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        parrafos = soup.find_all("p")
        texto = " ".join(p.get_text() for p in parrafos[:10])
        return texto[:1200] if texto else ""
    except Exception:
        return ""


def generar_resumen_prensa(articulos: list, equipo1: str, equipo2: str) -> dict:
    """
    Analiza artículos de prensa y genera un resumen estructurado
    enfocado en ayudar a predecir el marcador exacto.
    Devuelve dict con: texto (resumen HTML), puntos_clave, fuentes_unicas.
    """
    if not articulos:
        return {"texto": "", "puntos_clave": [], "fuentes_unicas": []}

    e1 = _sin_acentos(equipo1)
    e2 = _sin_acentos(equipo2)
    # También buscar por nombre en español si el equipo se ingresó en inglés
    e1_alt = _sin_acentos(NOMBRES_ES.get(equipo1.lower(), equipo1))
    e2_alt = _sin_acentos(NOMBRES_ES.get(equipo2.lower(), equipo2))

    KW_FAVORITO = ["favorit", "ganador", "ganar", "victoria", "vencer", "impon", "adelanta", "candidat", "mejor forma"]
    KW_LESION   = ["lesion", "baja", "ausenci", "no estará", "fuera del", "duda", "recuper", "sin jugar"]
    KW_GOLES    = ["gol", "marcador", "tanto", "ataque", "ofensiv", "anotad", "score", "portería", "defensa"]
    KW_FORMA    = ["forma", "racha", "invict", "consecutiv", "último", "recient", "sin perder"]
    KW_IA       = ["inteligencia artificial", "ia predice", "modelo predictivo", "ai prediction",
                   "machine learning", "estadística predice", "datos predicen", "modelo estadístico",
                   "análisis predictivo", "algoritmo predice", "ai predicts"]

    conteo = {"e1_fav": 0, "e2_fav": 0, "gen_fav": 0}
    lesion_snippets, gol_snippets, forma_snippets, ia_snippets = [], [], [], []
    todas_fuentes = set()

    for a in articulos:
        fuente = a.get("fuente", "")
        if fuente:
            todas_fuentes.add(fuente)

        titulo  = _sin_acentos(a.get("titulo", ""))
        snippet = _sin_acentos(a.get("resumen", ""))
        texto   = titulo + " " + snippet
        orig    = a.get("resumen", "") or a.get("titulo", "")

        menciona_e1 = e1 in texto or e1_alt in texto
        menciona_e2 = e2 in texto or e2_alt in texto

        # Favorito: comparar a nivel de frase para evitar falsos empates
        frases = [f.strip() for f in texto.replace("!", ".").replace("?", ".").split(".") if f.strip()]
        e1_cerca = sum(1 for f in frases if any(kw in f for kw in KW_FAVORITO) and (e1 in f or e1_alt in f))
        e2_cerca = sum(1 for f in frases if any(kw in f for kw in KW_FAVORITO) and (e2 in f or e2_alt in f))
        if e1_cerca > e2_cerca:
            conteo["e1_fav"] += 1
        elif e2_cerca > e1_cerca:
            conteo["e2_fav"] += 1
        elif any(kw in texto for kw in KW_FAVORITO):
            conteo["gen_fav"] += 1

        # Lesiones
        if any(kw in texto for kw in KW_LESION) and (menciona_e1 or menciona_e2) and orig and orig[:180] not in lesion_snippets:
            lesion_snippets.append(orig[:180])

        # Goles / ataque (solo si menciona a algún equipo del partido)
        if any(kw in texto for kw in KW_GOLES) and (menciona_e1 or menciona_e2) and orig and orig[:180] not in gol_snippets:
            gol_snippets.append(orig[:180])

        # Forma
        if any(kw in texto for kw in KW_FORMA) and (menciona_e1 or menciona_e2) and orig and orig[:180] not in forma_snippets:
            forma_snippets.append(orig[:180])

        # Predicciones IA (solo si menciona a algún equipo del partido)
        if any(kw in texto for kw in KW_IA) and (menciona_e1 or menciona_e2) and orig and orig[:200] not in ia_snippets:
            ia_snippets.append(orig[:200])

    # ── Construir texto resumen ─────────────────────────────────
    parrafos = []
    puntos   = []

    # Párrafo 1: Favorito
    e1f = conteo["e1_fav"]
    e2f = conteo["e2_fav"]
    if e1f > e2f:
        parrafos.append(
            f"La mayoría de los medios apunta a <strong>{equipo1}</strong> como favorito "
            f"en este encuentro. Los analistas le dan ventaja sobre {equipo2}."
        )
        puntos.append(f"Favorito de la prensa: {equipo1}")
    elif e2f > e1f:
        parrafos.append(
            f"La cobertura mediática sitúa a <strong>{equipo2}</strong> como favorito. "
            f"Los analistas ven con ventaja a {equipo2} frente a {equipo1}."
        )
        puntos.append(f"Favorito de la prensa: {equipo2}")
    else:
        parrafos.append(
            f"La prensa deportiva presenta un duelo equilibrado entre "
            f"<strong>{equipo1}</strong> y <strong>{equipo2}</strong>, sin un claro favorito."
        )
        puntos.append("Partido equilibrado según la prensa")

    # Párrafo 2: Lesionados
    if lesion_snippets:
        txt = lesion_snippets[0]
        if not txt.endswith("."):
            txt += "."
        parrafos.append("Sobre el estado físico: " + txt)
        puntos.append("Noticias de lesionados / bajas")

    # Párrafo 3: Goles o forma
    extra = gol_snippets[:1] or forma_snippets[:1]
    if extra:
        txt = extra[0]
        if not txt.endswith((".", "…")):
            txt += "."
        parrafos.append(txt)

    # Párrafo IA
    if ia_snippets:
        txt = ia_snippets[0]
        if not txt.endswith((".", "…")):
            txt += "."
        parrafos.append("Predicción de IA: " + txt)
        puntos.append("Predicción de inteligencia artificial disponible")

    # Fuentes destacadas encontradas
    destacadas_encontradas = sorted({
        fd for a in articulos
        for fd in FUENTES_DESTACADAS
        if fd in a.get("fuente", "").lower()
    })
    if destacadas_encontradas:
        puntos.append("Fuentes: " + ", ".join(destacadas_encontradas).title())

    # Fallback: usar los mejores snippets directamente
    if len(parrafos) < 2:
        for a in articulos[:3]:
            s = a.get("resumen", "")
            if s and len(s) > 60 and s[:200] not in " ".join(parrafos):
                parrafos.append(s[:200] + "…")

    texto_final = " ".join(parrafos) if parrafos else "Consulta las fuentes para ver el análisis completo."

    return {
        "texto": texto_final,
        "puntos_clave": puntos,
        "fuentes_unicas": sorted(todas_fuentes),
    }


def analizar_prensa(equipo1: str, equipo2: str) -> dict:
    """
    Recopila artículos de prensa sobre el partido equipo1 vs equipo2.
    Devuelve un dict con predicciones, lesionados y análisis de forma.
    Las búsquedas RSS se hacen en paralelo para reducir el tiempo total.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    print(f"\n  Buscando noticias: {equipo1} vs {equipo2}...")

    queries = [t.format(e1=equipo1, e2=equipo2) for t in TERMINOS_BUSQUEDA]
    secciones = {}

    with ThreadPoolExecutor(max_workers=6) as executor:
        future_to_query = {executor.submit(_buscar_rss, q, 4): q for q in queries}
        for future in as_completed(future_to_query, timeout=18):
            q = future_to_query[future]
            try:
                articulos = future.result()
                if articulos:
                    secciones[q] = articulos
            except Exception:
                pass

    # Consolidar todos los artículos únicos por título
    vistos = set()
    todos = []
    for arts in secciones.values():
        for a in arts:
            if a["titulo"] not in vistos:
                vistos.add(a["titulo"])
                todos.append(a)

    # Etiquetar artículos por tipo
    KW_IA_TAG = ["inteligencia artificial", "ia predice", "ai prediction", "machine learning",
                 "modelo predictivo", "algoritmo predice", "análisis predictivo"]
    for a in todos:
        texto_tag = (a.get("titulo", "") + " " + a.get("resumen", "")).lower()
        fuente_lower = a.get("fuente", "").lower()
        a["es_ia"] = any(kw in texto_tag for kw in KW_IA_TAG)
        a["es_destacada"] = any(fd in fuente_lower for fd in FUENTES_DESTACADAS)

    resumen = generar_resumen_prensa(todos, equipo1, equipo2)

    return {
        "partido": f"{equipo1} vs {equipo2}",
        "equipo1": equipo1,
        "equipo2": equipo2,
        "total_articulos": len(todos),
        "articulos": todos,
        "resumen_editorial": resumen,
    }


def imprimir_prensa(resultado: dict):
    """Imprime en consola el resumen de prensa de forma legible."""
    print(f"\n{'='*60}")
    print(f"  ANÁLISIS DE PRENSA: {resultado['partido']}")
    print(f"  Total artículos encontrados: {resultado['total_articulos']}")
    print(f"{'='*60}")

    for i, a in enumerate(resultado["articulos"], 1):
        print(f"\n  [{i}] {a['titulo']}")
        print(f"      Fuente: {a['fuente']}  |  {a['fecha']}")
        if a["resumen"]:
            print(f"      {a['resumen'][:200]}...")
        print(f"      URL: {a['link']}")


def guardar_csv_prensa(resultado: dict):
    """Guarda los artículos encontrados en un CSV."""
    import pandas as pd
    nombre = resultado["partido"].replace(" ", "_")
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    ruta = os.path.join(DATOS_DIR, f"prensa_{nombre}_{fecha_hoy}.csv")
    df = pd.DataFrame(resultado["articulos"])
    df.to_csv(ruta, index=False, encoding="utf-8-sig")
    print(f"  [✓] CSV guardado: {ruta}")


def analizar_prensa_todos(partidos: list, max_workers: int = 4) -> dict:
    """
    Busca noticias en paralelo para todos los partidos de la lista.
    Devuelve dict {nombre_partido: resultado_prensa}.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading

    resultados = {}
    lock = threading.Lock()
    total = len(partidos)
    contador = [0]

    def _fetch_uno(p):
        nombre = p.get("partido", "")
        partes = nombre.split(" vs ")
        if len(partes) < 2:
            return nombre, None
        local, visita = partes[0].strip(), partes[1].strip()
        prensa = analizar_prensa(local, visita)
        with lock:
            contador[0] += 1
            print(f"  [{contador[0]}/{total}] Noticias listas: {nombre} ({prensa['total_articulos']} art.)")
        return nombre, prensa

    print(f"\n  Cargando prensa para {total} partidos (paralelo, máx {max_workers} a la vez)...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_fetch_uno, p) for p in partidos]
        for future in as_completed(futures):
            nombre, prensa = future.result()
            if nombre and prensa:
                resultados[nombre] = prensa

    print(f"  [✓] Prensa cargada para {len(resultados)} partidos.\n")
    return resultados


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        e1, e2 = sys.argv[1], sys.argv[2]
    else:
        e1, e2 = "Argentina", "Francia"

    resultado = analizar_prensa(e1, e2)
    imprimir_prensa(resultado)
    guardar_csv_prensa(resultado)
