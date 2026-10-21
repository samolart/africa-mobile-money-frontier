"""Step 2. Reference implementation of the analysis in Python.

The Excel model repeats the forecast, pool sizing, scoring and business case with live formulas.
This script (a) estimates the regression coefficients and the growth-shrinkage parameter that the workbook
takes as inputs, and (b) provides an independent calculation that the workbook's Checks sheet compares against.

Run from the repository root:  python analysis/model.py
Writes outputs/py_results.json
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from stats_lib import logit, inv_logit, ols_cluster  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
panel = pd.read_csv(os.path.join(PROC, "panel.csv"))
wide = pd.read_csv(os.path.join(PROC, "wdi_wide.csv"))
seg = pd.read_csv(os.path.join(PROC, "segments_2024.csv"))

HOME = "KEN"
BASE_YEAR, TARGET = 2024, 2030
WAVE = {2014: 2014, 2017: 2017, 2021: 2021, 2022: 2021, 2024: 2024}  # the 2022 round replaces 2021 for 11 countries
P = dict(
    min_adults=3_000_000, ceiling=0.92,
    scen={"Low": dict(gm=0.5, arpu=15, s_new=0.08, s_exist=0.015),
          "Base": dict(gm=1.0, arpu=25, s_new=0.15, s_exist=0.03),
          "High": dict(gm=1.5, arpu=32, s_new=0.22, s_exist=0.05)},
    arpu_elast=0.35, arpu_lo=0.5, arpu_hi=1.3, led_elast=1.0, led_lo=0.25, led_hi=1.0,
    ramp={2027: 0.10, 2028: 0.35, 2029: 0.65, 2030: 1.0}, years=list(range(2027, 2036)),
    margin=0.50, fixed_opex=12.0, cac=3.0, launch_capex=20.0, tv_mult=5.0, wacc_base=0.12, wacc_prem_macro=0.04, wacc_prem_fcs=0.04,
)


def latest(iso, var, year, back=2):
    """Value of a WDI variable in `year`, else the latest observation in the previous `back` years."""
    s = wide[(wide.iso3 == iso) & (wide.year <= year) & (wide.year >= year - back)].sort_values("year")[var].dropna()
    return float(s.iloc[-1]) if len(s) else np.nan


def avg(iso, var, y0, y1):
    s = wide[(wide.iso3 == iso) & (wide.year.between(y0, y1))][var].dropna()
    return float(s.mean()) if len(s) else np.nan


# ------------------------------------------------------------------ 1. adoption regression
rows = []
for _, r in panel[panel.mobile_money.notna() & (panel.year >= 2014)].iterrows():
    d = dict(iso3=r.iso3, country=r.country, year=int(r.year), wave=WAVE[int(r.year)], y=float(logit(r.mobile_money)), fi=r.fi_account)
    d["ln_gdppc"] = np.log(latest(r.iso3, "gdppc_ppp", int(r.year)))
    d["urban"] = latest(r.iso3, "urban_pct", int(r.year))
    d["subs"] = min(latest(r.iso3, "mobile_subs_100", int(r.year)), 150.0)
    d["elec"] = latest(r.iso3, "electricity_pct", int(r.year))
    d["remit"] = min(latest(r.iso3, "remit_gdp", int(r.year)), 15.0)
    rows.append(d)
R = pd.DataFrame(rows)
n_before = len(R)
R = R.dropna(subset=["ln_gdppc", "urban", "subs", "elec", "remit", "fi"]).reset_index(drop=True)
WAVES = [2017, 2021, 2024]
XA = ["ln_gdppc", "urban", "subs", "elec", "remit"]


def design(df, cols):
    X = [np.ones(len(df))] + [df[c].values for c in cols] + [(df.wave == w).astype(float).values for w in WAVES]
    return np.column_stack(X)


def fit(df, cols):
    return ols_cluster(design(df, cols), df.y.values, df.iso3.values)


names = ["const"] + XA + [f"wave_{w}" for w in WAVES]
fitA = fit(R, XA)
fitB = fit(R, XA + ["fi"])
namesB = ["const"] + XA + ["fi"] + [f"wave_{w}" for w in WAVES]
reg = {
    "n_rows": int(fitA["n"]), "n_countries": int(fitA["G"]), "dropped_rows": int(n_before - len(R)),
    "A": {"names": names, "beta": fitA["beta"].tolist(), "se": fitA["se"].tolist(), "t": fitA["t"].tolist(), "r2": fitA["r2"]},
    "B": {"names": namesB, "beta": fitB["beta"].tolist(), "se": fitB["se"].tolist(), "t": fitB["t"].tolist(), "r2": fitB["r2"]},
}

# leave-one-country-out: expected 2024 adoption for each country from a model that never saw that country
loco = []
base_only = []
for iso in R[R.wave == 2024].iso3.unique():
    tr, te = R[R.iso3 != iso], R[(R.iso3 == iso) & (R.wave == 2024)]
    b = ols_cluster(design(tr, XA), tr.y.values, tr.iso3.values)["beta"]
    pred = float(inv_logit(design(te, XA) @ b)[0])
    # benchmark model: wave effects only
    X0 = np.column_stack([np.ones(len(tr))] + [(tr.wave == w).astype(float).values for w in WAVES])
    b0 = np.linalg.lstsq(X0, tr.y.values, rcond=None)[0]
    X0t = np.column_stack([np.ones(len(te))] + [(te.wave == w).astype(float).values for w in WAVES])
    pred0 = float(inv_logit(X0t @ b0)[0])
    actual = float(inv_logit(te.y.values)[0])
    loco.append(dict(iso3=iso, expected=pred, actual=actual))
    base_only.append(pred0)
L = pd.DataFrame(loco)
L["resid"] = L.actual - L.expected
reg["loco_rmse_pp"] = float(np.sqrt((L.resid ** 2).mean()) * 100)
reg["loco_rmse_naive_pp"] = float(np.sqrt(((L.actual - np.array(base_only)) ** 2).mean()) * 100)
reg["loco_n"] = int(len(L))

# ------------------------------------------------------------------ 2. growth trend, shrinkage and back-test
def raw_growth(sub):
    """OLS slope of logit(adoption) on year (per year) using all waves from 2014."""
    if len(sub) < 3 or sub.year.max() - sub.year.min() < 3:
        return np.nan
    x, y = sub.year.values.astype(float), logit(sub.mobile_money.values)
    return float(np.polyfit(x, y, 1)[0])


mm = panel[panel.mobile_money.notna() & (panel.year >= 2014)]


def growth_table(max_year):
    g = {}
    for iso, sub in mm[mm.year <= max_year].groupby("iso3"):
        sub = sub.sort_values("year")
        g[iso] = dict(raw=raw_growth(sub), n=len(sub), last_year=int(sub.year.iloc[-1]), last=float(sub.mobile_money.iloc[-1]))
    return g


def g_for(gt, w, cap=(0.0, 0.5)):
    vals = [v["raw"] for v in gt.values() if not np.isnan(v["raw"])]
    g0 = float(np.median(vals))
    return {iso: float(np.clip((1 - w) * g0 + w * (g0 if np.isnan(v["raw"]) else v["raw"]), *cap)) for iso, v in gt.items()}, g0


gt22 = growth_table(2022)
actual24 = mm[mm.year == 2024].set_index("iso3").mobile_money
bt = []
for w in [0.0, 0.25, 0.5, 0.75, 1.0]:
    gmap, g0_22 = g_for(gt22, w)
    errs, naive = [], []
    for iso, v in gt22.items():
        if iso in actual24.index:
            pred = float(inv_logit(logit(v["last"]) + gmap[iso] * (2024 - v["last_year"])))
            errs.append(pred - actual24[iso])
            naive.append(v["last"] - actual24[iso])
    bt.append(dict(w=w, mae_pp=float(np.mean(np.abs(errs)) * 100), bias_pp=float(np.mean(errs) * 100), naive_mae_pp=float(np.mean(np.abs(naive)) * 100), n=len(errs), g0=g0_22))
BT = pd.DataFrame(bt)
W_MOM = float(BT.loc[BT.mae_pp.idxmin(), "w"])
gt24 = growth_table(2024)
g_ctry, g0 = g_for(gt24, W_MOM)

# ------------------------------------------------------------------ 3. market table
p24 = panel[(panel.year == BASE_YEAR) & panel.mobile_money.notna()].copy()
p17 = panel[(panel.year == 2017)].set_index("iso3").mobile_money
recs = []
for _, r in p24.iterrows():
    iso = r.iso3
    recs.append(dict(
        iso3=iso, country=r.country, income_group=r.income_group, adults=float(r.pop_adult), mm24=float(r.mobile_money), mm17=float(p17.get(iso, np.nan)),
        fi24=float(r.fi_account), acct24=float(r.account), merchant=float(r.merchant_pay) if not pd.isna(r.merchant_pay) else np.nan,
        gdppc=latest(iso, "gdppc_ppp", 2024), urban_pct=latest(iso, "urban_pct", 2024), subs=latest(iso, "mobile_subs_100", 2024),
        inet=latest(iso, "internet_users_pct", 2024), elec=latest(iso, "electricity_pct", 2024), remit=latest(iso, "remit_gdp", 2024),
        pop_growth=latest(iso, "pop_growth", 2024), infl=avg(iso, "inflation", 2022, 2024), gdp_growth=avg(iso, "gdp_growth", 2022, 2024),
        fx_dep=avg(iso, "fx_dep_pct", 2022, 2024), g_raw=gt24[iso]["raw"] if iso in gt24 else np.nan, g=g_ctry.get(iso, g0), n_obs=gt24[iso]["n"] if iso in gt24 else 0))
M = pd.DataFrame(recs)
sg = seg[seg.group2.isin(["men", "women", "rural", "urban", "poorest 40%", "richest 60%"])].pivot_table(index="iso3", columns="group2", values="mobile_money")
sg = sg.rename(columns={"poorest 40%": "poor40", "richest 60%": "rich60", "urban": "urban_mm", "rural": "rural_mm"})
M = M.merge(sg, on="iso3", how="left")
M["gender_gap_pp"] = (M["men"] - M["women"]) * 100
M["rural_gap_pp"] = (M["urban_mm"] - M["rural_mm"]) * 100
M["income_gap_pp"] = (M["rich60"] - M["poor40"]) * 100
M = M.merge(L.rename(columns={"expected": "loco_expected"})[["iso3", "loco_expected"]], on="iso3", how="left")
ken = M[M.iso3 == HOME].iloc[0]

PROX = {"TZA": 100, "UGA": 100, "COD": 100, "ETH": 60, "ZMB": 60, "MWI": 60, "MOZ": 60}  # EAC members and border/corridor markets; judgement [A]
PROX_DEFAULT = 20
# World Bank FY26 list of fragile and conflict-affected situations (conflict = 0, institutional and social fragility = 40, not listed = 100)
FCS_CONFLICT = ["BFA", "CMR", "COD", "ETH", "MLI", "MOZ", "NER", "NGA", "CAF", "SOM", "SSD", "SDN"]
FCS_INSTIT = ["TCD", "COM", "COG", "ZWE", "BDI"]
M["prox"] = M.iso3.map(PROX).fillna(PROX_DEFAULT)
M["fcs"] = [0 if i in FCS_CONFLICT else 40 if i in FCS_INSTIT else 100 for i in M.iso3]
M["is_home"] = M.iso3 == HOME
M["scale_ok"] = M.adults >= P["min_adults"]
M["candidate"] = (~M.is_home) & M.scale_ok


def adoption(row, year, gm):
    z = logit(row.mm24) + row.g * gm * (year - BASE_YEAR)
    return float(min(inv_logit(z), max(P["ceiling"], row.mm24)))


def adults_t(row, year):
    return row.adults * (1 + row.pop_growth / 100) ** (year - BASE_YEAR)


def led_share(row):
    return min(1.0, row.mm24 / row.acct24)


def arpu_i(row, scen):
    f = (row.gdppc / ken.gdppc) ** P["arpu_elast"]
    h = (led_share(row) / led_share(ken)) ** P["led_elast"]
    return P["scen"][scen]["arpu"] * float(np.clip(f, P["arpu_lo"], P["arpu_hi"])) * float(np.clip(h, P["led_lo"], P["led_hi"]))


for scen in P["scen"]:
    gm, s = P["scen"][scen]["gm"], P["scen"][scen]
    M[f"a30_{scen}"] = [adoption(r, TARGET, gm) for r in M.itertuples()]
    M[f"users30_{scen}"] = [adults_t(r, TARGET) * a for r, a in zip(M.itertuples(), M[f"a30_{scen}"])]
    M[f"exist_{scen}"] = [adults_t(r, TARGET) * r.mm24 for r in M.itertuples()]
    M[f"arpu_{scen}"] = [arpu_i(r, scen) for r in M.itertuples()]
    M[f"pool30_{scen}"] = M[f"users30_{scen}"] * M[f"arpu_{scen}"] / 1e6
    new = (M[f"users30_{scen}"] - M[f"exist_{scen}"]).clip(lower=0)
    M[f"win_users_{scen}"] = s["s_exist"] * M[f"exist_{scen}"] + s["s_new"] * new
    M[f"win_rev_{scen}"] = M[f"win_users_{scen}"] * M[f"arpu_{scen}"] / 1e6
M["pool24"] = [adults_t(r, BASE_YEAR) * r.mm24 * arpu_i(r, "Base") / 1e6 for r in M.itertuples()]
M["pool_cagr"] = (M.pool30_Base / M.pool24) ** (1 / (TARGET - BASE_YEAR)) - 1

# ------------------------------------------------------------------ 4. scoring (candidates only)
C = M[M.candidate].copy()
FILL = {}


def fill(col, cap=None, floor=None, src=None):
    """Clip, then fill gaps with the median across ALL markets with data (the workbook does the same with MEDIAN over a helper column)."""
    allv = M[col].copy() if src is None else src
    if cap is not None:
        allv = allv.clip(upper=cap)
    if floor is not None:
        allv = allv.clip(lower=floor)
    med = float(allv.median())
    s = C[col].copy() if src is None else src.loc[C.index]
    if cap is not None:
        s = s.clip(upper=cap)
    if floor is not None:
        s = s.clip(lower=floor)
    FILL[col] = dict(median=med, n_missing=int(s.isna().sum()), cap=cap, floor=floor)
    return s.fillna(med)


def mm01(s):
    return 100 * (s - s.min()) / (s.max() - s.min())


C["x_size"] = np.log(C.win_rev_Base)
C["x_growth"] = C.pool_cagr
M["h_merch"] = (ken.merchant - M.merchant).clip(lower=0) * 100
M["h_incl"] = pd.concat([M.gender_gap_pp, M.income_gap_pp], axis=1).mean(axis=1)
M["h_mom"] = (M.mm24 - M.mm17) * 100
C["h_merch"], C["h_incl"], C["h_mom"] = M.loc[C.index, "h_merch"], M.loc[C.index, "h_incl"], M.loc[C.index, "h_mom"]
C["x_merch"] = fill("h_merch")
C["x_remit"] = fill("remit", cap=15.0)
C["x_incl"] = fill("h_incl")
A_W = dict(size=0.35, growth=0.20, merch=0.15, remit=0.15, incl=0.15)
for k in A_W:
    C[f"s_{k}"] = mm01(C[f"x_{k}"])
C["A"] = sum(A_W[k] * C[f"s_{k}"] for k in A_W)

C["x_subs"] = fill("subs", cap=120.0); C["x_inet"] = fill("inet"); C["x_elec"] = fill("elec"); C["x_urban"] = fill("urban_pct")
C["s_ready"] = (mm01(C.x_subs) + mm01(C.x_inet) + mm01(C.x_elec) + mm01(C.x_urban)) / 4
C["x_infl"] = fill("infl", cap=40.0); C["x_fx"] = fill("fx_dep", cap=40.0, floor=-5.0); C["x_gdpg"] = fill("gdp_growth")
C["s_macro"] = (mm01(-C.x_infl) + mm01(-C.x_fx) + mm01(C.x_gdpg)) / 3
C["x_led"] = (C.mm24 / C.acct24).clip(upper=1.0)  # no gaps in the data
C["s_led"] = mm01(C.x_led)
C["s_prox"] = mm01(C.prox)
C["x_mom"] = fill("h_mom")
C["s_mom"] = mm01(C.x_mom)
C["s_fcs"] = C.fcs.astype(float)
E_W = dict(ready=0.20, macro=0.20, led=0.15, prox=0.15, mom=0.10, fcs=0.20)
C["E"] = sum(E_W[k] * C[f"s_{k}"] for k in E_W)
C["priority"] = np.sqrt(C.A * C.E)
C["rank"] = C.priority.rank(ascending=False, method="first").astype(int)
C["wacc"] = P["wacc_base"] + P["wacc_prem_macro"] * (1 - C.s_macro / 100) + P["wacc_prem_fcs"] * (1 - C.s_fcs / 100)

# ------------------------------------------------------------------ 5. business case
def case(row, scen, share_scale=1.0, arpu_override=None):
    s = P["scen"][scen]
    scale = min(2.0, max(0.6, (row.adults / 20e6) ** 0.4))
    arpu = arpu_override if arpu_override is not None else getattr(row, f"arpu_{scen}")
    gm = s["gm"]
    U_prev, cfs, rows = 0.0, {}, []
    for t in P["years"]:
        ad = adults_t(row, t)
        a = adoption(row, t, gm)
        Et = ad * row.mm24
        Nt = max(0.0, ad * a - Et)
        ramp = P["ramp"].get(t, 1.0)
        U = ramp * share_scale * (s["s_exist"] * Et + s["s_new"] * Nt)
        rev = U * arpu / 1e6
        cac = P["cac"] * max(0.0, U - U_prev) / 1e6
        ebitda = rev * P["margin"] - P["fixed_opex"] * scale - cac
        cfs[t] = ebitda
        rows.append(dict(year=t, users=U, rev=rev, cac=cac, ebitda=ebitda))
        U_prev = U
    wacc = row.wacc
    pv = sum(cf / (1 + wacc) ** (t - 2026) for t, cf in cfs.items())
    tv = P["tv_mult"] * cfs[2035] / (1 + wacc) ** (2035 - 2026)
    capex = P["launch_capex"] * scale
    npv = -capex + pv + tv
    cum, peak = -capex, -capex
    pay = None
    for t in P["years"]:
        cum += cfs[t]
        peak = min(peak, cum)
        if pay is None and cum >= 0:
            pay = t
    return dict(npv=npv, peak_funding=-peak, payback=pay, rev2030=[r for r in rows if r["year"] == 2030][0]["rev"], users2030=[r for r in rows if r["year"] == 2030][0]["users"],
                ebitda2030=cfs[2030], rows=rows, capex=capex, scale=scale)


for scen in P["scen"]:
    res = [case(r, scen) for r in C.itertuples()]
    C[f"npv_{scen}"] = [x["npv"] for x in res]
    C[f"peak_{scen}"] = [x["peak_funding"] for x in res]
    C[f"payback_{scen}"] = [x["payback"] for x in res]
    C[f"rev30op_{scen}"] = [x["rev2030"] for x in res]


def breakeven_scale(row, scen="Base"):
    lo, hi = 0.0, 20.0
    if case(row, scen, hi)["npv"] < 0:
        return None
    for _ in range(60):
        mid = (lo + hi) / 2
        if case(row, scen, mid)["npv"] >= 0:
            hi = mid
        else:
            lo = mid
    return hi


C["breakeven_scale"] = [breakeven_scale(r) for r in C.itertuples()]
P["prob"] = {"Low": 0.25, "Base": 0.5, "High": 0.25}
C["npv_exp"] = sum(P["prob"][s] * C[f"npv_{s}"] for s in P["prob"])
C["users2030_op_Base"] = [case(r, "Base")["users2030"] for r in C.itertuples()]

# ------------------------------------------------------------------ 6. robustness: random weights
rng = np.random.default_rng(20261020)
comp_A = ["s_size", "s_growth", "s_merch", "s_remit", "s_incl"]
comp_E = ["s_ready", "s_macro", "s_led", "s_prox", "s_mom", "s_fcs"]
top1 = {i: 0 for i in C.iso3}; top2 = {i: 0 for i in C.iso3}; top3 = {i: 0 for i in C.iso3}; N = 5000
for _ in range(N):
    wa, we = rng.dirichlet(np.ones(5)), rng.dirichlet(np.ones(6))
    A = (C[comp_A].values * wa).sum(1); E = (C[comp_E].values * we).sum(1)
    pr = np.sqrt(A * E)
    order = C.iso3.values[np.argsort(-pr)]
    top1[order[0]] += 1
    for i in order[:2]: top2[i] += 1
    for i in order[:3]: top3[i] += 1
C["top1_freq"] = C.iso3.map(lambda i: top1[i] / N); C["top2_freq"] = C.iso3.map(lambda i: top2[i] / N); C["top3_freq"] = C.iso3.map(lambda i: top3[i] / N)

# ------------------------------------------------------------------ outputs
os.makedirs(os.path.join(ROOT, "outputs"), exist_ok=True)
Mout = M.merge(C[[c for c in C.columns if c not in M.columns or c == "iso3"]], on="iso3", how="left")
out = dict(params={k: v for k, v in P.items() if k not in ("scen", "ramp", "years", "prob")}, prob=P["prob"], scen=P["scen"], ramp=P["ramp"], reg=reg, backtest=BT.to_dict("records"), w_mom=W_MOM,
           g0=g0, a_weights=A_W, e_weights=E_W, fill=FILL, prox=PROX, prox_default=PROX_DEFAULT, fcs_conflict=FCS_CONFLICT, fcs_instit=FCS_INSTIT, n_draws=N, market=Mout.replace({np.nan: None}).to_dict("records"))
json.dump(out, open(os.path.join(ROOT, "outputs", "py_results.json"), "w"), indent=1, default=float)
Mout.to_csv(os.path.join(PROC, "market_table.csv"), index=False)

if __name__ == "__main__":
    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 50); pd.set_option("display.max_rows", 100)
    print("REG rows", reg["n_rows"], "countries", reg["n_countries"], "dropped", reg["dropped_rows"], "R2 A/B", round(reg["A"]["r2"], 3), round(reg["B"]["r2"], 3))
    print("LOCO RMSE pp", round(reg["loco_rmse_pp"], 1), "wave-only benchmark", round(reg["loco_rmse_naive_pp"], 1), "n", reg["loco_n"])
    print(BT.round(2).to_string()); print("chosen momentum weight", W_MOM, "g0", round(g0, 4))
    print("candidates", len(C), "fills", FILL)
    cols = ["country", "adults", "mm24", "a30_Base", "win_rev_Base", "A", "E", "priority", "rank", "wacc", "npv_Low", "npv_Base", "npv_High", "peak_Base", "payback_Base", "breakeven_scale", "top2_freq", "top3_freq"]
    print(C.sort_values("rank")[cols].round(2).to_string())
