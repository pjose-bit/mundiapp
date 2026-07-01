import os

# ── API de cuotas ─────────────────────────────────────────────────────────────
# Localmente: define ODDS_API_KEY como variable de entorno o reemplaza "" con tu clave
# En Vercel:  agrega ODDS_API_KEY en Settings → Environment Variables
ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")

# Competición FIFA World Cup 2026
SPORT_KEY    = "soccer_fifa_world_cup"
ODDS_REGIONS = "eu"
ODDS_MARKETS = "h2h"
ODDS_FORMAT  = "decimal"

# Idioma para búsqueda de noticias
NEWS_LANG    = "es"
NEWS_COUNTRY = "CL"

# Directorios de salida (en Vercel se usa /tmp)
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
DATOS_DIR    = os.environ.get("DATOS_DIR", os.path.join(BASE_DIR, "datos"))
REPORTES_DIR = os.environ.get("REPORTES_DIR", os.path.join(BASE_DIR, "reportes"))

# Número máximo de artículos de prensa por búsqueda
MAX_ARTICULOS = 8

# Caché y límite diario de consultas a la API
CACHE_TTL_MINUTOS  = 30
MAX_CONSULTAS_DIA  = 15

# Casas de apuestas preferidas para resaltar
BOOKMAKERS_PREFERIDOS = ["bwin", "coolbet", "bet365", "betfair"]
