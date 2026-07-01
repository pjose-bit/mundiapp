# Mundial 2026 – Sistema de Análisis y Predicciones

Sistema que combina cuotas de casas de apuestas con análisis de prensa deportiva para predecir resultados del Mundial FIFA 2026. Genera un dashboard web interactivo con probabilidades, marcadores exactos y noticias.

---

## Requisitos

- Python 3.14
- Dependencias: `pip install -r requirements.txt`
- API key gratuita de [the-odds-api.com](https://the-odds-api.com) (500 consultas/mes)

---

## Estructura de archivos

```
estadistica mundial/
├── main.py                → Punto de entrada principal
├── config.py              → Configuración (API key, rutas, parámetros)
├── scraper_apuestas.py    → Cuotas de casas de apuestas + marcadores exactos (Poisson)
├── scraper_prensa.py      → Noticias y predicciones desde Google News RSS
├── generar_reporte.py     → Genera el dashboard HTML
├── servidor.py            → Servidor local para ver desde el celular (WiFi)
├── requirements.txt       → Dependencias Python
├── imagen.webp            → Imagen de referencia del diseño
├── datos/                 → CSVs con cuotas y noticias guardadas
└── reportes/              → Dashboards HTML generados
```

---

## Cómo usar

### Ver todos los partidos disponibles
```
python main.py
```

### Analizar un partido específico
```
python main.py "Netherlands" "Morocco"
python main.py "France" "Sweden"
python main.py "Argentina" "Cape Verde"
```
Genera un dashboard HTML en `/reportes/` y lo abre en el navegador.

### Ver desde el celular (mismo WiFi)
1. Genera el reporte con `main.py`
2. Ejecuta el servidor:
```
python servidor.py
```
3. Escanea el QR que aparece en la esquina del dashboard

---

## Fuentes de datos

### 1. Casas de apuestas — The Odds API
- Cuotas 1X2 de múltiples casas (bwin, bet365, betfair, coolbet, etc.)
- Detecta partidos EN VIVO automáticamente
- Calcula probabilidad implícita por resultado
- **Marcador exacto**: estimado con distribución de Poisson calibrada desde las cuotas

### 2. Prensa deportiva — Google News RSS
- Busca predicciones, previas y análisis de ambos equipos
- Sin API key requerida
- Resultados en español (configurado para Chile)

---

## Configuración (config.py)

| Variable | Descripción | Valor actual |
|---|---|---|
| `ODDS_API_KEY` | Clave de The Odds API | configurada |
| `SPORT_KEY` | Competición | `soccer_fifa_world_cup` |
| `ODDS_REGIONS` | Región de cuotas | `eu` (europeas/decimales) |
| `MAX_ARTICULOS` | Artículos de prensa por búsqueda | `8` |
| `BOOKMAKERS_PREFERIDOS` | Casas a destacar | bwin, coolbet, bet365, betfair |

---

## Dashboard — lo que muestra

- **Barra superior**: todos los partidos disponibles con % de probabilidad; punto rojo animado si el partido está en vivo
- **Columna izquierda**: navegación por competición y fase
- **Centro**: tarjetas de todos los partidos con cuotas y probabilidades en tiempo real
- **Panel derecho**:
  - Ganador del partido con botones SÍ/NO estilo mercado de predicción
  - Marcador exacto: top 15 resultados más probables con barras animadas (verde = gana local, gris = empate, rojo = gana visitante)
  - Noticias de prensa deportiva
  - QR para ver desde el celular

---

## Pendiente / Próximas mejoras

- [ ] Marcador exacto: barras animadas al cargar (actualmente hay un bug de visibilidad)
- [ ] Agregar mercado de totales (over/under goles) desde la API
- [ ] Historial de partidos analizados en la página principal
- [ ] Comparador de múltiples partidos lado a lado
- [ ] Alertas cuando cambian las cuotas significativamente
- [ ] Exportar reporte a PDF

---

## Comandos rápidos

```bash
# Instalar dependencias (solo la primera vez)
python -m pip install -r requirements.txt

# Generar reporte de un partido
python main.py "Spain" "Austria"

# Iniciar servidor para celular
python servidor.py

# Solo cuotas (sin prensa)
python scraper_apuestas.py

# Solo prensa (sin cuotas)
python scraper_prensa.py "Argentina" "Cape Verde"
```

---

## Notas técnicas

- Las cuotas se obtienen en formato decimal (europeo). La probabilidad implícita es `1 / cuota × 100%`
- El marcador exacto usa distribución de Poisson con goles esperados calibrados desde la ratio de probabilidades 1X2. Promedio histórico del Mundial: 2.4 goles/partido
- El servidor local corre en el puerto `8080`. Si hay conflicto cambiar `PORT` en `servidor.py`
- Los archivos CSV en `/datos/` acumulan histórico de cuotas y noticias por partido y fecha
