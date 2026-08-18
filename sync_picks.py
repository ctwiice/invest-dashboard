#!/usr/bin/env python3
"""Keep quant.py's PICKS dict in sync with insights.json's Top 3 tickers.
ETFs (present in refresh_data's INDEX_ETFS) get kind 'e', stocks 's'."""
import json, re
ins = json.load(open("insights.json"))
tickers = [p["ticker"] for p in ins.get("top_picks", [])][:3]
src = open("refresh_data.py").read()
etfs = set(re.findall(r'\("([A-Z]+)",\s*"e"\)', src))
picks = {t: ("e" if t in etfs else "s") for t in tickers}
q = open("quant.py").read()
new = re.sub(r'PICKS = \{[^}]*\}', "PICKS = " + json.dumps(picks).replace('"', '"'), q, count=1)
open("quant.py", "w").write(new)
print("PICKS ->", picks)
