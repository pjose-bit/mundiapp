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
.center  { display: none; }
.panel   {
  border-left: none;
  display: flex; flex-direction: column;
  min-height: calc(100vh - 56px);
}

/* Desktop: 3 columns, fixed height */
@media (min-width: 769px) {
  body { height: 100vh; overflow: hidden; }
  .layout {
    display: grid;
    grid-template-columns: 200px 1fr 360px;
    height: calc(100vh - 64px);
  }
  .sidebar { display: block; }
  .center  { display: block; overflow-y: auto; }
  .panel {
    border-left: 1px solid var(--border);
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
.center { overflow-y: auto; padding: 20px 16px; }
.center-header {
  display: flex; align-items: flex-end; justify-content: space-between;
  margin-bottom: 16px;
}
.center-title { font-size: 22px; font-weight: 800; letter-spacing: -0.5px; }
.center-sub { font-size: 12px; color: var(--muted); margin-top: 2px; }
.center-date { font-size: 11px; color: #94a3b8; }

/* ── MATCH CARD ── */
.match-card {
  background: var(--surface); border-radius: var(--r-md);
  border: 1.5px solid var(--border);
  padding: 16px 18px; margin-bottom: 10px; cursor: pointer;
  transition: box-shadow 0.2s, border-color 0.2s, transform 0.15s;
  position: relative; overflow: hidden;
}
.match-card::before {
  content: ""; position: absolute; left: 0; top: 0; bottom: 0;
  width: 3px; background: transparent; transition: background 0.2s;
}
.match-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}
.match-card:hover::before { background: #e2e8f0; }
.match-card.selected { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(16,185,129,.12); }
.match-card.selected::before { background: var(--primary); }
.match-card.live-match {
  border-color: rgba(239,68,68,.35);
  background: linear-gradient(135deg, #fff5f5 0%, white 60%);
}
.match-card.live-match::before { background: var(--live); }
.match-card.live-match:hover { box-shadow: 0 4px 20px rgba(239,68,68,.15); }

.card-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.card-label {
  font-size: 9px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1px; color: #94a3b8;
  display: flex; align-items: center; gap: 6px;
}
.card-title { font-size: 15px; font-weight: 800; letter-spacing: -0.3px; margin-bottom: 2px; }
.card-date { font-size: 11px; color: var(--muted); margin-bottom: 14px; }

.card-teams { display: flex; flex-direction: column; gap: 2px; }
.card-team {
  display: flex; align-items: center; gap: 10px;
  padding: 6px 0;
}
.card-team + .card-team { border-top: 1px solid #f1f5f9; }
.card-flag { font-size: 20px; width: 26px; text-align: center; }
.card-name { flex: 1; font-size: 13px; font-weight: 600; color: #1e293b; }
.card-odds { font-size: 11px; color: #94a3b8; margin-right: 8px; font-weight: 500; }

.prob-pill {
  border-radius: 99px; padding: 4px 12px;
  font-size: 12px; font-weight: 800; min-width: 54px; text-align: center;
  transition: transform 0.15s;
}
.match-card:hover .prob-pill { transform: scale(1.05); }
.prob-pill.high { background: #ecfdf5; color: var(--primary); border: 1.5px solid #a7f3d0; }
.prob-pill.mid  { background: #fffbeb; color: #d97706;        border: 1.5px solid #fde68a; }
.prob-pill.low  { background: #fff1f2; color: var(--away);    border: 1.5px solid #fecdd3; }

/* ── RIGHT PANEL ── */
.panel {
  background: var(--surface); border-left: 1px solid var(--border);
  overflow-y: auto; display: flex; flex-direction: column;
}
.panel-header {
  padding: 20px 20px 0; position: sticky; top: 0;
  background: var(--surface); z-index: 5;
  border-bottom: 1px solid var(--border); padding-bottom: 0;
}
.panel-eyebrow {
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1px; color: #94a3b8; margin-bottom: 4px;
  display: flex; align-items: center; gap: 8px;
}
.panel-title { font-size: 19px; font-weight: 800; letter-spacing: -0.4px; line-height: 1.3; margin-bottom: 14px; }
.panel-tabs { display: flex; gap: 0; margin: 0 -20px; }
.panel-tab {
  flex: 1; padding: 10px 16px; text-align: center;
  font-size: 12px; font-weight: 700; cursor: pointer;
  color: var(--muted); border-bottom: 2px solid transparent;
  transition: color 0.2s, border-color 0.2s;
  letter-spacing: 0.3px; text-transform: uppercase;
}
.panel-tab:hover { color: var(--text); }
.panel-tab.active { color: var(--primary); border-bottom-color: var(--primary); }
.panel-body { padding: 20px; flex: 1; }

/* ── TAB CONTENT ── */
.tab-content { display: none; }
.tab-content.active { display: block; }

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

/* ── EMPTY STATE ── */
.empty { text-align: center; padding: 40px 20px; color: #94a3b8; }
.empty-icon { font-size: 40px; margin-bottom: 12px; }
.empty-text { font-size: 14px; font-weight: 600; }
.empty-sub  { font-size: 12px; margin-top: 4px; }

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
  // Tarjetas centro
  document.querySelectorAll('.match-card').forEach(c => c.classList.remove('selected'));
  const card = document.querySelector('[data-partido="' + nombre + '"]');
  if (card) {
    card.classList.add('selected');
    card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
  // Tarjetas header
  document.querySelectorAll('.feat-card').forEach(c => c.classList.remove('active'));
  const feat = document.querySelector('.feat-card[data-partido="' + nombre + '"]');
  if (feat) feat.classList.add('active');

  // Cambiar cuerpo del panel
  document.querySelectorAll('.match-body').forEach(b => b.classList.remove('active'));
  const body = document.getElementById('body-' + _mid(nombre));
  if (body) body.classList.add('active');

  // Actualizar encabezado del panel
  const eyebrow = document.getElementById('panel-eyebrow');
  const title   = document.getElementById('panel-title');
  if (eyebrow && title) {
    const isLive = card && card.classList.contains('live-match');
    eyebrow.innerHTML = isLive
      ? '<span class="live-badge"><span class="live-dot"></span>EN VIVO</span>'
      : 'FIFA WORLD CUP 2026';
    title.textContent = nombre;
  }

  // Desktop: scroll panel al tope
  const panel = document.querySelector('.panel');
  if (panel) panel.scrollTop = 0;

  // Mobile: hacer scroll a la seccion del panel
  if (window.innerWidth <= 768) {
    const sticky = document.querySelector('.panel-sticky');
    if (sticky) sticky.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}
"""


# ── Helpers ────────────────────────────────────────────────────────────────────

def _pill(pct: float) -> str:
    pct = int(pct)
    if pct >= 55:   cls = "high"
    elif pct >= 40: cls = "mid"
    else:           cls = "low"
    return f'<span class="prob-pill {cls}">{pct}%</span>'


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
      <div class="sidebar-item">Marcador exacto</div>
      <div class="sidebar-section">Fase</div>
      <div class="sidebar-item">Octavos de final</div>
      <div class="sidebar-item">Cuartos de final</div>
      <div class="sidebar-item">Semifinales</div>
      <div class="sidebar-item">Final</div>
    </nav>"""


def _match_cards(todos: list, partido_actual: str) -> str:
    if not todos:
        return """<div class="empty">
          <div class="empty-icon">📊</div>
          <div class="empty-text">Sin datos de apuestas</div>
          <div class="empty-sub">Configura ODDS_API_KEY en config.py</div>
        </div>"""

    cards = ""
    for p in todos:
        nombre   = p["partido"]
        local    = p["local"]
        visita   = p["visitante"]
        fecha    = p["fecha"]
        pb       = p.get("probabilidades", {})
        pr       = p.get("promedios", {})
        p1       = int(pb.get(local,  0))
        p2       = int(pb.get(visita, 0))
        o1       = pr.get("1", "–")
        o2       = pr.get("2", "–")
        en_vivo  = p.get("en_vivo", False)
        activo   = "selected" if nombre == partido_actual else ""
        live_cls = "live-match" if en_vivo else ""
        live_lbl = '<span class="live-badge"><span class="live-dot"></span>EN VIVO</span>' if en_vivo else ""

        cards += f"""
        <div class="match-card {activo} {live_cls}" data-partido="{nombre}"
             onclick="seleccionar('{nombre.replace("'", "\\'")}')">
          <div class="card-top">
            <div class="card-label">⚽ FIFA WORLD CUP &nbsp;·&nbsp; {fecha}</div>
            {live_lbl}
          </div>
          <div class="card-title">{local} vs {visita}</div>
          <div class="card-date">{fecha}</div>
          <div class="card-teams">
            <div class="card-team">
              <span class="card-flag">{bandera(local)}</span>
              <span class="card-name">{local}</span>
              <span class="card-odds">{o1}x</span>
              {_pill(p1)}
            </div>
            <div class="card-team">
              <span class="card-flag">{bandera(visita)}</span>
              <span class="card-name">{visita}</span>
              <span class="card-odds">{o2}x</span>
              {_pill(p2)}
            </div>
          </div>
        </div>"""
    return cards


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
    """Tarjeta de conclusión: marcador recomendado combinando Poisson + prensa."""
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

    press_fav = None
    for p in puntos:
        if "Favorito de la prensa:" in p:
            press_fav = p.replace("Favorito de la prensa:", "").strip()
            break

    # Buscar en los primeros 5 marcadores el que coincide con el favorito de prensa
    recomendado = marcadores[0]
    razon_alineado = False
    if press_fav:
        fav_l  = press_fav.lower()
        loc_l  = local.lower()
        vis_l  = visita.lower()
        es_local  = fav_l in loc_l or loc_l in fav_l
        es_visita = fav_l in vis_l or vis_l in fav_l
        for m in marcadores[:5]:
            try:
                g1, g2 = map(int, m["marcador"].split("-"))
                if es_local  and g1 > g2:
                    recomendado = m; razon_alineado = True; break
                if es_visita and g2 > g1:
                    recomendado = m; razon_alineado = True; break
            except ValueError:
                pass

    tipo = recomendado["resultado"]
    color  = {"local": "#10b981", "empate": "#64748b", "visita": "#f43f5e"}.get(tipo, "#10b981")
    bg     = {"local": "#f0fdf4", "empate": "#f8fafc", "visita": "#fff1f2"}.get(tipo, "#f0fdf4")
    border = {"local": "#a7f3d0", "empate": "#e2e8f0", "visita": "#fecdd3"}.get(tipo, "#a7f3d0")

    razones = []
    if press_fav and razon_alineado:
        razones.append(f"Prensa: favorito {press_fav}")
    elif press_fav:
        razones.append(f"Prensa: {press_fav} favorito (sin marcador alineado en top-5)")
    razones.append(f"Probabilidad Poisson: {recomendado['prob']}%")
    razon_txt = " &nbsp;·&nbsp; ".join(razones)

    tiene_ia = any("inteligencia artificial" in p.lower() or "ia" in p.lower() for p in puntos)
    ia_note = '<span style="font-size:10px;background:#ede9fe;color:#7c3aed;padding:2px 8px;border-radius:99px;font-weight:700;margin-left:8px;">+ IA</span>' if tiene_ia else ""

    return f"""
    <div style="background:{bg};border:2px solid {border};border-radius:14px;padding:16px 18px;margin-bottom:18px;">
      <div style="font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:1.2px;color:{color};margin-bottom:10px;display:flex;align-items:center;">
        🎯 Conclusión — Marcador recomendado{ia_note}
      </div>
      <div style="display:flex;align-items:center;gap:20px;">
        <div style="font-size:44px;font-weight:900;color:{color};letter-spacing:4px;line-height:1;">
          {recomendado["marcador"]}
        </div>
        <div>
          <div style="font-size:14px;font-weight:800;color:#1e293b;margin-bottom:5px;">{local} vs {visita}</div>
          <div style="font-size:11px;color:#64748b;line-height:1.7;">{razon_txt}</div>
        </div>
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
        summary_html = f"""
        <div class="press-summary">
          <div class="press-summary-header">📰 Resumen de los medios</div>
          <div class="press-summary-text">{texto}</div>
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
    Genera el aside con:
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
          {conclusion}
          <div class="section-label">Marcador exacto</div>
          {scores}
          <div class="section-label" style="margin-top:20px">Ganador del partido</div>
          {winner}
          {news}
        </div>"""

    return f"""
    <aside class="panel">
      {header}
      <div class="panel-body">
        {bodies}
      </div>
    </aside>"""


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


# ── Función principal ─────────────────────────────────────────────────────────

def construir_html(partido_apuestas, partido_prensa: dict, todos_partidos: list = None,
                   todas_prensas: dict = None) -> str:
    """Genera y retorna el HTML sin guardar en disco (usado por Flask/Vercel)."""
    nombre   = partido_prensa["partido"]
    fecha_ok = datetime.now().strftime("%d/%m/%Y %H:%M")
    todos    = todos_partidos or []
    n        = len(todos) if todos else 1

    from scraper_apuestas import get_api_uso
    topbar  = _topbar(todos, nombre, get_api_uso())
    sidebar = _sidebar(n)
    cards   = _match_cards(todos, nombre)
    panel   = _panel(partido_apuestas, partido_prensa, todos, "", todas_prensas)

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
  <title>Mundial 2026 – {nombre}</title>
  <style>{CSS}</style>
</head>
<body>
  {topbar}
  <div class="layout">
    {sidebar}
    <main class="center">
      <div class="center-header">
        <div>
          <div class="center-title">⚽ Fútbol — FIFA World Cup 2026</div>
          <div class="center-sub">{n} partidos disponibles con cuotas en tiempo real</div>
        </div>
        <div class="center-date">{fecha_ok}</div>
      </div>
      {cards}
    </main>
    {panel}
  </div>
  <script>{js}</script>
</body>
</html>"""


def guardar_reporte(partido_apuestas, partido_prensa: dict, todos_partidos: list = None,
                    todas_prensas: dict = None):
    nombre   = partido_prensa["partido"]
    fecha    = datetime.now().strftime("%Y-%m-%d")
    fecha_ok = datetime.now().strftime("%d/%m/%Y %H:%M")
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
    cards   = _match_cards(todos, nombre)
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
      <div class="center-header">
        <div>
          <div class="center-title">⚽ Fútbol — FIFA World Cup 2026</div>
          <div class="center-sub">{n} partidos disponibles con cuotas en tiempo real</div>
        </div>
        <div class="center-date">{fecha_ok}</div>
      </div>
      {cards}
    </main>
    {panel}
  </div>
  <script>{js}</script>
</body>
</html>"""

    with open(ruta, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n  [✓] Dashboard generado: {ruta}")
    return ruta
