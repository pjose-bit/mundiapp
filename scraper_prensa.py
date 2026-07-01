"""
Módulo: scraper_prensa.py
Busca predicciones y noticias de prensa deportiva sobre un partido del Mundial.
Usa feeds RSS de Google News (sin API key requerida).
"""

import feedparser
import requests
from bs4 import BeautifulSoup
import json
import os
import re
import unicodedata
from datetime import datetime
from config import NEWS_LANG, NEWS_COUNTRY, MAX_ARTICULOS, DATOS_DIR, GEMINI_API_KEY, GEMINI_MODEL


def _sin_acentos(texto: str) -> str:
    """Elimina acentos para comparación robusta: México → mexico, etc."""
    return unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf-8').lower()


def _limpiar_titulo(titulo: str, fuente: str) -> str:
    """Google News pega '- {Fuente}' al final del título; se recorta para poder usarlo como oración."""
    if fuente and titulo.lower().endswith(f"- {fuente.lower()}"):
        return titulo[: -(len(fuente) + 2)].strip()
    return titulo


def _extraer_frase(orig: str, keywords: list, largo: int = 200) -> str:
    """
    Devuelve la frase de `orig` que realmente contiene alguna keyword, en vez
    de los primeros N caracteres del texto (que con contenido real de 1200
    caracteres casi nunca es la parte relevante).
    """
    frases = [f.strip() for f in re.split(r'(?<=[.!?])\s+', orig) if f.strip()]
    for f in frases:
        if any(kw in _sin_acentos(f) for kw in keywords):
            return f[:largo]
    return orig[:largo]


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
    # Previa directa del partido
    "{e1} vs {e2} octavos final mundial 2026",
    "{e1} vs {e2} prediccion mundial 2026",
    "{e1} {e2} previa octavos de final",
    "{e1} {e2} pronostico julio 2026",
    # Lesionados y estado del equipo
    "{e1} lesionados baja mundial 2026",
    "{e2} lesionados baja mundial 2026",
    # Medios especializados
    "{e1} {e2} site:marca.com",
    "{e1} {e2} site:as.com",
    "{e1} vs {e2} world cup round of 16 site:espn.com",
    "{e1} vs {e2} world cup prediction site:si.com",
    "{e1} vs {e2} site:fifa.com",
    # Predicciones de inteligencia artificial
    "{e1} {e2} prediccion inteligencia artificial mundial 2026",
]

FUENTES_DESTACADAS = {"marca", "as", "espn", "sports illustrated", "si", "fifa", "diario as"}

# Artículos sin valor editorial: horarios/streaming, entradas, merchandising,
# páginas de "en vivo" genéricas. Se descartan antes de armar el resumen.
KW_IRRELEVANTE = [
    "como ver", "donde ver", "canales, streaming", "streaming y horarios",
    "a que hora", "cuando juegan", "horario y tv", "comentarios en vivo",
    "compra entradas", "entradas oficiales", "mejores precios y asientos",
    "camiseta de la", "camiseta oficial", "equipacion de", "official fifa store",
    "tienda oficial",
]

# Señales de que un artículo es realmente analítico (predicción/previa/lesionados)
# y vale la pena leer su contenido completo, no solo el titular.
KW_ANALITICO = [
    "prediccion", "pronostico", "previa", "analisis", "favorit",
    "lesion", "baja", "forma", "clave", "duelo", "apuestas", "cuotas",
]


def _es_articulo_irrelevante(titulo: str) -> bool:
    """Detecta artículos de horarios/entradas/merchandising/live genérico sin valor analítico."""
    t = _sin_acentos(titulo)
    if any(kw in t for kw in KW_IRRELEVANTE):
        return True
    if len(titulo) < 40 and (t.endswith(" live") or t.endswith("en vivo")):
        return True
    return False


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


def _decodificar_link_google_news(url: str) -> str:
    """
    Los links que entrega el RSS de Google News son redirects ofuscados que
    solo resuelven con JavaScript en el navegador (no son un HTTP redirect
    normal). Se decodifican llamando al mismo endpoint interno que usa
    Google News para resolverlos en el navegador. Si algo falla o cambia
    el formato interno de Google, devuelve la URL original sin modificar.
    """
    if "news.google.com" not in url:
        return url
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; WorldCupBot/1.0)"}
        resp = requests.get(url, headers=headers, timeout=8)
        m = re.search(
            r'<c-wiz[^>]*>.*?data-n-a-id="([^"]+)".*?data-n-a-ts="([^"]+)".*?data-n-a-sg="([^"]+)"',
            resp.text, re.S,
        )
        if not m:
            return url
        art_id, ts, sg = m.group(1), m.group(2), m.group(3)

        payload_inner = [
            "garturlreq",
            [["X", "X", ["X", "X"], None, None, 1, 1, "US:en", None, 1,
              None, None, None, None, None, 0, 1],
             "X", "X", 1, [1, 1, 1], 1, 1, None, 0, 0, None, 0],
            art_id, int(ts), sg,
        ]
        freq = json.dumps([[["Fbv4je", json.dumps(payload_inner, separators=(",", ":")), None, "generic"]]])

        batch_resp = requests.post(
            "https://news.google.com/_/DotsSplashUi/data/batchexecute",
            headers={
                "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
                "user-agent": "Mozilla/5.0 (compatible; WorldCupBot/1.0)",
            },
            data={"f.req": freq}, timeout=8,
        )
        cuerpo = batch_resp.text.split("\n\n", 1)[1]
        inner = json.loads(json.loads(cuerpo)[0][2])
        return inner[1] if inner[0] == "garturlres" else url
    except Exception:
        return url


def _intentar_leer_articulo(url: str) -> tuple[str, str]:
    """Intenta obtener el texto principal de un artículo (best-effort).
    Devuelve (url_real, texto) — url_real ya decodificada si venía de Google News."""
    url_real = _decodificar_link_google_news(url)
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; WorldCupBot/1.0)"}
        resp = requests.get(url_real, headers=headers, timeout=8)
        # resp.content (bytes): deja que BeautifulSoup detecte el charset real
        # desde el <meta> del HTML. resp.text usa el charset que adivina
        # requests desde el header HTTP, que a menudo está mal y produce
        # mojibake (ej. "serÃ¡" en vez de "será").
        soup = BeautifulSoup(resp.content, "lxml")
        # Eliminar scripts y estilos
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        parrafos = soup.find_all("p")
        texto = " ".join(p.get_text() for p in parrafos[:10])
        return url_real, (texto[:1200] if texto else "")
    except Exception:
        return url_real, ""


def _enriquecer_con_contenido_real(articulos: list, max_fetch: int = 5) -> None:
    """
    El campo "resumen" que entrega Google News RSS es casi siempre el título
    repetido (no hay contenido real). Para los artículos más analíticos
    (predicción/previa/lesionados/etc.) se decodifica su link real y se lee
    el cuerpo de la noticia, en paralelo. Modifica in-place; nunca falla.
    """
    candidatos = [
        a for a in articulos
        if a.get("link") and any(kw in _sin_acentos(a.get("titulo", "")) for kw in KW_ANALITICO)
    ]
    candidatos.sort(key=lambda a: not a.get("es_destacada", False))
    candidatos = candidatos[:max_fetch]
    if not candidatos:
        return

    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_art = {executor.submit(_intentar_leer_articulo, a["link"]): a for a in candidatos}
        for future in as_completed(future_to_art, timeout=25):
            a = future_to_art[future]
            try:
                url_real, texto = future.result()
                if texto and len(texto) > 80:
                    a["resumen"] = texto
                    a["link"] = url_real
                    a["contenido_real"] = True
            except Exception:
                pass


def _resumen_llm(equipo1: str, equipo2: str, articulos: list, lesion_snippets: list,
                  favorito_regla: str = None) -> dict:
    """
    Genera un resumen editorial con Gemini a partir de los artículos recopilados,
    con foco en sacar una conclusión concreta sobre el efecto de bajas/lesionados.
    Devuelve None si no hay API key configurada o si la llamada falla
    (el llamador debe usar el resumen por reglas como respaldo).
    """
    if not GEMINI_API_KEY or not articulos:
        return None

    contexto_articulos = "\n".join(
        f"- [{a.get('fuente', '')}] {a.get('titulo', '')}: {a.get('resumen', '')[:220]}"
        for a in articulos[:12]
    )
    contexto_bajas = "\n".join(f"- {s}" for s in lesion_snippets) or "Sin información de bajas/lesionados en los artículos."

    prompt = f"""Eres un editor de prensa deportiva. Analiza estas noticias sobre el partido {equipo1} vs {equipo2} del Mundial 2026 y redacta un resumen editorial breve en español, natural y fluido (no una lista de datos sueltos).

ARTÍCULOS ENCONTRADOS:
{contexto_articulos}

INFORMACIÓN DE BAJAS/LESIONADOS DETECTADA EN LOS ARTÍCULOS:
{contexto_bajas}

FAVORITO SEGÚN CONTEO DE MENCIONES EN PRENSA: {favorito_regla or "sin favorito claro, partido parejo"}

Instrucciones:
- "texto": 2 a 4 frases periodísticas que resuman favorito, forma del equipo y contexto relevante del partido. Usa las etiquetas <strong>{equipo1}</strong> y <strong>{equipo2}</strong> para destacar los nombres de los equipos cuando corresponda.
- "conclusion_bajas": UNA frase concreta que explique cómo las bajas/lesionados listados arriba podrían influir en el resultado o el marcador esperado (ej. menos gol si falta un delantero clave, más solidez defensiva si vuelve un jugador). Si el listado de bajas dice que no hay información, responde null.
- No inventes jugadores, lesiones, cifras ni datos que no estén en el material entregado arriba.

Responde solo el JSON pedido."""

    schema = {
        "type": "object",
        "properties": {
            "texto": {"type": "string"},
            "conclusion_bajas": {"type": ["string", "null"]},
        },
        "required": ["texto", "conclusion_bajas"],
    }

    try:
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}")
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "response_schema": schema,
                "temperature": 0.4,
            },
        }
        resp = requests.post(url, json=body, timeout=20)
        resp.raise_for_status()
        raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(raw)
        texto = (parsed.get("texto") or "").strip()
        if not texto:
            return None
        return {"texto": texto, "conclusion_bajas": parsed.get("conclusion_bajas") or None}
    except Exception:
        return None


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
        # El "resumen" de RSS es el título repetido (título + fuente pegados);
        # solo se usa como oración si viene de contenido real ya leído.
        orig    = (a.get("resumen", "") if a.get("contenido_real")
                   else _limpiar_titulo(a.get("titulo", ""), a.get("fuente", "")))

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
        if any(kw in texto for kw in KW_LESION) and (menciona_e1 or menciona_e2) and orig:
            frase = _extraer_frase(orig, KW_LESION, 180)
            if frase not in lesion_snippets:
                lesion_snippets.append(frase)

        # Goles / ataque (solo si menciona a algún equipo del partido)
        if any(kw in texto for kw in KW_GOLES) and (menciona_e1 or menciona_e2) and orig:
            frase = _extraer_frase(orig, KW_GOLES, 180)
            if frase not in gol_snippets:
                gol_snippets.append(frase)

        # Forma
        if any(kw in texto for kw in KW_FORMA) and (menciona_e1 or menciona_e2) and orig:
            frase = _extraer_frase(orig, KW_FORMA, 180)
            if frase not in forma_snippets:
                forma_snippets.append(frase)

        # Predicciones IA (solo si menciona a algún equipo del partido)
        if any(kw in texto for kw in KW_IA) and (menciona_e1 or menciona_e2) and orig:
            frase = _extraer_frase(orig, KW_IA, 200)
            if frase not in ia_snippets:
                ia_snippets.append(frase)

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

    # Fallback: usar los mejores snippets directamente (solo contenido real,
    # nunca el título repetido de RSS)
    if len(parrafos) < 2:
        for a in articulos[:3]:
            if not a.get("contenido_real"):
                continue
            s = a.get("resumen", "")
            if s and len(s) > 60 and s[:200] not in " ".join(parrafos):
                parrafos.append(s[:200] + "…")

    texto_regla = " ".join(parrafos) if parrafos else "Consulta las fuentes para ver el análisis completo."

    favorito_regla = None
    if e1f > e2f:
        favorito_regla = equipo1
    elif e2f > e1f:
        favorito_regla = equipo2

    llm = _resumen_llm(equipo1, equipo2, articulos, lesion_snippets, favorito_regla)

    return {
        "texto": llm["texto"] if llm else texto_regla,
        "puntos_clave": puntos,
        "fuentes_unicas": sorted(todas_fuentes),
        "conclusion_bajas": llm["conclusion_bajas"] if llm else None,
        "generado_por_ia": bool(llm),
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

    # Consolidar artículos únicos y filtrar los que no mencionan ningún equipo
    e1_norm = _sin_acentos(equipo1)
    e2_norm = _sin_acentos(equipo2)
    e1_alt_norm = _sin_acentos(NOMBRES_ES.get(equipo1.lower(), equipo1))
    e2_alt_norm = _sin_acentos(NOMBRES_ES.get(equipo2.lower(), equipo2))

    vistos = set()
    todos = []
    for arts in secciones.values():
        for a in arts:
            if a["titulo"] in vistos:
                continue
            texto_norm = _sin_acentos(a.get("titulo", "") + " " + a.get("resumen", ""))
            menciona_e1 = e1_norm in texto_norm or e1_alt_norm in texto_norm
            menciona_e2 = e2_norm in texto_norm or e2_alt_norm in texto_norm
            if not (menciona_e1 or menciona_e2):
                continue  # Descartar artículos que no hablan de ningún equipo del partido
            if _es_articulo_irrelevante(a.get("titulo", "")):
                continue  # Horarios, entradas, merchandising, "en vivo" genérico
            vistos.add(a["titulo"])
            todos.append(a)

    # Etiquetar artículos por tipo
    KW_IA_TAG = ["inteligencia artificial", "ia predice", "ai prediction", "machine learning",
                 "modelo predictivo", "algoritmo predice", "análisis predictivo"]
    for a in todos:
        texto_tag = _sin_acentos(a.get("titulo", "") + " " + a.get("resumen", ""))
        fuente_lower = a.get("fuente", "").lower()
        a["es_ia"] = any(kw in texto_tag for kw in KW_IA_TAG)
        a["es_destacada"] = any(fd in fuente_lower for fd in FUENTES_DESTACADAS)

    # El "resumen" de RSS es solo el título repetido: se intenta leer el
    # cuerpo real para los artículos más analíticos antes de sintetizar.
    _enriquecer_con_contenido_real(todos)

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
