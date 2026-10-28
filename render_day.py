#!/usr/bin/env python3
"""Genera la imagen de la cartelera del dia.
Uso: python3 render_day.py eventos.json salida.png "MIÉRCOLES 28 OCT"
eventos.json: lista de {"t":"HH:MM" (hora Monterrey, 24h),"league":"","match":"","ch":"","p":1-7,"sub":0,"tent":false,"kind":"soc|nfl|nba|cfb|mlb"}
"""
import html, json, sys
from playwright.sync_api import sync_playwright

DUR = {"soc": 120, "nfl": 195, "nba": 150, "cfb": 210, "mlb": 210}
PCOL = {1: "#d62828", 2: "#f77f00", 3: "#c79a00", 4: "#2a9d8f", 5: "#3a6ea5", 6: "#7b4fa3", 7: "#6b7280"}
LEGEND = {1: "Tigres y Rayados", 2: "Liguilla, clásicos y Serie Mundial", 3: "NFL (Dallas, SF, Steelers, KC, Bills, Pats)",
          4: "Champions y ligas de Europa", 5: "NBA", 6: "MLB regular", 7: "College Football"}
MX = ("Canal 5", "TUDN", "ViX", "Azteca")
CSS = """*{box-sizing:border-box;margin:0;padding:0}
body{width:820px;background:#f4f5f7;font-family:'Inter','DejaVu Sans',sans-serif;color:#111827}
.hdr{background:#0f172a;color:#fff;padding:22px 26px 16px}
.hdr .t{font-size:20px;color:#94a3b8;font-weight:700;letter-spacing:1px}
.hdr h1{font-size:44px;font-weight:800;letter-spacing:.4px;line-height:1.1}
.hdr .sub{font-size:19px;color:#cbd5e1;margin-top:3px}
.legend{padding:12px 26px 10px;display:flex;flex-wrap:wrap;gap:6px 16px;background:#fff;border-bottom:2px solid #e5e7eb}
.lgi{font-size:15px;display:flex;align-items:center;gap:6px;color:#1f2937}
.how{padding:9px 26px 12px;background:#fff;font-size:16.5px;color:#374151;border-bottom:2px solid #e5e7eb;line-height:1.3}
.how b{color:#111827}
.row{display:flex;align-items:center;gap:10px;padding:9px 22px 9px 16px;background:#fff;border-bottom:1px solid #e5e7eb}
.row.star{background:#fff8dc;border-left:7px solid #f5b700;padding-left:9px}
.st{width:20px;font-size:20px;color:#f5b700;text-align:center}
.time{width:100px;font-size:21px;font-weight:700;white-space:nowrap}
.badge{color:#fff;font-weight:800;font-size:16px;border-radius:7px;padding:4px 0;width:38px;text-align:center}
.badge.sm{font-size:12px;width:28px;padding:2px 0}
.mid{flex:1;min-width:0}
.match{font-size:23px;font-weight:700;line-height:1.12}
.row:not(.star) .match{font-weight:600}
.lg{font-size:14.5px;color:#6b7280;margin-top:1px}
.ch{font-size:15.5px;color:#374151;text-align:right;max-width:210px;line-height:1.15}
.empty{padding:30px 26px;background:#fff;font-size:20px;color:#374151}
.ftr{padding:14px 26px 20px;font-size:15px;color:#4b5563;line-height:1.4}"""

def mins(t):
    h, m = t.split(":"); return int(h) * 60 + int(m)

def fmt(t):
    h, m = map(int, t.split(":")); return f"{h % 12 or 12}:{m:02d} {'am' if h < 12 else 'pm'}"

def chan(c):
    return c if any(m in c for m in MX) else c + " / Firestick"

evs = [e for e in json.load(open(sys.argv[1])) if mins(e["t"]) >= 660]
evs.sort(key=lambda e: (mins(e["t"]), e["p"], e.get("sub", 0)))
key = lambda e: (e["p"], e.get("sub", 0))
dur = lambda e: DUR.get(e.get("kind", "soc"), 120)
for e in evs:
    s, f = mins(e["t"]), mins(e["t"]) + dur(e)
    e["star"] = not any(o is not e and mins(o["t"]) < f and s < mins(o["t"]) + dur(o) and key(o) < key(e) for o in evs)
rows = []
for e in evs:
    rows.append(
        f'<div class="{"row star" if e["star"] else "row"}"><span class="st">{"★" if e["star"] else ""}</span>'
        f'<div class="time">{fmt(e["t"])}{"*" if e.get("tent") else ""}</div>'
        f'<div class="badge" style="background:{PCOL[e["p"]]}">P{e["p"]}</div>'
        f'<div class="mid"><div class="match">{html.escape(e["match"])}</div><div class="lg">{html.escape(e["league"])}</div></div>'
        f'<div class="ch">{html.escape(chan(e["ch"]))}</div></div>')
used = sorted({e["p"] for e in evs})
leg = "".join(f'<div class="lgi"><span class="badge sm" style="background:{PCOL[q]}">P{q}</span>{html.escape(LEGEND[q])}</div>' for q in used)
note = "* Hora por confirmar. " if any(e.get("tent") for e in evs) else ""
page = f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="hdr"><div class="t">PARTIDOS DEL DÍA</div><h1>{html.escape(sys.argv[3])}</h1><div class="sub">Hora de Monterrey</div></div>
<div class="legend">{leg}</div>
<div class="how"><b>★ = poner este primero.</b> Es el de mayor prioridad entre los que se empalman. El gerente decide.</div>
{"".join(rows)}
<div class="ftr">{note}Los canales con Firestick se buscan en la app del Firestick. Los horarios pueden cambiar.</div></body></html>"""
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 820, "height": 800}, device_scale_factor=2)
    pg.set_content(page); pg.wait_for_timeout(300); pg.screenshot(path=sys.argv[2], full_page=True); b.close()
print("ok", sys.argv[2])
