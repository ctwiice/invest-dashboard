#!/usr/bin/env python3
"""Quant lab for the Top 3 picks.

Computes, from ~10 years of public price history (stockanalysis.com, no keys):
  - historical stats: CAGR, annualized vol, Sharpe, Sortino, max drawdown,
    monthly win rate, and 10Y beta vs SPY.
  - strategy backtests: buy-and-hold vs a 40-week (about 200-day) trend filter,
    plus a 3-pick portfolio (equal-weight vs momentum rotation vs SPY).
  - market and per-name regime detection (trend + volatility state).
  - volatility-based trade levels: entry, stop (2.5x ATR / below the 200-day),
    take-profit (the Monte Carlo 75th-percentile one-year outcome), and R:R.
  - Monte Carlo: bootstrap of weekly returns over 1-year and 3-year horizons,
    giving probability of loss, the return distribution, and the bear case.

Pure stdlib so it runs anywhere the rest of the pipeline runs. Deterministic
(fixed seed) so the numbers are stable between runs on the same data.
Writes quant_data.json.
"""
import json, subprocess, math, time, random
import statistics as stat

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
RF = 0.03            # risk-free assumption for Sharpe/Sortino (disclosed on the page)
MC_PATHS = 10000     # Monte Carlo paths per horizon
RNG = random.Random(20260704)

PICKS = {"VOO": "e", "LLY": "s", "SMH": "e"}   # ticker -> kind
BENCH = ("SPY", "e")
NAMES = {"VOO": "Vanguard S&P 500 ETF", "LLY": "Eli Lilly", "SMH": "VanEck Semiconductor ETF", "SPY": "S&P 500 ETF"}


def get(url):
    out = subprocess.run(["curl", "-s", "--max-time", "30", "-A", UA, url],
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def hist(sym, kind, rng, period):
    d = get(f"https://stockanalysis.com/api/symbol/{kind}/{sym}/history?range={rng}&period={period}")
    return sorted(d.get("data", []), key=lambda r: r["t"])


def rets(closes):
    return [closes[i] / closes[i - 1] - 1 for i in range(1, len(closes))]


def logrets(closes):
    return [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]


def max_drawdown(curve):
    peak, mdd = curve[0], 0.0
    for v in curve:
        peak = max(peak, v)
        mdd = min(mdd, v / peak - 1)
    return mdd * 100


def cagr(curve, years):
    if years <= 0 or curve[0] <= 0:
        return None
    return ((curve[-1] / curve[0]) ** (1 / years) - 1) * 100


def sharpe(weekly, rf=RF):
    if len(weekly) < 5:
        return None
    mu = stat.mean(weekly) * 52
    sd = stat.pstdev(weekly) * math.sqrt(52)
    return (mu - rf) / sd if sd else None


def sortino(weekly, rf=RF):
    if len(weekly) < 5:
        return None
    mu = stat.mean(weekly) * 52
    downs = [min(w, 0) for w in weekly]
    dd = math.sqrt(sum(x * x for x in downs) / len(downs)) * math.sqrt(52)
    return (mu - rf) / dd if dd else None


def monthly_from(rows):
    """Last close per calendar month -> {'YYYY-MM': close}."""
    m = {}
    for r in rows:
        m[r["t"][:7]] = r["c"]
    return dict(sorted(m.items()))


def pctl(sorted_vals, p):
    if not sorted_vals:
        return None
    k = (len(sorted_vals) - 1) * p
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return sorted_vals[int(k)]
    return sorted_vals[lo] * (hi - k) + sorted_vals[hi] * (k - lo)


# ---------------------------------------------------------------- fetch data
weekly = {}   # ticker -> list of rows (10Y weekly)
daily = {}    # ticker -> list of rows (1Y daily)
for t, k in list(PICKS.items()) + [BENCH]:
    weekly[t] = hist(t, k, "10Y", "Weekly")
    daily[t] = hist(t, k, "1Y", "Daily")
    time.sleep(0.3)

spy_w_closes = [r["c"] for r in weekly["SPY"]]
spy_w_r = rets(spy_w_closes)
spy_dates = [r["t"] for r in weekly["SPY"]]


# ------------------------------------------------------------ backtest engine
def backtest_buyhold(closes):
    r = rets(closes)
    curve = [1.0]
    for x in r:
        curve.append(curve[-1] * (1 + x))
    yrs = (len(closes) - 1) / 52
    return {"cagr": cagr(curve, yrs), "sharpe": sharpe(r), "maxdd": max_drawdown(curve),
            "winrate": winrate_monthly(closes), "time_in_mkt": 100.0, "trades": None}


def winrate_monthly(closes_or_rows):
    if closes_or_rows and isinstance(closes_or_rows[0], dict):
        mc = list(monthly_from(closes_or_rows).values())
    else:
        mc = closes_or_rows
    mr = rets(mc)
    if not mr:
        return None
    return 100 * sum(1 for x in mr if x > 0) / len(mr)


def backtest_trend(rows, win=40):
    """40-week SMA trend filter. In when last close > SMA(win); cash earns RF."""
    closes = [r["c"] for r in rows]
    r = rets(closes)                         # r[i] is return from close[i] to close[i+1]
    curve = [1.0]
    strat_r = []
    pos_prev = 0
    seg_start_val = None
    trades = []
    inmkt_weeks = 0
    for i in range(len(r)):
        # decision at close[i] using SMA of closes[..i]
        if i + 1 < win:
            pos = 0
        else:
            sma = sum(closes[i + 1 - win:i + 1]) / win
            pos = 1 if closes[i] > sma else 0
        wk = r[i] if pos else RF / 52
        strat_r.append(wk if pos else 0.0)   # for Sharpe treat cash as ~0 excess
        curve.append(curve[-1] * (1 + wk))
        inmkt_weeks += pos
        # trade accounting on in-market segments
        if pos and not pos_prev:
            seg_start_val = curve[-2]
        if pos_prev and not pos and seg_start_val is not None:
            trades.append(curve[-1] / seg_start_val - 1)
            seg_start_val = None
        pos_prev = pos
    if pos_prev and seg_start_val is not None:
        trades.append(curve[-1] / seg_start_val - 1)
    yrs = (len(closes) - 1) / 52
    wr = 100 * sum(1 for t in trades if t > 0) / len(trades) if trades else None
    return {"cagr": cagr(curve, yrs), "sharpe": sharpe([x for x in strat_r]),
            "maxdd": max_drawdown(curve), "winrate": wr,
            "time_in_mkt": 100 * inmkt_weeks / len(r) if r else None,
            "trades": len(trades)}


def backtest_portfolio():
    """Monthly: equal-weight the 3 picks vs momentum rotation (top trailing-3mo
    with positive trend) vs SPY buy-and-hold, on the common month window."""
    m = {t: monthly_from(weekly[t]) for t in list(PICKS) + ["SPY"]}
    months = sorted(set.intersection(*[set(m[t]) for t in m]))
    ew, mo, bench = [1.0], [1.0], [1.0]
    ew_r, mo_r, bench_r = [], [], []
    picks = list(PICKS)
    for j in range(3, len(months) - 1):
        cur, nxt = months[j], months[j + 1]
        # equal weight of next-month returns
        rs = [m[t][nxt] / m[t][cur] - 1 for t in picks]
        ewr = sum(rs) / len(rs)
        ew_r.append(ewr); ew.append(ew[-1] * (1 + ewr))
        # momentum: pick top trailing 3-month performer if its 3mo return > 0
        tr = {t: m[t][cur] / m[t][months[j - 3]] - 1 for t in picks}
        best = max(tr, key=tr.get)
        mor = (m[best][nxt] / m[best][cur] - 1) if tr[best] > 0 else RF / 12
        mo_r.append(mor); mo.append(mo[-1] * (1 + mor))
        # benchmark
        br = m["SPY"][nxt] / m["SPY"][cur] - 1
        bench_r.append(br); bench.append(bench[-1] * (1 + br))
    yrs = (len(ew) - 1) / 12

    def pack(curve, rr, is_mo=False):
        mu = stat.mean(rr) * 12
        sd = stat.pstdev(rr) * math.sqrt(12)
        return {"cagr": cagr(curve, yrs), "sharpe": (mu - RF) / sd if sd else None,
                "maxdd": max_drawdown(curve),
                "winrate": 100 * sum(1 for x in rr if x > 0) / len(rr)}
    return {"equal_weight": pack(ew, ew_r), "momentum": pack(mo, mo_r),
            "benchmark_spy": pack(bench, bench_r),
            "months": len(ew) - 1, "start": months[3], "end": months[-1]}


# --------------------------------------------------------- regime + trade lvls
def atr(rows, win=14):
    trs = []
    for i in range(1, len(rows)):
        h, l, pc = rows[i]["h"], rows[i]["l"], rows[i - 1]["c"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(trs[-win:]) / win if len(trs) >= win else (sum(trs) / len(trs) if trs else None)


def realized_vol_ann(rows, win=20):
    closes = [r["c"] for r in rows][-win - 1:]
    r = rets(closes)
    return stat.pstdev(r) * math.sqrt(252) * 100 if len(r) > 2 else None


def regime(rows):
    closes = [r["c"] for r in rows]
    price = closes[-1]
    sma50 = sum(closes[-50:]) / min(50, len(closes))
    sma200 = sum(closes[-200:]) / min(200, len(closes))
    mom3 = (price / closes[-63] - 1) * 100 if len(closes) >= 63 else None
    vol = realized_vol_ann(rows)
    # 1Y median 20d vol for a "elevated?" reference
    vols = []
    for i in range(21, len(rows)):
        vols.append(stat.pstdev(rets([r["c"] for r in rows[i - 21:i]])) * math.sqrt(252) * 100)
    volmed = stat.median(vols) if vols else vol
    up = price > sma200
    hot = vol and volmed and vol > 1.2 * volmed
    label = ("Uptrend" if up else "Downtrend") + (", elevated volatility" if hot else ", normal volatility")
    return {"label": label, "trend": "up" if up else "down",
            "vs_sma50": (price / sma50 - 1) * 100, "vs_sma200": (price / sma200 - 1) * 100,
            "mom3": mom3, "vol_ann": vol, "vol_median": volmed, "sma50": sma50, "sma200": sma200}


# --------------------------------------------------------------- Monte Carlo
def monte_carlo(lr, weeks):
    finals = []
    for _ in range(MC_PATHS):
        s = sum(RNG.choices(lr, k=weeks))
        finals.append(math.exp(s) - 1)
    finals.sort()
    return {
        "prob_loss": 100 * sum(1 for x in finals if x < 0) / len(finals),
        "mean": stat.mean(finals) * 100, "median": pctl(finals, 0.5) * 100,
        "p5": pctl(finals, 0.05) * 100, "p25": pctl(finals, 0.25) * 100,
        "p75": pctl(finals, 0.75) * 100, "p95": pctl(finals, 0.95) * 100,
        "worst": finals[0] * 100, "best": finals[-1] * 100,
    }


# ---------------------------------------------------------------- assemble
out = {"as_of": time.strftime("%Y-%m-%d"), "rf": RF, "mc_paths": MC_PATHS, "picks": {}}

bh_spy = backtest_buyhold(spy_w_closes)
out["benchmark"] = {"ticker": "SPY", "name": NAMES["SPY"],
                    "cagr": bh_spy["cagr"], "sharpe": bh_spy["sharpe"],
                    "maxdd": bh_spy["maxdd"], "winrate": bh_spy["winrate"],
                    "years": round((len(spy_w_closes) - 1) / 52, 1)}
out["market_regime"] = regime(daily["SPY"])

for t in PICKS:
    wk = weekly[t]
    closes = [r["c"] for r in wk]
    r = rets(closes)
    lr = logrets(closes)
    dates = [x["t"] for x in wk]
    # align pick vs SPY weekly returns by date for beta
    spy_map = dict(zip(spy_dates[1:], spy_w_r))
    pr = {d: rr for d, rr in zip(dates[1:], r)}
    common = [d for d in pr if d in spy_map]
    pv = [pr[d] for d in common]
    sv = [spy_map[d] for d in common]
    var_spy = stat.pvariance(sv)
    cov = sum((pv[i] - stat.mean(pv)) * (sv[i] - stat.mean(sv)) for i in range(len(pv))) / len(pv)
    beta = cov / var_spy if var_spy else None
    curve = [1.0]
    for x in r:
        curve.append(curve[-1] * (1 + x))
    yrs = (len(closes) - 1) / 52
    reg = regime(daily[t])
    a = atr(daily[t])
    price = daily[t][-1]["c"]
    mc1 = monte_carlo(lr, 52)
    mc3 = monte_carlo(lr, 156)
    # trade levels: stop = max downside room of 2.5*ATR or 4% below the 200-day;
    # target = the MC 1-year 75th percentile (a good-but-plausible year).
    stop = round(min(price - 2.5 * a, reg["sma200"] * 0.96), 2)
    risk_pct = (price - stop) / price * 100
    reward_pct = mc1["p75"]
    take = round(price * (1 + reward_pct / 100), 2)
    rr = reward_pct / risk_pct if risk_pct else None
    out["picks"][t] = {
        "name": NAMES[t], "price": round(price, 2),
        "stats": {"cagr": round(cagr(curve, yrs), 1), "vol": round(stat.pstdev(r) * math.sqrt(52) * 100, 1),
                  "sharpe": round(sharpe(r), 2), "sortino": round(sortino(r), 2),
                  "maxdd": round(max_drawdown(curve), 1), "winrate": round(winrate_monthly(wk), 0),
                  "beta": round(beta, 2) if beta else None, "years": round(yrs, 1)},
        "regime": {k: (round(v, 1) if isinstance(v, float) else v) for k, v in reg.items()},
        "backtest": {"buyhold": backtest_buyhold(closes), "trend": backtest_trend(wk)},
        "trade": {"entry": round(price, 2), "stop": stop, "take_profit": take,
                  "risk_pct": round(risk_pct, 1), "reward_pct": round(reward_pct, 1),
                  "rr": round(rr, 2) if rr else None, "atr": round(a, 2),
                  "sma50": round(reg["sma50"], 2), "sma200": round(reg["sma200"], 2)},
        "mc": {"h1": {k: round(v, 1) for k, v in mc1.items()},
               "h3": {k: round(v, 1) for k, v in mc3.items()}},
    }

out["portfolio"] = backtest_portfolio()

json.dump(out, open("quant_data.json", "w"), indent=1)
print("WROTE quant_data.json")
for t, d in out["picks"].items():
    tr = d["trade"]; s = d["stats"]; mc = d["mc"]["h1"]
    print(f"{t}: CAGR {s['cagr']}% Sharpe {s['sharpe']} MaxDD {s['maxdd']}% "
          f"| entry {tr['entry']} stop {tr['stop']} tp {tr['take_profit']} RR {tr['rr']} "
          f"| MC1y probLoss {mc['prob_loss']}% p5 {mc['p5']}% med {mc['median']}%")
print("portfolio:", {k: round(v['cagr'], 1) for k, v in out['portfolio'].items() if isinstance(v, dict)})
print("market regime:", out["market_regime"]["label"])
