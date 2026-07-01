"""
generar_reporte.py  –  Dashboard moderno para análisis del Mundial 2026.
"""

import json
import os
from datetime import datetime
from config import REPORTES_DIR
from scraper_apuestas import estimar_marcadores

# ── Banderas ─────────────────────────────────────────────────────────────────
BANDERAS = {
    "argentina":"🇦🇷","france":"🇫🇷","francia":"🇫🇷","netherlands":"🇳🇱",
    "holanda":"🇳🇱","morocco":"🇲🇦","marruecos":"🇲🇦","brazil":"🇧🇷",
    "brasil":"🇧🇷","germany":"🇩🇪","alemania":"🇩🇪","spain":"🇪🇸","españa":"🇪🇸",
    "england":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","inglaterra":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","portugal":"🇵🇹",
    "united states":"🇺🇸","usa":"🇺🇸","estados unidos":"🇺🇸",
    "mexico":"🇲🇽","méxico":"🇲🇽","uruguay":"🇺🇾","colombia":"🇨🇴",
    "chile":"🇨🇱","ecuador":"🇪🇨","peru":"🇵🇪","perú":"🇵🇪",
    "japan":"🇯🇵","japón":"🇯🇵","south korea":"🇰🇷","corea del sur":"🇰🇷",
    "australia":"🇦🇺","saudi arabia":"🇸🇦","arabia saudita":"🇸🇦",
    "senegal":"🇸🇳","nigeria":"🇳🇬","ghana":"🇬🇭","cameroon":"🇨🇲","camerún":"🇨🇲",
    "croatia":"🇭🇷","croacia":"🇭🇷","serbia":"🇷🇸","poland":"🇵🇱","polonia":"🇵🇱",
    "switzerland":"🇨🇭","suiza":"🇨🇭","belgium":"🇧🇪","bélgica":"🇧🇪",
    "denmark":"🇩🇰","dinamarca":"🇩🇰","sweden":"🇸🇪","suecia":"🇸🇪",
    "norway":"🇳🇴","noruega":"🇳🇴","turkey":"🇹🇷","turquía":"🇹🇷",
    "canada":"🇨🇦","canadá":"🇨🇦","costa rica":"🇨🇷","panama":"🇵🇦","panamá":"🇵🇦",
    "venezuela":"🇻🇪","paraguay":"🇵🇾","bolivia":"🇧🇴","qatar":"🇶🇦",
    "iran":"🇮🇷","irán":"🇮🇷","slovakia":"🇸🇰","eslovaquia":"🇸🇰",
    "austria":"🇦🇹","ukraine":"🇺🇦","ucrania":"🇺🇦","egypt":"🇪🇬","egipto":"🇪🇬",
    "tunisia":"🇹🇳","túnez":"🇹🇳","new zealand":"🇳🇿","nueva zelanda":"🇳🇿",
    "albania":"🇦🇱","slovenia":"🇸🇮","eslovenia":"🇸🇮",
    "ivory coast":"🇨🇮","costa de marfil":"🇨🇮",
    "dr congo":"🇨🇩","congo":"🇨🇩","indonesia":"🇮🇩","slovakia":"🇸🇰",
}

def bandera(nombre: str) -> str:
    n = nombre.lower()
    for k, v in BANDERAS.items():
        if k in n:
            return v
    return "⚽"


# ── CSS ───────────────────────────────────────────────────────────────────────
CSS = """
:root {
  --bg:        #f1f5f9;
  --surface:   #ffffff;
  --border:    #e2e8f0;
  --primary:   #10b981;
  --primary-d: #059669;
  --live:      #ef4444;
  --away:      #f43f5e;
  --draw:      #94a3b8;
  --text:      #0f172a;
  --muted:     #64748b;
  --header-bg: #0f172a;
  --shadow-sm: 0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.04);
  --shadow-md: 0 4px 16px rgba(0,0,0,.08), 0 2px 6px rgba(0,0,0,.04);
  --shadow-lg: 0 12px 40px rgba(0,0,0,.12), 0 4px 12px rgba(0,0,0,.06);
  --r-sm: 8px; --r-md: 14px; --r-lg: 18px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg); color: var(--text);
  font-size: 14px; min-height: 100vh;
}

/* ── SCROLLBARS ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

/* ── HEADER ── */
.header {
  background: var(--header-bg);
  display: flex; align-items: center;
  height: 64px; padding: 0 20px;
  position: relative; z-index: 10;
  box-shadow: 0 2px 20px rgba(0,0,0,.3);
}
.brand {
  display: flex; align-items: center; gap: 10px;
  font-weight: 800; font-size: 16px; color: white;
  letter-spacing: -0.3px; flex-shrink: 0;
  padding-right: 20px; margin-right: 20px;
  border-right: 1px solid rgba(255,255,255,.12);
}
.brand-icon { font-size: 22px; }
.brand-sub { font-size: 10px; font-weight: 500; color: #94a3b8;
  display: block; letter-spacing: 0.5px; text-transform: uppercase; }

.feat-strip {
  display: flex; gap: 8px; overflow-x: auto; flex: 1;
  padding: 0 4px; scrollbar-width: none;
}
.feat-strip::-webkit-scrollbar { display: none; }

.feat-card {
  flex-shrink: 0; background: rgba(255,255,255,.06);
  border: 1px solid rgba(255,255,255,.1);
  border-radius: var(--r-sm); padding: 8px 14px;
  cursor: pointer; min-width: 180px;
  transition: background 0.2s, border-color 0.2s;
  position: relative;
}
.feat-card:hover { background: rgba(255,255,255,.1); border-color: rgba(255,255,255,.2); }
.feat-card.active { background: rgba(16,185,129,.15); border-color: rgba(16,185,129,.4); }
.feat-card.live-card { border-color: rgba(239,68,68,.5); background: rgba(239,68,68,.1); }

.feat-label { font-size: 9px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1px; color: #64748b; margin-bottom: 5px;
  display: flex; align-items: center; gap: 6px; }
.feat-team { display: flex; align-items: center; gap: 7px; padding: 2px 0; }
.feat-flag { font-size: 15px; width: 20px; text-align: center; }
.feat-name { font-size: 12px; font-weight: 500; color: rgba(255,255,255,.85); flex: 1; }
.feat-pct { font-size: 12px; font-weight: 800; color: var(--primary); }

/* Live dot */
.live-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--live); display: inline-block;
  animation: pulse-dot 1.5s ease-in-out infinite;
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.5; transform: scale(1.4); }
}
.live-badge {
  font-size: 9px; font-weight: 800; color: var(--live);
  text-transform: uppercase; letter-spacing: 1px;
  display: inline-flex; align-items: center; gap: 4px;
}

/* ── LAYOUT: mobile first (single column) ── */
.layout {
  display: flex;
  flex-direction: column;
}
.sidebar { display: none; }
.center  {
  display: flex; flex-direction: column;
  min-height: calc(100vh - 56px);
}

/* Desktop: 2 columns, fixed height. El centro muestra el detalle del partido seleccionado arriba. */
@media (min-width: 769px) {
  body { height: 100vh; overflow: hidden; }
  .layout {
    display: grid;
    grid-template-columns: 200px 1fr;
    height: calc(100vh - 64px);
  }
  .sidebar { display: block; }
  .center {
    overflow-y: auto; min-height: unset;
    display: flex; flex-direction: column;
  }
}

/* ── SIDEBAR ── */
.sidebar {
  background: var(--surface); border-right: 1px solid var(--border);
  overflow-y: auto; padding: 16px 0;
}
.sidebar-section {
  padding: 12px 18px 4px;
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1px; color: #94a3b8;
}
.sidebar-item {
  padding: 9px 18px; cursor: pointer; font-size: 13px;
  color: var(--muted); display: flex; align-items: center;
  justify-content: space-between; gap: 8px;
  border-left: 3px solid transparent;
  transition: all 0.15s;
}
.sidebar-item:hover { background: #f8fafc; color: var(--text); }
.sidebar-item.active {
  color: var(--primary); font-weight: 700;
  border-left-color: var(--primary); background: #ecfdf5;
}
.sidebar-count {
  font-size: 11px; color: #cbd5e1; background: #f1f5f9;
  padding: 1px 7px; border-radius: 99px; font-weight: 600;
}
.sidebar-item.active .sidebar-count { background: #d1fae5; color: var(--primary); }

/* ── CENTER ── */
/* ── DETALLE DEL PARTIDO (dentro del centro) ── */
.panel {
  background: var(--surface);
  flex: 1; display: flex; flex-direction: column;
}
.panel-eyebrow {
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1px; color: #94a3b8; margin-bottom: 4px;
  display: flex; align-items: center; gap: 8px;
}
.panel-title { font-size: 19px; font-weight: 800; letter-spacing: -0.4px; line-height: 1.3; margin-bottom: 14px; }
.panel-body { padding: 20px; flex: 1; }

/* ── WINNER OUTCOMES ── */
.outcome-card {
  border: 1.5px solid var(--border); border-radius: var(--r-md);
  padding: 16px; margin-bottom: 10px;
  transition: box-shadow 0.2s, border-color 0.2s;
}
.outcome-card:hover { box-shadow: var(--shadow-sm); }
.outcome-card.winner {
  border-color: #a7f3d0; background: #f0fdf4;
  box-shadow: 0 0 0 3px rgba(16,185,129,.08);
}
.outcome-card.draw-card { border-color: #e2e8f0; background: #f8fafc; }
.outcome-card.loser { border-color: #fecdd3; background: #fff1f2; }

.outcome-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.outcome-flag { font-size: 28px; }
.outcome-info { flex: 1; }
.outcome-name { font-size: 14px; font-weight: 800; }
.outcome-sub  { font-size: 11px; color: var(--muted); margin-top: 1px; }
.fav-badge {
  font-size: 9px; font-weight: 800; text-transform: uppercase;
  letter-spacing: 0.8px; padding: 3px 10px; border-radius: 99px;
  background: var(--primary); color: white;
}

.outcome-buttons { display: flex; align-items: center; gap: 8px; }
.btn-si {
  background: var(--primary); color: white; border: none;
  border-radius: 99px; padding: 7px 20px;
  font-weight: 800; font-size: 13px; cursor: pointer;
  transition: background 0.2s, transform 0.15s;
  letter-spacing: 0.3px;
}
.btn-si:hover { background: var(--primary-d); transform: scale(1.03); }
.btn-no {
  background: white; color: var(--muted); border: 1.5px solid var(--border);
  border-radius: 99px; padding: 7px 20px;
  font-weight: 700; font-size: 13px; cursor: pointer;
  transition: border-color 0.2s, color 0.2s;
}
.btn-no:hover { border-color: #94a3b8; color: var(--text); }
.btn-pct { font-size: 11px; color: #94a3b8; font-weight: 600; }

.no-api { background: #fffbeb; border: 1.5px solid #fde68a; border-radius: var(--r-sm);
  padding: 14px; font-size: 12px; color: #92400e; line-height: 1.6; margin-bottom: 12px; }
.no-api code { background: #fef3c7; padding: 1px 5px; border-radius: 4px; font-size: 11px; }

/* ── MARCADOR EXACTO ── */
.scores-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 14px;
}
.scores-legend { display: flex; gap: 14px; }
.leg-item { display: flex; align-items: center; gap: 5px; font-size: 11px; color: var(--muted); font-weight: 600; }
.leg-dot { width: 8px; height: 8px; border-radius: 50%; }
.leg-dot.local { background: var(--primary); }
.leg-dot.draw  { background: var(--draw); }
.leg-dot.away  { background: var(--away); }

.score-row {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 0; border-bottom: 1px solid #f8fafc;
}
.score-rank { font-size: 11px; color: #cbd5e1; font-weight: 700; width: 18px; text-align: right; }
.score-badge {
  font-size: 18px; font-weight: 900; min-width: 56px; text-align: center;
  padding: 5px 10px; border-radius: 10px; letter-spacing: 1px;
}
.score-badge.local  { background: #ecfdf5; color: var(--primary); }
.score-badge.empate { background: #f1f5f9; color: #475569; }
.score-badge.visita { background: #fff1f2; color: var(--away); }
.score-bar-wrap { flex: 1; height: 8px; background: #f1f5f9; border-radius: 99px; overflow: hidden; }
.score-bar {
  height: 100%; border-radius: 99px;
  transition: width 0.7s cubic-bezier(.4,0,.2,1);
}
.score-bar.local  { background: linear-gradient(90deg, #10b981, #34d399); }
.score-bar.empate { background: linear-gradient(90deg, #94a3b8, #cbd5e1); }
.score-bar.visita { background: linear-gradient(90deg, #f43f5e, #fb7185); }
.score-pct { font-size: 13px; font-weight: 800; min-width: 42px; text-align: right; color: var(--text); }

.scores-model-note {
  margin-top: 14px; padding: 10px 12px; background: #f8fafc;
  border-radius: var(--r-sm); font-size: 11px; color: #94a3b8; line-height: 1.5;
}

/* Mobile score section: card destacada */
@media (max-width: 768px) {
  .score-row { padding: 12px 0; }
  .score-badge { font-size: 22px; min-width: 64px; padding: 7px 12px; border-radius: 12px; }
  .score-pct { font-size: 14px; min-width: 46px; }
  .score-bar-wrap { height: 10px; }
}

/* ── NOTICIAS ── */
.news-sep {
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.8px; color: #94a3b8;
  padding: 16px 0 12px;
  display: flex; align-items: center; gap: 10px;
}
.news-sep::after { content: ""; flex: 1; height: 1px; background: var(--border); }
.news-count { font-size: 10px; background: #f1f5f9; color: #94a3b8;
  padding: 2px 8px; border-radius: 99px; font-weight: 700; }

.news-item { padding: 11px 0; border-bottom: 1px solid #f8fafc; }
.news-item:last-child { border-bottom: none; }
.news-link {
  color: var(--text); font-size: 13px; font-weight: 600;
  text-decoration: none; line-height: 1.4; display: block;
  transition: color 0.15s;
}
.news-link:hover { color: var(--primary); }
.news-meta { font-size: 10px; color: #94a3b8; margin-top: 3px; font-weight: 500; }
.news-snippet { font-size: 12px; color: #64748b; margin-top: 5px; line-height: 1.5; }

/* ── RESUMEN PRENSA ── */
.press-summary {
  background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
  border: 1.5px solid #a7f3d0;
  border-radius: var(--r-md);
  padding: 14px 16px;
  margin-bottom: 12px;
}
.press-summary-header {
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1px; color: var(--primary);
  margin-bottom: 8px; display: flex; align-items: center; gap: 6px;
}
.press-summary-text {
  font-size: 13px; color: #1e293b; line-height: 1.75;
}
.press-key-points { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
.press-key-tag {
  font-size: 11px; font-weight: 600; color: var(--primary);
  background: white; border: 1px solid #a7f3d0;
  border-radius: 99px; padding: 3px 10px;
}
.press-ia-badge {
  font-size: 9px; font-weight: 700; color: #7c3aed;
  background: #ede9fe; border-radius: 99px;
  padding: 2px 8px; letter-spacing: 0.3px; text-transform: none;
}
.press-injury-note {
  font-size: 12.5px; color: #92400e; line-height: 1.6;
  background: #fffbeb; border: 1px solid #fde68a;
  border-radius: 8px; padding: 8px 11px; margin-top: 10px;
}

/* ── FUENTES COLAPSABLES ── */
.sources-details { margin-top: 10px; }
.sources-toggle {
  display: flex; align-items: center; gap: 8px;
  font-size: 12px; font-weight: 700; color: var(--muted);
  cursor: pointer; padding: 9px 13px;
  background: #f8fafc; border-radius: var(--r-sm);
  border: 1.5px solid var(--border);
  list-style: none; user-select: none;
  transition: background 0.15s, border-color 0.15s;
}
.sources-toggle::-webkit-details-marker { display: none; }
.sources-toggle::before {
  content: "▶"; font-size: 9px; color: #94a3b8;
  transition: transform 0.2s; flex-shrink: 0;
}
details[open] > .sources-toggle::before { transform: rotate(90deg); }
.sources-toggle:hover { background: #f1f5f9; border-color: #cbd5e1; color: var(--text); }
.sources-list {
  border: 1.5px solid var(--border); border-top: none;
  border-radius: 0 0 var(--r-sm) var(--r-sm);
  padding: 4px 13px 6px;
  background: var(--surface);
}

/* ── SECTION LABEL ── */
.section-label {
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1px; color: #94a3b8;
  margin-bottom: 10px; display: flex; align-items: center; gap: 8px;
}
.section-label::after { content:""; flex:1; height:1px; background:var(--border); }

/* ── PANEL HEADER ── */
.panel-sticky {
  position: sticky; top: 0; z-index: 5;
  background: var(--surface); border-bottom: 1px solid var(--border);
  padding: 16px 20px 12px;
}
.panel-top-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }

/* ── QR ── */
.qr-block { text-align: center; flex-shrink: 0; }
.qr-block img { width: 72px; height: 72px; border-radius: 8px;
  border: 1px solid var(--border); display: block; }
.qr-label { font-size: 9px; color: #94a3b8; margin-top: 4px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.5px; }

/* ── API BADGE ── */
.api-badge {
  display: flex; align-items: center; gap: 10px;
  flex-shrink: 0; margin-left: 12px; padding-left: 16px;
  border-left: 1px solid rgba(255,255,255,.12);
}
.api-ring { width: 40px; height: 40px; flex-shrink: 0; }
.api-ring svg { width: 100%; height: 100%; transform: rotate(-90deg); }
.api-info { display: flex; flex-direction: column; line-height: 1.3; }
.api-num { font-size: 17px; font-weight: 800; }
.api-label { font-size: 9px; color: #64748b; font-weight: 500;
  text-transform: uppercase; letter-spacing: 0.4px; }

/* ── PANEL BODIES ── */
.match-body { display: none; }
.match-body.active { display: block; }
.no-news-note {
  background: #f8fafc; border: 1.5px dashed #e2e8f0; border-radius: var(--r-sm);
  padding: 14px 16px; font-size: 12px; color: #94a3b8; line-height: 1.8;
  margin-top: 8px;
}
.no-news-note code { background: #f1f5f9; padding: 2px 6px; border-radius: 4px;
  font-size: 11px; color: #475569; }

/* ── MOBILE HEADER COMPACTO ── */
@media (max-width: 768px) {
  .header { height: 56px; padding: 0 12px; gap: 8px; }
  .brand { padding-right: 12px; margin-right: 8px; font-size: 14px; }
  .brand-sub { display: none; }
  .brand-icon { font-size: 18px; }
  .feat-card { min-width: 130px; padding: 5px 10px; }
  .feat-name { font-size: 11px; }
  .feat-pct  { font-size: 11px; }
  .api-badge { display: none; }
  .panel-sticky { padding: 12px 14px 10px; }
  .panel-title  { font-size: 16px; }
  .panel-body   { padding: 14px; }
  .panel-eyebrow { font-size: 9px; }
  .outcome-card { padding: 12px; }
  .outcome-flag { font-size: 22px; }
  .outcome-name { font-size: 13px; }
  .btn-si, .btn-no { padding: 6px 14px; font-size: 12px; }
  .section-label { font-size: 10px; margin-bottom: 8px; }
}

/* ── MOBILE: match-body visible + scroll suave ── */
@media (max-width: 768px) {
  .match-body { display: none; }
  .match-body.active { display: block; }
}
"""

# ── JS (sin f-string) ─────────────────────────────────────────────────────────
JS_TEMPLATE = """
function _mid(nombre) {
  return nombre.replace(/ /g, '_').replace(/[^a-zA-Z0-9_]/g, '-');
}

function seleccionar(nombre) {
  // Tarjetas del header (unico selector de partido)
  document.querySelectorAll('.feat-card').forEach(c => c.classList.remove('active'));
  const feat = document.querySelector('.feat-card[data-partido="' + nombre + '"]');
  if (feat) {
    feat.classList.add('active');
    feat.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
  }

  // Cambiar cuerpo del panel
  document.querySelectorAll('.match-body').forEach(b => b.classList.remove('active'));
  const body = document.getElementById('body-' + _mid(nombre));
  if (body) body.classList.add('active');

  // Actualizar encabezado del panel
  const eyebrow = document.getElementById('panel-eyebrow');
  const title   = document.getElementById('panel-title');
  if (eyebrow && title) {
    const isLive = feat && feat.classList.contains('live-card');
    eyebrow.innerHTML = isLive
      ? '<span class="live-badge"><span class="live-dot"></span>EN VIVO</span>'
      : 'FIFA WORLD CUP 2026';
    title.textContent = nombre;
  }

  // Desktop: scroll del centro al tope
  const center = document.querySelector('.center');
  if (center) center.scrollTop = 0;

  // Mobile: hacer scroll a la seccion del panel
  if (window.innerWidth <= 768) {
    const sticky = document.querySelector('.panel-sticky');
    if (sticky) sticky.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}
"""


# ── Helpers ────────────────────────────────────────────────────────────────────

def _topbar(todos: list, partido_actual: str, api_uso: dict = None) -> str:
    items = ""
    for p in todos[:14]:
        nombre  = p["partido"]
        local   = p["local"]
        visita  = p["visitante"]
        pb      = p.get("probabilidades", {})
        p1      = int(pb.get(local,  0))
        p2      = int(pb.get(visita, 0))
        activo  = "active" if nombre == partido_actual else ""
        en_vivo = p.get("en_vivo", False)
        live_cls = "live-card" if en_vivo else ""
        live_lbl = '<span class="live-dot"></span>' if en_vivo else "FIFA WC 2026"

        items += f"""
        <div class="feat-card {activo} {live_cls}" data-partido="{nombre}"
             onclick="seleccionar('{nombre.replace("'", "\\'")}')">
          <div class="feat-label">{live_lbl}</div>
          <div class="feat-team">
            <span class="feat-flag">{bandera(local)}</span>
            <span class="feat-name">{local}</span>
            <span class="feat-pct">{p1}%</span>
          </div>
          <div class="feat-team">
            <span class="feat-flag">{bandera(visita)}</span>
            <span class="feat-name">{visita}</span>
            <span class="feat-pct">{p2}%</span>
          </div>
        </div>"""

    if not items:
        partes = partido_actual.split(" vs ")
        l = partes[0] if partes else "Local"
        v = partes[1] if len(partes) > 1 else "Visitante"
        items = f"""
        <div class="feat-card active">
          <div class="feat-label">FIFA WC 2026</div>
          <div class="feat-team"><span class="feat-flag">{bandera(l)}</span>
            <span class="feat-name">{l}</span></div>
          <div class="feat-team"><span class="feat-flag">{bandera(v)}</span>
            <span class="feat-name">{v}</span></div>
        </div>"""

    # ── Badge de cuota API ──────────────────────────────────────────
    api_badge = ""
    if api_uso and api_uso.get("restantes") is not None:
        restantes = api_uso["restantes"]
        usadas    = api_uso.get("usadas", 0)
        total     = restantes + usadas
        pct       = round(restantes / total * 100) if total else 0
        if pct > 50:
            color = "#10b981"   # verde
        elif pct > 20:
            color = "#f59e0b"   # amarillo
        else:
            color = "#ef4444"   # rojo
        api_badge = f"""
        <div class="api-badge" title="Consultas API este mes">
          <div class="api-ring">
            <svg viewBox="0 0 36 36">
              <circle cx="18" cy="18" r="15" fill="none" stroke="rgba(255,255,255,.1)" stroke-width="3"/>
              <circle cx="18" cy="18" r="15" fill="none" stroke="{color}" stroke-width="3"
                stroke-dasharray="{pct * 0.942} 94.2"
                stroke-dashoffset="23.55" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="api-info">
            <span class="api-num" style="color:{color}">{restantes}</span>
            <span class="api-label">de {total} consultas<br>restantes</span>
          </div>
        </div>"""

    return f"""
    <header class="header">
      <div class="brand">
        <span class="brand-icon">⚽</span>
        <div><span>Mundial 2026</span><span class="brand-sub">Análisis & Predicciones</span></div>
      </div>
      <div class="feat-strip">{items}</div>
      {api_badge}
    </header>"""


def _sidebar(n: int) -> str:
    return f"""
    <nav class="sidebar">
      <div class="sidebar-section">Competición</div>
      <div class="sidebar-item active">FIFA World Cup <span class="sidebar-count">{n}</span></div>
      <div class="sidebar-section">Mercado</div>
      <div class="sidebar-item active">Ganador del partido</div>
      <div class="sidebar-section">Fase</div>
      <div class="sidebar-item">Octavos de final</div>
      <div class="sidebar-item">Cuartos de final</div>
      <div class="sidebar-item">Semifinales</div>
      <div class="sidebar-item">Final</div>
    </nav>"""


def _panel_winner(partido_apuestas, partido_prensa: dict) -> str:
    nombre = partido_prensa["partido"]
    partes = nombre.split(" vs ")
    local  = partes[0] if len(partes) > 0 else "Local"
    visita = partes[1] if len(partes) > 1 else "Visitante"

    if partido_apuestas and partido_apuestas.get("tabla_bookmakers"):
        pb  = partido_apuestas["probabilidades"]
        pr  = partido_apuestas["promedios"]
        mas = partido_apuestas["mas_probable"]
        p1  = int(pb.get(local,   0))
        px  = int(pb.get("Empate", 0))
        p2  = int(pb.get(visita,  0))
        o1  = pr.get("1", "–"); o2 = pr.get("2", "–"); ox = pr.get("X", "–")

        def _oc(eq, prob, odds, tp):
            is_winner = mas == eq or (eq == "Empate" and mas == "Empate")
            cls   = "winner" if is_winner else ("draw-card" if eq == "Empate" else "loser")
            badge = '<span class="fav-badge">Favorito</span>' if is_winner else ""
            flag  = bandera(eq) if eq != "Empate" else "🤝"
            no_p  = 100 - prob
            return f"""
            <div class="outcome-card {cls}">
              <div class="outcome-header">
                <span class="outcome-flag">{flag}</span>
                <div class="outcome-info">
                  <div class="outcome-name">{"Empate" if eq == "Empate" else eq + " avanza"}</div>
                  <div class="outcome-sub">Cuota promedio: {odds}x</div>
                </div>
                {badge}
              </div>
              <div class="outcome-buttons">
                <button class="btn-si">SÍ &nbsp;{prob}¢</button>
                <button class="btn-no">NO &nbsp;{no_p}¢</button>
                <span class="btn-pct">{prob}% probable</span>
              </div>
            </div>"""

        cuotas = _oc(local, p1, o1, "local") + _oc("Empate", px, ox, "draw") + _oc(visita, p2, o2, "visita")
    else:
        cuotas = f"""<div class="no-api">
          ⚠️ Sin datos de cuotas. Agrega tu <code>ODDS_API_KEY</code> en
          <code>config.py</code> para ver probabilidades de casas de apuestas.
        </div>"""

    return cuotas


def _panel_scores(partido_apuestas, partido_prensa: dict) -> str:
    nombre = partido_prensa["partido"]
    partes = nombre.split(" vs ")
    local  = partes[0] if len(partes) > 0 else "Local"
    visita = partes[1] if len(partes) > 1 else "Visitante"

    if not partido_apuestas or not partido_apuestas.get("tabla_bookmakers"):
        return """<div class="no-api">
          ⚠️ Se necesitan cuotas de apuestas para calcular marcadores.<br>
          Configura <code>ODDS_API_KEY</code> en <code>config.py</code>.
        </div>"""

    marcadores = estimar_marcadores(partido_apuestas)
    max_prob   = marcadores[0]["prob"] if marcadores else 1

    rows = ""
    for i, m in enumerate(marcadores, 1):
        ancho = round(m["prob"] / max_prob * 100)
        tipo  = m["resultado"]
        rows += f"""
        <div class="score-row">
          <span class="score-rank">{i}</span>
          <span class="score-badge {tipo}">{m['marcador']}</span>
          <div class="score-bar-wrap">
            <div class="score-bar {tipo}" style="width:{ancho}%"></div>
          </div>
          <span class="score-pct">{m['prob']}%</span>
        </div>"""

    return f"""
    <div class="scores-header">
      <strong style="font-size:13px">Probabilidad por marcador</strong>
      <div class="scores-legend">
        <span class="leg-item"><span class="leg-dot local"></span>{local}</span>
        <span class="leg-item"><span class="leg-dot draw"></span>Empate</span>
        <span class="leg-item"><span class="leg-dot away"></span>{visita}</span>
      </div>
    </div>
    {rows}
    <div class="scores-model-note">
      📐 Calculado con distribución de Poisson calibrada desde cuotas 1X2.
      Promedio histórico de goles en el Mundial: 2.4 por partido.
    </div>"""


def _panel_conclusion(partido_apuestas, partido_prensa: dict) -> str:
    """Tarjeta de conclusión: Poisson, prensa y análisis combinado."""
    if not partido_apuestas or not partido_apuestas.get("tabla_bookmakers"):
        return ""

    nombre = partido_prensa.get("partido", "") if partido_prensa else ""
    partes = nombre.split(" vs ")
    local  = partes[0] if partes else ""
    visita = partes[1] if len(partes) > 1 else ""

    marcadores = estimar_marcadores(partido_apuestas)
    if not marcadores:
        return ""

    resumen = (partido_prensa or {}).get("resumen_editorial", {}) or {}
    puntos  = resumen.get("puntos_clave", [])

    # ── Favorito según prensa ──────────────────────────────────────────
    press_fav = None
    for p in puntos:
        if "Favorito de la prensa:" in p:
            press_fav = p.replace("Favorito de la prensa:", "").strip()
            break

    # ── Marcador Poisson (top probabilidad) ───────────────────────────
    poisson_top = marcadores[0]

    # ── Marcador prensa (primer score que alinea con favorito de prensa) ──
    press_score = None
    if press_fav:
        fav_l = press_fav.lower()
        loc_l = local.lower()
        vis_l = visita.lower()
        es_local  = fav_l in loc_l or loc_l in fav_l
        es_visita = fav_l in vis_l or vis_l in fav_l
        for m in marcadores[:5]:
            try:
                g1, g2 = map(int, m["marcador"].split("-"))
                if es_local  and g1 > g2: press_score = m; break
                if es_visita and g2 > g1: press_score = m; break
            except ValueError:
                pass

    # ── Estado de la prensa ────────────────────────────────────────────
    has_articles    = (partido_prensa or {}).get("total_articulos", 0) > 0
    press_equilib   = has_articles and press_fav is None
    tiene_ia        = any("inteligencia artificial" in p.lower() or "ia" in p.lower() for p in puntos)

    # ── Recomendación: siempre basada en Poisson; prensa confirma o advierte ──
    recomendado = poisson_top

    if press_fav and press_score:
        acuerdo = press_score["marcador"] == poisson_top["marcador"]
        diff_prob = poisson_top["prob"] - press_score["prob"]
        if acuerdo:
            analisis = (f"✅ Poisson y prensa <strong>coinciden</strong>: ambos apuntan a "
                        f"<strong>{press_fav}</strong> como ganador. "
                        f"Alta confianza en <strong>{poisson_top['marcador']}</strong> ({poisson_top['prob']}%).")
        elif diff_prob <= 4:
            # Probabilidades muy cercanas → prensa inclina la balanza
            recomendado = press_score
            analisis = (f"⚖️ Divergencia ajustada: Poisson prefiere {poisson_top['marcador']} ({poisson_top['prob']}%) "
                        f"pero la prensa favorece a <strong>{press_fav}</strong> "
                        f"(marcador {press_score['marcador']}, {press_score['prob']}%). "
                        f"Probabilidades similares — la prensa inclina la recomendación.")
        else:
            # Poisson claramente superior en probabilidad → ignorar prensa para el marcador
            analisis = (f"⚠️ Divergencia: la prensa favorece a <strong>{press_fav}</strong> "
                        f"(marcador alineado {press_score['marcador']}, {press_score['prob']}%), "
                        f"pero Poisson da mayor probabilidad a <strong>{poisson_top['marcador']}</strong> "
                        f"({poisson_top['prob']}%). Se recomienda el marcador estadístico.")
    elif press_fav and not press_score:
        analisis = (f"📰 Prensa señala a <strong>{press_fav}</strong> como favorito, pero ningún "
                    f"marcador del top-5 Poisson alinea con ese resultado. "
                    f"Se recomienda <strong>{poisson_top['marcador']}</strong> ({poisson_top['prob']}%) por estadística.")
    elif press_equilib:
        analisis = (f"📰 La prensa no identifica un favorito claro — partido equilibrado según los medios. "
                    f"Recomendación basada en Poisson: <strong>{poisson_top['marcador']}</strong> ({poisson_top['prob']}%).")
    else:
        analisis = (f"📊 Sin prensa cargada para este partido. "
                    f"Recomendación basada en modelo Poisson: "
                    f"<strong>{poisson_top['marcador']}</strong> ({poisson_top['prob']}%). "
                    f"Selecciona el partido para cargar noticias en tiempo real.")

    if tiene_ia:
        analisis += " <span style='color:#7c3aed;font-weight:700;'>· IA disponible en prensa.</span>"

    # ── Colores ────────────────────────────────────────────────────────
    def _colors(tipo):
        return {
            "local":  ("#10b981", "#f0fdf4", "#a7f3d0"),
            "empate": ("#64748b", "#f8fafc", "#e2e8f0"),
            "visita": ("#f43f5e", "#fff1f2", "#fecdd3"),
        }.get(tipo, ("#10b981", "#f0fdf4", "#a7f3d0"))

    def _score_block(marcador_dict, label):
        tipo = marcador_dict["resultado"]
        c, bg, border = _colors(tipo)
        return f"""
        <div style="text-align:center;background:{bg};border:1.5px solid {border};border-radius:10px;padding:10px 14px;min-width:80px;">
          <div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:{c};margin-bottom:4px;">{label}</div>
          <div style="font-size:32px;font-weight:900;color:{c};letter-spacing:3px;line-height:1;">{marcador_dict["marcador"]}</div>
          <div style="font-size:10px;color:#64748b;margin-top:3px;">{marcador_dict["prob"]}%</div>
        </div>"""

    def _press_placeholder(msg):
        return f'<div style="text-align:center;padding:10px 14px;min-width:80px;color:#94a3b8;font-size:11px;border:1.5px dashed #e2e8f0;border-radius:10px;">{msg}</div>'

    ia_badge = '<span style="font-size:10px;background:#ede9fe;color:#7c3aed;padding:2px 8px;border-radius:99px;font-weight:700;margin-left:8px;">+ IA</span>' if tiene_ia else ""

    poisson_block = _score_block(poisson_top, "📊 Poisson")
    if press_score:
        press_block = _score_block(press_score, "📰 Prensa")
    elif press_equilib:
        press_block = _press_placeholder("⚖️ Prensa<br>equilibrada")
    else:
        press_block = _press_placeholder("📰 Prensa<br>no cargada")

    rec_tipo = recomendado["resultado"]
    rc, rbg, rborder = _colors(rec_tipo)

    return f"""
    <div style="background:#f8fafc;border:2px solid #e2e8f0;border-radius:14px;padding:16px 18px;margin-bottom:18px;">
      <div style="font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:1.2px;color:#334155;margin-bottom:12px;">
        🎯 Análisis del partido{ia_badge}
      </div>
      <div style="display:flex;gap:10px;margin-bottom:14px;">
        {poisson_block}
        {press_block}
        <div style="text-align:center;background:{rbg};border:2px solid {rborder};border-radius:10px;padding:10px 14px;min-width:80px;flex:1;">
          <div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:{rc};margin-bottom:4px;">✅ Recomendado</div>
          <div style="font-size:36px;font-weight:900;color:{rc};letter-spacing:3px;line-height:1;">{recomendado["marcador"]}</div>
          <div style="font-size:10px;color:#64748b;margin-top:3px;">{recomendado["prob"]}%</div>
        </div>
      </div>
      <div style="font-size:11px;color:#475569;line-height:1.6;background:#fff;border-radius:8px;padding:10px 12px;border-left:3px solid {rc};">
        {analisis}
      </div>
    </div>"""


def _panel_news(partido_prensa: dict) -> str:
    articulos = partido_prensa.get("articulos", [])
    n = len(articulos)
    resumen_data = partido_prensa.get("resumen_editorial", {}) or {}

    if not articulos and not resumen_data.get("texto"):
        return '<p style="color:#94a3b8;font-style:italic;font-size:13px">No se encontraron artículos.</p>'

    # ── Resumen de los medios ────────────────────────────────────
    summary_html = ""
    texto = resumen_data.get("texto", "")
    if texto:
        tags_html = ""
        puntos = resumen_data.get("puntos_clave", [])
        if puntos:
            tags = "".join(f'<span class="press-key-tag">{p}</span>' for p in puntos)
            tags_html = f'<div class="press-key-points">{tags}</div>'

        conclusion_bajas = resumen_data.get("conclusion_bajas")
        conclusion_html = (
            f'<div class="press-injury-note">🩹 <strong>Impacto de bajas:</strong> {conclusion_bajas}</div>'
            if conclusion_bajas else ""
        )

        ia_label = (
            '<span class="press-ia-badge">✨ IA</span>' if resumen_data.get("generado_por_ia") else ""
        )

        summary_html = f"""
        <div class="press-summary">
          <div class="press-summary-header">📰 Resumen de los medios{ia_label}</div>
          <div class="press-summary-text">{texto}</div>
          {conclusion_html}
          {tags_html}
        </div>"""

    # ── Lista de artículos (colapsable) ─────────────────────────
    items = ""
    for a in articulos[:15]:
        snippet = a.get("resumen", "")[:160]
        badges = ""
        if a.get("es_destacada"):
            badges += '<span style="font-size:9px;background:#dbeafe;color:#1d4ed8;padding:1px 7px;border-radius:99px;font-weight:700;margin-right:4px;">MEDIA</span>'
        if a.get("es_ia"):
            badges += '<span style="font-size:9px;background:#ede9fe;color:#7c3aed;padding:1px 7px;border-radius:99px;font-weight:700;margin-right:4px;">IA</span>'
        items += f"""
        <div class="news-item">
          <a class="news-link" href="{a['link']}" target="_blank">{a['titulo']}</a>
          <div class="news-meta">{badges}{a['fuente']} &nbsp;·&nbsp; {a['fecha']}</div>
          {'<div class="news-snippet">' + snippet + "…</div>" if snippet else ""}
        </div>"""

    sources_html = f"""
    <details class="sources-details">
      <summary class="sources-toggle">Ver fuentes · {n} artículos</summary>
      <div class="sources-list">{items}</div>
    </details>"""

    return f"""
    <div class="news-sep">Prensa deportiva <span class="news-count">{n}</span></div>
    {summary_html}
    {sources_html}"""


def _match_id(nombre: str) -> str:
    import re
    return re.sub(r'[^a-zA-Z0-9_]', '-', nombre.replace(' ', '_'))


def _panel(partido_principal: dict, partido_prensa: dict,
           todos_partidos: list, qr_b64: str = "",
           todas_prensas: dict = None) -> str:
    """
    Genera el panel de detalle (vive dentro del centro, no como columna aparte):
    - Cabecera sticky (título dinámico)
    - Un .match-body por cada partido en todos_partidos (oculto)
    - El partido_principal arranca con .active y tiene noticias
    """
    nombre_principal = partido_prensa["partido"]

    qr_html = f"""
      <div class="qr-block">
        <img src="data:image/png;base64,{qr_b64}" alt="QR celular">
        <div class="qr-label">Ver en celular</div>
      </div>""" if qr_b64 else ""

    # ── Cabecera sticky (se actualiza con JS) ──────────────────────
    partes   = nombre_principal.split(" vs ")
    local_p  = partes[0] if partes else ""
    visita_p = partes[1] if len(partes) > 1 else ""
    en_vivo_p = partido_principal.get("en_vivo", False) if partido_principal else False
    eyebrow_init = '<span class="live-badge"><span class="live-dot"></span>EN VIVO</span>' if en_vivo_p else "FIFA WORLD CUP 2026"

    header = f"""
      <div class="panel-sticky">
        <div class="panel-top-row">
          <div>
            <div class="panel-eyebrow" id="panel-eyebrow">{eyebrow_init}</div>
            <div class="panel-title" id="panel-title">{nombre_principal}</div>
          </div>
          {qr_html}
        </div>
      </div>"""

    # ── Cuerpos de cada partido ────────────────────────────────────
    bodies = ""
    for p in todos_partidos:
        nombre = p["partido"]
        mid    = _match_id(nombre)
        activo = "active" if nombre == nombre_principal else ""

        winner = _panel_winner(p, {"partido": nombre})
        scores = _panel_scores(p, {"partido": nombre})

        # Prensa: partido principal usa partido_prensa; resto busca en todas_prensas
        if nombre == nombre_principal:
            prensa_match = partido_prensa
        elif todas_prensas and nombre in todas_prensas:
            prensa_match = todas_prensas[nombre]
        else:
            prensa_match = None

        if prensa_match:
            news = _panel_news(prensa_match)
        else:
            partes2 = nombre.split(" vs ")
            l2 = partes2[0] if partes2 else ""
            v2 = partes2[1] if len(partes2) > 1 else ""
            news = f"""
            <div class="news-sep">Prensa deportiva <span class="news-count">—</span></div>
            <div class="no-news-note">
              Noticias no cargadas para este partido.<br>
              Para verlas ejecuta:<br>
              <code>python main.py "{l2}" "{v2}"</code>
            </div>"""

        conclusion = _panel_conclusion(p, prensa_match or {"partido": nombre})

        bodies += f"""
        <div class="match-body {activo}" id="body-{mid}">
          {news}
          <div class="section-label" style="margin-top:20px">Ganador del partido</div>
          {winner}
          <div class="section-label" style="margin-top:20px">Marcador exacto</div>
          {scores}
          <div style="margin-top:20px">{conclusion}</div>
        </div>"""

    return f"""
    <div class="panel">
      {header}
      <div class="panel-body">
        {bodies}
      </div>
    </div>"""


# ── QR y red local ───────────────────────────────────────────────────────────

import socket, io, base64

def _ip_local() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.254.254.254", 1))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()

def _generar_qr_b64(url: str) -> str:
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=4, border=2,
                           error_correction=qrcode.constants.ERROR_CORRECT_M)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0f172a", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return ""


# ── Panel de exactitud histórica ──────────────────────────────────────────────

def _panel_accuracy() -> str:
    """Tarjeta de rendimiento: qué tan bien acertaron Poisson, apuestas y prensa."""
    try:
        from tracker import calcular_exactitud
        stats = calcular_exactitud()
    except Exception:
        return ""

    if stats["total"] == 0:
        return ""

    def _barra(pct, color):
        if pct is None:
            return '<span style="color:#94a3b8;font-size:11px;">Sin datos</span>'
        w = max(4, int(pct))
        return (f'<div style="display:flex;align-items:center;gap:8px;">'
                f'<div style="flex:1;background:#e2e8f0;border-radius:99px;height:8px;">'
                f'<div style="width:{w}%;background:{color};border-radius:99px;height:8px;"></div></div>'
                f'<span style="font-size:12px;font-weight:700;color:{color};min-width:36px;">{pct}%</span></div>')

    def _icono(pct):
        if pct is None: return "—"
        if pct >= 75:   return "🟢"
        if pct >= 50:   return "🟡"
        return "🔴"

    pp = stats["poisson"];  pa = stats["apuestas"]; pr = stats["prensa"]

    # Tabla de partidos recientes
    filas = ""
    for p in sorted(stats["partidos"], key=lambda x: x["fecha"], reverse=True)[:6]:
        r  = p["resultado_real"]
        gp = p.get("prediccion_poisson") or {}
        ga = p.get("prediccion_apuestas") or {}
        gr = p.get("prediccion_prensa") or {}

        def _tick(pred, real):
            if pred is None: return '<span style="color:#94a3b8">—</span>'
            return '✅' if pred == real else '❌'

        filas += f"""<tr style="border-bottom:1px solid #f1f5f9;">
          <td style="padding:6px 8px;font-size:12px;font-weight:600;">{p['local']} vs {p['visitante']}</td>
          <td style="padding:6px 8px;font-size:12px;text-align:center;">{r['marcador']}</td>
          <td style="padding:6px 8px;font-size:13px;text-align:center;">{_tick(gp.get('ganador'), r['ganador'])}</td>
          <td style="padding:6px 8px;font-size:13px;text-align:center;">{_tick(ga.get('ganador'), r['ganador'])}</td>
          <td style="padding:6px 8px;font-size:13px;text-align:center;">{_tick(gr.get('ganador') if not gr.get('equilibrado') else None, r['ganador'])}</td>
        </tr>"""

    # Mejor casa de apuestas
    bk_html = ""
    if stats["bookmakers"]:
        bk_rows = ""
        for bk, v in list(stats["bookmakers"].items())[:5]:
            bar = _barra(v["pct"], "#3b82f6")
            bk_rows += f'<div style="margin-bottom:6px;"><div style="font-size:11px;color:#475569;margin-bottom:3px;">{bk} ({v["aciertos"]}/{v["total"]})</div>{bar}</div>'
        bk_html = f"""
        <div style="margin-top:16px;">
          <div style="font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:1px;color:#64748b;margin-bottom:8px;">Casas de apuestas</div>
          {bk_rows}
        </div>"""

    return f"""
    <div style="margin-top:24px;background:#fff;border:1.5px solid #e2e8f0;border-radius:14px;padding:18px 20px;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;">
        <div style="font-size:13px;font-weight:800;color:#1e293b;">📊 Rendimiento de predicciones — {stats['total']} partido(s)</div>
        <div style="font-size:10px;color:#94a3b8;">Ganador del partido</div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:16px;">
        <div style="background:#f0fdf4;border:1.5px solid #a7f3d0;border-radius:10px;padding:12px;">
          <div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:#10b981;margin-bottom:6px;">{_icono(pp['pct'])} Poisson</div>
          {_barra(pp['pct'], '#10b981')}
          <div style="font-size:10px;color:#64748b;margin-top:4px;">{pp['aciertos']}/{pp['total']} aciertos</div>
        </div>
        <div style="background:#eff6ff;border:1.5px solid #bfdbfe;border-radius:10px;padding:12px;">
          <div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:#3b82f6;margin-bottom:6px;">{_icono(pa['pct'])} Apuestas</div>
          {_barra(pa['pct'], '#3b82f6')}
          <div style="font-size:10px;color:#64748b;margin-top:4px;">{pa['aciertos']}/{pa['total']} aciertos</div>
        </div>
        <div style="background:#fdf4ff;border:1.5px solid #e9d5ff;border-radius:10px;padding:12px;">
          <div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:#a855f7;margin-bottom:6px;">{_icono(pr['pct'])} Prensa</div>
          {_barra(pr['pct'], '#a855f7')}
          <div style="font-size:10px;color:#64748b;margin-top:4px;">{pr['aciertos']}/{pr['total']} aciertos</div>
        </div>
      </div>
      <table style="width:100%;border-collapse:collapse;">
        <thead>
          <tr style="background:#f8fafc;">
            <th style="padding:6px 8px;font-size:10px;text-align:left;color:#64748b;font-weight:700;">Partido</th>
            <th style="padding:6px 8px;font-size:10px;text-align:center;color:#64748b;font-weight:700;">Resultado</th>
            <th style="padding:6px 8px;font-size:10px;text-align:center;color:#10b981;font-weight:700;">📊 Poisson</th>
            <th style="padding:6px 8px;font-size:10px;text-align:center;color:#3b82f6;font-weight:700;">🏦 Apuestas</th>
            <th style="padding:6px 8px;font-size:10px;text-align:center;color:#a855f7;font-weight:700;">📰 Prensa</th>
          </tr>
        </thead>
        <tbody>{filas}</tbody>
      </table>
      {bk_html}
    </div>"""


# ── Función principal ─────────────────────────────────────────────────────────

def construir_html(partido_apuestas, partido_prensa: dict, todos_partidos: list = None,
                   todas_prensas: dict = None) -> str:
    """Genera y retorna el HTML sin guardar en disco (usado por Flask/Vercel)."""
    nombre   = partido_prensa["partido"]
    todos    = todos_partidos or []
    n        = len(todos) if todos else 1

    from scraper_apuestas import get_api_uso
    topbar   = _topbar(todos, nombre, get_api_uso())
    sidebar  = _sidebar(n)
    panel    = _panel(partido_apuestas, partido_prensa, todos, "", todas_prensas)
    accuracy = _panel_accuracy()

    todos_json = json.dumps(todos, ensure_ascii=False)
    js = JS_TEMPLATE.replace("%TODOS_JSON%", todos_json)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="theme-color" content="#0f172a">
  <title>Mundial 2026 – {nombre} | v2</title>
  <style>{CSS}</style>
</head>
<body>
  {topbar}
  <div class="layout">
    {sidebar}
    <main class="center">
      {panel}
      {accuracy}
    </main>
  </div>
  <script>{js}</script>
</body>
</html>"""


def guardar_reporte(partido_apuestas, partido_prensa: dict, todos_partidos: list = None,
                    todas_prensas: dict = None):
    nombre   = partido_prensa["partido"]
    fecha    = datetime.now().strftime("%Y-%m-%d")
    todos    = todos_partidos or []
    n        = len(todos) if todos else 1

    nombre_archivo = nombre.replace(" ", "_").replace("/", "-")
    ruta = os.path.join(REPORTES_DIR, f"dashboard_{nombre_archivo}_{fecha}.html")

    ip       = _ip_local()
    url_red  = f"http://{ip}:8080/reportes/dashboard_{nombre_archivo}_{fecha}.html"
    qr_b64   = _generar_qr_b64(url_red)

    from scraper_apuestas import get_api_uso
    topbar  = _topbar(todos, nombre, get_api_uso())
    sidebar = _sidebar(n)
    panel   = _panel(partido_apuestas, partido_prensa, todos, qr_b64, todas_prensas)

    todos_json = json.dumps(todos, ensure_ascii=False)
    js = JS_TEMPLATE.replace("%TODOS_JSON%", todos_json)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Mundial 2026 – {nombre}</title>
  <style>{CSS}</style>
</head>
<body>
  {topbar}
  <div class="layout">
    {sidebar}
    <main class="center">
      {panel}
    </main>
  </div>
  <script>{js}</script>
</body>
</html>"""

    with open(ruta, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n  [✓] Dashboard generado: {ruta}")
    return ruta
