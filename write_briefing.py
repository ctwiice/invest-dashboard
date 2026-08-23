#!/usr/bin/env python3
"""Write the daily briefing (insights.json) with Claude, in the cloud.

Reads market_data.json (fresh numbers from refresh_data.py) plus the current
insights.json (for continuity), asks Claude Opus 5 to research the day's news
with web search and rewrite the briefing, validates the result, and writes
insights.json back. Runs inside GitHub Actions; needs ANTHROPIC_API_KEY.

Fails loudly (non-zero exit) on any problem so the workflow keeps yesterday's
briefing rather than publishing a broken one. Never writes secrets anywhere.
"""
import json
import os
import re
import sys
from datetime import date, datetime, timezone, timedelta

import anthropic

MODEL = "claude-opus-5"
BRIEFING_KEYS = ["date", "asof", "close_date", "macro", "top_picks", "top_picks_note",
                 "insights", "smart_money", "primer", "macro_strategy", "watchlist_notes", "thesis"]


def load(path):
    with open(path) as f:
        return json.load(f)


def compact_market(md):
    """Trim market_data.json to what the writer needs (numbers, not sparklines)."""
    out = {"fetched_at": md.get("fetched_at"), "sectors": {}, "indices": {},
           "macro_auto": md.get("macro_auto"), "cot": md.get("cot"),
           "treasury10y": {k: v for k, v in (md.get("treasury10y") or {}).items() if k != "spark"}}
    for sector, syms in md.get("sectors", {}).items():
        out["sectors"][sector] = {}
        for s, row in syms.items():
            q, st, pos = row.get("quote") or {}, row.get("stats") or {}, row.get("pos") or {}
            n = lambda k: (st.get(k) or {}).get("n")
            out["sectors"][sector][s] = {
                "price": q.get("p"), "day_pct": q.get("cp"), "asof": q.get("u"),
                "fwd_pe": n("peForward"), "pe": n("pe"), "peg": n("pegRatio"),
                "roe": n("roe"), "de": n("debtEquity"), "ch1y": n("ch1y"),
                "sma200": n("sma200"), "mktcap": (st.get("marketcap") or {}).get("v"),
                "ch30": pos.get("ch30"), "pos30": pos.get("pos30"),
                "vs50": pos.get("vs50"), "ddays": pos.get("ddays"),
                "heavy": pos.get("heavy"), "volRatio": pos.get("volRatio"),
            }
    for name, d in md.get("indices", {}).items():
        out["indices"][name] = {"price": d.get("price"), "day_pct": d.get("chgPct"),
                                "pos": d.get("pos")}
    return out


def build_prompt(market, prev, today):
    return f"""You are the analyst who writes the daily briefing for a private long-term investing dashboard.
Today is {today}. Below are (1) the fresh market data pulled this morning and (2) yesterday's briefing JSON.

Your job: research what actually happened in markets since yesterday's briefing using web search, then
return an UPDATED briefing as a single JSON object with EXACTLY these top-level keys and the same shapes
as yesterday's: {", ".join(BRIEFING_KEYS)}.

Research checklist (use web search; cite real URLs you actually found):
- Latest market session recap (S&P, Nasdaq, what led and lagged, volume character)
- Fed / FOMC developments and the direction of the 10-year Treasury yield
- Goldman Sachs prime brokerage hedge fund flow headlines (search "Goldman Sachs prime brokerage hedge fund flows")
- Hyperscaler AI capex, semiconductor / memory / fiber-optic news, nuclear / uranium / SMR news, space news
- Healthcare policy (drug pricing) and anything moving the Top 3 picks

Ground every claim in the market data provided. The user's core daily questions are: where are prices
relative to their recent ranges, are institutions pulling out (distribution days, volume ratios, COT
week-over-week), and what does the macro regime favor? Use those numbers explicitly.

Rules for the JSON:
- date: the full weekday date for {today}. asof: state the actual last market close date the quotes
  reflect (from the data's asof fields) and note that macro chips come from FRED with a lag.
  close_date: that close date in "Mon D, YYYY" form.
- macro: ONLY the two chips nextCpi and nextFomc (label/value/delta/tone); the rest is automated.
- top_picks: keep the same three tickers unless there is thesis-breaking news or it is the first
  trading day of a new month (then you may rotate). Refresh why_now/risk text with current numbers.
- insights: 5 to 7 cards. ALWAYS include a LIQUIDATION card grounded in the distribution-day and
  volume data. Cover more than AI: healthcare, macro, whatever mattered.
- smart_money: keep 3 to 4 items and ALWAYS include one tagged PRIME BROKERAGE with the latest GS flow
  headlines. Keep the "signal, not a guarantee" framing.
- macro_strategy, primer, top_picks_note, watchlist_notes: update if the facts moved, else carry
  forward with light edits.
- thesis: the Roaring-20s five-battlefields object (objective/constraint/focus, metrics, risks,
  watchlist). Update the metrics values and trends when the facts move (hyperscaler capex guidance,
  power demand, uranium spot, GPU supply tightness, AI-infra credit spreads, 10Y); refresh the
  watchlist with the actual upcoming catalysts; keep risks current. Each metric keeps label/value/
  trend(up|down|flat)/tone(good|warn|bad)/delta/note.
- Every card ends with a practical takeaway for a long-term, buy-and-hold investor referencing tickers
  on the board. Plain English; the reader is not an economist. Not financial advice.
- STYLE: never use em dashes or en dashes anywhere. Use commas, colons, parentheses, or periods.
- Output ONLY the JSON object. No prose before or after it, no code fences.

=== FRESH MARKET DATA ===
{json.dumps(market, separators=(",", ":"))}

=== YESTERDAY'S BRIEFING (for shape and continuity) ===
{json.dumps(prev, separators=(",", ":"))}
"""


def extract_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in model output")
    return json.loads(text[start:end + 1])


def validate(new, prev):
    missing = [k for k in BRIEFING_KEYS if k not in new]
    if missing:
        raise ValueError(f"briefing missing keys: {missing}")
    if not isinstance(new["insights"], list) or not (4 <= len(new["insights"]) <= 8):
        raise ValueError("insights must be a list of 4-8 cards")
    if not any(c.get("tag", "").upper().startswith("LIQUID") for c in new["insights"]):
        raise ValueError("no LIQUIDATION card")
    for c in new["insights"]:
        for k in ("tag", "title", "body", "matters", "sources"):
            if k not in c:
                raise ValueError(f"insight card missing {k}")
    if len(new["top_picks"]) != 3:
        raise ValueError("top_picks must have exactly 3 entries")
    for k in ("nextCpi", "nextFomc"):
        if k not in new["macro"]:
            raise ValueError(f"macro missing {k}")
    blob = json.dumps(new)
    if "—" in blob or "–" in blob:
        raise ValueError("em/en dash found in briefing text")


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set; skipping briefing write", file=sys.stderr)
        sys.exit(2)
    market = compact_market(load("market_data.json"))
    prev = load("insights.json")
    today = datetime.now(timezone(timedelta(hours=-6))).strftime("%A, %B %-d, %Y")

    client = anthropic.Anthropic()
    with client.messages.stream(
        model=MODEL,
        max_tokens=48000,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": 14}],
        messages=[{"role": "user", "content": build_prompt(market, prev, today)}],
    ) as stream:
        resp = stream.get_final_message()

    if resp.stop_reason == "refusal":
        raise SystemExit("model refused; keeping previous briefing")
    text = "".join(b.text for b in resp.content if b.type == "text")
    new = extract_json(text)
    validate(new, prev)

    with open("insights.json", "w") as f:
        json.dump(new, f, indent=2, ensure_ascii=False)
    u = resp.usage
    print(f"briefing written for {new['date']} | tokens in={u.input_tokens} out={u.output_tokens} "
          f"| cards={len(new['insights'])} picks={[p['ticker'] for p in new['top_picks']]}")


if __name__ == "__main__":
    main()
