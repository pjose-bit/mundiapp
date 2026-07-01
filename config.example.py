import os

# ─────────────────────────────────────────────
#  CONFIGURACIÓN PRINCIPAL
#  Copia este archivo como config.py y completa tu API key
# ─────────────────────────────────────────────

# API key gratuita de The Odds API
# Regístrate en: https://the-odds-api.com  (500 req/mes gratis)
ODDS_API_KEY = ""   # <-- pega tu clave aquí

# Competición FIFA World Cup 2026
SPORT_KEY = "soccer_fifa_world_cup"
ODDS_REGIONS = "eu"          # cuotas europeas (decimales)
ODDS_MARKETS = "h2h"         # mercado 1X2 (local / empate / visita)
ODDS_FORMAT  = "decimal"

# Idioma para búsqueda de noticias
NEWS_LANG   = "es"
NEWS_COUNTRY = "CL"

# Resumen de prensa con IA (opcional)
# Consigue una key gratuita en https://aistudio.google.com/apikey
# Déjala vacía para usar el resumen por reglas (sin costo, sin dependencias externas).
# Recomendado: solo configurarla localmente, no en Vercel (evita timeouts en producción).
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL   = "gemini-2.0-flash"

# Directorios de salida
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATOS_DIR   = os.path.join(BASE_DIR, "datos")
REPORTES_DIR = os.path.join(BASE_DIR, "reportes")

# Número de artículos de prensa a mostrar por equipo
MAX_ARTICULOS = 8

# Casas de apuestas preferidas para resaltar (opcional)
BOOKMAKERS_PREFERIDOS = ["bwin", "coolbet", "bet365", "betfair"]
