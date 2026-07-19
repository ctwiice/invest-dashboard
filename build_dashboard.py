#!/usr/bin/env python3
"""Build the Long-Term Investing Monitor HTML from market_data.json + insights.json.

Covers the AI build-out supply chain (silicon to steel) plus nuclear power, and
now widens the lens: Big Tech / hyperscalers, healthcare & pharma, a broad ETF
shelf, a Top 3 Picks section, a Smart Money & Political Signals section, an
AI-data-center primer, and plain-English hover tooltips on every KPI.
"""
import json, html

MD = json.load(open("market_data.json"))
INS = json.load(open("insights.json"))
try:
    QUANT = json.load(open("quant_data.json"))
except (FileNotFoundError, json.JSONDecodeError):
    QUANT = None
E = html.escape

NAMES = {
    "NVDA": "Nvidia", "AMD": "AMD", "AVGO": "Broadcom", "TSM": "TSMC",
    "ASML": "ASML", "MU": "Micron", "SMCI": "Supermicro", "DELL": "Dell",
    "VRT": "Vertiv", "ANET": "Arista", "COHR": "Coherent", "LITE": "Lumentum",
    "CIEN": "Ciena", "GLW": "Corning", "ETN": "Eaton", "PWR": "Quanta Services",
    "ATKR": "Atkore", "WCC": "WESCO", "HUBB": "Hubbell", "NUE": "Nucor",
    "CEG": "Constellation", "VST": "Vistra", "CCJ": "Cameco", "BWXT": "BWX Tech",
    "OKLO": "Oklo", "SMR": "NuScale", "LEU": "Centrus", "GEV": "GE Vernova",
    "AAPL": "Apple", "MSFT": "Microsoft", "GOOGL": "Alphabet", "AMZN": "Amazon",
    "META": "Meta", "ORCL": "Oracle", "LLY": "Eli Lilly", "NVO": "Novo Nordisk",
    "UNH": "UnitedHealth", "JNJ": "Johnson & Johnson", "ABBV": "AbbVie",
    "MRK": "Merck", "IONQ": "IonQ", "RGTI": "Rigetti", "QBTS": "D-Wave Quantum",
    "QUBT": "Quantum Computing Inc", "IBM": "IBM",
    "SNDK": "SanDisk", "WDC": "Western Digital", "INTC": "Intel",
    "PLTR": "Palantir", "RKLB": "Rocket Lab", "LUNR": "Intuitive Machines",
    "ASTS": "AST SpaceMobile", "MP": "MP Materials", "LAC": "Lithium Americas",
    "TSSI": "TSS Inc", "NNE": "Nano Nuclear",
    "NBIS": "Nebius Group", "CRWV": "CoreWeave", "AMAT": "Applied Materials",
    "LRCX": "Lam Research", "KLAC": "KLA Corp", "ALAB": "Astera Labs",
}

# US-government connection badges: direct equity stakes the government has
# taken, or a business that exists mainly on federal contracts. Shown as a
# GOV chip next to the name with the story on hover.
GOV = {
    "INTC": "The US government took a roughly 10% equity stake in Intel (2025), converting CHIPS Act grants to shares. Washington is literally a shareholder.",
    "MP": "The Department of Defense holds an equity stake (about 15%) in MP Materials and guarantees a price floor for its rare-earth magnets.",
    "LAC": "The US government took an equity position in Lithium Americas as part of restructuring its multi-billion-dollar DOE loan for the Thacker Pass lithium mine.",
    "LEU": "Centrus is the only US-owned, NRC-licensed uranium enricher; it holds a $900M DOE contract to build out HALEU enrichment capacity.",
    "BWXT": "BWX Technologies is the sole supplier of nuclear reactors for US Navy submarines and carriers, a de facto government franchise.",
    "RKLB": "Rocket Lab launches for NASA and the US Space Force and holds a growing national-security launch and satellite backlog.",
    "PLTR": "Palantir's core business is US government and defense software contracts (Army, CIA lineage, immigration and intelligence agencies).",
}

# (sector key, group number, kicker, description, board). board 1 = the
# established large-dollar sheet, board 2 = the smaller-dollar speculative
# sheet. Same columns and Bull Score logic on both.
SECTOR_META = [
    ("Semiconductors & Fab", "01", "SILICON",
     "GPU and chip designers plus the only fabs that can print them. The top of the stack: highest margins, highest expectations. Intel carries a GOV badge: Washington owns roughly 10% of it.", 1),
    ("Chip Equipment & EUV", "02", "THE IRREPLACEABLES",
     "The machines every fab on earth must buy and cannot substitute: ASML's EUV lithography monopoly, Applied Materials and Lam for deposition and etch, KLA for inspection. The deepest moats in the entire AI supply chain.", 1),
    ("Memory & Storage", "03", "MEMORY",
     "The memory supercycle: AI servers need several times the DRAM and NAND of a normal server. Micron and SanDisk are the US pure-plays; SK Hynix, the HBM leader, trades only in Seoul (000660.KS), so the US-listed way to own it is this group plus SOXX.", 1),
    ("Servers, Cooling & Networking", "04", "COMPUTE RACKS",
     "The chips have to live somewhere. Server builders, liquid cooling and power management, the switches that connect racks, and the connectivity chips (Astera) that tie GPUs together.", 1),
    ("Fiber Optics & Photonics", "05", "INTERCONNECT",
     "Light moves the data. Optical transceivers, lasers and glass fiber; optics content per GPU rises every hardware generation.", 1),
    ("Electrical, Conduit & Steel", "06", "ELECTRIFICATION",
     "The unglamorous physical layer: switchgear, steel conduit, cable tray, wire distribution and the steel it is made from.", 1),
    ("Nuclear & Power Majors", "07", "POWER",
     "The established side of nuclear: operating fleets, the biggest uranium miner, the Navy's reactor builder and the turbine giant. Real revenue, real cash flow.", 1),
    ("Big Tech & Hyperscalers", "08", "THE CUSTOMERS",
     "The mega-cap companies whose capital-expenditure budgets pay for the entire build-out above, plus the government-software giant. Owning them is the most diversified way to own the theme.", 1),
    ("Healthcare & Pharma", "09", "OUTSIDE THE THEME",
     "A reminder that good businesses live outside AI. Obesity drugs, insurers and diversified pharma, driven by demographics rather than compute demand.", 1),
    ("Nuclear Developers & Fuel", "S1", "NEXT-GEN NUCLEAR",
     "SMR developers and the US enrichment play. Mostly pre-revenue: the reactors are paper until the late 2020s. Venture-sized positions only.", 2),
    ("Quantum Pure-Plays", "S2", "FRONTIER COMPUTE",
     "Qubits instead of bits, at nosebleed price-to-sales. The theme is real; the timeline is 2029-plus; the drawdowns are 50%+. Size like lottery tickets.", 2),
    ("Space & Defense", "S3", "ORBIT",
     "Launch, lunar landers and satellite-direct-to-phone. Rocket Lab is the operating business of the group; the others are still proving the model.", 2),
    ("Gov-Backed Materials & Small AI Infra", "S4", "STRATEGIC ASSETS",
     "Names where the US government is an owner or anchor customer (rare earths, lithium) plus small-cap AI data-center infrastructure. Policy is the moat and the risk.", 2),
    ("AI Neoclouds", "S5", "GPU LANDLORDS",
     "The rent-a-GPU layer: they borrow billions, buy Nvidia chips, and lease the compute to AI labs and hyperscalers. Real revenue growing triple digits, but debt-heavy, unprofitable, and hostage to GPU prices: that is why they live on this sheet despite large market caps.", 2),
]

# What each ETF actually holds, its role in a portfolio, and its expense ratio
# (the small yearly fee). Keyed by ticker.
ETF_META = {
    "SPY":  ("Core",        "The 500 largest US companies (S&P 500). The default market benchmark.", "0.09%"),
    "VOO":  ("Core",        "The same S&P 500 index, Vanguard's ultra-low-cost version.", "0.03%"),
    "VTI":  ("Core",        "The entire US stock market, large-cap down to small-cap in one fund.", "0.03%"),
    "QQQ":  ("Growth",      "The Nasdaq-100: 100 largest non-financial Nasdaq names, tech-heavy.", "0.20%"),
    "QQQM": ("Growth",      "The same Nasdaq-100 as QQQ, cheaper and built for buy-and-hold.", "0.15%"),
    "SCHD": ("Dividend",    "100 quality US dividend payers. A value and income tilt that balances growth.", "0.06%"),
    "VGT":  ("Sector",      "US technology only: software, hardware and chip makers.", "0.09%"),
    "SMH":  ("Sector",      "The semiconductor industry: chip designers and equipment makers.", "0.35%"),
    "SOXX": ("Sector",      "iShares Semiconductor ETF: the iShares version of SMH. Also the closest thing to a memory ETF: it holds Micron, SanDisk, Western Digital, Nvidia and AMD in one fund.", "0.35%"),
    "ARTY": ("Thematic",    "iShares Future AI & Tech (formerly IRBO): a broad AI basket across chips, software and robotics.", "0.47%"),
    "ITA":  ("Sector",      "iShares US Aerospace & Defense: the government-spending basket (defense primes, space suppliers).", "0.40%"),
    "NLR":  ("Thematic",    "VanEck Uranium & Nuclear: reactors, utilities and fuel. iShares has no nuclear fund; this is the standard one, more utility-heavy (steadier) than URA.", "0.61%"),
    "XLV":  ("Sector",      "US healthcare: pharma, insurers and medical devices.", "0.09%"),
    "URA":  ("Thematic",    "Uranium miners and nuclear-fuel companies. The purest nuclear basket.", "0.69%"),
    "IGF":  ("Thematic",    "Global infrastructure: utilities, transport and energy pipelines.", "0.41%"),
    "QTUM": ("Thematic",    "Quantum computing and disruptive tech (chips, AI, quantum). The diversified, lower-risk way to own the quantum theme.", "0.40%"),
    "WQTM": ("Thematic",    "WisdomTree Classiq quantum-computing basket. The US listing of the same fund that trades as QWTM in London: a purer, newer quantum play than QTUM.", "0.45%"),
    "BOTZ": ("Thematic",    "Global X Robotics & AI: companies in industrial robotics, automation and AI. The US analog of the Canada-listed RBOT.", "0.68%"),
    "UFO":  ("Thematic",    "Procure Space ETF: satellites, launch, rockets and space-tech names. The US analog of London's JEDG (VanEck Space Innovators).", "0.75%"),
    "SEMI": ("Sector",      "Columbia Select Technology ETF (formerly Semiconductor & Technology): a concentrated chip-and-tech basket. Overlaps SMH and VGT.", "0.75%"),
    "VXUS": ("International","Stocks outside the US, developed and emerging markets.", "0.05%"),
}
ETF_ROLE_ORDER = {"Core": 0, "Growth": 1, "Dividend": 2, "Sector": 3, "Thematic": 4, "International": 5}

# Plain-English hover text for the macro chips (non-economist audience).
MACRO_TIPS = {
    "cpi": "CPI (Consumer Price Index) tracks the average price of everyday goods and services. The YoY number is how much prices rose versus a year ago. Higher means inflation is hotter, which tends to keep interest rates high.",
    "core": "Core CPI strips out food and energy (the jumpy stuff) to show the underlying inflation trend the Fed watches most closely.",
    "fed": "The Fed Funds rate is the interest rate the Federal Reserve sets. Higher rates cool inflation but make borrowing costlier and pressure high-priced growth stocks.",
    "energy": "Energy prices, led by oil (WTI crude). Falling oil is disinflationary: it takes pressure off the headline CPI number and, at the margin, helps the case for lower rates.",
    "nextCpi": "The date the next inflation report is released. These prints often move the whole market in one morning.",
    "nextFomc": "The date of the next Federal Reserve meeting, when it decides whether to raise, hold or cut interest rates.",
}
T10_TIP = ("The 10-year Treasury yield is the interest the US government pays to borrow for 10 years. "
           "It is the benchmark 'risk-free' rate the market uses to value everything else. When it rises, "
           "expensive growth stocks usually get cheaper because future profits are worth less today.")


def n(stats, key):
    m = (stats or {}).get(key) or {}
    return m.get("n")


def compact():
    out = []
    for sector, syms in MD["sectors"].items():
        rows = []
        for s, row in syms.items():
            q = row.get("quote", {}) or {}
            st = row.get("stats", {}) or {}
            pos = row.get("pos", {}) or {}
            p = q.get("p")
            sma200 = n(st, "sma200")
            v200 = round((p / sma200 - 1) * 100, 1) if (p and sma200) else None
            rows.append({
                "v200": v200, "gov": GOV.get(s),
                "s": s, "nm": NAMES.get(s, s),
                "p": q.get("p"), "cp": q.get("cp"),
                "mc": (st.get("marketcap") or {}).get("v"),
                "pe": n(st, "pe"), "fpe": n(st, "peForward"), "peg": n(st, "pegRatio"),
                "pb": n(st, "pb"), "roe": n(st, "roe"), "eps": n(st, "eps"),
                "de": n(st, "debtEquity"), "b": n(st, "beta"),
                "y": n(st, "ch1y"), "rsi": n(st, "rsi"),
                "rg": n(st, "revenueGrowth"), "spark": row.get("spark", []),
                "c30": pos.get("ch30"), "p30": pos.get("pos30"),
                "lo30": pos.get("lo30"), "hi30": pos.get("hi30"),
                "v50": pos.get("vs50"), "dd": pos.get("ddays"),
                "hv": pos.get("heavy"), "vr": pos.get("volRatio"),
            })
        out.append({"sector": sector, "rows": rows})
    return out


DATA = {"sectors": compact(), "indices": MD.get("indices", {}),
        "t10": MD.get("treasury10y", {}), "fetched": MD.get("fetched_at", "")}
MACRO_AUTO = MD.get("macro_auto") or {}
COT = MD.get("cot") or {}

# Fast lookup of live metrics by ticker, for the Top Picks stat lines.
METR = {r["s"]: r for sec in DATA["sectors"] for r in sec["rows"]}


def idx_ticker(name):
    return name.split(" ")[0]


def idx_year_pct(d):
    sp = d.get("spark") or []
    if len(sp) >= 2 and sp[0]:
        return (sp[-1] / sp[0] - 1) * 100
    return None


IDX_BY_TICKER = {idx_ticker(nm): (nm, d) for nm, d in DATA["indices"].items()}


def fmt(v, d=2):
    if v is None:
        return None
    try:
        return f"{float(v):,.{d}f}"
    except (ValueError, TypeError):
        return None


def signed(v, d=1, suf="%"):
    f = fmt(v, d)
    if f is None:
        return None
    return ("+" if float(v) > 0 else "") + f + suf


# ---------------------------------------------------------------- Top 3 picks
def pick_stats(ticker):
    """Compact live stat line for a pick, from stock rows or the ETF shelf."""
    r = METR.get(ticker)
    if r:
        bits = []
        if r.get("p") is not None:
            cp = signed(r.get("cp"), 2)
            bits.append(("Price", "$" + fmt(r["p"]) + (f' <span class="{cls_updown(r.get("cp"))}">{cp}</span>' if cp else "")))
        if r.get("c30") is not None:
            bits.append(("30D", f'<span class="{cls_updown(r["c30"])}">{signed(r["c30"])}</span>'))
        if r.get("y") is not None:
            bits.append(("1Y", f'<span class="{cls_updown(r["y"])}">{signed(r["y"])}</span>'))
        if r.get("peg") is not None:
            bits.append(("PEG", fmt(r["peg"])))
        if r.get("roe") is not None:
            bits.append(("ROE", fmt(r["roe"], 0) + "%"))
        if r.get("p30") is not None:
            bits.append(("30D range", f'{r["p30"]}%'))
        return bits
    if ticker in IDX_BY_TICKER:
        nm, d = IDX_BY_TICKER[ticker]
        p = d.get("pos") or {}
        bits = []
        if d.get("price") is not None:
            cp = signed(d.get("chgPct"), 2)
            bits.append(("Price", "$" + fmt(d["price"]) + (f' <span class="{cls_updown(d.get("chgPct"))}">{cp}</span>' if cp else "")))
        if p.get("ch30") is not None:
            bits.append(("30D", f'<span class="{cls_updown(p["ch30"])}">{signed(p["ch30"])}</span>'))
        y1 = idx_year_pct(d)
        if y1 is not None:
            bits.append(("1Y", f'<span class="{cls_updown(y1)}">{signed(y1)}</span>'))
        meta = ETF_META.get(ticker)
        if meta:
            bits.append(("Fee", meta[2]))
        return bits
    return []


def cls_updown(v):
    if v is None:
        return ""
    return "pos" if float(v) > 0 else "neg" if float(v) < 0 else ""


def top_picks_section():
    picks = INS.get("top_picks")
    if not picks:
        return ""
    cards = []
    for p in picks:
        stats = pick_stats(p.get("ticker", ""))
        stat_html = "".join(
            f'<span class="ps-item"><span class="ps-k">{E(k)}</span> {v}</span>' for k, v in stats)
        srcs = " &middot; ".join(
            f'<a href="{E(u)}" target="_blank" rel="noopener">{E(t)}</a>' for t, u in p.get("sources", []))
        risk = f'<p class="pick-risk"><span class="pick-lbl">Risk</span> {E(p["risk"])}</p>' if p.get("risk") else ""
        why = f'<p class="pick-why"><span class="pick-lbl">Why now</span> {E(p["why_now"])}</p>' if p.get("why_now") else ""
        bear = f'<p class="pick-bear"><span class="pick-lbl bear">Bear case</span> {E(p["bear_case"])}</p>' if p.get("bear_case") else ""
        fac = f'<p class="pick-fac"><span class="pick-lbl">Political / structural</span> {E(p["factors"])}</p>' if p.get("factors") else ""
        comp = ""
        if p.get("competitors"):
            lis = "".join(f'<li><strong>{E(c["name"])}</strong> {E(c["note"])}</li>' for c in p["competitors"])
            comp = f'<div class="pick-comp"><span class="pick-lbl">Vs the competition</span><ul>{lis}</ul></div>'
        grade = ""
        g = p.get("grade")
        if g:
            gl = str(g.get("letter", ""))
            grade = f'<span class="pick-grade g-{gl[0].lower()}" title="{E(g.get("note", ""))}">{E(gl)}</span>'
        deep = ""
        if bear or comp or fac or srcs:
            deep = (f'<details class="pick-deep"><summary>Full analysis: bear case, competitors, policy</summary>'
                    f'{bear}{comp}{fac}<p class="sources">{srcs}</p></details>')
        cards.append(f"""
        <article class="pick">
          <div class="pick-rank">#{E(str(p.get("rank", "")))}</div>
          <div class="pick-body">
            <div class="pick-head">
              <span class="pick-tkr">{E(p.get("ticker", ""))}</span>
              <span class="pick-nm">{E(p.get("name", ""))}</span>
              <span class="pick-type">{E(p.get("type", ""))}</span>
              {grade}
            </div>
            <div class="pick-stats">{stat_html}</div>
            <p class="pick-thesis">{E(p.get("thesis", ""))}</p>
            {why}
            {risk}
            {deep}
          </div>
        </article>""")
    note = INS.get("top_picks_note", "")
    note_html = f'<p class="section-sub">{E(note)}</p>' if note else ""
    return f"""
    <section class="picks-sec">
      <h2 class="section-title">Top 3 Picks This Month</h2>
      <p class="section-sub">One editor's-eye ranking for a long-term buyer, weighing valuation, positioning, macro, policy and structural demand across the whole board (not just AI and nuclear). ETFs count. This is research, not advice: do your own homework and size positions you can hold for years.</p>
      {note_html}
      <div class="picks">{"".join(cards)}</div>
    </section>"""


# ---------------------------------------------------------- liquidation watch
def liquidation_watch():
    all_rows = [r for sec in DATA["sectors"] for r in sec["rows"]]
    mkt = []
    for name in ["SPY (S&P 500)", "VOO (S&P 500)", "QQQ (Nasdaq 100)", "SMH (Semiconductors)"]:
        d = DATA["indices"].get(name, {})
        p = d.get("pos") or {}
        if p:
            mkt.append((name.split(" ")[0], p))
    spy_dd = next((p["ddays"] for nm, p in mkt if nm == "SPY"), 0) or 0
    if spy_dd >= 5:
        verdict, vcls = "CAUTION: institutions are distributing. Heavy-volume selling is stacking up on the index itself; respect the tape and slow new buys.", "m-bad"
    elif spy_dd >= 3:
        verdict, vcls = "Elevated: selling pressure is above normal churn but not yet a rout. Keep position sizes honest.", "m-warn"
    else:
        verdict, vcls = "Normal churn: no broad volume-confirmed exodus from the market right now.", "m-good"

    def ddcls(v):
        return "m-bad" if (v or 0) >= 5 else "m-warn" if (v or 0) >= 3 else "m-good"
    mkt_rows = "".join(
        f'<tr><td>{nm}</td><td class="{ddcls(p["ddays"])}">{p["ddays"]}</td>'
        f'<td class="{"pos" if p["vs50"] > 0 else "neg"}">{p["vs50"]:+.1f}%</td>'
        f'<td>{p["pos30"]}%</td></tr>' for nm, p in mkt)
    heavy = sorted([r for r in all_rows if (r.get("hv") or 0) > 0], key=lambda r: -(r.get("hv") or 0))
    heavy_html = ", ".join(
        f'<strong>{r["s"]}</strong> ({r["hv"]} event{"s" if r["hv"] > 1 else ""})' for r in heavy) or "None in the last 5 sessions."
    dd_top = sorted([r for r in all_rows if (r.get("dd") or 0) >= 4], key=lambda r: -(r.get("dd") or 0))[:8]
    dd_html = ", ".join(f'<strong>{r["s"]}</strong> ({r["dd"]})' for r in dd_top) or "No ticker has 4 or more."
    return f"""
    <section class="liq">
      <h2 class="section-title">Liquidation Watch</h2>
      <p class="section-sub">A TIMING aid, not a stock-picking one: it tells you when to be patient with new buys, never what to own. Distribution days count sessions down &ge;0.2% on above-average volume over the last 25 sessions: the classic footprint of institutional selling. Heavy events are drops &ge;1.5% on &ge;1.5x average volume within the last 5 sessions.</p>
      <div class="liq-grid">
        <div class="liq-card">
          <h4>Market basis: where is the index, and who is selling it</h4>
          <div class="table-wrap liq-tbl"><table class="mini"><thead><tr><th title="The index basket.">Index</th><th title="Distribution days: recent sessions the index fell on heavy volume, a sign big money is selling. 5 or more warns of a correction.">D-Days</th><th title="How far the index is above or below its 50-day average price.">vs 50D avg</th><th title="Where the index sits inside its last 30 days of range, from low (0%) to high (100%).">30D range pos</th></tr></thead><tbody>{mkt_rows}</tbody></table></div>
          <p class="verdict {vcls}">{verdict}</p>
        </div>
        <div class="liq-card">
          <h4>Heavy liquidation events, last 5 sessions</h4>
          <p class="liq-list">{heavy_html}</p>
          <h4 class="liq-h2">Most distribution days on the board (25 sessions)</h4>
          <p class="liq-list">{dd_html}</p>
        </div>
      </div>
    </section>"""


MACRO_CHIPS = INS["macro"]


def insight_cards():
    cards = []
    for it in INS["insights"]:
        srcs = " &middot; ".join(f'<a href="{E(u)}" target="_blank" rel="noopener">{E(t)}</a>' for t, u in it["sources"])
        cards.append(f"""
        <article class="insight">
          <div class="insight-head"><span class="tag">{E(it["tag"])}</span></div>
          <h3>{E(it["title"])}</h3>
          <p>{E(it["body"])}</p>
          <p class="matters"><span class="matters-label">Why it matters</span> {E(it["matters"])}</p>
          <p class="sources">{srcs}</p>
        </article>""")
    return "\n".join(cards)


# ------------------------------------------------ smart money & political
def smart_money_section():
    sm = INS.get("smart_money")
    if not sm:
        return ""
    cards = []
    for it in sm.get("items", []):
        srcs = " &middot; ".join(f'<a href="{E(u)}" target="_blank" rel="noopener">{E(t)}</a>' for t, u in it.get("sources", []))
        matters = f'<p class="matters"><span class="matters-label">Why it matters</span> {E(it["matters"])}</p>' if it.get("matters") else ""
        cards.append(f"""
        <article class="insight sm-card">
          <div class="insight-head"><span class="tag sm-tag">{E(it.get("tag", ""))}</span></div>
          <h3>{E(it.get("title", ""))}</h3>
          <p>{E(it.get("body", ""))}</p>
          {matters}
          <p class="sources">{srcs}</p>
        </article>""")
    intro = sm.get("intro", "")
    return f"""
    <section class="smart">
      <h2 class="section-title">Smart Money &amp; Political Signals</h2>
      <p class="section-sub">{E(intro)}</p>
      <div class="insights">{"".join(cards)}</div>
      <p class="watchnote sm-note">&#9888; Following politicians or big funds is a signal, not a guarantee. Disclosures lag the actual trade by up to 45 days, sizes are often small, and lawmakers can be wrong. Use it as a prompt to research, never as a reason to buy blind.</p>
    </section>"""


# ------------------------------------------------------------------ ETF shelf
def etf_shelf():
    rows = []
    items = []
    for name, d in DATA["indices"].items():
        if not d or d.get("price") is None:
            continue
        t = idx_ticker(name)
        meta = ETF_META.get(t, ("", "", ""))
        items.append((t, name, d, meta))
    items.sort(key=lambda x: (ETF_ROLE_ORDER.get(x[3][0], 9), x[0]))
    for t, name, d, meta in items:
        role, holds, er = meta
        p = d.get("pos") or {}
        y1 = idx_year_pct(d)
        cp = d.get("chgPct")
        rangebar = ""
        if p.get("pos30") is not None:
            cls = "r-lo" if p["pos30"] <= 25 else "r-hi" if p["pos30"] >= 75 else ""
            rangebar = (f'<span class="rbar {cls}" title="30-day range: now at {p["pos30"]}% of the last 30 days">'
                        f'<span style="left:{p["pos30"]}%"></span></span>')
        rows.append(f"""
        <tr>
          <td class="co"><span class="sym">{E(t)}</span><span class="etf-role">{E(role)}</span></td>
          <td>${fmt(d.get("price"))} <span class="{cls_updown(cp)}">{signed(cp, 2) or ""}</span></td>
          <td class="{cls_updown(p.get("ch30"))}">{signed(p.get("ch30")) or "n/a"}</td>
          <td class="{cls_updown(y1)}">{signed(y1) or "n/a"}</td>
          <td>{rangebar or "n/a"}</td>
          <td>{E(er)}</td>
          <td class="etf-holds">{E(holds)}</td>
        </tr>""")
    return f"""
    <section class="etf-sec">
      <h2 class="section-title">ETF Shelf: Own the Whole Field</h2>
      <p class="section-sub">Funds give you a slice of an entire market or sector in one holding, so a single company blowing up cannot sink you. Sorted by role: core (own the market), growth, dividend, sector, thematic, international. The fee column is the yearly expense ratio, the small cost of holding the fund. Hover any column header for a definition.</p>
      <div class="table-wrap"><table class="etf-table"><thead><tr>
        <th title="The fund's ticker and its role in a portfolio.">ETF</th>
        <th title="Latest share price and today's move.">Price</th>
        <th title="Price change over the last 30 days.">30D %</th>
        <th title="Price change over the past year.">1Y %</th>
        <th title="Where the price sits inside its last 30 days of range, low (0%) to high (100%).">30D Range</th>
        <th title="Expense ratio: the small yearly fee to hold the fund. Lower is better for long-term holders.">Fee</th>
        <th title="What the fund actually owns.">What it holds</th>
      </tr></thead><tbody>{"".join(rows)}</tbody></table></div>
    </section>"""


# -------------------------------------------------------------------- primer
def primer_section():
    pr = INS.get("primer")
    if not pr:
        return ""
    blocks = []
    for sec in pr.get("sections", []):
        blocks.append(f'<div class="prim-block"><h4>{E(sec.get("h", ""))}</h4><p>{E(sec.get("p", ""))}</p></div>')
    intro = f'<p class="prim-intro">{E(pr.get("intro", ""))}</p>' if pr.get("intro") else ""
    return f"""
    <section class="primer">
      <h2 class="section-title">Primer: How AI Infrastructure Makes Money</h2>
      <p class="section-sub">A plain-English tour of what actually goes into an AI data center and where the dollars land, layer by layer. No jargon required.</p>
      {intro}
      <div class="prim-grid">{"".join(blocks)}</div>
    </section>"""


def _q(v, d=1, suf=""):
    if v is None:
        return "n/a"
    try:
        return f"{float(v):,.{d}f}{suf}"
    except (ValueError, TypeError):
        return "n/a"


def quant_lab_section():
    if not QUANT or not QUANT.get("picks"):
        return ""
    ins_by_t = {p.get("ticker"): p for p in INS.get("top_picks", [])}
    reg = QUANT.get("market_regime", {})
    order = [p.get("ticker") for p in INS.get("top_picks", []) if p.get("ticker") in QUANT["picks"]]
    for t in QUANT["picks"]:
        if t not in order:
            order.append(t)
    cards = []
    for t in order:
        d = QUANT["picks"][t]
        s, bt, tr, mc, rg = d["stats"], d["backtest"], d["trade"], d["mc"], d["regime"]
        reason = (ins_by_t.get(t, {}) or {}).get("trade_reasoning", "")
        stat_items = [
            ("CAGR (10Y)", _q(s["cagr"], 1, "%")), ("Sharpe", _q(s["sharpe"], 2)),
            ("Sortino", _q(s["sortino"], 2)), ("Max DD", _q(s["maxdd"], 0, "%")),
            ("Ann. Vol", _q(s["vol"], 0, "%")), ("Win rate (mo)", _q(s["winrate"], 0, "%")),
            ("Beta vs SPY", _q(s["beta"], 2)),
        ]
        stat_html = "".join(f'<div class="qstat"><span class="qk">{k}</span><span class="qv">{v}</span></div>' for k, v in stat_items)

        def btrow(nm, b, extra):
            return (f'<tr><td class="co">{nm}</td><td>{_q(b["cagr"], 1, "%")}</td>'
                    f'<td>{_q(b["sharpe"], 2)}</td><td class="neg">{_q(b["maxdd"], 0, "%")}</td>'
                    f'<td>{_q(b["winrate"], 0, "%")}</td><td class="qhint">{extra}</td></tr>')
        bh, tf = bt["buyhold"], bt["trend"]
        better = ("the trend filter improved risk-adjusted return, mostly by dodging drawdowns"
                  if (tf["sharpe"] or 0) > (bh["sharpe"] or 0)
                  else "buy-and-hold won; the trend filter whipsawed and gave up return")
        bt_html = ('<table class="qbt"><thead><tr>'
                   '<th class="co">Strategy</th>'
                   '<th title="Compound annual growth rate: the smoothed yearly return.">CAGR</th>'
                   '<th title="Return per unit of risk. Higher is better; above 1 is good.">Sharpe</th>'
                   '<th title="The worst peak-to-trough drop over the period.">Max DD</th>'
                   '<th title="Share of months (buy-hold) or trades (trend) that were positive.">Win</th>'
                   '<th title="Buy-and-hold is always invested; the trend filter is only in when price is above its 40-week (about 200-day) average.">In mkt / trades</th>'
                   '</tr></thead><tbody>'
                   + btrow("Buy &amp; hold", bh, "always invested")
                   + btrow("40-wk trend filter", tf, f'{_q(tf["time_in_mkt"], 0, "%")} in, {tf["trades"]} trades')
                   + '</tbody></table>')
        trade_html = (
            '<div class="qtrade"><div class="qtrade-grid">'
            f'<div><span class="qk">Entry</span><span class="qv">${_q(tr["entry"], 2)}</span></div>'
            f'<div><span class="qk">Stop loss</span><span class="qv neg">${_q(tr["stop"], 2)}</span><span class="qsub">-{_q(tr["risk_pct"], 1)}%</span></div>'
            f'<div><span class="qk">Take profit</span><span class="qv pos">${_q(tr["take_profit"], 2)}</span><span class="qsub">+{_q(tr["reward_pct"], 1)}%</span></div>'
            f'<div><span class="qk">Risk / reward</span><span class="qv">{_q(tr["rr"], 2)} : 1</span></div>'
            f'</div><p class="qreason">{E(reason)}</p></div>')

        def mc_block(h, label):
            gauge = (f'<div class="mc-gauge"><span class="loss" style="width:{h["prob_loss"]}%"></span>'
                     f'<span class="gain" style="width:{100 - h["prob_loss"]}%"></span></div>')
            return (f'<div class="mc-h"><div class="mc-head"><span>{label}</span>'
                    f'<span class="mc-pl">{_q(h["prob_loss"], 0)}% chance of a loss</span></div>{gauge}'
                    f'<div class="mc-pct"><span>Bear (5th): <b class="neg">{_q(h["p5"], 0, "%")}</b></span>'
                    f'<span>Typical: <b>{_q(h["median"], 0, "%")}</b></span>'
                    f'<span>Bull (95th): <b class="pos">{_q(h["p95"], 0, "%")}</b></span>'
                    f'<span>Worst sim: <b class="neg">{_q(h["worst"], 0, "%")}</b></span></div></div>')
        mc_html = mc_block(mc["h1"], "1-year outcome") + mc_block(mc["h3"], "3-year outcome")
        cards.append(f'''
        <article class="qcard">
          <div class="qcard-head"><span class="pick-tkr">{E(t)}</span><span class="pick-nm">{E(d.get("name", ""))}</span>
            <span class="qregime">{E(rg.get("label", ""))} &middot; {_q(rg.get("vs_sma200"), 1, "%")} vs 200-day</span></div>
          <div class="qstats">{stat_html}</div>
          <div class="qsplit">
            <div><h5>Strategy backtest ({_q(s["years"], 0)}Y history)</h5>{bt_html}<p class="qnote">Verdict: {better}.</p></div>
            <div><h5>Trade setup</h5>{trade_html}</div>
          </div>
          <div class="qmc"><h5>Monte Carlo ({QUANT.get("mc_paths", "?")} simulated paths)</h5><div class="mc-wrap">{mc_html}</div></div>
        </article>''')

    port = QUANT.get("portfolio", {})

    def prow(nm, b, hint):
        if not b:
            return ""
        return (f'<tr><td class="co">{nm}</td><td>{_q(b["cagr"], 1, "%")}</td><td>{_q(b["sharpe"], 2)}</td>'
                f'<td class="neg">{_q(b["maxdd"], 0, "%")}</td><td>{_q(b["winrate"], 0, "%")}</td><td class="qhint">{hint}</td></tr>')
    port_html = ""
    if port:
        port_html = (f'<div class="qport"><h4>Portfolio backtest: the three together ({E(port.get("start", ""))} to {E(port.get("end", ""))})</h4>'
                     '<div class="table-wrap"><table class="qbt"><thead><tr><th class="co">Approach</th><th>CAGR</th><th>Sharpe</th><th>Max DD</th><th>Win (mo)</th><th>What it does</th></tr></thead><tbody>'
                     + prow("Equal-weight, monthly rebalance", port.get("equal_weight"), "Hold all three in equal parts")
                     + prow("Momentum rotation", port.get("momentum"), "Hold the strongest of the three each month")
                     + prow("SPY buy &amp; hold (benchmark)", port.get("benchmark_spy"), "The market, for comparison")
                     + '</tbody></table></div>'
                     '<p class="qnote">Takeaway: simply equal-weighting the three and rebalancing beat both the momentum-timing rule and the S&amp;P on risk-adjusted return over this window. For a long-term investor, that is the case for owning all three and rebalancing, not trying to time between them.</p></div>')
    bench = QUANT.get("benchmark", {})
    note = (f'Methodology: about {_q(bench.get("years"), 0)} years of weekly history. Sharpe and Sortino use a {int(QUANT.get("rf", 0) * 100)}% risk-free rate. '
            "The Monte Carlo bootstraps real weekly returns, so it inherits the last decade's unusually strong, mostly-bull distribution: treat the upside percentiles as optimistic, and the loss odds and the bear (5th percentile) as the more decision-useful numbers. Backtests are hypothetical and ignore taxes and slippage. Research, not financial advice.")
    return f'''
    <section class="quant">
      <h2 class="section-title">Quant Lab: Backtests, Regime &amp; Monte Carlo</h2>
      <p class="section-sub">The three picks put through a hedge-fund-style workup: 10-year historical stats, a strategy backtest, volatility-based trade levels, and a Monte Carlo simulation of the year and three years ahead. Current market regime: <strong>{E(reg.get("label", ""))}</strong> ({_q(reg.get("vs_sma200"), 1, "%")} vs the 200-day, {_q(reg.get("vol_ann"), 0, "%")} annualized volatility).</p>
      <div class="qcards">{"".join(cards)}</div>
      {port_html}
      <p class="qmethod">{E(note)}</p>
    </section>'''


def macro_strategy_section():
    ms = INS.get("macro_strategy")
    if not ms:
        return ""
    drivers = "".join(
        f'<div class="mdriver"><h5>{E(d["driver"])}</h5><p class="mread">{E(d["reading"])}</p><p class="mplay">{E(d["playbook"])}</p></div>'
        for d in ms.get("drivers", []))
    scen = "".join(
        f'<li><span class="mtrig">{E(s["trigger"])}:</span> {E(s["response"])}</li>' for s in ms.get("scenarios", []))
    return f'''
    <section class="macrostrat">
      <h2 class="section-title">Macro Playbook: Rates, Inflation &amp; Growth</h2>
      <p class="section-sub">How to position for the current backdrop. Regime read: <strong>{E(ms.get("regime_label", ""))}</strong>. {E(ms.get("regime_detail", ""))}</p>
      <div class="mdrivers">{drivers}</div>
      <div class="mscen"><h4>If / then: the next two prints</h4><ul>{scen}</ul></div>
      <p class="mpos"><span class="pick-lbl">Net positioning</span> {E(ms.get("positioning", ""))}</p>
    </section>'''


MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _mon(datestr):
    try:
        return MONTHS[int(datestr[5:7])] + " " + datestr[:4]
    except (ValueError, IndexError, TypeError):
        return datestr or ""


def chip(label, value, delta, tone, tip):
    return (f'<div class="chip t-{tone}" title="{E(tip)}">'
            f'<span class="chip-label">{E(label)}</span>'
            f'<span class="chip-value">{value}</span>'
            f'<span class="chip-delta">{E(delta)}</span></div>')


def macro_strip():
    """The macro command strip. Every number here is pulled automatically from
    FRED at refresh time; only the two calendar chips come from the briefing."""
    chips = []
    ma = MACRO_AUTO

    c = ma.get("cpi") or {}
    if c.get("yoy") is not None:
        tone = "bad" if c["yoy"] >= 3.5 else "warn" if c["yoy"] >= 2.5 else "good"
        chips.append(chip(f"CPI YoY ({_mon(c.get('date'))})", f"{c['yoy']:.1f}%",
                          f"prior month {c.get('prev_yoy')}%", tone, MACRO_TIPS["cpi"]))
    c = ma.get("core_cpi") or {}
    if c.get("yoy") is not None:
        tone = "bad" if c["yoy"] >= 3.5 else "warn" if c["yoy"] >= 2.5 else "good"
        chips.append(chip("Core CPI YoY", f"{c['yoy']:.1f}%",
                          f"prior month {c.get('prev_yoy')}%", tone, MACRO_TIPS["core"]))
    c = ma.get("fedfunds") or {}
    if c.get("value") is not None:
        chips.append(chip("Fed Funds (eff.)", f"{c['value']:.2f}%",
                          f"as of {_mon(c.get('date'))}", "warn", MACRO_TIPS["fed"]))
    t10 = DATA.get("t10") or {}
    if t10.get("value") is not None:
        diff = (t10["value"] - t10["prev30"]) if t10.get("prev30") is not None else None
        delta = f"{diff:+.2f}pp vs 30 days ago" if diff is not None else ""
        chips.append(chip("10Y Treasury", f"{t10['value']:.2f}%", delta,
                          "warn" if (diff or 0) > 0 else "good", T10_TIP))
    t2 = ma.get("t2y") or {}
    if t2.get("value") is not None and t10.get("value") is not None:
        spread = t10["value"] - t2["value"]
        tone = "bad" if spread < 0 else "warn" if spread < 0.4 else "good"
        note = ("INVERTED: a classic recession warning" if spread < 0
                else "flat-ish: late-cycle" if spread < 0.4 else "normal upward slope")
        chips.append(chip("Yield Curve (10Y-2Y)", f"{spread:+.2f}pp", note, tone,
                          "The gap between 10-year and 2-year Treasury yields. When it goes NEGATIVE (inverted), short-term money pays more than long-term: historically one of the most reliable recession warnings, usually 6-18 months ahead. A healthy economy has a positive (upward) curve."))
    c = ma.get("vix") or {}
    if c.get("value") is not None:
        v = c["value"]
        tone = "good" if v < 15 else "warn" if v < 25 else "bad"
        note = "calm, complacent even" if v < 15 else "normal caution" if v < 25 else "fear elevated: big swings"
        chips.append(chip("VIX (fear index)", f"{v:.1f}", note, tone,
                          "The VIX measures how much turbulence options traders expect over the next 30 days. Under 15 is calm, 15-25 normal, over 25 fearful. Long-term buyers get their best prices when the VIX is HIGH and everyone else is scared."))
    c = ma.get("wti") or {}
    if c.get("value") is not None:
        d30 = c.get("prev30")
        delta = f"{(c['value'] / d30 - 1) * 100:+.0f}% vs 30 days ago" if d30 else ""
        tone = "warn" if d30 and c["value"] > d30 * 1.05 else "info"
        chips.append(chip("Oil (WTI)", f"${c['value']:.0f}", delta, tone, MACRO_TIPS["energy"]))
    c = ma.get("unemployment") or {}
    if c.get("value") is not None:
        tone = "good" if c["value"] < 4.5 else "warn" if c["value"] < 5.5 else "bad"
        chips.append(chip(f"Unemployment ({_mon(c.get('date'))})", f"{c['value']:.1f}%",
                          "labor market health", tone,
                          "The share of people looking for work who cannot find it. A rising trend is the clearest sign the economy is rolling over; under ~4.5% is historically strong."))
    for key in ("nextCpi", "nextFomc"):
        mc = MACRO_CHIPS.get(key)
        if mc:
            chips.append(chip(mc["label"], E(mc["value"]), mc["delta"], "info", MACRO_TIPS.get(key, "")))
    return "\n".join(chips)


def cot_section():
    """CFTC Commitments of Traders: what the two big kinds of institutional
    money are actually positioned for, from the weekly government filing."""
    if not COT:
        return ""
    date = next(iter(COT.values())).get("date", "")

    def knum(v):
        if v is None:
            return "n/a"
        return f"{v / 1000:+,.0f}k"

    def wow(v):
        if v is None:
            return ""
        arrow = "\\u2191" if v > 0 else "\\u2193" if v < 0 else "\\u2192"
        return f'<span class="{"pos" if v > 0 else "neg" if v < 0 else ""}">{arrow} {abs(v) / 1000:,.0f}k wk</span>'

    READS = {
        "S&P 500 e-mini": lambda d: ("Real money (pensions, asset managers) stays heavily long the market; hedge funds hold the short/hedge side."
                                     + (" Hedge funds added to shorts this week." if d["lev_wow"] < -1000 else " Hedge funds trimmed shorts this week." if d["lev_wow"] > 1000 else "")),
        "Nasdaq-100 e-mini": lambda d: ("Same split on tech: long-term money long, fast money short."
                                        + (" The fast-money short grew this week: they are leaning against the tech bounce." if d["lev_wow"] < -1000 else "")),
        "10Y Treasury note": lambda d: "Asset managers long bonds (expecting yields to fall or hedging stocks); leveraged funds short them (the basis trade plus higher-for-longer bets).",
        "VIX futures": lambda d: ("Positioning for calm." if d["am_net"] < 0 else "Paying up for crash protection."),
    }
    rows = []
    for label in ["S&P 500 e-mini", "Nasdaq-100 e-mini", "10Y Treasury note", "VIX futures"]:
        d = COT.get(label)
        if not d:
            continue
        read = READS.get(label, lambda d: "")(d)
        rows.append(f"""
        <tr>
          <td class="co">{E(label)}</td>
          <td class="{'pos' if d['am_net'] > 0 else 'neg'}">{knum(d['am_net'])}</td>
          <td>{wow(d['am_wow'])}</td>
          <td class="{'pos' if d['lev_net'] > 0 else 'neg'}">{knum(d['lev_net'])}</td>
          <td>{wow(d['lev_wow'])}</td>
          <td class="cot-read">{read}</td>
        </tr>""")
    spx = COT.get("S&P 500 e-mini", {})
    verdict = ""
    if spx:
        if (spx.get("lev_wow") or 0) < -10000:
            verdict = "This week's tell: hedge funds meaningfully increased their S&P short. They are either hedging harder or betting on more downside; either way the fast money is defensive."
        elif (spx.get("lev_wow") or 0) > 10000:
            verdict = "This week's tell: hedge funds covered part of their S&P short, a modest vote of confidence from the fast money."
        else:
            verdict = "This week's tell: positioning barely moved. Nobody big changed their mind this week."
    return f"""
    <section class="cot">
      <h2 class="section-title">Institutional Positioning (CFTC COT)</h2>
      <p class="section-sub">A TIMING aid: hedge-fund positioning says nothing about where a business will be in five years, but extremes mark moments patient buyers get better prices. Every Friday the CFTC publishes who holds what in the futures market (data as of Tuesday {E(date)}). Two groups matter: <strong>asset managers</strong> (pensions, insurers, mutual funds: the slow, long-term money) and <strong>leveraged funds</strong> (hedge funds: the fast money). Net = long contracts minus short. This is the closest public, free equivalent to the prime-brokerage flow data Goldman Sachs sells its clients; the GS flow headlines, when they leak into the press, land in the Smart Money section below.</p>
      <div class="table-wrap"><table class="mini cot-table"><thead><tr>
        <th title="The futures contract.">Contract</th>
        <th title="Asset managers' net position: pensions, insurers, mutual funds. Positive = net long (betting on / positioned for upside).">Asset mgrs net</th>
        <th title="How the asset-manager net position changed versus last week's report.">wk chg</th>
        <th title="Leveraged funds' net position: hedge funds. They are often net short index futures as a hedge on stock books, so the LEVEL matters less than the CHANGE.">Hedge funds net</th>
        <th title="How the hedge-fund net position changed versus last week's report.">wk chg</th>
        <th title="Plain-English read of the positioning.">Read</th>
      </tr></thead><tbody>{"".join(rows)}</tbody></table></div>
      <p class="verdict">{E(verdict)} A caution on reading COT: hedge-fund index shorts are often hedges on stock they own, not outright bearish bets, so watch the week-over-week CHANGE more than the level, and treat extremes (records either way) as contrarian signals.</p>
    </section>"""


def sector_sections(board):
    parts = []
    for sector, num_, kicker, desc, b in SECTOR_META:
        if b != board or sector not in {s["sector"] for s in DATA["sectors"]}:
            continue
        parts.append(f"""
      <section class="layer" id="layer-{num_}">
        <header class="layer-head">
          <div class="layer-rail"><span class="layer-num">{num_}</span></div>
          <div>
            <p class="layer-kicker">{num_} &middot; {E(kicker)}</p>
            <h2>{E(sector)}</h2>
            <p class="layer-desc">{E(desc)}</p>
          </div>
        </header>
        <div class="table-wrap"><table data-sector="{E(sector)}"></table></div>
      </section>""")
    return "\n".join(parts)


CLOSE_DATE = INS.get("close_date", "the latest market close")


def fold(summary, inner):
    """Collapse a full section into a click-to-expand block to keep the page lean."""
    if not inner:
        return ""
    return (f'<details class="fold"><summary><span class="fold-title">{summary}</span>'
            f'<span class="fold-hint">expand</span></summary>{inner}</details>')

page = f"""<title>Long-Term Investing Monitor</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<style>
:root {{
  --bg: #12171E; --panel: #1A212B; --panel-2: #202936; --line: #2B3644;
  --ink: #E7E2D8; --mut: #8C96A4; --dim: #5C6775;
  --copper: #D6904F; --copper-soft: rgba(214,144,79,.14);
  --up: #57B583; --down: #E0654F; --warn: #D4AF54;
  --disp: "Avenir Next Condensed", "Arial Narrow", "Helvetica Neue", sans-serif;
  --body: "Avenir Next", "Avenir", "Segoe UI", system-ui, sans-serif;
  --mono: ui-monospace, "SF Mono", "Cascadia Code", Menlo, monospace;
}}
html {{ background: var(--bg); }}
body {{ margin: 0; background: var(--bg); color: var(--ink); font-family: var(--body);
  font-size: 15px; line-height: 1.55; -webkit-font-smoothing: antialiased; }}
a {{ color: var(--copper); text-decoration: none; border-bottom: 1px solid rgba(214,144,79,.35); }}
a:hover, a:focus-visible {{ border-bottom-color: var(--copper); }}
a:focus-visible {{ outline: 2px solid var(--copper); outline-offset: 2px; }}
.wrap {{ max-width: 1180px; margin: 0 auto; padding: 0 24px 80px; }}

/* masthead */
.mast {{ padding: 34px 0 20px; border-bottom: 1px solid var(--line);
  display: flex; flex-wrap: wrap; align-items: baseline; gap: 8px 24px; }}
.mast h1 {{ font-family: var(--disp); font-weight: 600; letter-spacing: .12em;
  font-size: 30px; margin: 0; text-transform: uppercase; }}
.mast h1 .amp {{ color: var(--copper); }}
.mast .date {{ color: var(--mut); font-size: 13px; }}
.kicker-sub {{ margin: 6px 0 0; color: var(--mut); font-size: 13px; }}
.asof {{ margin: 8px 0 0; color: var(--dim); font-size: 12.5px; font-family: var(--mono); }}
.tiphint {{ margin: 6px 0 0; color: var(--copper); font-size: 12px; }}

/* macro strip */
.macro {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 10px; margin: 22px 0 10px; }}
.chip {{ background: var(--panel); border: 1px solid var(--line); border-radius: 4px;
  padding: 10px 12px 9px; display: flex; flex-direction: column; gap: 1px; cursor: help; }}
.chip-label {{ font-size: 10.5px; letter-spacing: .1em; text-transform: uppercase; color: var(--mut);
  text-decoration: underline dotted rgba(140,150,164,.5); text-underline-offset: 3px; }}
.chip-value {{ font-family: var(--mono); font-size: 21px; font-variant-numeric: tabular-nums; }}
.chip-delta {{ font-size: 11.5px; color: var(--mut); }}
.t-bad .chip-value {{ color: var(--down); }}
.t-warn .chip-value {{ color: var(--warn); }}
.t-good .chip-value {{ color: var(--up); }}

/* index/etf quick strip */
.indices {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(215px, 1fr));
  gap: 10px; margin: 10px 0 0; }}
.idx {{ background: var(--panel); border: 1px solid var(--line); border-radius: 4px;
  padding: 10px 12px; display: flex; flex-direction: column; align-items: flex-start; gap: 3px; }}
.idx .meta {{ min-width: 0; width: 100%; }}
.idx .nm {{ font-size: 11px; letter-spacing: .06em; text-transform: uppercase;
  color: var(--mut); white-space: normal; line-height: 1.35; }}
.idx .px {{ font-family: var(--mono); font-size: 16px; font-variant-numeric: tabular-nums; }}
.idx canvas {{ margin-top: 4px; flex: none; }}

/* section headers */
.section-title {{ font-family: var(--disp); text-transform: uppercase; letter-spacing: .14em;
  font-size: 16px; font-weight: 600; color: var(--copper); margin: 0 0 4px; }}
.section-sub {{ color: var(--mut); font-size: 13.5px; margin: 0 0 18px; max-width: 90ch; }}

/* top picks */
.picks-sec {{ margin-top: 34px; }}
.picks {{ display: grid; gap: 12px; }}
.pick {{ display: flex; gap: 16px; background: var(--panel); border: 1px solid var(--line);
  border-left: 3px solid var(--copper); border-radius: 4px; padding: 16px 18px; }}
.pick-rank {{ font-family: var(--disp); font-size: 34px; font-weight: 600; color: var(--copper);
  line-height: 1; flex: none; width: 46px; }}
.pick-body {{ min-width: 0; }}
.pick-head {{ display: flex; flex-wrap: wrap; align-items: baseline; gap: 8px 10px; }}
.pick-tkr {{ font-family: var(--mono); font-weight: 700; font-size: 18px; color: var(--ink); }}
.pick-nm {{ color: var(--mut); font-size: 14px; }}
.pick-type {{ font-family: var(--mono); font-size: 10px; letter-spacing: .1em; text-transform: uppercase;
  color: var(--copper); background: var(--copper-soft); border: 1px solid rgba(214,144,79,.3);
  border-radius: 3px; padding: 2px 7px; }}
.pick-stats {{ display: flex; flex-wrap: wrap; gap: 6px 16px; margin: 8px 0 10px;
  font-family: var(--mono); font-size: 12.5px; }}
.ps-k {{ color: var(--mut); font-size: 10px; letter-spacing: .06em; text-transform: uppercase; }}
.pick-thesis {{ margin: 0; font-size: 13.8px; color: #C6C9CE; }}
.pick-why, .pick-risk {{ margin: 7px 0 0; font-size: 13px; color: #C6C9CE; }}
.pick-lbl {{ font-family: var(--mono); font-size: 10px; letter-spacing: .1em; text-transform: uppercase;
  color: var(--copper); margin-right: 6px; }}
.pick-risk .pick-lbl {{ color: var(--warn); }}

/* insights */
.brief {{ margin-top: 38px; }}
.insights {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 14px; }}
.insight {{ background: var(--panel); border: 1px solid var(--line); border-radius: 4px;
  padding: 18px 20px 14px; display: flex; flex-direction: column; gap: 8px; }}
.insight h3 {{ margin: 0; font-size: 16.5px; line-height: 1.35; text-wrap: balance; font-weight: 600; }}
.insight p {{ margin: 0; font-size: 13.8px; color: #C6C9CE; }}
.insight .tag {{ display: inline-block; font-family: var(--mono); font-size: 10.5px;
  letter-spacing: .12em; color: var(--copper); background: var(--copper-soft);
  border: 1px solid rgba(214,144,79,.3); border-radius: 3px; padding: 2px 8px; }}
.sm-tag {{ color: #7FA7D9; background: rgba(127,167,217,.13); border-color: rgba(127,167,217,.3); }}
.matters {{ border-top: 1px solid var(--line); padding-top: 8px; }}
.matters-label {{ font-family: var(--mono); font-size: 10px; letter-spacing: .12em;
  text-transform: uppercase; color: var(--copper); margin-right: 6px; }}
.sources {{ font-size: 12px; color: var(--dim); }}
.sources a {{ color: var(--mut); border-bottom-color: var(--line); }}
.watchnote {{ margin: 16px 0 0; padding: 10px 14px; background: var(--copper-soft);
  border: 1px solid rgba(214,144,79,.3); border-radius: 4px; font-size: 13.5px; }}
.smart {{ margin-top: 38px; }}
.sm-note {{ background: rgba(127,167,217,.1); border-color: rgba(127,167,217,.3); }}

/* etf shelf */
.etf-sec {{ margin-top: 38px; }}
table.etf-table {{ min-width: 900px; }}
.etf-role {{ color: var(--mut); font-size: 11px; margin-left: 8px; font-family: var(--body); }}
.etf-holds {{ text-align: left; font-family: var(--body); color: var(--mut); white-space: normal;
  min-width: 240px; font-size: 12.5px; }}

/* layers / tables */
.stack {{ margin-top: 44px; }}
.layer {{ margin-top: 34px; }}
.layer-head {{ display: flex; gap: 16px; align-items: flex-start; margin-bottom: 12px; }}
.layer-rail {{ flex: none; width: 40px; display: flex; flex-direction: column; align-items: center; }}
.layer-num {{ font-family: var(--disp); font-size: 22px; font-weight: 600; color: var(--copper);
  border: 1px solid rgba(214,144,79,.45); border-radius: 3px; width: 40px; height: 40px;
  display: grid; place-items: center; background: var(--copper-soft); }}
.layer-kicker {{ font-family: var(--mono); font-size: 10.5px; letter-spacing: .16em;
  color: var(--copper); margin: 0 0 2px; }}
.layer h2 {{ font-family: var(--disp); font-weight: 600; letter-spacing: .06em;
  text-transform: uppercase; font-size: 21px; margin: 0; }}
.layer-desc {{ color: var(--mut); font-size: 13px; margin: 3px 0 0; max-width: 68ch; }}
.table-wrap {{ overflow-x: auto; border: 1px solid var(--line); border-radius: 4px;
  background: var(--panel); }}
table {{ border-collapse: collapse; width: 100%; min-width: 880px; font-size: 13px; }}
table.mini {{ min-width: 0; }}
th, td {{ padding: 8px 10px; text-align: right; white-space: nowrap; }}
th {{ font-family: var(--mono); font-size: 10.5px; letter-spacing: .08em; text-transform: uppercase;
  color: var(--mut); border-bottom: 1px solid var(--line); cursor: pointer; user-select: none;
  position: sticky; top: 0; background: var(--panel-2); }}
th:hover {{ color: var(--copper); }}
th[data-tip] {{ cursor: help; text-decoration: underline dotted rgba(140,150,164,.5); text-underline-offset: 3px; }}
th .arr {{ color: var(--copper); }}
th:first-child, td:first-child {{ text-align: left; padding-left: 14px; }}
tbody tr {{ border-bottom: 1px solid rgba(43,54,68,.55); }}
tbody tr:last-child {{ border-bottom: none; }}
tbody tr:hover {{ background: rgba(214,144,79,.05); }}
td {{ font-family: var(--mono); font-variant-numeric: tabular-nums; color: #CDD2D9; }}
td.co {{ font-family: var(--body); }}
td.co .sym {{ font-family: var(--mono); font-weight: 700; color: var(--ink); }}
td.co .nm {{ color: var(--mut); font-size: 12px; margin-left: 7px; }}
.pos {{ color: var(--up); }} .neg {{ color: var(--down); }}
.m-good {{ color: var(--up); }} .m-warn {{ color: var(--warn); }} .m-bad {{ color: var(--down); }}
.m-na {{ color: var(--dim); }}
td.spark-cell {{ padding: 3px 10px 0; }}

/* liquidation watch */
.liq {{ margin-top: 38px; }}
.liq-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 14px; }}
.liq-card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 4px; padding: 16px 18px; }}
.liq-card h4 {{ margin: 0 0 8px; font-size: 13px; letter-spacing: .04em; }}
.liq-card .liq-h2 {{ margin-top: 14px; }}
.liq-tbl table.mini {{ min-width: 0; }}
.liq-list {{ margin: 0; font-family: var(--mono); font-size: 13px; color: #C6C9CE; line-height: 1.8; }}
.liq-list strong {{ color: var(--ink); }}
.verdict {{ margin: 10px 0 0; font-size: 13px; }}

/* primer */
.primer {{ margin-top: 40px; }}
.prim-intro {{ font-size: 14px; color: #C6C9CE; max-width: 85ch; margin: 0 0 16px; }}
.prim-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 12px; }}
.prim-block {{ background: var(--panel); border: 1px solid var(--line); border-radius: 4px; padding: 14px 16px; }}
.prim-block h4 {{ margin: 0 0 5px; font-size: 13.5px; color: var(--copper); }}
.prim-block p {{ margin: 0; font-size: 13px; color: #C6C9CE; }}

/* 30-day range bar */
.rbar {{ position: relative; width: 76px; height: 6px; background: var(--panel-2);
  border: 1px solid var(--line); border-radius: 3px; display: inline-block; vertical-align: middle; }}
.rbar span {{ position: absolute; top: -3px; width: 3px; height: 10px; border-radius: 1px;
  background: var(--ink); transform: translateX(-50%); }}
.rbar.r-lo span {{ background: var(--down); }}
.rbar.r-hi span {{ background: var(--up); }}

/* gov badge */
.govbadge {{ display: inline-block; margin-left: 7px; padding: 1px 6px; border-radius: 3px;
  font-family: var(--mono); font-size: 9.5px; letter-spacing: .1em; font-weight: 700;
  color: #7FB2E5; background: rgba(127,178,229,.12); border: 1px solid rgba(127,178,229,.35);
  cursor: help; vertical-align: 1px; }}

/* bull score */
.score {{ display: inline-block; min-width: 40px; text-align: center; padding: 2px 8px;
  border-radius: 3px; font-weight: 700; font-size: 12.5px; cursor: help; }}
.sc-good {{ background: rgba(87,181,131,.16); color: var(--up); border: 1px solid rgba(87,181,131,.4); }}
.sc-mid {{ background: rgba(212,175,84,.14); color: var(--warn); border: 1px solid rgba(212,175,84,.4); }}
.sc-bad {{ background: rgba(224,101,79,.14); color: var(--down); border: 1px solid rgba(224,101,79,.4); }}
.daychip {{ font-size: 11px; }}
td.score-cell {{ text-align: center; }}

/* cot */
.cot {{ margin-top: 38px; }}
.cot-table td.cot-read {{ white-space: normal; font-family: var(--body); font-size: 12.5px;
  color: var(--mut); min-width: 260px; text-align: left; }}
.cot .verdict {{ margin-top: 10px; font-size: 13px; color: #C6C9CE; }}

/* folded deep-dive sections */
.fold {{ margin-top: 26px; border: 1px solid var(--line); border-radius: 4px; background: var(--panel); }}
.fold > summary {{ cursor: pointer; list-style: none; padding: 14px 18px; display: flex;
  align-items: baseline; gap: 12px; }}
.fold > summary::-webkit-details-marker {{ display: none; }}
.fold > summary::before {{ content: "\\25B8"; color: var(--copper); }}
.fold[open] > summary::before {{ content: "\\25BE"; }}
.fold-title {{ font-family: var(--disp); text-transform: uppercase; letter-spacing: .1em;
  font-size: 14.5px; font-weight: 600; color: var(--copper); }}
.fold-hint {{ margin-left: auto; font-size: 11px; color: var(--dim); font-family: var(--mono); }}
.fold[open] .fold-hint {{ display: none; }}
.fold > section {{ margin-top: 0; padding: 0 18px 18px; }}
.pick-deep {{ margin-top: 8px; border-top: 1px solid var(--line); padding-top: 8px; }}
.pick-deep > summary {{ cursor: pointer; font-size: 12.5px; color: var(--mut);
  font-family: var(--mono); list-style: none; }}
.pick-deep > summary::-webkit-details-marker {{ display: none; }}
.pick-deep > summary::before {{ content: "\\25B8 "; color: var(--copper); }}
.pick-deep[open] > summary::before {{ content: "\\25BE "; }}

/* legend */
.legend {{ margin-top: 48px; border-top: 1px solid var(--line); padding-top: 26px; }}
.legend-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 12px; }}
.lg {{ background: var(--panel); border: 1px solid var(--line); border-radius: 4px; padding: 14px 16px; }}
.lg h4 {{ margin: 0 0 4px; font-size: 13.5px; }}
.lg h4 .k {{ font-family: var(--mono); color: var(--copper); }}
.lg p {{ margin: 0; font-size: 12.8px; color: var(--mut); }}
.lg .rule {{ display: block; margin-top: 6px; font-family: var(--mono); font-size: 11.5px; color: #AEB6C0; }}
.foot {{ margin-top: 36px; color: var(--dim); font-size: 12px; border-top: 1px solid var(--line);
  padding-top: 14px; }}
/* pick grade + extra blocks */
.pick-grade {{ margin-left: auto; font-family: var(--disp); font-weight: 600; font-size: 26px;
  line-height: 1; width: 40px; height: 40px; display: grid; place-items: center; border-radius: 5px;
  border: 1px solid var(--line); cursor: help; }}
.pick-grade.g-a {{ color: var(--up); background: rgba(87,181,131,.14); border-color: rgba(87,181,131,.4); }}
.pick-grade.g-b {{ color: var(--copper); background: var(--copper-soft); border-color: rgba(214,144,79,.4); }}
.pick-grade.g-c {{ color: var(--warn); background: rgba(212,175,84,.12); border-color: rgba(212,175,84,.4); }}
.pick-grade.g-d, .pick-grade.g-f {{ color: var(--down); background: rgba(224,101,79,.12); border-color: rgba(224,101,79,.4); }}
.pick-bear {{ margin: 7px 0 0; font-size: 13px; color: #C6C9CE; }}
.pick-bear .bear {{ color: var(--down); }}
.pick-fac {{ margin: 7px 0 0; font-size: 12.8px; color: var(--mut); }}
.pick-comp {{ margin: 8px 0 0; }}
.pick-comp ul {{ margin: 4px 0 0; padding-left: 16px; }}
.pick-comp li {{ font-size: 12.8px; color: #C6C9CE; margin: 2px 0; }}
.pick-comp strong {{ color: var(--ink); font-family: var(--mono); font-size: 12px; }}

/* quant lab */
.quant {{ margin-top: 38px; }}
.qcards {{ display: grid; gap: 14px; }}
.qcard {{ background: var(--panel); border: 1px solid var(--line); border-radius: 4px; padding: 16px 18px; }}
.qcard-head {{ display: flex; flex-wrap: wrap; align-items: baseline; gap: 8px 12px; border-bottom: 1px solid var(--line); padding-bottom: 10px; }}
.qregime {{ margin-left: auto; font-family: var(--mono); font-size: 11.5px; color: var(--mut); }}
.qcard h5 {{ margin: 0 0 7px; font-size: 11px; letter-spacing: .1em; text-transform: uppercase; color: var(--copper); font-family: var(--mono); }}
.qstats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(96px, 1fr)); gap: 8px; margin: 12px 0; }}
.qstat {{ background: var(--panel-2); border: 1px solid var(--line); border-radius: 3px; padding: 7px 9px; display: flex; flex-direction: column; gap: 2px; }}
.qk {{ font-size: 9.5px; letter-spacing: .06em; text-transform: uppercase; color: var(--mut); }}
.qv {{ font-family: var(--mono); font-size: 15px; font-variant-numeric: tabular-nums; }}
.qsub {{ font-family: var(--mono); font-size: 11px; color: var(--mut); }}
.qsplit {{ display: grid; grid-template-columns: 1.15fr 1fr; gap: 16px; margin-top: 4px; }}
table.qbt {{ min-width: 0; width: 100%; font-size: 12.5px; }}
table.qbt th {{ position: static; background: var(--panel-2); }}
table.qbt td.co {{ color: var(--ink); }}
.qbt .qhint {{ color: var(--mut); font-family: var(--body); font-size: 11.5px; text-align: right; }}
.qnote {{ margin: 8px 0 0; font-size: 12px; color: var(--mut); }}
.qtrade-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }}
.qtrade-grid > div {{ background: var(--panel-2); border: 1px solid var(--line); border-radius: 3px; padding: 8px 10px; display: flex; flex-direction: column; gap: 1px; }}
.qreason {{ margin: 9px 0 0; font-size: 12.8px; color: #C6C9CE; }}
.qmc {{ margin-top: 14px; border-top: 1px solid var(--line); padding-top: 12px; }}
.mc-wrap {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; }}
.mc-head {{ display: flex; justify-content: space-between; font-size: 12.5px; margin-bottom: 5px; }}
.mc-head span:first-child {{ color: var(--ink); font-weight: 600; }}
.mc-pl {{ color: var(--warn); font-family: var(--mono); }}
.mc-gauge {{ display: flex; height: 12px; border-radius: 3px; overflow: hidden; border: 1px solid var(--line); }}
.mc-gauge .loss {{ background: rgba(224,101,79,.75); }}
.mc-gauge .gain {{ background: rgba(87,181,131,.6); }}
.mc-pct {{ display: flex; flex-wrap: wrap; gap: 4px 14px; margin-top: 7px; font-size: 12px; color: var(--mut); }}
.mc-pct b {{ font-family: var(--mono); }}
.qport {{ margin-top: 16px; }}
.qport h4 {{ margin: 0 0 8px; font-size: 13.5px; }}
.qmethod {{ margin: 14px 0 0; font-size: 11.5px; color: var(--dim); font-style: italic; }}

/* macro playbook */
.macrostrat {{ margin-top: 38px; }}
.mdrivers {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; }}
.mdriver {{ background: var(--panel); border: 1px solid var(--line); border-radius: 4px; padding: 14px 16px; }}
.mdriver h5 {{ margin: 0 0 5px; font-size: 13.5px; color: var(--copper); }}
.mread {{ margin: 0 0 6px; font-size: 12.5px; color: var(--ink); font-family: var(--mono); }}
.mplay {{ margin: 0; font-size: 13px; color: #C6C9CE; }}
.mscen {{ margin-top: 14px; background: var(--panel); border: 1px solid var(--line); border-radius: 4px; padding: 14px 18px; }}
.mscen h4 {{ margin: 0 0 8px; font-size: 13.5px; }}
.mscen ul {{ margin: 0; padding-left: 18px; }}
.mscen li {{ font-size: 13px; color: #C6C9CE; margin: 5px 0; }}
.mtrig {{ color: var(--ink); font-weight: 600; }}
.mpos {{ margin: 14px 0 0; padding: 12px 16px; background: var(--copper-soft); border: 1px solid rgba(214,144,79,.3); border-radius: 4px; font-size: 13.5px; color: #E7E2D8; }}

/* custom KPI tooltip (hover on desktop, tap on touch; escapes table scroll clipping) */
[data-tip] {{ cursor: help; }}
th[data-tip], td[data-tip] {{ cursor: help; }}
#kpi-tip {{ position: fixed; z-index: 9999; max-width: 300px; background: #0C1116; color: var(--ink);
  border: 1px solid var(--copper); border-radius: 6px; padding: 9px 12px; font-family: var(--body);
  font-size: 12.6px; line-height: 1.46; box-shadow: 0 10px 30px rgba(0,0,0,.55); pointer-events: none;
  visibility: hidden; opacity: 0; transform: translateY(4px); transition: opacity .12s ease, transform .12s ease; }}
#kpi-tip.show {{ visibility: visible; opacity: 1; transform: translateY(0); }}
.tiphint {{ cursor: default; }}

@media (max-width: 640px) {{ .mast h1 {{ font-size: 24px; }} table {{ min-width: 860px; }} table.mini {{ min-width: 0; }} table.qbt {{ min-width: 0; }} .pick {{ flex-direction: column; gap: 8px; }} .pick-rank {{ width: auto; }} .qsplit {{ grid-template-columns: 1fr; }} }}
</style>

<div class="wrap">
  <header class="mast">
    <h1>Long-Term Investing <span class="amp">Monitor</span></h1>
    <span class="date">{E(INS["date"])}</span>
  </header>
  <p class="kicker-sub">Built for long-term holding decisions, in priority order: the macro regime, a six-check Bull Score on every name (valuation, profitability, balance sheet, trend), and the briefing. Flow and positioning data lives in the collapsed timing tools at the bottom: it helps you time buys, never choose them.</p>
  <p class="asof">{E(INS["asof"])} Refreshed daily.</p>
  <p class="tiphint">&#9432; Hover any KPI, column header, or macro chip for a plain-English explanation (on a phone, tap it).</p>

  <div class="macro">{macro_strip()}</div>
  <div class="indices" id="indices"></div>

  {top_picks_section()}

  <section class="brief">
    <h2 class="section-title">Daily Briefing</h2>
    <p class="section-sub">What moved, what it means for long-term positions, and what to watch next.</p>
    <div class="insights">{insight_cards()}</div>
    <p class="watchnote">&#9202; {E(INS["watchlist_notes"])}</p>
  </section>

  {macro_strategy_section()}

  <section class="stack">
    <h2 class="section-title">Sheet 1: Established, Large-Dollar Names</h2>
    <p class="section-sub">Nine columns, one verdict. Each row shows the numbers that decide a long-term bull case (valuation, profitability, balance sheet, trend, institutional selling) and a Bull Score counting how many of the six checks pass. Tables sort by Bull Score; click any header to re-sort, hover anything for a plain-English definition, hover a score to see which checks pass and fail. A <span class="govbadge">GOV</span> chip means the US government holds a stake in the company or is its anchor customer; hover it for the story.</p>
    {sector_sections(1)}
  </section>

  <section class="stack stack-small">
    <h2 class="section-title">Sheet 2: Smaller-Dollar &amp; Speculative</h2>
    <p class="section-sub">The identical sheet, same columns and Bull Score logic, for the smaller and earlier-stage names. Expect low scores here: most are pre-profit, so they fail the valuation and profitability checks by construction. On this sheet the score mostly measures how speculative the bet is; size these like venture stakes, not core holdings.</p>
    {sector_sections(2)}
  </section>

  {etf_shelf()}

  {fold("Timing tool: Liquidation Watch (is big money selling right now?)", liquidation_watch())}

  {fold("Timing tool: CFTC institutional positioning (who is long, who is short)", cot_section())}

  {fold("Timing tool: Smart Money &amp; Political Signals (Congress, 13Fs, prime-brokerage headlines)", smart_money_section())}

  {fold("Quant Lab: backtests, trade levels &amp; Monte Carlo on the Top 3", quant_lab_section())}

  {fold("Primer: how AI infrastructure makes money, layer by layer", primer_section())}

  <section class="legend">
    <h2 class="section-title">Field Guide: The Numbers That Decide a Long-Term Buy</h2>
    <p class="section-sub">Every metric on the board, what high and low normally mean, and the threshold each Bull Score check uses. These are also the hover tooltips on every column.</p>
    <div class="legend-grid">
      <div class="lg"><h4><span class="k">P/E &amp; Fwd P/E</span> The price of a dollar of profit</h4>
        <p>P/E is the share price divided by yearly profit per share: literally the dollars you pay for each dollar the company earns. A LOW P/E (under ~15) normally means the stock is cheap OR the market doubts the profits will last (value trap risk). A HIGH P/E (over ~30) normally means the market expects strong growth and you are pre-paying for it; if the growth disappoints, the multiple deflates hard (this month's AI selloff was exactly that). Forward P/E uses next year's expected profit: when it is far below the trailing P/E, analysts expect earnings to grow into the price. Always compare within an industry, and pair with PEG before judging.</p>
        <span class="rule">check: Fwd P/E below trailing P/E = earnings expected to grow</span></div>
      <div class="lg"><h4><span class="k">PEG</span> The growth-adjusted price tag</h4>
        <p>P/E divided by the expected profit growth rate. It answers the question P/E alone cannot: is the growth worth the price? Around 1.0 is fair; under 1.0 you are getting growth at a discount; over 2.0 you are paying up on faith.</p>
        <span class="rule">check: PEG &le; 1.5 &middot; green &le; 1.0 &middot; amber &gt; 2.0</span></div>
      <div class="lg"><h4><span class="k">ROE</span> The quality engine</h4>
        <p>Profit per dollar of shareholder capital. This is the compounding engine of a long-term holding: 10-20% is strong, sustained above 20% is elite, negative means the company burns money. High ROE with low debt is the quality signature.</p>
        <span class="rule">check: ROE &ge; 10% &middot; red if negative</span></div>
      <div class="lg"><h4><span class="k">D/E</span> The survival test</h4>
        <p>Debt versus the shareholders' own money. Low debt means the company controls its fate through downturns and high-rate periods; high debt means refinancing risk decides for it. Matters double while the Fed is hawkish.</p>
        <span class="rule">check: D/E &le; 1.5 &middot; green &le; 0.5</span></div>
      <div class="lg"><h4><span class="k">vs 200D</span> The long-term trend</h4>
        <p>Distance from the 200-day moving average, the classic dividing line between long-term uptrend and downtrend. Above it, time is on your side; below it, you are fighting the tide (fine for slow accumulation of quality, bad for lump sums). More than 10% below is serious trend damage.</p>
        <span class="rule">check: price above the 200-day &middot; red &lt; -10%</span></div>
      <div class="lg"><h4><span class="k">D-Days</span> Is big money leaving?</h4>
        <p>Distribution days: sessions in the last 25 that fell at least 0.2% on above-average volume, the footprint of institutions selling into the market. A cluster warns you even when price looks fine. &#9888; flags a heavy dump (down &ge;1.5% on &ge;1.5x volume) within the last 5 sessions.</p>
        <span class="rule">check: fewer than 5 and no &#9888; &middot; amber at 3-4</span></div>
      <div class="lg"><h4><span class="k">Bull Score</span> The verdict column</h4>
        <p>How many of the six checks above pass right now. 5-6: the data supports a bull case (valuation, quality, safety, trend and flows all agree). 3-4: mixed, the thesis needs a specific reason. 0-2: the data argues against it; if you still want it, you are making a contrarian bet and should size it that way. Hover any score to see exactly which checks fail.</p>
        <span class="rule">5-6 green &middot; 3-4 amber &middot; 0-2 red</span></div>
      <div class="lg"><h4><span class="k">COT</span> Who is positioned where</h4>
        <p>A timing aid only: it never makes something a good or bad business. The CFTC's weekly Commitments of Traders filing shows the actual futures positions of asset managers (slow, long-term money) and leveraged funds (hedge funds). Watch the week-over-week change, not the level: hedge funds are structurally short index futures as a hedge. Extremes are contrarian: record shorts often precede rallies, record longs precede tops.</p>
        <span class="rule">published Fridays, data as of Tuesday</span></div>
      <div class="lg"><h4><span class="k">Yield curve &amp; VIX</span> The two macro tells</h4>
        <p>The 10Y-2Y yield curve inverts (goes negative) when the bond market expects trouble: it has preceded most recessions by 6-18 months. The VIX prices expected turbulence: under 15 is calm, over 25 is fear. Long-term buyers do their best buying when the VIX is high, not when it is comfortable.</p>
        <span class="rule">curve negative = recession warning &middot; VIX &gt; 25 = fear (and opportunity)</span></div>
    </div>
  </section>

  <p class="foot">Prices and fundamentals from StockAnalysis.com and Yahoo Finance as of the {E(CLOSE_DATE)} close. ETF expense ratios and holdings are approximate reference figures; verify with the fund provider. Fundamentals are trailing-12-month unless noted. This dashboard is research, not financial advice; verify figures and do your own diligence before trading. Deeper dives: <a href="https://finance.yahoo.com" target="_blank" rel="noopener">Yahoo Finance</a> &middot; <a href="https://www.morningstar.com" target="_blank" rel="noopener">Morningstar</a>.</p>
</div>

<script>
const DATA = {json.dumps(DATA)};

// ---- plain-English tooltip engine: hover on desktop, tap on touch, and it
// escapes the table's horizontal-scroll clipping by living on document.body ----
function harvest(root) {{
  (root || document).querySelectorAll("[title]").forEach(el => {{
    el.dataset.tip = el.getAttribute("title");
    el.removeAttribute("title");
  }});
}}
(function () {{
  const tip = document.createElement("div");
  tip.id = "kpi-tip"; tip.setAttribute("role", "tooltip");
  document.body.appendChild(tip);
  let cur = null;
  function show(el) {{
    if (!el.dataset.tip) return;
    cur = el; tip.textContent = el.dataset.tip; tip.classList.add("show");
    const r = el.getBoundingClientRect(), tw = tip.offsetWidth, th = tip.offsetHeight;
    let left = Math.max(8, Math.min(r.left + r.width / 2 - tw / 2, window.innerWidth - tw - 8));
    let top = r.top - th - 10;
    if (top < 8) top = r.bottom + 10;
    tip.style.left = left + "px"; tip.style.top = top + "px";
  }}
  function hide() {{ cur = null; tip.classList.remove("show"); }}
  const canHover = !window.matchMedia || window.matchMedia("(hover: hover)").matches;
  if (canHover) {{
    document.addEventListener("pointerover", e => {{
      const el = e.target.closest("[data-tip]"); if (el && el !== cur) show(el);
    }});
    document.addEventListener("pointerout", e => {{
      const el = e.target.closest("[data-tip]"); if (!el) return;
      if (e.relatedTarget && el.contains(e.relatedTarget)) return;
      hide();
    }});
  }}
  document.addEventListener("click", e => {{
    const el = e.target.closest("[data-tip]");
    if (!el) {{ hide(); return; }}
    if (cur === el) hide(); else show(el);
  }});
  window.addEventListener("scroll", hide, true);
  window.addEventListener("resize", hide);
  harvest(document);
}})();

const fmt = (v, d=2) => (v === null || v === undefined || Number.isNaN(v)) ? null
  : Number(v).toLocaleString("en-US", {{minimumFractionDigits: d, maximumFractionDigits: d}});

function cell(v, cls, txt) {{
  return v === null ? '<td class="m-na">n/a</td>' : `<td class="${{cls||''}}">${{txt}}</td>`;
}}
function flag(v, rules) {{
  if (v === null || v === undefined) return "m-na";
  for (const [test, cls] of rules) if (test(v)) return cls;
  return "";
}}

// The six bull checks: each answers one question a long-term buyer needs a
// yes to. true = pass, false = fail, null = not enough data to judge.
const CHECKS = [
  {{key: "valuation", label: "Growth is cheap (PEG \\u2264 1.5)",
    test: r => r.peg === null || r.peg === undefined ? null : r.peg <= 1.5}},
  {{key: "profit", label: "Profitable & efficient (ROE \\u2265 10%)",
    test: r => r.roe === null || r.roe === undefined ? null : r.roe >= 10}},
  {{key: "growth", label: "Earnings expected to grow (Fwd P/E below trailing)",
    test: r => (r.fpe === null || r.fpe === undefined) ? null
      : (r.pe === null || r.pe === undefined) ? true : r.fpe < r.pe}},
  {{key: "debt", label: "Balance sheet safe (D/E \\u2264 1.5)",
    test: r => r.de === null || r.de === undefined ? null : r.de <= 1.5}},
  {{key: "trend", label: "Long-term uptrend (price above 200-day avg)",
    test: r => r.v200 === null || r.v200 === undefined ? null : r.v200 > 0}},
  {{key: "selling", label: "No institutional selling (D-Days < 5, no heavy dumps)",
    test: r => r.dd === null || r.dd === undefined ? null : (r.dd < 5 && !r.hv)}},
];
function bullScore(r) {{
  let pass = 0, avail = 0;
  const detail = [];
  for (const c of CHECKS) {{
    const v = c.test(r);
    if (v === null) {{ detail.push("? " + c.label); continue; }}
    avail++;
    if (v) {{ pass++; detail.push("\\u2713 " + c.label); }}
    else detail.push("\\u2717 " + c.label);
  }}
  return {{pass, avail, detail}};
}}

const COLS = [
  {{k:"co", label:"Company", tip:"The company's ticker symbol and name.", sort:(r)=>r.s}},
  {{k:"p", label:"Price", tip:"The most recent share price, with the latest session's move.", sort:(r)=>r.p}},
  {{k:"spark", label:"52 wk", tip:"A mini chart of weekly closing prices over the past year. Green ended the year up, red down. The copper dot is the latest close.", sort:(r)=>r.y}},
  {{k:"fpe", label:"Fwd P/E", tip:"Forward P/E: today's price divided by next year's EXPECTED profit per share. Low (under ~15) usually means cheap or doubted; high (over ~30) means the market expects big growth and has already paid for some of it. Compare within an industry, not across.", sort:(r)=>r.fpe}},
  {{k:"peg", label:"PEG", tip:"PEG: the P/E adjusted for how fast profits are growing. Around 1.0 is fair value, under 1.0 growth is going cheap, over 2.0 you are paying up. The single best one-number valuation check for a growth stock.", sort:(r)=>r.peg}},
  {{k:"roe", label:"ROE", tip:"Return on equity: profit earned per dollar of shareholder money. 10-20% is strong, sustained higher is elite, negative means losses. Quality compounds through ROE.", sort:(r)=>r.roe}},
  {{k:"de", label:"D/E", tip:"Debt to equity: how much borrowed money the company runs on. Under 0.5 is conservative; over 1.5 is risky when rates are high.", sort:(r)=>r.de}},
  {{k:"v200", label:"vs 200D", tip:"How far the price sits above or below its 200-day average, the long-term trend line. Above = long-term uptrend intact. Buying quality below it is fine for accumulation, but the trend is against you until it reclaims the line.", sort:(r)=>r.v200}},
  {{k:"dd", label:"D-Days", tip:"Distribution days: sessions in the last 25 that fell on heavier-than-usual volume, the footprint of institutions selling. 5+ is a warning; the triangle flags a heavy one-day dump this week.", sort:(r)=>r.dd}},
  {{k:"score", label:"Bull Score", tip:"How many of the six long-term bull checks this name passes right now: cheap growth (PEG), profitability (ROE), growing earnings (Fwd P/E vs trailing), safe balance sheet (D/E), long-term uptrend (vs 200D), and no institutional selling (D-Days). Hover a score to see which checks pass and fail. 5-6 = the bull case is supported by the data; 0-2 = the data argues against it.", sort:(r)=>bullScore(r).pass}},
];
function parseMc(s) {{
  if (!s) return null;
  const m = String(s).match(/([\\d.]+)([TBM]?)/);
  if (!m) return null;
  const mult = {{T: 1e12, B: 1e9, M: 1e6, "": 1}}[m[2]];
  return parseFloat(m[1]) * mult;
}}

function sparkline(canvas, pts, upTrend) {{
  const dpr = window.devicePixelRatio || 1, w = 110, h = 26;
  canvas.width = w * dpr; canvas.height = h * dpr;
  canvas.style.width = w + "px"; canvas.style.height = h + "px";
  const ctx = canvas.getContext("2d"); ctx.scale(dpr, dpr);
  if (!pts || pts.length < 2) return;
  const min = Math.min(...pts), max = Math.max(...pts), range = (max - min) || 1;
  const x = i => 2 + i * (w - 6) / (pts.length - 1);
  const y = v => h - 3 - (v - min) / range * (h - 7);
  const color = upTrend ? "#57B583" : "#E0654F";
  ctx.beginPath();
  pts.forEach((v, i) => i ? ctx.lineTo(x(i), y(v)) : ctx.moveTo(x(i), y(v)));
  ctx.strokeStyle = color; ctx.globalAlpha = .85; ctx.lineWidth = 1.3; ctx.stroke();
  ctx.lineTo(x(pts.length - 1), h); ctx.lineTo(x(0), h); ctx.closePath();
  ctx.globalAlpha = .12; ctx.fillStyle = color; ctx.fill();
  ctx.globalAlpha = 1;
  ctx.beginPath();
  ctx.arc(x(pts.length - 1), y(pts[pts.length - 1]), 2.1, 0, 7);
  ctx.fillStyle = "#D6904F"; ctx.fill();
}}

function rangeBar(r) {{
  if (r.p30 === null || r.p30 === undefined) return '<td class="m-na">n/a</td>';
  const cls = r.p30 <= 25 ? "r-lo" : r.p30 >= 75 ? "r-hi" : "";
  return `<td title="30-day close range: $${{fmt(r.lo30)}} to $${{fmt(r.hi30)}} &middot; now at ${{r.p30}}% of range">` +
    `<span class="rbar ${{cls}}"><span style="left:${{r.p30}}%"></span></span></td>`;
}}

function rowHtml(r) {{
  const dayCls = r.cp > 0 ? "pos" : r.cp < 0 ? "neg" : "";
  const ddTxt = r.dd === null || r.dd === undefined ? null
    : r.dd + (r.hv ? " \\u26A0" : "");
  const sc = bullScore(r);
  const scCls = sc.avail === 0 ? "m-na" : sc.pass >= 5 ? "sc-good" : sc.pass >= 3 ? "sc-mid" : "sc-bad";
  const scTxt = sc.avail === 0 ? "n/a" : `${{sc.pass}}/${{sc.avail}}`;
  const dayTxt = r.cp === null || r.cp === undefined ? "" :
    ` <span class="${{dayCls}} daychip">${{(r.cp > 0 ? "+" : "") + fmt(r.cp, 1)}}%</span>`;
  const gov = r.gov ? `<span class="govbadge" title="${{r.gov.replace(/"/g, "&quot;")}}">GOV</span>` : "";
  return `<tr>
    <td class="co"><span class="sym">${{r.s}}</span><span class="nm">${{r.nm}}</span>${{gov}}</td>
    ${{cell(r.p, "", "$" + fmt(r.p) + dayTxt)}}
    <td class="spark-cell"><canvas data-sym="${{r.s}}" role="img" aria-label="52 week price trend for ${{r.s}}"></canvas></td>
    ${{cell(r.fpe, flag(r.fpe, [[v => v > 40, "m-warn"], [v => v <= 20, "m-good"]]), fmt(r.fpe, 1))}}
    ${{cell(r.peg, flag(r.peg, [[v => v <= 1, "m-good"], [v => v > 2, "m-warn"]]), fmt(r.peg))}}
    ${{cell(r.roe, flag(r.roe, [[v => v < 0, "m-bad"], [v => v >= 10, "m-good"]]), fmt(r.roe, 1) + "%")}}
    ${{cell(r.de, flag(r.de, [[v => v <= 0.5, "m-good"], [v => v > 1.5, "m-warn"]]), fmt(r.de))}}
    ${{cell(r.v200, flag(r.v200, [[v => v > 0, "m-good"], [v => v < -10, "m-bad"], [v => true, "m-warn"]]), (r.v200 > 0 ? "+" : "") + fmt(r.v200, 1) + "%")}}
    ${{cell(r.dd, flag(r.dd, [[v => v >= 5 || r.hv, "m-bad"], [v => v >= 3, "m-warn"], [v => true, "m-good"]]), ddTxt)}}
    <td class="score-cell"><span class="score ${{scCls}}" title="${{sc.detail.join("\\n")}}">${{scTxt}}</span></td>
  </tr>`;
}}

const sortState = {{}};
function renderTable(tbl, rows, sortKey, dir) {{
  const sorted = [...rows];
  if (sortKey) {{
    const col = COLS.find(c => c.k === sortKey);
    sorted.sort((a, b) => {{
      const av = col.sort(a), bv = col.sort(b);
      if (av === null || av === undefined) return 1;
      if (bv === null || bv === undefined) return -1;
      return (av < bv ? -1 : av > bv ? 1 : 0) * dir;
    }});
  }}
  tbl.innerHTML = "<thead><tr>" + COLS.map(c =>
    `<th data-k="${{c.k}}" title="${{c.tip || ''}}">${{c.label}}${{sortKey === c.k ? `<span class="arr"> ${{dir > 0 ? "\\u25B4" : "\\u25BE"}}</span>` : ""}}</th>`
  ).join("") + "</tr></thead><tbody>" + sorted.map(rowHtml).join("") + "</tbody>";
  harvest(tbl);
  tbl.querySelectorAll("canvas").forEach(cv => {{
    const r = rows.find(x => x.s === cv.dataset.sym);
    if (r && r.spark.length) sparkline(cv, r.spark, r.spark[r.spark.length - 1] >= r.spark[0]);
  }});
  tbl.querySelectorAll("th").forEach(th => th.addEventListener("click", () => {{
    const k = th.dataset.k;
    const st = sortState[tbl.dataset.sector] || {{}};
    const nd = st.k === k ? -st.dir : (k === "co" ? 1 : -1);
    sortState[tbl.dataset.sector] = {{k, dir: nd}};
    renderTable(tbl, rows, k, nd);
  }}));
}}

document.querySelectorAll("table[data-sector]").forEach(tbl => {{
  const sec = DATA.sectors.find(s => s.sector === tbl.dataset.sector);
  if (sec) {{
    sortState[tbl.dataset.sector] = {{k: "score", dir: -1}};
    renderTable(tbl, sec.rows, "score", -1);
  }}
}});

const idxWrap = document.getElementById("indices");
Object.entries(DATA.indices).forEach(([name, d]) => {{
  if (!d || d.price === undefined || d.price === null) return;
  const el = document.createElement("div");
  el.className = "idx";
  const chg = d.chgPct, cls = chg > 0 ? "pos" : chg < 0 ? "neg" : "";
  const p = d.pos || {{}};
  const posLine = p.ch30 !== undefined && p.ch30 !== null
    ? `<div class="nm" style="margin-top:2px">${{p.ch30 > 0 ? "+" : ""}}${{fmt(p.ch30, 1)}}% 30D &middot; ${{p.ddays}} d-day${{p.ddays === 1 ? "" : "s"}}</div>` : "";
  el.innerHTML = `<div class="meta"><div class="nm">${{name}}</div>
    <div class="px">$${{fmt(d.price)}} <span class="${{cls}}">${{chg > 0 ? "+" : ""}}${{fmt(chg)}}%</span></div>${{posLine}}</div>
    <canvas role="img" aria-label="52 week trend for ${{name}}"></canvas>`;
  idxWrap.appendChild(el);
  const cv = el.querySelector("canvas");
  if (d.spark && d.spark.length) sparkline(cv, d.spark, d.spark[d.spark.length - 1] >= d.spark[0]);
}});
</script>
"""

with open("dashboard.html", "w") as f:
    f.write(page)
print(f"WROTE dashboard.html ({len(page)//1024} KB)")
