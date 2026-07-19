#!/usr/bin/env python3
"""Fetch quote+stats+spark+positioning for specific tickers and merge them into
an existing market_data.json sector. Usage: python3 fetch_one.py SECTOR T1 T2..."""
import json, sys, time

# reuse the fetch helpers without running the full module pipeline
import importlib.util
spec = importlib.util.spec_from_file_location("rd", "refresh_data.py")


def helpers():
    src = open("refresh_data.py").read()
    cut = src.index('out = {"fetched_at"')
    ns = {}
    exec(src[:cut], ns)
    return ns


ns = helpers()
sector, tickers = sys.argv[1], sys.argv[2:]
data = json.load(open("market_data.json"))
data["sectors"].setdefault(sector, {})
for s in tickers:
    row = {}
    for key, fn in [("quote", lambda: ns["get_quote"](s)),
                    ("stats", lambda: ns["get_stats"](s)),
                    ("spark", lambda: ns["weekly_closes"](s)),
                    ("pos", lambda: ns["positioning"](s))]:
        try:
            row[key] = fn()
        except Exception as e:
            print(f"{key} {s} FAILED: {e}", file=sys.stderr)
        time.sleep(0.4)
    data["sectors"][sector][s] = row
    print(f"done {s}", file=sys.stderr)
json.dump(data, open("market_data.json", "w"))
print("MERGED")
