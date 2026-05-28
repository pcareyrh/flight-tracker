#!/usr/bin/env python3
"""
Build dashboard.html from data/flights.json
Run after each scrape: python scripts/build_dashboard.py
"""

import json
import os
from datetime import datetime, timezone
from collections import defaultdict

BASE_DIR   = os.path.join(os.path.dirname(__file__), "..")
JSON_FILE  = os.path.join(BASE_DIR, "data", "flights.json")
OUT_FILE   = os.path.join(BASE_DIR, "dashboard.html")

AIRLINE_COLORS = {
    "Jetstar":          "#ff6900",
    "Virgin Australia": "#e4002b",
    "Qantas":           "#e40000",
    "Rex":              "#005baa",
}
DEFAULT_COLOR = "#555"


def load() -> list[dict]:
    if not os.path.exists(JSON_FILE):
        return []
    with open(JSON_FILE) as f:
        return json.load(f)


def airline_color(name: str) -> str:
    for k, v in AIRLINE_COLORS.items():
        if k.lower() in name.lower():
            return v
    return DEFAULT_COLOR


def build_price_history(records: list[dict]) -> dict:
    """Return {airline: [(date, price), ...]} sorted by date."""
    by_airline: dict[str, list] = defaultdict(list)
    for r in records:
        date = r["timestamp"][:10]
        by_airline[r["airline"]].append((date, r["price_aud"]))
    # Keep only the lowest price per airline per day
    result = {}
    for airline, pairs in by_airline.items():
        daily: dict[str, float] = {}
        for date, price in pairs:
            if date not in daily or price < daily[date]:
                daily[date] = price
        result[airline] = sorted(daily.items())
    return result


def latest_per_airline(records: list[dict]) -> list[dict]:
    """Return the most recent record per airline (lowest price if tie)."""
    best: dict[str, dict] = {}
    for r in records:
        a = r["airline"]
        if a not in best:
            best[a] = r
        else:
            if r["timestamp"] > best[a]["timestamp"]:
                best[a] = r
            elif r["timestamp"] == best[a]["timestamp"] and r["price_aud"] < best[a]["price_aud"]:
                best[a] = r
    return sorted(best.values(), key=lambda x: x["price_aud"])


def price_delta(history: list[tuple]) -> str:
    """Return formatted delta between last two data points."""
    if len(history) < 2:
        return ""
    prev = history[-2][1]
    curr = history[-1][1]
    diff = curr - prev
    if diff > 0:
        return f'<span class="delta up">▲ ${diff:.0f}</span>'
    elif diff < 0:
        return f'<span class="delta down">▼ ${abs(diff):.0f}</span>'
    return '<span class="delta flat">— no change</span>'


def chart_sparkline(history: list[tuple], color: str) -> str:
    """SVG sparkline for price history."""
    if len(history) < 2:
        return "<span class='no-history'>Not enough data yet</span>"
    prices = [p for _, p in history]
    mn, mx = min(prices), max(prices)
    w, h = 200, 50
    pad = 4
    rng = (mx - mn) or 1
    pts = []
    for i, p in enumerate(prices):
        x = pad + (i / (len(prices) - 1)) * (w - 2 * pad)
        y = h - pad - ((p - mn) / rng) * (h - 2 * pad)
        pts.append(f"{x:.1f},{y:.1f}")
    return (
        f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" class="sparkline">'
        f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="2.5" stroke-linejoin="round"/>'
        f'<circle cx="{pts[-1].split(",")[0]}" cy="{pts[-1].split(",")[1]}" r="3.5" fill="{color}"/>'
        f"</svg>"
    )


def js_chart_data(history_map: dict) -> str:
    datasets = []
    all_dates = sorted({d for pts in history_map.values() for d, _ in pts})
    for airline, pts in history_map.items():
        price_by_date = dict(pts)
        color = airline_color(airline)
        data_vals = [price_by_date.get(d, "null") for d in all_dates]
        datasets.append({
            "label": airline,
            "data": data_vals,
            "borderColor": color,
            "backgroundColor": color + "22",
            "tension": 0.3,
            "pointRadius": 4,
        })
    return json.dumps({"labels": all_dates, "datasets": datasets})


def render(records: list[dict]) -> str:
    generated = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")
    history   = build_price_history(records)
    latest    = latest_per_airline(records)
    chart_data = js_chart_data(history)
    total_snapshots = len(records)

    # ── Cards ───────────────────────────────────────────────────────────────
    cards_html = ""
    for r in latest:
        color = airline_color(r["airline"])
        hist  = history.get(r["airline"], [])
        delta = price_delta(hist)
        spark = chart_sparkline(hist, color)
        direct_badge = (
            '<span class="badge direct">Direct</span>'
            if r.get("direct")
            else '<span class="badge stop">Via stopover</span>'
        )
        unverified = ""
        if "unverified" in (r.get("notes") or ""):
            unverified = '<p class="unverified">⚠ Unverified – manual check recommended</p>'
        cards_html += f"""
        <div class="card" style="--accent:{color}">
          <div class="card-header">
            <span class="airline-name">{r["airline"]}</span>
            {direct_badge}
          </div>
          <div class="price-row">
            <span class="price">${r["price_aud"]:.0f}</span>
            <span class="currency">AUD return</span>
            {delta}
          </div>
          <div class="legs">
            <div class="leg">
              <span class="leg-label">OUT 26 Sep</span>
              <span class="leg-info">{r.get("flight_out","—")} · {r.get("depart_out","—")} → {r.get("arrive_out","—")}</span>
            </div>
            <div class="leg">
              <span class="leg-label">RET 3 Oct</span>
              <span class="leg-info">{r.get("flight_return","—")} · {r.get("depart_return","—")} → {r.get("arrive_return","—")}</span>
            </div>
          </div>
          <div class="spark-row">{spark}</div>
          {unverified}
          <a class="book-btn" href="{r.get("source_url","#")}" target="_blank" rel="noopener">View fare →</a>
        </div>"""

    # ── Full history table ───────────────────────────────────────────────────
    rows_html = ""
    for r in sorted(records, key=lambda x: x["timestamp"], reverse=True):
        color = airline_color(r["airline"])
        rows_html += f"""
        <tr>
          <td>{r["timestamp"][:16].replace("T"," ")}</td>
          <td style="color:{color};font-weight:600">{r["airline"]}</td>
          <td>{r.get("flight_out","—")}</td>
          <td>{r.get("depart_out","—")} → {r.get("arrive_out","—")}</td>
          <td>{r.get("flight_return","—")}</td>
          <td>{r.get("depart_return","—")} → {r.get("arrive_return","—")}</td>
          <td>{"✈ Direct" if r.get("direct") else "⤳ Stop"}</td>
          <td class="price-cell">${r.get("price_aud",0):.0f}</td>
          <td><a href="{r.get("source_url","#")}" target="_blank">Link</a></td>
        </tr>"""

    if not rows_html:
        rows_html = '<tr><td colspan="9" style="text-align:center;opacity:.5">No data yet — run the routine to populate.</td></tr>'

    no_data_note = "" if records else '<p class="no-data">No flight data yet. The routine will populate this dashboard on its first run.</p>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>✈ SYD → MCY Flight Tracker</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Sora:wght@300;600;700&display=swap');

  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  :root {{
    --bg:        #0d0f14;
    --surface:   #161920;
    --border:    #252830;
    --text:      #e8eaf0;
    --muted:     #6b7280;
    --green:     #22c55e;
    --red:       #ef4444;
    --yellow:    #f59e0b;
  }}

  body {{
    font-family: 'Sora', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    padding: 2rem 1rem 4rem;
  }}

  /* ── Header ── */
  .site-header {{
    text-align: center;
    padding: 3rem 0 2.5rem;
  }}
  .route-pill {{
    display: inline-block;
    font-family: 'DM Mono', monospace;
    font-size: .8rem;
    letter-spacing: .15em;
    text-transform: uppercase;
    background: var(--border);
    border: 1px solid #2e323d;
    padding: .35rem 1rem;
    border-radius: 999px;
    color: var(--muted);
    margin-bottom: 1rem;
  }}
  h1 {{
    font-size: clamp(2rem, 5vw, 3.5rem);
    font-weight: 700;
    line-height: 1.1;
    letter-spacing: -.02em;
  }}
  h1 span {{ color: var(--muted); }}
  .sub {{
    margin-top: .75rem;
    font-size: .9rem;
    color: var(--muted);
    font-weight: 300;
  }}
  .meta-bar {{
    display: flex;
    justify-content: center;
    gap: 2rem;
    margin-top: 1.5rem;
    font-family: 'DM Mono', monospace;
    font-size: .75rem;
    color: var(--muted);
  }}
  .meta-bar span b {{ color: var(--text); }}

  /* ── Cards grid ── */
  .cards {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1.25rem;
    max-width: 1100px;
    margin: 2.5rem auto 0;
  }}
  .card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-top: 3px solid var(--accent);
    border-radius: 12px;
    padding: 1.4rem;
    display: flex;
    flex-direction: column;
    gap: .85rem;
    transition: transform .15s, box-shadow .15s;
  }}
  .card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 12px 32px rgba(0,0,0,.4);
  }}
  .card-header {{
    display: flex;
    align-items: center;
    gap: .6rem;
  }}
  .airline-name {{
    font-weight: 600;
    font-size: 1rem;
  }}
  .badge {{
    font-family: 'DM Mono', monospace;
    font-size: .65rem;
    padding: .2rem .5rem;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: .06em;
  }}
  .badge.direct {{ background: rgba(34,197,94,.15); color: var(--green); }}
  .badge.stop   {{ background: rgba(245,158,11,.12); color: var(--yellow); }}

  .price-row {{
    display: flex;
    align-items: baseline;
    gap: .5rem;
    flex-wrap: wrap;
  }}
  .price {{
    font-family: 'DM Mono', monospace;
    font-size: 2.4rem;
    font-weight: 500;
    color: var(--accent);
    line-height: 1;
  }}
  .currency {{
    font-size: .75rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: .06em;
  }}
  .delta {{ font-family: 'DM Mono', monospace; font-size: .8rem; margin-left: auto; }}
  .delta.up   {{ color: var(--red); }}
  .delta.down {{ color: var(--green); }}
  .delta.flat {{ color: var(--muted); }}

  .legs {{ display: flex; flex-direction: column; gap: .4rem; }}
  .leg  {{ display: flex; gap: .5rem; font-size: .8rem; }}
  .leg-label {{
    font-family: 'DM Mono', monospace;
    font-size: .7rem;
    background: var(--border);
    padding: .15rem .45rem;
    border-radius: 4px;
    color: var(--muted);
    white-space: nowrap;
  }}
  .leg-info {{ color: var(--text); opacity: .85; }}

  .spark-row {{ overflow-x: auto; }}
  .sparkline  {{ display: block; }}
  .no-history {{ font-size: .75rem; color: var(--muted); font-style: italic; }}

  .unverified {{ font-size: .75rem; color: var(--yellow); }}

  .book-btn {{
    display: inline-block;
    text-align: center;
    background: var(--accent);
    color: #fff;
    font-size: .8rem;
    font-weight: 600;
    padding: .55rem 1rem;
    border-radius: 8px;
    text-decoration: none;
    transition: opacity .15s;
    margin-top: auto;
  }}
  .book-btn:hover {{ opacity: .85; }}

  /* ── Chart ── */
  .chart-wrap {{
    max-width: 900px;
    margin: 3rem auto 0;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.75rem;
  }}
  .section-title {{
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 1.25rem;
    letter-spacing: -.01em;
  }}
  .section-title span {{ color: var(--muted); font-weight: 300; }}
  canvas {{ max-width: 100%; }}

  /* ── Table ── */
  .table-wrap {{
    max-width: 1100px;
    margin: 2.5rem auto 0;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
  }}
  .table-header {{
    padding: 1.2rem 1.5rem;
    border-bottom: 1px solid var(--border);
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: .82rem;
  }}
  th {{
    text-align: left;
    font-family: 'DM Mono', monospace;
    font-size: .7rem;
    letter-spacing: .08em;
    text-transform: uppercase;
    color: var(--muted);
    padding: .7rem 1rem;
    border-bottom: 1px solid var(--border);
    background: var(--bg);
  }}
  td {{
    padding: .7rem 1rem;
    border-bottom: 1px solid var(--border);
    color: var(--text);
  }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: rgba(255,255,255,.02); }}
  td a {{ color: var(--muted); text-decoration: underline; }}
  .price-cell {{
    font-family: 'DM Mono', monospace;
    font-weight: 500;
    font-size: .95rem;
  }}

  .no-data {{
    text-align: center;
    padding: 3rem;
    color: var(--muted);
    font-style: italic;
  }}

  footer {{
    text-align: center;
    padding: 3rem 0 0;
    font-size: .75rem;
    color: var(--muted);
    font-family: 'DM Mono', monospace;
  }}
</style>
</head>
<body>

<header class="site-header">
  <div class="route-pill">Sydney NSW &nbsp;✈&nbsp; Sunshine Coast QLD</div>
  <h1>Flight Price <span>Tracker</span></h1>
  <p class="sub">Outbound 26 Sep 2026 &nbsp;·&nbsp; Return 3 Oct 2026</p>
  <div class="meta-bar">
    <span>Updated <b>{generated}</b></span>
    <span>Snapshots <b>{total_snapshots}</b></span>
  </div>
</header>

{no_data_note}

<section class="cards" aria-label="Latest prices by airline">
  {cards_html or '<p class="no-data">No data yet.</p>'}
</section>

<div class="chart-wrap">
  <p class="section-title">Price history <span>— all airlines, lowest daily fare</span></p>
  <canvas id="priceChart" height="300"></canvas>
</div>

<div class="table-wrap">
  <div class="table-header">
    <p class="section-title">All recorded snapshots</p>
  </div>
  <table>
    <thead>
      <tr>
        <th>Timestamp (UTC)</th>
        <th>Airline</th>
        <th>Out Flight</th>
        <th>Outbound</th>
        <th>Ret Flight</th>
        <th>Return</th>
        <th>Type</th>
        <th>Price AUD</th>
        <th>Booking</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
</div>

<footer>
  <p>Auto-generated by Claude Code Routine · SYD→MCY tracker · data in <code>data/flights.json</code> &amp; <code>data/flights.csv</code></p>
</footer>

<script>
const chartData = {chart_data};
if (chartData.labels.length > 0) {{
  const ctx = document.getElementById('priceChart').getContext('2d');
  new Chart(ctx, {{
    type: 'line',
    data: chartData,
    options: {{
      responsive: true,
      interaction: {{ mode: 'index', intersect: false }},
      plugins: {{
        legend: {{
          labels: {{
            color: '#9ca3af',
            font: {{ family: 'DM Mono', size: 11 }},
            boxWidth: 12,
          }}
        }},
        tooltip: {{
          backgroundColor: '#161920',
          borderColor: '#252830',
          borderWidth: 1,
          titleColor: '#e8eaf0',
          bodyColor: '#9ca3af',
          callbacks: {{
            label: ctx => ` ${{ctx.dataset.label}}: $AUD ${{ctx.parsed.y}}`
          }}
        }}
      }},
      scales: {{
        x: {{
          ticks: {{ color: '#6b7280', font: {{ family: 'DM Mono', size: 10 }} }},
          grid:  {{ color: '#1f2229' }},
        }},
        y: {{
          ticks: {{
            color: '#6b7280',
            font: {{ family: 'DM Mono', size: 10 }},
            callback: v => '$' + v
          }},
          grid: {{ color: '#1f2229' }},
        }}
      }}
    }}
  }});
}} else {{
  document.getElementById('priceChart').parentElement.insertAdjacentHTML(
    'beforeend',
    '<p style="text-align:center;color:#6b7280;padding:2rem;font-style:italic">Chart will appear after the first routine run.</p>'
  );
  document.getElementById('priceChart').remove();
}}
</script>
</body>
</html>"""


if __name__ == "__main__":
    records = load()
    html = render(records)
    with open(OUT_FILE, "w") as f:
        f.write(html)
    print(f"✅ Dashboard written to {OUT_FILE}  ({len(records)} records)")
