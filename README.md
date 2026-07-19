# Long-Term Investing Monitor

SIMPLIFIED PHILOSOPHY (Jul 19, 2026): the board shows ONLY metrics that argue
for or against a long-term bull case: Fwd P/E, PEG, ROE, D/E, vs 200-day,
D-Days, and a six-check Bull Score per name (hover a score for the check
detail). Macro leads the page (all chips auto from FRED), institutional
positioning comes from the CFTC COT report plus Goldman prime-brokerage flow
headlines found via daily news search (GS PB data itself is proprietary).
Deep-dive sections (Quant Lab, ETF shelf, Primer, Smart Money) are collapsed
folds. Do not re-add removed columns (P/B, Beta, RSI, EPS, day%, 30D range bar,
vs 50D, mkt cap) to the board without the user asking.

Daily-refreshed market monitor built for a long-term, buy-and-hold investor. The
AI build-out value chain (semiconductors, servers/cooling, fiber optics,
electrical/conduit/steel) and nuclear power are the core, but the board is
deliberately wider: Big Tech / hyperscalers, healthcare & pharma, and a full ETF
shelf. It also generates a Top 3 Picks of the month, a Smart Money & Political
Signals section, an AI-data-center primer, and plain-English hover tooltips on
every KPI (the user is not an economist).

**Live artifact:** https://claude.ai/code/artifact/7a04e61f-e3c5-4ed9-bd92-6237c16cb9ac
(favicon 📡, title "Long-Term Investing Monitor")

## Daily refresh pipeline

Run from this directory, in order:

1. `python3 refresh_data.py` - pulls quotes, fundamentals, 1Y weekly
   sparklines, and positioning analytics (30-day range position, vs 50-day,
   distribution days, heavy liquidation events, volume ratio) for all watchlist
   tickers and ETFs, PLUS two automated macro blocks:
   - `macro_auto`: FRED series with no API key: CPI YoY (computed), Core CPI
     YoY, effective Fed Funds, 2Y yield (for the 10Y-2Y curve chip), VIX,
     WTI oil, unemployment. The whole macro strip renders from this.
   - `cot`: CFTC Traders-in-Financial-Futures weekly positioning (asset
     managers vs leveraged funds; S&P, Nasdaq, 10Y note, VIX futures) with
     week-over-week changes. Renders the Institutional Positioning section.
   Writes `market_data.json`. Takes a few minutes. No API keys needed.
1b. `python3 quant.py` - pulls ~10 years of weekly + 1 year of daily history for
   the current Top 3 picks (its `PICKS` dict) plus SPY, and computes backtests
   (CAGR, Sharpe, Sortino, max drawdown, win rate), a strategy comparison
   (buy-hold vs 40-week trend filter, plus a 3-pick portfolio), market and
   per-name regime detection, volatility-based trade levels (entry, stop,
   take-profit, R:R), and a Monte Carlo simulation (1Y and 3Y: probability of
   loss, return distribution, worst case). Pure stdlib, deterministic (fixed
   seed). Writes `quant_data.json`. If you change which tickers are in
   `top_picks`, update `PICKS` in quant.py to match and rerun.
2. Update `insights.json` - FIRST inspect market_data.json positioning data
   (index distribution-day counts, tickers at range extremes, heavy liquidation
   events, which sectors are being rotated into vs out of), THEN research the
   day's news. Rewrite these keys, keeping the same JSON shape:
   - `date`, `asof`, `close_date` (the footer date reads from `close_date`).
   - `macro` (six chips: CPI, Core CPI, Fed Funds, Oil/Energy, next CPI, next
     FOMC; the 10Y chip is auto-generated).
   - `top_picks` (3 ranked picks, sector-agnostic, ETFs allowed; each with
     rank/ticker/name/type/thesis/why_now/risk/sources plus grade/bear_case/
     competitors/factors/trade_reasoning) + `top_picks_note`. Live price/PEG/ROE
     stat lines and all numeric quant (entry/stop/TP/RR, backtests, Monte Carlo)
     are pulled automatically from quant_data.json by the build script.
   - `macro_strategy` (rates/inflation/growth playbook: regime_label,
     regime_detail, drivers, scenarios, positioning).
   - `insights` (5-7 cards; always keep a LIQUIDATION card; cover more than
     AI/nuclear).
   - `smart_money` (intro + 3-4 items on congressional trades, 13F moves, policy
     tailwinds, hyperscaler capex; keep the "signal, not a guarantee" framing).
   - `primer` (AI-data-center explainer; mostly evergreen).
   - `watchlist_notes`.
3. `python3 build_dashboard.py` - regenerates `dashboard.html`. The Liquidation
   Watch panel, 10Y chip, positioning columns, Top Picks stat lines + grades,
   the Quant Lab (backtests, regime, trade setups, Monte Carlo), the Macro
   Playbook, ETF shelf, and KPI hover tooltips are all generated automatically
   from market_data.json + insights.json + quant_data.json. quant_data.json is
   loaded defensively, so the page still builds without it (minus the Quant Lab).
4. Redeploy: publish `dashboard.html` with the Claude Artifact tool to the SAME
   artifact URL above (pass it as the `url` parameter, favicon 📡, keep title
   "Long-Term Investing Monitor").

## Style rules for insights copy

- No em dashes or en dashes in any prose (user's global rule). Use commas,
  colons, parentheses, or periods.
- Do NOT over-weight AI/nuclear. Surface good long-term buys anywhere, including
  healthcare/pharma and broad ETFs. The user favors ETFs for diversified,
  lower-single-name-risk exposure.
- Every insight and pick ends with a practical takeaway for a long-term
  investor, referencing tickers on the board where relevant.
- Metrics framework (user's): PEG ~1.0 fair value; P/B 1-3 healthy baseline;
  ROE 10-20% strong; low D/E preferred; Beta >1 = more volatile than market.
- Keep KPI explanations plain (the user is not an economist); the build script
  renders them as hover tooltips on every column header and macro chip.
- Always note the data "as of" date and upcoming macro dates (CPI, FOMC).
- Not financial advice; keep the footer disclaimer.

## Watchlist

Two boards, same columns (as of Jul 19, 2026, at the user's request):
- Sheet 1 (established, large-dollar): Semis & Fab (incl. INTC), Memory &
  Storage (MU, SNDK, WDC; SK Hynix is Seoul-only so noted in the sector blurb),
  Servers/Cooling, Fiber, Electrical/Conduit/Steel, Nuclear & Power Majors
  (CEG VST CCJ BWXT GEV), Big Tech (incl. IBM, PLTR), Healthcare.
- Sheet 2 (smaller-dollar / speculative): Nuclear Developers & Fuel (OKLO SMR
  LEU NNE), Quantum Pure-Plays, Space & Defense (RKLB LUNR ASTS), Gov-Backed
  Materials & Small AI Infra (MP LAC TSSI).
- GOV badges (build_dashboard.py `GOV` dict): names where the US government
  holds equity (INTC, MP, LAC) or is the anchor customer (LEU, BWXT, RKLB,
  PLTR). The user explicitly wants government-holding names flagged.
- The user mentioned a ticker "TWS" that could not be identified; TSSI was
  added as the closest small-cap AI-infra guess. Swap it if she clarifies.

Edit `WATCHLIST` and `INDEX_ETFS` in `refresh_data.py`, and `NAMES`, `GOV`,
`SECTOR_META`, `ETF_META` in `build_dashboard.py`, to add or remove
tickers/sectors/ETFs. Keep SECTOR_META board tags (1 or 2) in sync with
WATCHLIST sections.
