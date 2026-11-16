"""Rebuild data.json from the NVIDIA Tracking Google Sheet.

Reads two CSV exports of the sheet ('Daily Values' and 'Holdings'), checks them,
and writes data.json only if the closes or holdings changed.

CSV URLs come from environment variables (set them as GitHub repository variables):
  DAILY_CSV_URL     CSV of the 'Daily Values' tab
  HOLDINGS_CSV_URL  CSV of the 'Holdings' tab
If unset, the sheet's export URLs are used (works when the sheet is shared as
"Anyone with the link: Viewer").
"""
import csv
import io
import json
import os
import re
import sys
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

SHEET_ID = "1e50paCsTkIdS9p6XlXTmusQOddYu8wqMEJgWiiOMC_M"
GID_DAILY = "1090873625"
GID_HOLDINGS = "162926829"
EXPORT = "https://docs.google.com/spreadsheets/d/{id}/export?format=csv&gid={gid}"

DAILY_URL = os.environ.get("DAILY_CSV_URL") or EXPORT.format(id=SHEET_ID, gid=GID_DAILY)
HOLD_URL = os.environ.get("HOLDINGS_CSV_URL") or EXPORT.format(id=SHEET_ID, gid=GID_HOLDINGS)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data.json")

# Sheet layout (1-based rows, as in the workbook)
DAILY_FIRST, DAILY_LAST = 8, None       # 'Daily Values'!A8:B (all rows from 8 down)
HOLD_FIRST, HOLD_LAST = 9, 34           # Holdings!A9:P34


def fetch_csv(url):
    req = urllib.request.Request(url, headers={"User-Agent": "nvda-tracker-sync"})
    with urllib.request.urlopen(req, timeout=60) as r:
        text = r.read().decode("utf-8-sig")
    if text.lstrip().startswith("<"):
        sys.exit(f"Got HTML instead of CSV from {url}. Is the sheet shared or published to the web?")
    return list(csv.reader(io.StringIO(text)))


def trim(row):
    row = [c.strip() for c in row]
    while row and row[-1] == "":
        row.pop()
    return row


def num(s):
    s = s.replace("$", "").replace(",", "").strip()
    return float(s) if re.fullmatch(r"-?\d*\.?\d+", s) else None


def main():
    daily_rows = fetch_csv(DAILY_URL)
    hold_rows = fetch_csv(HOLD_URL)

    daily = []
    for row in daily_rows[DAILY_FIRST - 1:DAILY_LAST]:
        row = trim(row[:2])
        if row:
            daily.append(row)
    holdings = [trim(r[:16]) for r in hold_rows[HOLD_FIRST - 1:HOLD_LAST]]

    # ---- checks: stop (no write) if anything looks wrong ----
    if not re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", daily[0][0] if daily and daily[0] else ""):
        sys.exit(f"Unexpected first date cell in Daily Values: {daily[:1]}")
    closes = [num(r[1]) if len(r) > 1 else None for r in daily]
    filled = [c for c in closes if c is not None]
    if len(filled) < 200:
        sys.exit(f"Only {len(filled)} closes found; expected 200+.")
    last_i = max(i for i, c in enumerate(closes) if c is not None)
    gaps = [daily[i][0] for i in range(last_i) if closes[i] is None]
    if gaps:
        print(f"Note: blank closes before the latest date (holidays?): {gaps}")
    if any(not (20 <= c <= 2000) for c in filled):
        sys.exit("A close is outside the 20-2000 range.")
    fund_rows = [r for r in holdings if len(r) >= 6 and re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", r[4])]
    if len(fund_rows) < 20:
        sys.exit(f"Only {len(fund_rows)} fund rows found on Holdings; expected 25.")

    old = {}
    if os.path.exists(OUT):
        with open(OUT) as f:
            old = json.load(f)
    if old.get("daily") == daily and old.get("holdings") == holdings:
        print("No change in closes or holdings; data.json left as is.")
        return

    now = datetime.now(ZoneInfo("America/New_York"))
    out = {
        "updated_at": now.isoformat(timespec="seconds"),
        "updated_note": f"Synced from the Google Sheet; closes through {daily[last_i][0]}",
        "sheet_id": SHEET_ID,
        "daily": daily,
        "holdings": holdings,
    }
    with open(OUT, "w") as f:
        json.dump(out, f, indent=0)
    print(f"data.json updated: closes through {daily[last_i][0]} ({daily[last_i][1]}), {len(fund_rows)} funds.")


if __name__ == "__main__":
    main()
