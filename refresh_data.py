#!/usr/bin/env python3
"""Refresh market data for the AI Infrastructure & Nuclear dashboard.

Pulls quotes, fundamentals, and 1Y weekly sparklines for the watchlist from
stockanalysis.com public endpoints (no auth). Writes market_data.json.
Run from this directory: python3 refresh_data.py
"""
import json, time, subprocess, sys

UA_STR = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"

# Two boards, same columns: Sheet 1 = established large-dollar names,
# Sheet 2 = smaller-dollar / speculative. SK Hynix is Seoul-listed (000660.KS)
# with no usable US data feed; MU/SNDK/WDC plus SOXX carry the memory theme.
WATCHLIST = {
    # ---- Sheet 1: established ----
    "Semiconductors & Fab": ["NVDA", "AMD", "AVGO", "TSM", "ASML", "INTC"],
    "Memory & Storage": ["MU", "SNDK", "WDC"],
    "Servers, Cooling & Networking": ["SMCI", "DELL", "VRT", "ANET"],
    "Fiber Optics & Photonics": ["COHR", "LITE", "CIEN", "GLW"],
    "Electrical, Conduit & Steel": ["ETN", "PWR", "ATKR", "WCC", "HUBB", "NUE"],
    "Nuclear & Power Majors": ["CEG", "VST", "CCJ", "BWXT", "GEV"],
    "Big Tech & Hyperscalers": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "ORCL", "IBM", "PLTR"],
    "Healthcare & Pharma": ["LLY", "NVO", "UNH", "JNJ", "ABBV", "MRK"],
    # ---- Sheet 2: smaller-dollar / speculative ----
    "Nuclear Developers & Fuel": ["OKLO", "SMR", "LEU", "NNE"],
    "Quantum Pure-Plays": ["IONQ", "RGTI", "QBTS", "QUBT"],
    "Space & Defense": ["RKLB", "LUNR", "ASTS"],
    "Gov-Backed Materials & Small AI Infra": ["MP", "LAC", "TSSI"],
}
# ETFs get the quote + sparkline + positioning treatment (no per-share fundamentals;
# stockanalysis serves ETF stats under a different path). Broad + sector + thematic
# so a diversified, lower-single-name-risk investor can shop the whole field.
INDEX_ETFS = {
    "SPY (S&P 500)": ("SPY", "e"),
    "VOO (S&P 500)": ("VOO", "e"),
    "VTI (Total US Market)": ("VTI", "e"),
    "QQQ (Nasdaq 100)": ("QQQ", "e"),
    "QQQM (Nasdaq 100, low fee)": ("QQQM", "e"),
    "SCHD (Dividend Value)": ("SCHD", "e"),
    "VGT (US Technology)": ("VGT", "e"),
    "SMH (Semiconductors)": ("SMH", "e"),
    "SOXX (iShares Semis)": ("SOXX", "e"),
    "ARTY (iShares AI & Tech)": ("ARTY", "e"),
    "ITA (iShares Defense)": ("ITA", "e"),
    "XLV (Healthcare)": ("XLV", "e"),
    "URA (Uranium & Nuclear)": ("URA", "e"),
    "NLR (Uranium+Nuclear, VanEck)": ("NLR", "e"),
    "IGF (Global Infrastructure)": ("IGF", "e"),
    "QTUM (Quantum & Computing)": ("QTUM", "e"),
    "WQTM (Quantum Computing)": ("WQTM", "e"),
    "BOTZ (Robotics & AI)": ("BOTZ", "e"),
    "UFO (Space)": ("UFO", "e"),
    "SEMI (Semiconductor & Tech)": ("SEMI", "e"),
    "VXUS (International ex-US)": ("VXUS", "e"),
}

def get(url):
    out = subprocess.run(["curl", "-s", "--max-time", "20", "-A", UA_STR, url],
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)

def resolve(flat, idx, depth=0):
    if depth > 14 or not isinstance(idx, int) or idx < 0 or idx >= len(flat):
        return None
    v = flat[idx]
    if isinstance(v, dict):
        return {k: resolve(flat, i, depth + 1) for k, i in v.items()}
    if isinstance(v, list):
        return [resolve(flat, i, depth + 1) for i in v]
    return v

def num(s):
    if s is None: return None
    t = str(s).replace(",", "").replace("%", "").replace("$", "").strip()
    if t in ("", "n/a", "-"): return None
    try: return float(t)
    except ValueError: return None

def get_stats(sym):
    """Flatten stockanalysis statistics page (SvelteKit __data.json) by metric id."""
    d = get(f"https://stockanalysis.com/stocks/{sym}/statistics/__data.json")
    for node in d.get("nodes", []):
        if not node or node.get("type") != "data":
            continue
        flat = node["data"]
        for i, item in enumerate(flat):
            if isinstance(item, dict) and "ratios" in item and "valuation" in item:
                root = resolve(flat, i)
                out = {}
                for sec in root.values():
                    if isinstance(sec, dict) and isinstance(sec.get("data"), list):
                        for m in sec["data"]:
                            if isinstance(m, dict) and m.get("id"):
                                out[m["id"]] = {"v": m.get("value"),
                                                "n": num(m.get("hover", m.get("value")))}
                return out
    return {}

def weekly_closes(sym, kind="s"):
    d = get(f"https://stockanalysis.com/api/symbol/{kind}/{sym}/history?range=1Y&period=Weekly")
    rows = sorted(d.get("data", []), key=lambda r: r["t"])
    return [round(r["c"], 2) for r in rows]

def positioning(sym, kind="s"):
    """WHERE the price is, not just what it is: 30-day range position, distance
    from the 50-day average, and volume-confirmed selling (distribution days)."""
    d = get(f"https://stockanalysis.com/api/symbol/{kind}/{sym}/history?range=6M&period=Daily")
    rows = sorted(d.get("data", []), key=lambda r: r["t"])
    if len(rows) < 25:
        return {}
    closes = [r["c"] for r in rows]
    vols = [r.get("v") or 0 for r in rows]
    chs = [r.get("ch") for r in rows]
    p = closes[-1]
    last21 = closes[-21:]                       # ~30 calendar days of sessions
    hi30, lo30 = max(last21), min(last21)
    pos30 = 50.0 if hi30 == lo30 else (p - lo30) / (hi30 - lo30) * 100
    ch30 = (p / closes[-22] - 1) * 100 if len(closes) >= 22 else None
    sma50 = sum(closes[-50:]) / min(50, len(closes))
    vs50 = (p / sma50 - 1) * 100
    # distribution days: down >=0.2% on volume above the prior 20-day average,
    # counted over the last 25 sessions (classic institutional-selling gauge)
    ddays, heavy = 0, 0
    for i in range(max(21, len(rows) - 25), len(rows)):
        avg20 = sum(vols[i - 20:i]) / 20
        if not avg20 or chs[i] is None:
            continue
        if chs[i] <= -0.2 and vols[i] > avg20:
            ddays += 1
        if i >= len(rows) - 5 and chs[i] <= -1.5 and vols[i] >= 1.5 * avg20:
            heavy += 1                          # heavy liquidation, last 5 sessions
    avg20 = sum(vols[-21:-1]) / 20 if len(vols) >= 21 else None
    vr = round(vols[-1] / avg20, 2) if avg20 else None
    return {"pos30": round(pos30), "hi30": round(hi30, 2), "lo30": round(lo30, 2),
            "ch30": round(ch30, 2) if ch30 is not None else None,
            "vs50": round(vs50, 2), "ddays": ddays, "heavy": heavy, "volRatio": vr}

def fred_series(series_id):
    """Full (date, value) history for a FRED series, no auth needed."""
    out = subprocess.run(["curl", "-s", "--max-time", "20",
                          f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"],
                         capture_output=True, text=True, check=True)
    rows = [l.split(",") for l in out.stdout.strip().splitlines()[1:]]
    return [(d, float(v)) for d, v in rows if len(rows) and v not in (".", "")]

def treasury_10y():
    rows = fred_series("DGS10")
    last45 = rows[-45:]
    return {"date": last45[-1][0], "value": last45[-1][1],
            "prev30": last45[-22][1] if len(last45) >= 22 else None,
            "spark": [v for _, v in last45]}

def macro_auto():
    """The macro command strip, fully automated from FRED.

    Daily series report latest + ~30-days-ago; monthly CPI series report YoY
    computed against the value 12 months earlier."""
    m = {}
    def daily(sid, take=45):
        rows = fred_series(sid)[-take:]
        return {"date": rows[-1][0], "value": rows[-1][1],
                "prev30": rows[-22][1] if len(rows) >= 22 else None,
                "spark": [v for _, v in rows]}
    def yoy(sid):
        rows = fred_series(sid)
        cur_d, cur_v = rows[-1]
        base = next((v for d, v in rows if d[:7] == f"{int(cur_d[:4])-1:04d}-{cur_d[5:7]}"), None)
        prev_d, prev_v = rows[-2]
        prev_base = next((v for d, v in rows if d[:7] == f"{int(prev_d[:4])-1:04d}-{prev_d[5:7]}"), None)
        return {"date": cur_d,
                "yoy": round((cur_v / base - 1) * 100, 1) if base else None,
                "prev_yoy": round((prev_v / prev_base - 1) * 100, 1) if prev_base else None}
    for key, sid, kind in [("cpi", "CPIAUCSL", "yoy"), ("core_cpi", "CPILFESL", "yoy"),
                           ("fedfunds", "FEDFUNDS", "daily"), ("t2y", "DGS2", "daily"),
                           ("vix", "VIXCLS", "daily"), ("unemployment", "UNRATE", "daily"),
                           ("wti", "DCOILWTICO", "daily")]:
        try:
            m[key] = yoy(sid) if kind == "yoy" else daily(sid)
        except Exception as e:
            print(f"macro {key} FAILED: {e}", file=sys.stderr)
        time.sleep(0.3)
    return m

# CFTC Traders in Financial Futures (weekly, futures-only). Field layout after
# the quoted market name: [1]yymmdd [2]date ... [7]open interest, then
# long/short/spread for Dealer(8-10), Asset Manager(11-13), Leveraged(14-16),
# Other(17-19); [25..36] are the week-over-week changes for the same 12 fields.
COT_CONTRACTS = {
    "E-MINI S&P 500 ": "S&P 500 e-mini",
    "NASDAQ MINI ": "Nasdaq-100 e-mini",
    "UST 10Y NOTE ": "10Y Treasury note",
    "VIX FUTURES ": "VIX futures",
}

def cot_positioning():
    out = subprocess.run(["curl", "-s", "--max-time", "30",
                          "https://www.cftc.gov/dea/newcot/FinFutWk.txt"],
                         capture_output=True, text=True, check=True)
    import csv, io
    res = {}
    for row in csv.reader(io.StringIO(out.stdout)):
        if not row or len(row) < 37:
            continue
        name = row[0].strip()
        label = next((v for k, v in COT_CONTRACTS.items() if name.startswith(k)), None)
        if not label or label in res:
            continue
        f = [x.strip() for x in row]
        def num_at(i):
            try: return int(f[i].replace(",", ""))
            except (ValueError, IndexError): return None
        oi = num_at(7)
        am_net = (num_at(11) or 0) - (num_at(12) or 0)
        lev_net = (num_at(14) or 0) - (num_at(15) or 0)
        d_am = (num_at(25 + 3) or 0) - (num_at(25 + 4) or 0)
        d_lev = (num_at(25 + 6) or 0) - (num_at(25 + 7) or 0)
        res[label] = {"date": f[2], "oi": oi, "am_net": am_net, "lev_net": lev_net,
                      "am_wow": d_am, "lev_wow": d_lev,
                      "am_net_pct": round(am_net / oi * 100, 1) if oi else None,
                      "lev_net_pct": round(lev_net / oi * 100, 1) if oi else None}
    return res

def get_quote(sym, kind="s"):
    return get(f"https://stockanalysis.com/api/quotes/{kind}/{sym}").get("data", {})

out = {"fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"), "sectors": {}, "indices": {}}

for sector, syms in WATCHLIST.items():
    out["sectors"][sector] = {}
    for s in syms:
        row = {}
        for key, fn in [("quote", lambda: get_quote(s)),
                        ("stats", lambda: get_stats(s)),
                        ("spark", lambda: weekly_closes(s)),
                        ("pos", lambda: positioning(s))]:
            try:
                row[key] = fn()
            except Exception as e:
                print(f"{key} {s} FAILED: {e}", file=sys.stderr)
            time.sleep(0.4)
        out["sectors"][sector][s] = row
        print(f"done {s}", file=sys.stderr)

for name, (sym, kind) in INDEX_ETFS.items():
    try:
        q = get_quote(sym, kind)
        out["indices"][name] = {"price": q.get("p"), "chgPct": q.get("cp"),
                                "spark": weekly_closes(sym, kind),
                                "pos": positioning(sym, kind)}
    except Exception as e:
        print(f"index {name} FAILED: {e}", file=sys.stderr)
    time.sleep(0.4)

try:
    out["treasury10y"] = treasury_10y()
except Exception as e:
    print(f"treasury FAILED: {e}", file=sys.stderr)

try:
    out["macro_auto"] = macro_auto()
except Exception as e:
    print(f"macro_auto FAILED: {e}", file=sys.stderr)

try:
    out["cot"] = cot_positioning()
except Exception as e:
    print(f"cot FAILED: {e}", file=sys.stderr)

json.dump(out, open("market_data.json", "w"))
print("WROTE market_data.json")
