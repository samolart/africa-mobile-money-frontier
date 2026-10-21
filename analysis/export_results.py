"""Step 4. Export every number the deck and documents use from the RECALCULATED workbook (no hand-typed figures)."""
import json, os, sys
from openpyxl import load_workbook
sys.path.insert(0, os.path.dirname(__file__))
from sources import SOURCES, LIMITS
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
wb = load_workbook(os.path.join(ROOT, "model", "africa_mobile_money_model.xlsx"), data_only=True)
PY = json.load(open(os.path.join(ROOT, "outputs", "py_results.json")))
F, L = 6, 39
def v(sh, col, r): return wb[sh][f"{col}{r}"].value
inp = {}
ws = wb["Inputs"]
for r in range(5, ws.max_row + 1):
    if ws.cell(r, 1).value and ws.cell(r, 4).value is not None:
        inp[ws.cell(r, 1).value] = dict(low=ws.cell(r, 3).value, base=ws.cell(r, 4).value, high=ws.cell(r, 5).value, tag=ws.cell(r, 6).value)
mk = []
for r in range(F, L + 1):
    d = dict(country=v("Data", "A", r), iso=v("Data", "B", r), income=v("Data", "C", r), adults=v("Data", "D", r), mm24=v("Data", "E", r), acct24=v("Data", "F", r), mm17=v("Data", "I", r),
             merchant=v("Data", "H", r), gdppc=v("Data", "J", r), cand=v("Data", "AB", r), fcs=v("Data", "X", r), prox=v("Data", "W", r),
             a30=[v("Forecast", c, r) for c in "IJK"], users30=[v("Forecast", c, r) for c in "LMN"],
             arpu=[v("Pools", c, r) for c in "HIJ"], pool30=[v("Pools", c, r) for c in "KLM"], win_rev=[v("Pools", c, r) for c in "QRS"], win_users=[v("Pools", c, r) for c in "NOP"],
             pool24=v("Pools", "T", r), pool_cagr=v("Pools", "U", r), cover=v("Pools", "V", r), scale=v("Pools", "G", r))
    if d["cand"] == 1:
        d.update(A=v("Scorecard", "AC", r), E=v("Scorecard", "AQ", r), priority=v("Scorecard", "AR", r), rank=v("Scorecard", "AS", r), wacc=v("Scorecard", "AT", r), quad=v("Scorecard", "AU", r),
                 s_size=v("Scorecard", "X", r), s_growth=v("Scorecard", "Y", r), s_merch=v("Scorecard", "Z", r), s_remit=v("Scorecard", "AA", r), s_incl=v("Scorecard", "AB", r),
                 s_ready=v("Scorecard", "AH", r), s_macro=v("Scorecard", "AL", r), s_led=v("Scorecard", "AM", r), s_prox=v("Scorecard", "AN", r), s_mom=v("Scorecard", "AO", r), s_fcs=v("Scorecard", "AP", r))
    mk.append(d)
cs = wb["Cases"]
summ = []
for r in range(6, 11):
    summ.append(dict(rank=cs.cell(r, 1).value, country=cs.cell(r, 2).value, iso=cs.cell(r, 3).value, priority=cs.cell(r, 4).value, npv=[cs.cell(r, c).value for c in (5, 6, 7)], exp_npv=cs.cell(r, 8).value,
                     peak=cs.cell(r, 9).value, payback=cs.cell(r, 10).value, users30=cs.cell(r, 11).value, rev30=cs.cell(r, 12).value, ebitda30=cs.cell(r, 13).value, be=cs.cell(r, 14).value, be_share=cs.cell(r, 15).value, wacc=cs.cell(r, 16).value))
BLK0, BLK_H = 18, 40
blocks = {}
for k in range(1, 6):
    for j, s in enumerate(["Low", "Base", "High"]):
        r0 = BLK0 + ((k - 1) * 3 + j) * BLK_H
        rh = r0 + 12
        rows = {nm: [cs.cell(rh + 1 + q, 3 + i).value for i in range(10)] for q, nm in enumerate(["adults", "adopt", "exist", "new", "ramp", "users", "rev", "cac", "fixed", "contrib", "ebitda", "df", "pv", "cum", "pay"])}
        blocks[f"{k}|{s}"] = dict(rows=rows, npv=cs.cell(r0 + 30, 2).value, peak=cs.cell(r0 + 31, 2).value, rv=cs.cell(r0 + 33, 2).value, cv=cs.cell(r0 + 34, 2).value, L=cs.cell(r0 + 35, 2).value, capex=cs.cell(r0 + 29, 2).value)
sn = wb["Sensitivity"]
grids = {}
for k in range(1, 4):
    r = 4 + (k - 1) * 10
    g1 = dict(cols=[sn.cell(r + 2, 2 + q).value for q in range(5)], rows=[sn.cell(r + 3 + p, 1).value for p in range(5)], vals=[[sn.cell(r + 3 + p, 2 + q).value for q in range(5)] for p in range(5)])
    g2 = dict(cols=[sn.cell(r + 2, 9 + q).value for q in range(5)], rows=[sn.cell(r + 3 + p, 8).value for p in range(5)], vals=[[sn.cell(r + 3 + p, 9 + q).value for q in range(5)] for p in range(5)])
    grids[k] = dict(name=sn.cell(r, 1).value, g1=g1, g2=g2)
ck = wb["Checks"]
checks = [(ck.cell(r, 1).value, ck.cell(r, 4).value) for r in range(5, 40) if ck.cell(r, 1).value and ck.cell(r, 1).value != "OVERALL"]
overall = [ck.cell(r, 4).value for r in range(5, 40) if ck.cell(r, 1).value == "OVERALL"][0]
panel_t = {}
import pandas as pd
pn = pd.read_csv(os.path.join(ROOT, "data", "processed", "panel.csv"))
for iso in ("KEN", "TZA", "UGA", "NGA", "ETH", "COD", "CIV", "GHA"):
    s = pn[(pn.iso3 == iso) & pn.mobile_money.notna()][["year", "mobile_money"]]
    panel_t[iso] = {int(a): float(b) for a, b in s.values}
allpan = {}
for iso, sub in pn[pn.mobile_money.notna() & (pn.year >= 2014)].groupby("iso3"):
    allpan[iso] = {int(a): float(b) for a, b in sub[["year", "mobile_money"]].values}
out = dict(inputs=inp, markets=mk, summary=summ, blocks=blocks, grids=grids, checks=checks, overall=overall, trend=panel_t, trend_all=allpan,
           reg=PY["reg"], backtest=PY["backtest"], g0=PY["g0"], w_mom=PY["w_mom"], n_draws=PY["n_draws"], sources=SOURCES, limits=LIMITS,
           mc={m["iso3"]: dict(top1=m["top1_freq"], top2=m["top2_freq"], top3=m["top3_freq"]) for m in PY["market"] if m.get("candidate")},
           loco={m["iso3"]: dict(expected=m["loco_expected"], actual=m["mm24"]) for m in PY["market"] if m.get("loco_expected") is not None})
json.dump(out, open(os.path.join(ROOT, "outputs", "results.json"), "w"), indent=1, default=float)
print("overall", overall, "markets", len(mk), "cand", sum(1 for m in mk if m["cand"] == 1))
