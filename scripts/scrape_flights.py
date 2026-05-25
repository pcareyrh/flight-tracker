#!/usr/bin/env python3
"""
Flight price tracker: NTL → MCY (Newcastle NSW → Sunshine Coast QLD)
Outbound: 26 Sep 2026 | Return: 3 Oct 2026

Run this script to fetch current prices and append to data/flights.json and data/flights.csv.
Designed to be invoked by a Claude Code Routine on a daily schedule.
"""

import json
import csv
import os
import sys
from datetime import datetime, timezone

# ── Constants ───────────────────────────────────────────────────────────────
ORIGIN      = "SYD"   # Sydney Airport, NSW
DESTINATION = "MCY"   # Sunshine Coast Airport, QLD
DEPART_DATE = "2026-09-26"
RETURN_DATE = "2026-10-03"
DATA_DIR    = os.path.join(os.path.dirname(__file__), "..", "data")
JSON_FILE   = os.path.join(DATA_DIR, "flights.json")
CSV_FILE    = os.path.join(DATA_DIR, "flights.csv")

# ── Search queries Claude should use ─────────────────────────────────────────
SEARCH_QUERIES = [
    f"Jetstar flights Newcastle to Sunshine Coast 26 September 2026 return 3 October 2026 price",
    f"Virgin Australia flights NTL MCY 26 Sep 2026 return 3 Oct 2026 fare",
    f"Qantas flights Newcastle NSW Sunshine Coast QLD 26 September 2026 return October 3 price",
    f"cheapest flights Newcastle Airport to Sunshine Coast Airport September 26 October 3 2026",
]

CSV_HEADERS = [
    "timestamp", "airline", "flight_out", "depart_out", "arrive_out",
    "flight_return", "depart_return", "arrive_return",
    "cabin", "price_aud", "direct", "source_url", "notes"
]


def load_existing(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


def save_json(records: list[dict], path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(records, f, indent=2)


def save_csv(records: list[dict], path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def build_record(
    airline: str,
    flight_out: str,
    depart_out: str,
    arrive_out: str,
    flight_return: str,
    depart_return: str,
    arrive_return: str,
    cabin: str,
    price_aud: float,
    direct: bool,
    source_url: str,
    notes: str = "",
) -> dict:
    return {
        "timestamp":      datetime.now(timezone.utc).isoformat(),
        "airline":        airline,
        "flight_out":     flight_out,
        "depart_out":     depart_out,
        "arrive_out":     arrive_out,
        "flight_return":  flight_return,
        "depart_return":  depart_return,
        "arrive_return":  arrive_return,
        "cabin":          cabin,
        "price_aud":      price_aud,
        "direct":         direct,
        "source_url":     source_url,
        "notes":          notes,
    }


def append_records(new_records: list[dict]):
    """Load existing data, append new records, save both formats."""
    existing = load_existing(JSON_FILE)
    combined = existing + new_records
    save_json(combined, JSON_FILE)
    save_csv(combined, CSV_FILE)
    print(f"✅ Appended {len(new_records)} record(s). Total: {len(combined)}")


# ── Routine entry point ───────────────────────────────────────────────────────
# Claude Code Routine instructions (Claude reads these when running the script):
ROUTINE_INSTRUCTIONS = """
CLAUDE ROUTINE INSTRUCTIONS
============================
You are running the NTL→MCY flight price tracker.

TASK:
1. Use your web_search tool with the queries listed in SEARCH_QUERIES above.
2. For each result, extract:
   - Airline name
   - Outbound flight number(s), depart/arrive times for 26 Sep 2026
   - Return flight number(s), depart/arrive times for 3 Oct 2026
   - Cabin class (Economy / Business)
   - Total return fare in AUD (both legs combined)
   - Whether flights are direct or have a stopover
   - The booking URL
3. Call append_records() with the structured data.
4. If a price cannot be confirmed with high confidence, set notes="unverified – manual check recommended"
5. After saving, run: python scripts/build_dashboard.py
6. Then commit and push:
     git add data/ dashboard.html
     git commit -m "chore: update flight prices $(date -u +%Y-%m-%dT%H:%M)Z"
     git push origin main

IMPORTANT:
- Search at least 3 sources before saving.
- Record ALL airlines found, not just the cheapest.
- If a route requires a connection (e.g. via Sydney), still record it; set direct=False.
- Do not duplicate records for the same airline/flight/price already in flights.json
  for today's date (compare timestamp date prefix YYYY-MM-DD).
"""

if __name__ == "__main__":
    print(ROUTINE_INSTRUCTIONS)
    print("\nSearch queries to use:")
    for q in SEARCH_QUERIES:
        print(f"  • {q}")
