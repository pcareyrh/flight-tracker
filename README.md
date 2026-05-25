# ✈ NTL → MCY Flight Price Tracker

Automated flight price tracker for:
- **Route:** Newcastle Airport (NTL, NSW) → Sunshine Coast Airport (MCY, QLD)
- **Outbound:** 26 September 2026
- **Return:** 3 October 2026

Prices are tracked daily by a Claude Code Routine and committed to this repo automatically.

---

## 📁 Files

| File | Description |
|---|---|
| `dashboard.html` | Human-readable price dashboard with charts — open in a browser or view via GitHub Pages |
| `data/flights.json` | All recorded price snapshots (append-only) |
| `data/flights.csv` | Same data in CSV format for spreadsheet analysis |
| `scripts/scrape_flights.py` | Claude Routine entry point — contains search logic and data model |
| `scripts/build_dashboard.py` | Generates `dashboard.html` from `data/flights.json` |

---

## 🤖 Claude Code Routine

This repo is updated automatically by a Claude Code Routine configured at [claude.ai/code/routines](https://claude.ai/code/routines).

**Routine name:** `NTL-MCY Flight Tracker`  
**Schedule:** Daily at 08:00 AEST  
**Trigger:** Scheduled

See [ROUTINE_PROMPT.md](ROUTINE_PROMPT.md) for the exact prompt used.

---

## 🌐 Dashboard

Enable GitHub Pages on this repo (Settings → Pages → Deploy from `main`, root `/`) to get a live URL for `dashboard.html`.

---

## 📊 Reading the dashboard

- **Cards** — current best price per airline, with price delta vs previous check (▲ up = more expensive, ▼ down = cheaper)
- **Sparkline** — mini price trend chart per airline
- **History chart** — all airlines on one chart over time
- **Table** — every recorded snapshot with timestamps

---

## 🔧 Manual run

```bash
python3 scripts/scrape_flights.py   # prints Routine instructions
python3 scripts/build_dashboard.py  # regenerates dashboard.html
```
