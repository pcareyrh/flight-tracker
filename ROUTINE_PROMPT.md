# Claude Code Routine Prompt

Copy the text below (everything inside the triple backticks) and paste it as the prompt when creating a new Routine at https://claude.ai/code/routines

---

```
You are running the NTL→MCY flight price tracker for the GitHub repository pcareyrh/flight-tracker.

ROUTE:
  Origin:      Newcastle Airport, NSW, Australia (NTL / IATA: NTL)
  Destination: Sunshine Coast Airport, QLD, Australia (MCY / IATA: MCY)
  Outbound:    26 September 2026
  Return:      3 October 2026

YOUR TASK:
1. Use web search to find current return flight prices for the above route and dates.
   Search for each of these queries in turn:
     - "Jetstar flights Newcastle to Sunshine Coast 26 September 2026 return 3 October 2026 price"
     - "Virgin Australia flights NTL MCY 26 Sep 2026 return 3 Oct 2026 fare"
     - "Qantas flights Newcastle NSW Sunshine Coast QLD 26 September 2026 return October 3 2026 price"
     - "cheapest flights Newcastle Airport to Sunshine Coast Airport 26 September 3 October 2026"
     - site:webjet.com.au OR site:skyscanner.com.au Newcastle Sunshine Coast Sep 26 Oct 3 2026

2. For each flight option found, extract:
   - Airline name
   - Outbound flight number(s) and departure/arrival times for 26 Sep 2026
   - Return flight number(s) and departure/arrival times for 3 Oct 2026
   - Cabin class (Economy / Business)
   - Total return fare in AUD (both legs combined — if only one-way prices shown, add them)
   - Whether flights are direct (no stops) or have a connection
   - The booking/source URL

3. Load the existing data:
   cat data/flights.json

4. Check today's date (UTC). Do NOT add duplicate records for an airline if you already recorded
   a price for that airline today (compare the "timestamp" field, first 10 chars YYYY-MM-DD).

5. Append new records by running:
   python3 scripts/scrape_flights.py
   
   Then directly edit data/flights.json to append the new records in this format:
   {
     "timestamp": "<ISO8601 UTC timestamp>",
     "airline": "<Airline name>",
     "flight_out": "<e.g. JQ123>",
     "depart_out": "<e.g. 07:30>",
     "arrive_out": "<e.g. 09:05>",
     "flight_return": "<e.g. JQ456>",
     "depart_return": "<e.g. 14:00>",
     "arrive_return": "<e.g. 15:45>",
     "cabin": "Economy",
     "price_aud": <number, no quotes>,
     "direct": <true or false>,
     "source_url": "<booking URL>",
     "notes": "<any caveats, or empty string>"
   }
   
   If a price cannot be confirmed with confidence, set notes to "unverified – manual check recommended".
   If the route requires a connection (e.g. via Sydney), still record it and set direct to false.
   Record ALL airlines found, not just the cheapest.

6. Regenerate the dashboard:
   python3 scripts/build_dashboard.py

7. Commit and push:
   git add data/flights.json data/flights.csv dashboard.html
   git commit -m "chore: flight price update $(date -u +%Y-%m-%dT%H:%M)Z"
   git push origin main

IMPORTANT RULES:
- Search at least 3 different sources before writing data.
- Be conservative: if you cannot find a confirmed price, note it as unverified rather than guessing.
- If a route is not currently bookable (too far out, no availability shown), record what you find and note it.
- The script data/flights.json must remain valid JSON at all times.
```

---

## Routine settings

| Setting | Value |
|---|---|
| **Name** | NTL-MCY Flight Tracker |
| **Repository** | `pcareyrh/flight-tracker` |
| **Schedule** | Daily — 08:00 AEST (22:00 UTC previous day) |
| **Connectors** | Web search (enable in Routine settings) |
| **Branch** | `main` |

## Steps to create the Routine

1. Go to [claude.ai/code/routines](https://claude.ai/code/routines)
2. Click **New routine**
3. Paste the prompt above
4. Select repo: `pcareyrh/flight-tracker`
5. Set schedule: **Daily** at your preferred time
6. Enable **Web search** connector
7. Save — it will run on next scheduled trigger
