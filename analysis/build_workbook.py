"""Step 3. Build the Excel model with live formulas.

Reads outputs/py_results.json (estimates + the Python reference results) and writes model/africa_mobile_money_model.xlsx.
Recalculate afterwards so the formulas carry cached values:
    soffice --headless --convert-to xlsx --outdir model/recalc model/africa_mobile_money_model.xlsx
Design rules: every number a reader sees is an input (blue) on Inputs/Data, or a formula. Inputs carry a tag:
[S] sourced, [A] analyst assumption, [E] estimated in Python (analysis/model.py), [S/A] sourced with adjustment.
"""
import json
import os
import sys

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as CL

sys.path.insert(0, os.path.dirname(__file__))
from sources import SOURCES, LIMITS  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = json.load(open(os.path.join(ROOT, "outputs", "py_results.json")))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "model", "africa_mobile_money_model.xlsx")

# ------------------------------------------------------------------ styles
FONT = "Arial"
f_norm, f_bold = Font(name=FONT, size=10), Font(name=FONT, size=10, bold=True)
f_in, f_link = Font(name=FONT, size=10, color="0000FF"), Font(name=FONT, size=10, color="008000")
f_head = Font(name=FONT, size=10, bold=True, color="FFFFFF")
f_title = Font(name=FONT, size=14, bold=True, color="1B1F5E")
f_note = Font(name=FONT, size=9, italic=True, color="555555")
fill_head, fill_sec = PatternFill("solid", fgColor="1B1F5E"), PatternFill("solid", fgColor="E7E8F4")
fill_key, fill_in = PatternFill("solid", fgColor="FFF2CC"), PatternFill("solid", fgColor="F4F7FF")
thin = Side(style="thin", color="BBBBBB")
b_bot = Border(bottom=thin)
FMT = dict(pct="0.0%", pct0="0%", num="#,##0", num1="#,##0.0", num2="#,##0.00", x="0.00x", usd="$#,##0.0", g="0.0000", int="0")

wb = Workbook()
wb.remove(wb.active)


def sheet(name, tab="1B1F5E"):
    ws = wb.create_sheet(name)
    ws.sheet_properties.tabColor = tab
    ws.sheet_view.showGridLines = False
    return ws


def put(ws, r, c, v, font=None, fmt=None, fill=None, align=None, border=None):
    cell = ws.cell(r, c, v)
    cell.font = font or f_norm
    if fmt:
        cell.number_format = FMT.get(fmt, fmt)
    if fill:
        cell.fill = fill
    if align:
        cell.alignment = align
    if border:
        cell.border = border
    return cell


def title(ws, text, sub=None):
    put(ws, 1, 1, text, f_title)
    if sub:
        put(ws, 2, 1, sub, f_note)


def hdr(ws, r, labels, c0=1, wrap=True):
    for i, l in enumerate(labels):
        put(ws, r, c0 + i, l, f_head, fill=fill_head, align=Alignment(horizontal="center", vertical="center", wrap_text=wrap))
    ws.row_dimensions[r].height = 42


def widths(ws, spec):
    for col, w in spec.items():
        ws.column_dimensions[col].width = w


def n(v):
    return None if v is None else float(v)


# ------------------------------------------------------------------ market data (alphabetical)
MK = sorted(PY["market"], key=lambda m: m["country"])
FIRST = 6
LAST = FIRST + len(MK) - 1
NYEARS_CELL = None
SC = ["Low", "Base", "High"]

# ==================================================================== README (filled at the end)
ws_readme = sheet("README", "7A7A7A")
ws_sum = sheet("Summary", "D9482B")
ws_in = sheet("Inputs", "2F55D4")
ws_d = sheet("Data", "2F55D4")
ws_f = sheet("Forecast")
ws_p = sheet("Pools")
ws_s = sheet("Scorecard")
ws_c = sheet("Cases")
ws_sen = sheet("Sensitivity")
ws_rob = sheet("Robustness", "7A7A7A")
ws_src = sheet("Sources", "7A7A7A")
ws_ref = sheet("PyRef", "7A7A7A")
ws_chk = sheet("Checks", "2E8B57")

# ==================================================================== INPUTS
ws = ws_in
title(ws, "Inputs and assumptions", "Blue = input you can change. Tags: [S] sourced, [A] analyst assumption, [E] estimated in Python, [S/A] sourced with analyst adjustment.")
hdr(ws, 4, ["Input", "Unit", "Low", "Base", "High", "Tag", "Source or rationale"])
IN = {}
row = [5]


def sec(label):
    r = row[0]
    for c in range(1, 8):
        put(ws, r, c, label if c == 1 else None, f_bold, fill=fill_sec)
    row[0] += 1


def inp(key, label, unit, base, low=None, high=None, tag="[A]", note="", fmt="num2", formula=False, key_input=False):
    r = row[0]
    IN[key] = r
    put(ws, r, 1, label)
    put(ws, r, 2, unit)
    for c, v in ((3, low), (4, base), (5, high)):
        if v is not None:
            put(ws, r, c, v, f_norm if (formula or (isinstance(v, str) and v.startswith("="))) else f_in, fmt, fill=fill_key if key_input else None)
    put(ws, r, 6, tag, align=Alignment(horizontal="center"))
    put(ws, r, 7, note, f_note, align=Alignment(wrap_text=True, vertical="top"))
    row[0] += 1


def I(key, col="D", sheet_prefix=True):
    return f"Inputs!${col}${IN[key]}"


sec("1. Timeline and forecast")
inp("base_year", "Base year (latest Findex survey)", "year", 2024, tag="[S]", note="S1: Global Findex 2025 reports the 2024 survey round.", fmt="int")
inp("target_year", "Target year", "year", 2030, tag="[A]", note="Planning horizon for the expansion decision.", fmt="int")
inp("n_years", "Years from base to target", "years", f"=D{row[0]-1}-D{row[0]-2}", tag="calc", fmt="int")
inp("ceiling", "Adoption ceiling in forecasts", "% of adults", 0.92, tag="[A]", note="Just above Kenya's 87.5% (S1). Keeps the logistic curve from passing near-universal use.", fmt="pct")
inp("min_adults", "Minimum market size to be a candidate", "adults", 3000000, tag="[A]", note="Below this, a regional platform cannot cover its fixed costs (see Pools column V).", fmt="num")
inp("g0", "Pooled growth of logit(adoption)", "per year", PY["g0"], tag="[E]", note="Median of country trends 2014-2024 (analysis/model.py). Back-test: beats country-specific trends (Robustness sheet).", fmt="g", key_input=True)
inp("w_mom", "Weight on a country's own trend", "0 to 1", PY["w_mom"], tag="[E]", note="Chosen by back-test: 0 gave the lowest 2024 forecast error. Raise it to give each country its own growth rate.", fmt="num2")
inp("g_lo", "Floor on growth", "per year", 0.0, tag="[A]", fmt="g")
inp("g_hi", "Cap on growth", "per year", 0.5, tag="[A]", fmt="g")
sec("2. Scenarios")
inp("gm", "Growth multiplier on adoption trend", "x", 1.0, 0.5, 1.5, "[A]", "Low halves the trend; High raises it by half. Back-test showed the Base trend over-predicted 2024 by 2.8 points on average.", "num2", key_input=True)
inp("arpu", "Revenue per active user in the reference market (Kenya income, mobile-led)", "USD per year", 25, 15, 32, "[S/A]",
    "S4: Airtel Money East Africa revenue per customer about $24.7. S3: M-Pesa about $32 per active user. Low = price compression; Airtel Money Nigeria is only about $3.3 (S4).", "num1", key_input=True)
inp("s_new", "Operator's share of NEW users by 2030", "%", 0.15, 0.08, 0.22, "[A]", "What a well-funded challenger wins of adults who start using mobile money after 2024. Tested through the break-even share.", "pct", key_input=True)
inp("s_exist", "Operator's share of EXISTING users", "%", 0.03, 0.015, 0.05, "[A]", "Switching or multi-homing by people who already use mobile money.", "pct", key_input=True)
inp("prob", "Scenario weight for expected NPV", "%", 0.5, 0.25, 0.25, "[A]", "Judgement weights; the Low and High cases are symmetric around Base.", "pct")
sec("3. Revenue per user by market")
inp("el_inc", "Income elasticity of revenue per user", "x", 0.35, tag="[A]", note="Revenue per user rises less than proportionally with income (Francophone Africa earns more per customer than its income implies: S4).", fmt="num2")
inp("el_lo", "Income factor floor", "x", 0.5, tag="[A]", fmt="num2")
inp("el_hi", "Income factor cap", "x", 1.3, tag="[A]", fmt="num2")
inp("el_led", "Elasticity to mobile-led share (mobile money / any account)", "x", 1.0, tag="[S/A]", note="Bank-led markets earn far less per mobile money customer: Airtel Money Nigeria about $3.3 against $24.7 in East Africa (S4).", fmt="num2")
inp("led_lo", "Structure factor floor", "x", 0.25, tag="[A]", fmt="num2")
inp("led_hi", "Structure factor cap", "x", 1.0, tag="[A]", fmt="num2")
sec("4. Business case for the entrant (USD millions unless stated)")
inp("margin", "Contribution margin after agent commissions and variable cost", "% of revenue", 0.50, tag="[A]", note="Mobile money is high-margin once agent commissions are paid; tested in Sensitivity.", fmt="pct", key_input=True)
inp("fixed", "Fixed operating cost per year (reference-size market)", "$m", 12.0, tag="[A]", note="Team, compliance, technology and brand. Scaled by market size (below).", fmt="num1")
inp("cac", "Acquisition cost per new operator user", "$", 3.0, tag="[A]", note="Agent onboarding and promotions.", fmt="num2")
inp("capex", "Launch investment (licence, platform, agent seeding), reference-size market", "$m", 20.0, tag="[A]", note="Spent in 2026, one year before launch. Assumes a build or partnership entry, not an acquisition.", fmt="num1")
inp("tv", "Terminal value multiple on 2035 EBITDA", "x", 5.0, tag="[A]", fmt="num1")
inp("scale_ref", "Reference market size for cost scaling", "adults", 20000000, tag="[A]", fmt="num")
inp("scale_exp", "Cost-scaling exponent", "x", 0.4, tag="[A]", note="Costs rise with market size, but less than proportionally.", fmt="num2")
inp("scale_lo", "Cost scale floor", "x", 0.6, tag="[A]", fmt="num2")
inp("scale_hi", "Cost scale cap", "x", 2.0, tag="[A]", fmt="num2")
inp("wacc_base", "Discount rate, base (USD)", "%", 0.12, tag="[A]", fmt="pct")
inp("prem_macro", "Premium for weak macro stability (at score 0)", "%", 0.04, tag="[A]", fmt="pct")
inp("prem_fcs", "Premium for fragility (at score 0)", "%", 0.04, tag="[A]", note="Scaled by the World Bank FY26 fragile-situations flag (S5).", fmt="pct")
inp("ramp27", "Share of target users reached, 2027 (launch year)", "%", 0.10, tag="[A]", fmt="pct0")
inp("ramp28", "Ramp 2028", "%", 0.35, tag="[A]", fmt="pct0")
inp("ramp29", "Ramp 2029", "%", 0.65, tag="[A]", fmt="pct0")
inp("ramp30", "Ramp 2030 and after", "%", 1.0, tag="[A]", fmt="pct0")
sec("5. Scoring weights (each block sums to 100%)")
for k, lab in (("size", "Winnable revenue in 2030 (log scale)"), ("growth", "Growth of the revenue pool 2024 to 2030"), ("merch", "Merchant-payment gap to Kenya"),
               ("remit", "Remittance intensity (share of GDP)"), ("incl", "Inclusion gap (gender and income)")):
    inp("wa_" + k, "Attractiveness: " + lab, "weight", PY["a_weights"][k], tag="[A]", fmt="pct0", key_input=True)
inp("wa_sum", "Attractiveness weights total", "check", f"=SUM(D{IN['wa_size']}:D{IN['wa_incl']})", tag="calc", fmt="pct0")
for k, lab in (("ready", "Digital readiness (phones, internet, electricity, urban)"), ("macro", "Macro stability (inflation, currency, growth)"),
               ("led", "Mobile-led market (mobile money share of accounts)"), ("prox", "Proximity to Kenya (EAC and corridor markets)"),
               ("mom", "Momentum (adoption gain 2017 to 2024)"), ("fcs", "Institutional stability (World Bank FY26 fragile-situations list)")):
    inp("we_" + k, "Ease: " + lab, "weight", PY["e_weights"][k], tag="[A]", fmt="pct0", key_input=True)
inp("we_sum", "Ease weights total", "check", f"=SUM(D{IN['we_ready']}:D{IN['we_fcs']})", tag="calc", fmt="pct0")
inp("cap_subs", "Cap on mobile subscriptions per 100 people", "per 100", 120, tag="[A]", fmt="num")
inp("cap_remit", "Cap on remittances (% of GDP)", "%", 15, tag="[A]", fmt="num")
inp("cap_infl", "Cap on inflation (average 2022 to 2024)", "%", 40, tag="[A]", fmt="num")
inp("cap_fx", "Cap on currency depreciation (average 2022 to 2024)", "% a year", 40, tag="[A]", fmt="num")
inp("floor_fx", "Floor on currency depreciation", "% a year", -5, tag="[A]", fmt="num")
sec("6. Home-market anchors (read from Data)")
D_ISO = f"Data!$B${FIRST}:$B${LAST}"


def dcol(c):
    return f"Data!${c}${FIRST}:${c}${LAST}"


inp("ken_gdppc", "Kenya GDP per capita, PPP (2021 intl $)", "$", f"=INDEX({dcol('J')},MATCH(\"KEN\",{D_ISO},0))", tag="[S]", fmt="num", formula=True)
inp("ken_led", "Kenya mobile-led share", "ratio", f"=MIN(1,INDEX({dcol('E')},MATCH(\"KEN\",{D_ISO},0))/INDEX({dcol('F')},MATCH(\"KEN\",{D_ISO},0)))", tag="[S]", fmt="num2", formula=True)
inp("ken_merch", "Kenya merchant-payment share of adults", "%", f"=INDEX({dcol('H')},MATCH(\"KEN\",{D_ISO},0))", tag="[S]", fmt="pct", formula=True)
sec("7. Calibration of revenue per user (sourced company figures)")
inp("c_mp_rev", "Safaricom M-Pesa revenue, FY to March 2026", "KES bn", 182.73, tag="[S]", note="S3: Safaricom FY2026 results as reported by HapaKenya.", fmt="num2")
inp("c_mp_users", "Safaricom M-Pesa active customers (group)", "million", 43.69, tag="[S]", note="S3. Definition (monthly or 30-day) not stated; group figure.", fmt="num2")
inp("c_fx", "KES per USD (WDI 2024)", "KES", 129.0, tag="[S]", note="S2: WDI PA.NUS.FCRF for Kenya, 2024 (approximate; used only for this calibration).", fmt="num1")
inp("c_mp_arpu", "M-Pesa revenue per active customer", "USD per year", f"=D{IN['c_mp_rev']}*1000/D{IN['c_mp_users']}/D{IN['c_fx']}", tag="calc", fmt="num1", formula=True)
inp("c_ea_rev", "Airtel Money East Africa revenue, FY to March 2026", "$m", 1009, tag="[S]", note="S4: Airtel Africa FY2026 final results.", fmt="num")
inp("c_ea_cust", "Airtel Money East Africa customers", "million", 40.9, tag="[S]", note="S4", fmt="num1")
inp("c_ea_arpu", "Airtel Money East Africa revenue per customer", "USD per year", f"=D{IN['c_ea_rev']}/D{IN['c_ea_cust']}", tag="calc", fmt="num1", formula=True)
inp("c_ng_rev", "Airtel Money Nigeria revenue", "$m", 9, tag="[S]", note="S4", fmt="num")
inp("c_ng_cust", "Airtel Money Nigeria customers", "million", 2.7, tag="[S]", note="S4", fmt="num1")
inp("c_ng_arpu", "Airtel Money Nigeria revenue per customer", "USD per year", f"=D{IN['c_ng_rev']}/D{IN['c_ng_cust']}", tag="calc", fmt="num1", formula=True)
widths(ws, {"A": 62, "B": 14, "C": 11, "D": 13, "E": 11, "F": 8, "G": 100})
ws.freeze_panes = "A5"

# ==================================================================== DATA
ws = ws_d
title(ws, "Market data: 34 sub-Saharan African markets with Global Findex 2024 results",
      "Sources: S1 Global Findex 2025 (survey 2024); S2 World Development Indicators (updated 8 Oct 2026); S5 World Bank FY26 fragile-situations list. Blank = not available.")
DH = ["Country", "ISO3", "Income group (World Bank)", "Adults 2024", "Mobile money account 2024", "Any account 2024", "Financial-institution account 2024", "Digital merchant payment 2024",
      "Mobile money account 2017", "GDP per capita, PPP (2021 intl $)", "Urban population %", "Mobile subscriptions per 100", "Internet users %", "Electricity access %",
      "Remittances % of GDP", "Population growth % a year", "Inflation, average 2022-24 %", "Currency depreciation, average 2022-24 % a year", "GDP growth, average 2022-24 %",
      "Gender gap in mobile money, pp (men minus women)", "Income gap, pp (richest 60% minus poorest 40%)", "Rural gap, pp (urban minus rural)", "Proximity to Kenya (0-100) [A]",
      "Institutional stability (0-100) [S]", "Own-trend growth of logit(adoption) per year", "Home market", "Meets size screen", "Candidate"]
hdr(ws, 5, DH)
ws.row_dimensions[5].height = 70
put(ws, 4, 4, "Findex (S1)", f_note)
put(ws, 4, 10, "WDI (S2)", f_note)
put(ws, 4, 20, "Findex segments (S1)", f_note)
put(ws, 4, 23, "Judgement / World Bank (S5)", f_note)
COLS = ["country", "iso3", "income_group", "adults", "mm24", "acct24", "fi24", "merchant", "mm17", "gdppc", "urban_pct", "subs", "inet", "elec", "remit", "pop_growth", "infl",
        "fx_dep", "gdp_growth", "gender_gap_pp", "income_gap_pp", "rural_gap_pp", "prox", "fcs", "g_raw"]
FM = ["", "", "", "num", "pct", "pct", "pct", "pct", "pct", "num", "num1", "num1", "num1", "num1", "num1", "num2", "num1", "num1", "num1", "num1", "num1", "num1", "num", "num", "g"]
for i, m in enumerate(MK):
    r = FIRST + i
    for j, k in enumerate(COLS):
        v = m.get(k)
        v = n(v) if j >= 3 else v
        if v is None:
            continue
        put(ws, r, j + 1, v, f_in if j >= 3 else f_norm, FM[j] or None)
    put(ws, r, 26, f'=IF(B{r}="KEN",1,0)', fmt="int")
    put(ws, r, 27, f"=IF(D{r}>={I('min_adults')},1,0)", fmt="int")
    put(ws, r, 28, f"=IF(AND(Z{r}=0,AA{r}=1),1,0)", fmt="int", fill=fill_key)
widths(ws, {"A": 20, "B": 7, "C": 20})
for c in range(4, 29):
    ws.column_dimensions[CL(c)].width = 13
ws.freeze_panes = "C6"

# ==================================================================== FORECAST
ws = ws_f
title(ws, "Adoption forecast to 2030", "Logistic diffusion: logit(adoption) rises by a common yearly growth rate (Inputs), scaled by the scenario multiplier, capped at the ceiling.")
hdr(ws, 5, ["Country", "ISO3", "Candidate", "Mobile money 2024", "logit(adoption 2024)", "Growth of logit per year", "Adults 2030", "Users at 2024 penetration, 2030",
            "Adoption 2030 Low", "Adoption 2030 Base", "Adoption 2030 High", "Users 2030 Low", "Users 2030 Base", "Users 2030 High", "New users vs 2024 penetration, Low",
            "New users Base", "New users High"])
ws.row_dimensions[5].height = 56
for i, m in enumerate(MK):
    r = FIRST + i
    put(ws, r, 1, f"=Data!A{r}", f_link); put(ws, r, 2, f"=Data!B{r}", f_link); put(ws, r, 3, f"=Data!AB{r}", f_link, "int")
    put(ws, r, 4, f"=Data!E{r}", f_link, "pct")
    put(ws, r, 5, f"=LN(MIN(0.995,MAX(0.005,D{r}))/(1-MIN(0.995,MAX(0.005,D{r}))))", fmt="num2")
    put(ws, r, 6, f'=MIN({I("g_hi")},MAX({I("g_lo")},(1-{I("w_mom")})*{I("g0")}+{I("w_mom")}*IF(Data!Y{r}="",{I("g0")},Data!Y{r})))', fmt="g")
    put(ws, r, 7, f"=Data!D{r}*(1+Data!P{r}/100)^{I('n_years')}", fmt="num")
    put(ws, r, 8, f"=G{r}*D{r}", fmt="num")
    for j, s in enumerate(SC):
        gmc = I("gm", "CDE"[j])
        put(ws, r, 9 + j, f"=MIN(1/(1+EXP(-(E{r}+F{r}*{gmc}*{I('n_years')}))),MAX({I('ceiling')},D{r}))", fmt="pct")
        put(ws, r, 12 + j, f"=G{r}*{CL(9+j)}{r}", fmt="num")
        put(ws, r, 15 + j, f"=MAX(0,{CL(12+j)}{r}-H{r})", fmt="num")
widths(ws, {"A": 20, "B": 7, "C": 10})
for c in range(4, 18):
    ws.column_dimensions[CL(c)].width = 14
ws.freeze_panes = "C6"

# ==================================================================== POOLS
ws = ws_p
title(ws, "Revenue pools and the winnable share, 2030 ($m)", "Pool = users x revenue per user. Winnable = the operator's share of existing users plus its share of new users.")
hdr(ws, 5, ["Country", "ISO3", "Candidate", "Income factor", "Mobile-led share", "Structure factor", "Cost scale factor", "Revenue per user Low ($)", "Revenue per user Base ($)",
            "Revenue per user High ($)", "Pool 2030 Low ($m)", "Pool 2030 Base ($m)", "Pool 2030 High ($m)", "Winnable users Low", "Winnable users Base", "Winnable users High",
            "Winnable revenue Low ($m)", "Winnable revenue Base ($m)", "Winnable revenue High ($m)", "Pool 2024 at Base revenue per user ($m)", "Pool growth per year 2024-30",
            "Contribution cover of fixed cost (Base)"])
ws.row_dimensions[5].height = 70
for i, m in enumerate(MK):
    r = FIRST + i
    put(ws, r, 1, f"=Data!A{r}", f_link); put(ws, r, 2, f"=Data!B{r}", f_link); put(ws, r, 3, f"=Data!AB{r}", f_link, "int")
    put(ws, r, 4, f"=MIN({I('el_hi')},MAX({I('el_lo')},(Data!J{r}/{I('ken_gdppc')})^{I('el_inc')}))", fmt="num2")
    put(ws, r, 5, f"=MIN(1,Data!E{r}/Data!F{r})", fmt="num2")
    put(ws, r, 6, f"=MIN({I('led_hi')},MAX({I('led_lo')},(E{r}/{I('ken_led')})^{I('el_led')}))", fmt="num2")
    put(ws, r, 7, f"=MIN({I('scale_hi')},MAX({I('scale_lo')},(Data!D{r}/{I('scale_ref')})^{I('scale_exp')}))", fmt="num2")
    for j, s in enumerate(SC):
        c = "CDE"[j]
        put(ws, r, 8 + j, f"={I('arpu', c)}*D{r}*F{r}", fmt="num1")
        put(ws, r, 11 + j, f"=Forecast!{CL(12+j)}{r}*{CL(8+j)}{r}/1000000", fmt="num1")
        put(ws, r, 14 + j, f"={I('s_exist', c)}*Forecast!H{r}+{I('s_new', c)}*Forecast!{CL(15+j)}{r}", fmt="num")
        put(ws, r, 17 + j, f"={CL(14+j)}{r}*{CL(8+j)}{r}/1000000", fmt="num1")
    put(ws, r, 20, f"=Data!D{r}*Data!E{r}*I{r}/1000000", fmt="num1")
    put(ws, r, 21, f"=(L{r}/T{r})^(1/{I('n_years')})-1", fmt="pct")
    put(ws, r, 22, f"=R{r}*{I('margin')}/({I('fixed')}*G{r})", fmt="x")
widths(ws, {"A": 20, "B": 7, "C": 10})
for c in range(4, 23):
    ws.column_dimensions[CL(c)].width = 13
ws.freeze_panes = "C6"

# ==================================================================== SCORECARD
ws = ws_s
title(ws, "Scorecard: attractiveness x ease of entry", "Scores run 0-100 across candidate markets only (min-max). Priority = square root of attractiveness x ease, which penalises a weak side.")
SH = ["Country", "ISO3", "Candidate", "Size: ln(winnable revenue 2030)", "Pool growth", "Merchant gap to Kenya (pp)", "Inclusion gap (pp)", "Remittances % GDP (capped)", "Adoption gain 2017-24 (pp)",
      "Merchant gap (filled)", "Inclusion gap (filled)", "Remittances (filled)", "Momentum (filled)", "Mobile subs per 100 (capped)", "Internet users %", "Electricity %", "Urban %",
      "Inflation (capped)", "Depreciation (capped)", "GDP growth", "Mobile-led share", "Proximity", "Institutional stability",
      "Score: size", "Score: growth", "Score: merchant gap", "Score: remittances", "Score: inclusion gap", "ATTRACTIVENESS",
      "Score: mobile subs", "Score: internet", "Score: electricity", "Score: urban", "Digital readiness", "Score: inflation", "Score: currency", "Score: growth (GDP)", "Macro stability",
      "Mobile-led", "Proximity", "Momentum", "Institutional stability", "EASE", "PRIORITY SCORE", "RANK", "Discount rate", "Quadrant"]
hdr(ws, 5, SH)
ws.row_dimensions[5].height = 70
CAND = f"$C${FIRST}:$C${LAST}"


def rg(c):
    return f"{c}${FIRST}:{c}${LAST}"


def mm(col, r, inv=False):
    lo, hi = f"_xlfn.MINIFS({rg(col)},{CAND},1)", f"_xlfn.MAXIFS({rg(col)},{CAND},1)"
    x = f"{col}{r}"
    return f'=IF($C{r}=1,100*({hi}-{x})/({hi}-{lo}),"")' if inv else f'=IF($C{r}=1,100*({x}-{lo})/({hi}-{lo}),"")'


for i, m in enumerate(MK):
    r = FIRST + i
    put(ws, r, 1, f"=Data!A{r}", f_link); put(ws, r, 2, f"=Data!B{r}", f_link); put(ws, r, 3, f"=Data!AB{r}", f_link, "int")
    put(ws, r, 4, f"=LN(MAX(Pools!R{r},0.000001))", fmt="num2")
    put(ws, r, 5, f"=Pools!U{r}", f_link, "pct")
    put(ws, r, 6, f'=IF(Data!H{r}="","",MAX(0,({I("ken_merch")}-Data!H{r})*100))', fmt="num1")
    put(ws, r, 7, f'=IF(COUNT(Data!T{r},Data!U{r})=0,"",AVERAGE(Data!T{r},Data!U{r}))', fmt="num1")
    put(ws, r, 8, f'=IF(Data!O{r}="","",MIN({I("cap_remit")},Data!O{r}))', fmt="num1")
    put(ws, r, 9, f'=IF(Data!I{r}="","",(Data!E{r}-Data!I{r})*100)', fmt="num1")
    for col, src in (("J", "F"), ("K", "G"), ("L", "H"), ("M", "I")):
        put(ws, r, ord(col) - 64, f'=IF({src}{r}="",MEDIAN({rg(src)}),{src}{r})', fmt="num1")
    put(ws, r, 14, f'=IF(Data!L{r}="",MIN({I("cap_subs")},MEDIAN({dcol("L")})),MIN({I("cap_subs")},Data!L{r}))', fmt="num1")
    for col, dc in (("O", "M"), ("P", "N"), ("Q", "K"), ("T", "S")):
        put(ws, r, ord(col) - 64, f'=IF(Data!{dc}{r}="",MEDIAN({dcol(dc)}),Data!{dc}{r})', fmt="num1")
    put(ws, r, 18, f'=IF(Data!Q{r}="",MIN({I("cap_infl")},MEDIAN({dcol("Q")})),MIN({I("cap_infl")},Data!Q{r}))', fmt="num1")
    put(ws, r, 19, f'=IF(Data!R{r}="",MAX({I("floor_fx")},MIN({I("cap_fx")},MEDIAN({dcol("R")}))),MAX({I("floor_fx")},MIN({I("cap_fx")},Data!R{r})))', fmt="num1")
    put(ws, r, 21, f"=Pools!E{r}", f_link, "num2")
    put(ws, r, 22, f"=Data!W{r}", f_link, "num")
    put(ws, r, 23, f"=Data!X{r}", f_link, "num")
    for col, src in (("X", "D"), ("Y", "E"), ("Z", "J"), ("AA", "L"), ("AB", "K")):
        put(ws, r, ord(col[-1]) - 64 + (26 if len(col) == 2 else 0), mm(src, r), fmt="num1")
    wa = lambda k: I("wa_" + k)  # noqa: E731
    we = lambda k: I("we_" + k)  # noqa: E731
    put(ws, r, 29, f'=IF($C{r}=1,{wa("size")}*X{r}+{wa("growth")}*Y{r}+{wa("merch")}*Z{r}+{wa("remit")}*AA{r}+{wa("incl")}*AB{r},"")', f_bold, "num1")
    for col, src in (("AD", "N"), ("AE", "O"), ("AF", "P"), ("AG", "Q")):
        put(ws, r, 30 + "ADAEAFAG".index(col) // 2, mm(src, r), fmt="num1")
    put(ws, r, 34, f'=IF($C{r}=1,AVERAGE(AD{r}:AG{r}),"")', fmt="num1")
    put(ws, r, 35, mm("R", r, inv=True), fmt="num1")
    put(ws, r, 36, mm("S", r, inv=True), fmt="num1")
    put(ws, r, 37, mm("T", r), fmt="num1")
    put(ws, r, 38, f'=IF($C{r}=1,AVERAGE(AI{r}:AK{r}),"")', fmt="num1")
    put(ws, r, 39, mm("U", r), fmt="num1")
    put(ws, r, 40, mm("V", r), fmt="num1")
    put(ws, r, 41, mm("M", r), fmt="num1")
    put(ws, r, 42, f'=IF($C{r}=1,W{r},"")', fmt="num1")
    put(ws, r, 43, f'=IF($C{r}=1,{we("ready")}*AH{r}+{we("macro")}*AL{r}+{we("led")}*AM{r}+{we("prox")}*AN{r}+{we("mom")}*AO{r}+{we("fcs")}*AP{r},"")', f_bold, "num1")
    put(ws, r, 44, f'=IF($C{r}=1,SQRT(AC{r}*AQ{r}),"")', f_bold, "num1", fill=fill_key)
    put(ws, r, 45, f'=IF($C{r}=1,COUNTIFS({CAND},1,$AR${FIRST}:$AR${LAST},">"&AR{r})+1,"")', f_bold, "int", fill=fill_key)
    put(ws, r, 46, f'=IF($C{r}=1,{I("wacc_base")}+{I("prem_macro")}*(1-AL{r}/100)+{I("prem_fcs")}*(1-AP{r}/100),"")', fmt="pct")
    put(ws, r, 47, f'=IF($C{r}=1,IF(AC{r}>=MEDIAN({rg("AC")}),IF(AQ{r}>=MEDIAN({rg("AQ")}),"Prioritise","Big but hard"),IF(AQ{r}>=MEDIAN({rg("AQ")}),"Easy but small","Deprioritise")),"")')
widths(ws, {"A": 20, "B": 7, "C": 10})
for c in range(4, 48):
    ws.column_dimensions[CL(c)].width = 12
ws.column_dimensions["AU"].width = 16
ws.freeze_panes = "D6"

# ==================================================================== PYREF (static Python results, row-aligned with Data)
ws = ws_ref
title(ws, "Python reference results (static values from analysis/model.py)", "Independent implementation. Columns V onward compare the workbook with these values; the Checks sheet totals the differences.")
PH = ["Country", "ISO3", "Candidate", "Adoption 2030 Base", "Pool 2030 Base ($m)", "Winnable revenue Base ($m)", "Attractiveness", "Ease", "Priority", "Rank", "Discount rate",
      "NPV Low", "NPV Base", "NPV High", "Expected NPV", "Peak funding Base", "Break-even share multiple", "Top-1 frequency", "Top-2 frequency", "Top-3 frequency", "",
      "diff adoption", "diff pool", "diff winnable", "diff A", "diff E", "diff priority", "diff rank", "diff WACC"]
hdr(ws, 5, PH)
PK = [("country", None), ("iso3", None), ("candidate", "int"), ("a30_Base", "pct"), ("pool30_Base", "num1"), ("win_rev_Base", "num1"), ("A", "num2"), ("E", "num2"), ("priority", "num2"),
      ("rank", "int"), ("wacc", "pct"), ("npv_Low", "num1"), ("npv_Base", "num1"), ("npv_High", "num1"), ("npv_exp", "num1"), ("peak_Base", "num1"), ("breakeven_scale", "num2"),
      ("top1_freq", "pct"), ("top2_freq", "pct"), ("top3_freq", "pct")]
for i, m in enumerate(MK):
    r = FIRST + i
    for j, (k, f) in enumerate(PK):
        v = m.get(k)
        if k == "candidate":
            v = 1 if v else 0
        if v is None:
            continue
        put(ws, r, j + 1, v if j < 2 else float(v), f_in, f)
    put(ws, r, 22, f"=ABS(Forecast!J{r}-D{r})", fmt="0.000000")
    put(ws, r, 23, f"=ABS(Pools!L{r}-E{r})", fmt="0.000000")
    put(ws, r, 24, f"=ABS(Pools!R{r}-F{r})", fmt="0.000000")
    put(ws, r, 25, f"=IF(C{r}=1,ABS(Scorecard!AC{r}-G{r}),0)", fmt="0.000000")
    put(ws, r, 26, f"=IF(C{r}=1,ABS(Scorecard!AQ{r}-H{r}),0)", fmt="0.000000")
    put(ws, r, 27, f"=IF(C{r}=1,ABS(Scorecard!AR{r}-I{r}),0)", fmt="0.000000")
    put(ws, r, 28, f"=IF(C{r}=1,ABS(Scorecard!AS{r}-J{r}),0)", fmt="0.000000")
    put(ws, r, 29, f"=IF(C{r}=1,ABS(Scorecard!AT{r}-K{r}),0)", fmt="0.000000")
widths(ws, {"A": 20, "B": 7})
for c in range(3, 30):
    ws.column_dimensions[CL(c)].width = 13
ws.freeze_panes = "C6"

# ==================================================================== CASES
ws = ws_c
TOPK = 5
BLK0, BLK_H = 18, 40
YRS = list(range(2026, 2036))
yc = lambda y: CL(3 + y - 2026)  # noqa: E731  C=2026 ... L=2035
title(ws, "Business case for the top five markets: three scenarios each (USD millions)",
      "Each block rebuilds the case for one market and scenario. The top five are picked live by rank from the Scorecard. NPV at 2026; launch spend in 2026, first revenue 2027.")
sumhdr = ["Rank", "Market", "ISO3", "Priority score", "NPV Low", "NPV Base", "NPV High", "Expected NPV", "Peak funding, Base", "Payback year, Base", "Operator users 2030, Base",
          "Operator revenue 2030, Base", "Operator EBITDA 2030, Base", "Break-even multiple of share assumption", "Break-even share of NEW users", "Discount rate"]
hdr(ws, 5, sumhdr)
ws.row_dimensions[5].height = 56
CB = {}


def sc_ix(sh, col, idx):
    return f"INDEX({sh}!${col}${FIRST}:${col}${LAST},{idx})"


for k in range(1, TOPK + 1):
    for j, s in enumerate(SC):
        r0 = BLK0 + ((k - 1) * 3 + j) * BLK_H
        cc = "CDE"[j]
        idx = f"$B${r0}"
        for c in range(1, 13):
            put(ws, r0, c, None, f_bold, fill=fill_sec)
        put(ws, r0, 1, f"Rank {k} | {s} scenario | row index in market list", f_bold, fill=fill_sec)
        put(ws, r0, 2, f"=MATCH({k},Scorecard!$AS${FIRST}:$AS${LAST},0)", f_bold, "int", fill=fill_sec)
        P_ = {}
        spec = [("name", "Market", sc_ix("Scorecard", "A", idx), None), ("adults", "Adults 2024", sc_ix("Data", "D", idx), "num"), ("pg", "Population growth % a year", sc_ix("Data", "P", idx), "num2"),
                ("mm24", "Mobile money adoption 2024", sc_ix("Data", "E", idx), "pct"), ("lg", "logit(adoption 2024)", sc_ix("Forecast", "E", idx), "num2"),
                ("g", "Growth of logit per year x scenario multiplier", f"{sc_ix('Forecast', 'F', idx)}*{I('gm', cc)}", "g"),
                ("arpu", "Revenue per user ($ a year)", sc_ix("Pools", "HIJ"[j], idx), "num1"), ("scale", "Cost scale factor", sc_ix("Pools", "G", idx), "num2"),
                ("wacc", "Discount rate", sc_ix("Scorecard", "AT", idx), "pct"), ("se", "Share of existing users won", f"={I('s_exist', cc)}", "pct"),
                ("sn", "Share of new users won", f"={I('s_new', cc)}", "pct")]
        for q, (key, lab, fml, fm) in enumerate(spec):
            rr = r0 + 1 + q
            put(ws, rr, 1, lab)
            put(ws, rr, 2, fml if fml.startswith("=") else "=" + fml, f_link, fm)
            P_[key] = f"$B${rr}"
        put(ws, r0 + 1, 3, f"=INDEX(Scorecard!$B${FIRST}:$B${LAST},{idx})", f_link)
        rh = r0 + 12
        put(ws, rh, 1, "Year", f_head, fill=fill_head)
        put(ws, rh, 2, None, f_head, fill=fill_head)
        for y in YRS:
            put(ws, rh, 3 + y - 2026, y, f_head, "int", fill=fill_head, align=Alignment(horizontal="center"))
        R = {nm: rh + 1 + q for q, nm in enumerate(["adults", "adopt", "exist", "new", "ramp", "users", "rev", "cac", "fixed", "contrib", "ebitda", "df", "pv", "cum", "pay"])}
        labels = {"adults": "Adults", "adopt": "Mobile money adoption", "exist": "Existing users at 2024 penetration", "new": "New users above 2024 penetration", "ramp": "Ramp (share of target reached)",
                  "users": "Operator users", "rev": "Operator revenue ($m)", "cac": "Acquisition cost ($m)", "fixed": "Fixed operating cost ($m)", "contrib": "Margin on revenue less acquisition cost ($m)",
                  "ebitda": "EBITDA ($m)", "df": "Discount factor", "pv": "PV of EBITDA ($m)", "cum": "Cumulative cash incl. launch spend ($m)", "pay": "Payback marker"}
        for nm, rr in R.items():
            put(ws, rr, 1, labels[nm])
        put(ws, R["users"], 3, 0, fmt="num")
        put(ws, R["cum"], 3, f"=-B{r0 + 29}", fmt="num1")
        for y in YRS[1:]:
            c = yc(y)
            pc = CL(2 + y - 2026 + 0)  # previous year column letter
            put(ws, R["adults"], 3 + y - 2026, f"={P_['adults']}*(1+{P_['pg']}/100)^({c}{rh}-2024)", fmt="num")
            put(ws, R["adopt"], 3 + y - 2026, f"=MIN(1/(1+EXP(-({P_['lg']}+{P_['g']}*({c}{rh}-2024)))),MAX({I('ceiling')},{P_['mm24']}))", fmt="pct")
            put(ws, R["exist"], 3 + y - 2026, f"={c}{R['adults']}*{P_['mm24']}", fmt="num")
            put(ws, R["new"], 3 + y - 2026, f"=MAX(0,{c}{R['adults']}*{c}{R['adopt']}-{c}{R['exist']})", fmt="num")
            rk = {2027: "ramp27", 2028: "ramp28", 2029: "ramp29"}.get(y, "ramp30")
            put(ws, R["ramp"], 3 + y - 2026, f"={I(rk)}", f_link, "pct0")
            put(ws, R["users"], 3 + y - 2026, f"={c}{R['ramp']}*({P_['se']}*{c}{R['exist']}+{P_['sn']}*{c}{R['new']})", fmt="num")
            put(ws, R["rev"], 3 + y - 2026, f"={c}{R['users']}*{P_['arpu']}/1000000", fmt="num1")
            put(ws, R["cac"], 3 + y - 2026, f"={I('cac')}*MAX(0,{c}{R['users']}-{pc}{R['users']})/1000000", fmt="num1")
            put(ws, R["fixed"], 3 + y - 2026, f"={I('fixed')}*{P_['scale']}", fmt="num1")
            put(ws, R["contrib"], 3 + y - 2026, f"={c}{R['rev']}*{I('margin')}-{c}{R['cac']}", fmt="num1")
            put(ws, R["ebitda"], 3 + y - 2026, f"={c}{R['contrib']}-{c}{R['fixed']}", fmt="num1")
            put(ws, R["df"], 3 + y - 2026, f"=1/(1+{P_['wacc']})^({c}{rh}-2026)", fmt="0.000")
            put(ws, R["pv"], 3 + y - 2026, f"={c}{R['ebitda']}*{c}{R['df']}", fmt="num1")
            put(ws, R["cum"], 3 + y - 2026, f"={pc}{R['cum']}+{c}{R['ebitda']}", fmt="num1")
            put(ws, R["pay"], 3 + y - 2026, f'=IF({c}{R["cum"]}>=0,{c}{rh},"")', fmt="int")
        rc = r0 + 29
        put(ws, rc, 1, "Launch investment ($m)"); put(ws, rc, 2, f"={I('capex')}*{P_['scale']}", fmt="num1")
        L_, D_ = "L", "D"
        res = [("NPV ($m)", f"=-B{rc}+SUM(D{R['pv']}:L{R['pv']})+{I('tv')}*L{R['ebitda']}*L{R['df']}", "num1"),
               ("Peak funding need ($m)", f"=-MIN(C{R['cum']}:L{R['cum']})", "num1"),
               ("Payback year", f'=IF(COUNT(C{R["pay"]}:L{R["pay"]})=0,"none",MIN(C{R["pay"]}:L{R["pay"]}))', "int"),
               ("PV of revenue incl. terminal value ($m)", f"=SUMPRODUCT(D{R['rev']}:L{R['rev']},D{R['df']}:L{R['df']})+{I('tv')}*L{R['rev']}*L{R['df']}", "num1"),
               ("PV of acquisition cost incl. terminal value ($m)", f"=SUMPRODUCT(D{R['cac']}:L{R['cac']},D{R['df']}:L{R['df']})+{I('tv')}*L{R['cac']}*L{R['df']}", "num1"),
               ("PV of launch spend and fixed cost incl. terminal value ($m)", f"=B{rc}+{I('fixed')}*{P_['scale']}*(SUM(D{R['df']}:L{R['df']})+{I('tv')}*L{R['df']})", "num1"),
               ("Closed-form NPV = margin x PV revenue - PV acquisition - PV fixed ($m)", f"={I('margin')}*B{rc+4}-B{rc+5}-B{rc+6}", "num1"),
               ("Break-even multiple of the share assumption", f'=IF({I("margin")}*B{rc+4}-B{rc+5}>0,B{rc+6}/({I("margin")}*B{rc+4}-B{rc+5}),"n/a")', "num2"),
               ("Closed-form gap (should be 0)", f"=ABS(B{rc+7}-B{rc+1})", "0.000000")]
        for q, (lab, fml, fm) in enumerate(res):
            put(ws, rc + 1 + q, 1, lab, f_bold if q == 0 else f_norm)
            put(ws, rc + 1 + q, 2, fml, f_bold if q == 0 else f_norm, fm, fill=fill_key if q in (0, 7) else None)
        CB[(k, s)] = dict(r0=r0, R=R, npv=f"B{rc+1}", peak=f"B{rc+2}", pay=f"B{rc+3}", rv=f"B{rc+4}", cv=f"B{rc+5}", L=f"B{rc+6}", be=f"B{rc+8}", gap=f"B{rc+9}", capex=f"B{rc}",
                          users30=f"G{R['users']}", rev30=f"G{R['rev']}", ebitda30=f"G{R['ebitda']}", name=P_["name"], iso=f"C{r0+1}", wacc=P_["wacc"])
for k in range(1, TOPK + 1):
    r = 5 + k
    b = {s: CB[(k, s)] for s in SC}
    put(ws, r, 1, k, f_bold, "int")
    put(ws, r, 2, f"={b['Base']['name']}", f_bold); put(ws, r, 3, f"={b['Base']['iso']}")
    put(ws, r, 4, f"=INDEX(Scorecard!$AR${FIRST}:$AR${LAST},{'$B$'+str(b['Base']['r0'])})", fmt="num1")
    for j, s in enumerate(SC):
        put(ws, r, 5 + j, f"={b[s]['npv']}", fmt="num1")
    put(ws, r, 8, f"={I('prob','C')}*E{r}+{I('prob','D')}*F{r}+{I('prob','E')}*G{r}", f_bold, "num1", fill=fill_key)
    put(ws, r, 9, f"={b['Base']['peak']}", fmt="num1"); put(ws, r, 10, f"={b['Base']['pay']}", fmt="int")
    put(ws, r, 11, f"={b['Base']['users30']}", fmt="num"); put(ws, r, 12, f"={b['Base']['rev30']}", fmt="num1"); put(ws, r, 13, f"={b['Base']['ebitda30']}", fmt="num1")
    put(ws, r, 14, f"={b['Base']['be']}", fmt="num2"); put(ws, r, 15, f'=IF(ISNUMBER(N{r}),N{r}*{I("s_new")},"n/a")', fmt="pct")
    put(ws, r, 16, f"={b['Base']['wacc']}", fmt="pct")
put(ws, 12, 1, "How to read: NPV is at 2026 in $m. 'Break-even multiple' is the multiple of the Base share assumption at which NPV = 0 (below 1.0 = positive at the assumed share). "
    "'Break-even share of NEW users' restates it as a share of adults who start using mobile money after 2024.", f_note)
put(ws, 13, 1, "Expected NPV weights Low, Base and High by the scenario weights on Inputs. Costs scale with market size (Inputs section 4).", f_note)
widths(ws, {"A": 56, "B": 18, "C": 12})
for c in range(4, 17):
    ws.column_dimensions[CL(c)].width = 13
ws.freeze_panes = "A6"

# ==================================================================== SENSITIVITY
ws = ws_sen
title(ws, "Sensitivity of NPV for the top three markets (Base scenario, $m)",
      "Closed-form recalculation: NPV = share multiple x (margin x revenue multiple x PV revenue - PV acquisition) - PV fixed. The centre cell of each grid equals the Base NPV on Cases.")
SG = {}
r = 4
for k in range(1, 4):
    b = CB[(k, "Base")]
    put(ws, r, 1, f"=\"Rank {k}: \"&Cases!{b['name']}", f_bold, fill=fill_sec)
    for c in range(2, 14):
        put(ws, r, c, None, fill=fill_sec)
    put(ws, r + 1, 1, "Grid 1: operator share (multiple of Base) across, revenue per user (multiple of Base) down", f_note)
    shares = [0.5, 0.75, 1.0, 1.25, 1.5]
    arpus = [0.6, 0.8, 1.0, 1.2, 1.4]
    for q, v in enumerate(shares):
        put(ws, r + 2, 2 + q, v, f_in, "0.00x", fill=fill_in)
    for p, a in enumerate(arpus):
        put(ws, r + 3 + p, 1, a, f_in, "0.00x", fill=fill_in)
        for q in range(len(shares)):
            col = CL(2 + q)
            put(ws, r + 3 + p, 2 + q, f"={col}${r+2}*({I('margin')}*$A{r+3+p}*Cases!{b['rv']}-Cases!{b['cv']})-Cases!{b['L']}", fmt="num1")
    put(ws, r + 1, 8, "Grid 2: fixed-cost multiple across, contribution margin down", f_note)
    fixm = [0.5, 0.75, 1.0, 1.5, 2.0]
    margins = [0.35, 0.425, 0.50, 0.575, 0.65]
    for q, v in enumerate(fixm):
        put(ws, r + 2, 9 + q, v, f_in, "0.00x", fill=fill_in)
    for p, mg in enumerate(margins):
        put(ws, r + 3 + p, 8, mg, f_in, "0.0%", fill=fill_in)
        for q in range(len(fixm)):
            col = CL(9 + q)
            put(ws, r + 3 + p, 9 + q, f"=($H{r+3+p}*Cases!{b['rv']}-Cases!{b['cv']})-(Cases!{b['capex']}+{col}${r+2}*(Cases!{b['L']}-Cases!{b['capex']}))", fmt="num1")
    SG[k] = (f"D{r+5}", f"K{r+5}", b["npv"])
    r += 10
from openpyxl.formatting.rule import CellIsRule  # noqa: E402
ws.conditional_formatting.add("B6:M40", CellIsRule(operator="lessThan", formula=["0"], font=Font(name=FONT, size=10, color="C00000", bold=True)))
widths(ws, {"A": 34, "H": 22})
for c in list(range(2, 8)) + list(range(9, 14)):
    ws.column_dimensions[CL(c)].width = 12

# ==================================================================== ROBUSTNESS (static)
ws = ws_rob
title(ws, "Robustness and validation (static results from analysis/model.py)", "These come from estimation in Python (regression, back-test, Monte Carlo). They are not live formulas; re-run model.py to refresh.")
REG, BT = PY["reg"], PY["backtest"]
r = 4
put(ws, r, 1, "A. Does an economic-fundamentals model predict mobile-money adoption? (leave-one-country-out test)", f_bold, fill=fill_sec)
for c in range(2, 9):
    put(ws, r, c, None, fill=fill_sec)
put(ws, r + 1, 1, "Prediction error for 2024 adoption, countries held out one at a time (percentage points, RMSE)")
put(ws, r + 2, 1, "Fundamentals model (income, urbanisation, phones, electricity, remittances, survey wave)"); put(ws, r + 2, 2, REG["loco_rmse_pp"], f_in, "num1")
put(ws, r + 3, 1, "Benchmark with no fundamentals (survey-wave average only)"); put(ws, r + 3, 2, REG["loco_rmse_naive_pp"], f_in, "num1")
put(ws, r + 4, 1, "Countries tested"); put(ws, r + 4, 2, REG["loco_n"], f_in, "int")
put(ws, r + 5, 1, "Reading: fundamentals do not beat the benchmark out-of-sample, so mobile-money success depends on the local ecosystem (regulation, operator, agents). That is why the plan includes a due-diligence gate.", f_note)
r += 7
put(ws, r, 1, "B. Regression coefficients (dependent variable: logit of mobile-money adoption; country-clustered standard errors)", f_bold, fill=fill_sec)
for c in range(2, 9):
    put(ws, r, c, None, fill=fill_sec)
hdr(ws, r + 1, ["Variable", "Model A coefficient", "Std. error", "t", "Model B coefficient", "Std. error", "t"])
ws.row_dimensions[r + 1].height = 30
A_, B_ = REG["A"], REG["B"]
for q, nm in enumerate(B_["names"]):
    rr = r + 2 + q
    put(ws, rr, 1, nm)
    if nm in A_["names"]:
        ia = A_["names"].index(nm)
        put(ws, rr, 2, A_["beta"][ia], f_in, "0.0000"); put(ws, rr, 3, A_["se"][ia], f_in, "0.0000"); put(ws, rr, 4, A_["t"][ia], f_in, "num2")
    put(ws, rr, 5, B_["beta"][q], f_in, "0.0000"); put(ws, rr, 6, B_["se"][q], f_in, "0.0000"); put(ws, rr, 7, B_["t"][q], f_in, "num2")
rr = r + 2 + len(B_["names"])
put(ws, rr, 1, "R-squared"); put(ws, rr, 2, A_["r2"], f_in, "0.000"); put(ws, rr, 5, B_["r2"], f_in, "0.000")
put(ws, rr + 1, 1, "Observations / countries"); put(ws, rr + 1, 2, f"{REG['n_rows']} / {REG['n_countries']}", f_in)
r = rr + 3
put(ws, r, 1, "C. Back-test of the adoption forecast: forecast 2024 from data up to the 2022 round", f_bold, fill=fill_sec)
for c in range(2, 9):
    put(ws, r, c, None, fill=fill_sec)
hdr(ws, r + 1, ["Weight on country's own trend", "Mean absolute error (pp)", "Bias (pp)", "Error if no growth is assumed (pp)", "Countries", "Pooled growth g0"])
ws.row_dimensions[r + 1].height = 44
for q, b in enumerate(BT):
    rr = r + 2 + q
    put(ws, rr, 1, b["w"], f_in, "num2"); put(ws, rr, 2, b["mae_pp"], f_in, "num2"); put(ws, rr, 3, b["bias_pp"], f_in, "num2"); put(ws, rr, 4, b["naive_mae_pp"], f_in, "num2")
    put(ws, rr, 5, b["n"], f_in, "int"); put(ws, rr, 6, b["g0"], f_in, "g")
put(ws, r + 2 + len(BT), 1, "Reading: a common growth rate beats country-specific trends, and any growth beats none. A positive bias means the forecast runs high, so the Low scenario matters.", f_note)
r = r + 4 + len(BT)
put(ws, r, 1, f"D. How stable is the ranking? {PY['n_draws']:,} random draws of all scoring weights", f_bold, fill=fill_sec)
for c in range(2, 9):
    put(ws, r, c, None, fill=fill_sec)
hdr(ws, r + 1, ["Market", "Base-weights rank", "Ranked #1", "In top 2", "In top 3"])
cands = sorted([m for m in MK if m.get("candidate")], key=lambda m: m["rank"])
for q, m in enumerate(cands):
    rr = r + 2 + q
    put(ws, rr, 1, m["country"]); put(ws, rr, 2, m["rank"], f_in, "int")
    put(ws, rr, 3, m["top1_freq"], f_in, "pct0"); put(ws, rr, 4, m["top2_freq"], f_in, "pct0"); put(ws, rr, 5, m["top3_freq"], f_in, "pct0")
widths(ws, {"A": 74, "B": 18, "C": 14, "D": 16, "E": 18, "F": 14, "G": 10})
ROB_END = r + 2 + len(cands)

# ==================================================================== SOURCES
ws = ws_src
title(ws, "Sources and limitations")
hdr(ws, 3, ["ID", "Source", "Publisher", "Link", "Used for"])
for q, s in enumerate(SOURCES):
    for c, v in enumerate(s):
        put(ws, 4 + q, 1 + c, v, align=Alignment(wrap_text=True, vertical="top"))
rr = 5 + len(SOURCES)
put(ws, rr, 1, "Limitations (also stated in the deck and the methods appendix)", f_bold, fill=fill_sec)
for c in range(2, 6):
    put(ws, rr, c, None, fill=fill_sec)
for q, t in enumerate(LIMITS):
    put(ws, rr + 1 + q, 1, f"L{q+1}", f_bold)
    ws.merge_cells(start_row=rr + 1 + q, start_column=2, end_row=rr + 1 + q, end_column=5)
    put(ws, rr + 1 + q, 2, t, align=Alignment(wrap_text=True, vertical="top"))
    ws.row_dimensions[rr + 1 + q].height = 44
widths(ws, {"A": 6, "B": 62, "C": 34, "D": 60, "E": 60})

# ==================================================================== CHECKS
ws = ws_chk
title(ws, "Checks", "Every row should read TRUE. The workbook is recalculated independently of the Python reference; differences should be at rounding level.")
hdr(ws, 4, ["Check", "Value", "Tolerance", "Pass"])
CHK = []


def chk(label, val, tol, kind="le"):
    r = 5 + len(CHK)
    put(ws, r, 1, label)
    put(ws, r, 2, val, fmt="0.000000")
    put(ws, r, 3, tol, f_in, "0.000000")
    put(ws, r, 4, f"=ABS(B{r})<=C{r}" if kind == "le" else f"=B{r}=C{r}", f_bold)
    CHK.append(r)


chk("Attractiveness weights sum to 100%", f"={I('wa_sum')}-1", 1e-9)
chk("Ease weights sum to 100%", f"={I('we_sum')}-1", 1e-9)
chk("Adoption forecast 2030 (Base) equals Python: total absolute difference", f"=SUM(PyRef!V{FIRST}:V{LAST})", 1e-6)
chk("Revenue pool 2030 (Base) equals Python", f"=SUM(PyRef!W{FIRST}:W{LAST})", 1e-3)
chk("Winnable revenue 2030 (Base) equals Python", f"=SUM(PyRef!X{FIRST}:X{LAST})", 1e-3)
chk("Attractiveness score equals Python", f"=SUM(PyRef!Y{FIRST}:Y{LAST})", 1e-6)
chk("Ease score equals Python", f"=SUM(PyRef!Z{FIRST}:Z{LAST})", 1e-6)
chk("Priority score equals Python", f"=SUM(PyRef!AA{FIRST}:AA{LAST})", 1e-6)
chk("Rank equals Python", f"=SUM(PyRef!AB{FIRST}:AB{LAST})", 0.0)
chk("Discount rate equals Python", f"=SUM(PyRef!AC{FIRST}:AC{LAST})", 1e-9)
chk("Number of ranked candidates equals count of candidate flags", f"=MAX(Scorecard!AS{FIRST}:AS{LAST})-SUM(Data!AB{FIRST}:AB{LAST})", 0.0)
chk("Home market (Kenya) is excluded from candidates", f"=INDEX(Data!AB{FIRST}:AB{LAST},MATCH(\"KEN\",Data!B{FIRST}:B{LAST},0))", 0.0)
gaps = "+".join(f"Cases!{CB[key]['gap']}" for key in CB)
chk("Closed-form NPV equals year-by-year NPV in all 15 case blocks (total gap)", f"={gaps}", 1e-6)
# NPV vs python for the top five
rrs = []
for k in range(1, TOPK + 1):
    for s, pc in (("Low", "L"), ("Base", "M"), ("High", "N")):
        iso = f"Cases!{CB[(k, s)]['iso']}"
        rrs.append(f"ABS(Cases!{CB[(k, s)]['npv']}-INDEX(PyRef!${pc}${FIRST}:${pc}${LAST},MATCH({iso},PyRef!$B${FIRST}:$B${LAST},0)))")
chk("NPV (Low, Base, High) for the top five equals Python: total absolute difference", "=" + "+".join(rrs), 1e-3)
rrs = []
for k in range(1, TOPK + 1):
    b = CB[(k, "Base")]
    rrs.append(f"IF(ISNUMBER(Cases!{b['be']}),ABS(Cases!{b['be']}-INDEX(PyRef!$Q${FIRST}:$Q${LAST},MATCH(Cases!{b['iso']},PyRef!$B${FIRST}:$B${LAST},0))),0)")
chk("Break-even share multiple for the top five equals Python's bisection", "=" + "+".join(rrs), 1e-4)
chk("Sensitivity grid centre cells equal Base NPV (total difference)", "=" + "+".join(f"ABS(Sensitivity!{SG[k][0]}-Cases!{SG[k][2]})+ABS(Sensitivity!{SG[k][1]}-Cases!{SG[k][2]})" for k in SG), 1e-6)
for sh, rng_ in (("Data", f"A{FIRST}:AB{LAST}"), ("Forecast", f"A{FIRST}:Q{LAST}"), ("Pools", f"A{FIRST}:V{LAST}"), ("Scorecard", f"A{FIRST}:AU{LAST}"), ("Cases", f"A5:P{BLK0+TOPK*3*BLK_H}"), ("Sensitivity", "A4:M40"),
                  ("Summary", "A4:M60")):
    chk(f"No error values on {sh}", f"=SUMPRODUCT(--ISERROR({sh}!{rng_}))", 0.0)
rr = 5 + len(CHK) + 1
put(ws, rr, 1, "OVERALL", f_bold)
put(ws, rr, 4, f'=IF(COUNTIF(D5:D{rr-2},TRUE)={len(CHK)},"ALL CHECKS PASS","CHECK FAILURES")', f_bold, fill=fill_key)
CHK_ALL = f"Checks!D{rr}"
widths(ws, {"A": 88, "B": 16, "C": 12, "D": 20})

# ==================================================================== SUMMARY
ws = ws_sum
title(ws, "Where should a Kenyan mobile-money operator expand next? Summary of results", "Everything here is a live link into the model. Change an input on the Inputs sheet and this page updates.")
NC = sum(1 for m in MK if m.get("candidate"))
put(ws, 3, 1, "Model integrity:", f_bold); put(ws, 3, 2, f"={CHK_ALL}", f_bold, fill=fill_key)
hdr(ws, 5, ["Rank", "Market", "ISO3", "Attractiveness (0-100)", "Ease of entry (0-100)", "Priority score", "Quadrant", "Adoption 2024", "Adoption 2030 Base", "Revenue pool 2030 Base ($m)",
            "Winnable revenue 2030 Base ($m)", "Discount rate", "NPV Base ($m, top five)"])
ws.row_dimensions[5].height = 56
for k in range(1, NC + 1):
    r = 5 + k
    ix = f"MATCH({k},Scorecard!$AS${FIRST}:$AS${LAST},0)"
    put(ws, r, 1, k, f_bold, "int")
    put(ws, r, 2, f"=INDEX(Scorecard!$A${FIRST}:$A${LAST},{ix})", f_bold)
    put(ws, r, 3, f"=INDEX(Scorecard!$B${FIRST}:$B${LAST},{ix})")
    put(ws, r, 4, f"=INDEX(Scorecard!$AC${FIRST}:$AC${LAST},{ix})", fmt="num1")
    put(ws, r, 5, f"=INDEX(Scorecard!$AQ${FIRST}:$AQ${LAST},{ix})", fmt="num1")
    put(ws, r, 6, f"=INDEX(Scorecard!$AR${FIRST}:$AR${LAST},{ix})", f_bold, "num1", fill=fill_key if k <= 3 else None)
    put(ws, r, 7, f"=INDEX(Scorecard!$AU${FIRST}:$AU${LAST},{ix})")
    put(ws, r, 8, f"=INDEX(Data!$E${FIRST}:$E${LAST},{ix})", fmt="pct")
    put(ws, r, 9, f"=INDEX(Forecast!$J${FIRST}:$J${LAST},{ix})", fmt="pct")
    put(ws, r, 10, f"=INDEX(Pools!$L${FIRST}:$L${LAST},{ix})", fmt="num")
    put(ws, r, 11, f"=INDEX(Pools!$R${FIRST}:$R${LAST},{ix})", fmt="num1")
    put(ws, r, 12, f"=INDEX(Scorecard!$AT${FIRST}:$AT${LAST},{ix})", fmt="pct")
    put(ws, r, 13, f'=IFERROR(INDEX(Cases!$F$6:$F${5+TOPK},MATCH(C{r},Cases!$C$6:$C${5+TOPK},0)),"")', fmt="num1")
put(ws, 7 + NC, 1, "Home market for reference:", f_bold)
put(ws, 8 + NC, 1, "Kenya mobile money adoption 2024"); put(ws, 8 + NC, 4, f"=INDEX(Data!$E${FIRST}:$E${LAST},MATCH(\"KEN\",Data!$B${FIRST}:$B${LAST},0))", fmt="pct")
put(ws, 9 + NC, 1, "Candidate markets scored (34 markets with 2024 data; home market and markets under the size screen excluded)"); put(ws, 9 + NC, 4, f"=SUM(Data!AB{FIRST}:AB{LAST})", fmt="int")
widths(ws, {"A": 8, "B": 22, "C": 8, "G": 16})
for c in [4, 5, 6, 8, 9, 10, 11, 12, 13]:
    ws.column_dimensions[CL(c)].width = 15
ws.freeze_panes = "A6"

# ==================================================================== README
ws = ws_readme
title(ws, "Africa's mobile-money frontier: market-selection model", "Question: which two sub-Saharan markets should a Kenya-based mobile-money operator enter by 2030?")
lines = [
    ("How to use", ""),
    ("1", "Change blue cells on Inputs (assumptions) or Data (market facts). Everything else is a formula and recalculates."),
    ("2", "Read Summary for the ranking, Cases for the NPV by market and scenario, Sensitivity for what moves the answer, Checks for integrity."),
    ("3", "Robustness and PyRef hold results estimated in Python (analysis/model.py). They are static. Re-run the script to refresh them."),
    ("Sheets", ""),
    ("Summary", "Ranking of candidate markets with attractiveness, ease, quadrant, pools and NPV."),
    ("Inputs", "All assumptions with a tag and a source or rationale. Includes calibration of revenue per user to company disclosures."),
    ("Data", "Findex 2024 and World Development Indicators for 34 markets, plus judgement inputs (proximity) and the World Bank fragility score."),
    ("Forecast", "Adoption to 2030 in three scenarios using a logistic curve."),
    ("Pools", "Users x revenue per user, winnable revenue, pool growth, and cost scale."),
    ("Scorecard", "Min-max scoring, attractiveness and ease, priority = sqrt(A x E), rank, discount rate, quadrant."),
    ("Cases", "Year-by-year business case for the top five markets in three scenarios; break-even share."),
    ("Sensitivity", "NPV grids for the top three markets: share x revenue per user, and margin x fixed cost."),
    ("Colour code", "Blue = input. Black = formula. Green = link to another sheet. Yellow fill = key assumption or key output."),
    ("Tags", "[S] sourced, [A] analyst assumption, [E] estimated in Python, [S/A] sourced with analyst adjustment."),
    ("Not a valuation", "The business case is an entry screen for choosing between markets. It ignores tax, working capital and detailed currency paths."),
]
for q, (a, b) in enumerate(lines):
    r = 4 + q
    put(ws, r, 1, a, f_bold if b == "" or a in ("Colour code", "Tags", "Not a valuation") else f_norm, fill=fill_sec if b == "" else None)
    put(ws, r, 2, b, align=Alignment(wrap_text=True, vertical="top"), fill=fill_sec if b == "" else None)
widths(ws, {"A": 18, "B": 130})

wb.move_sheet("Summary", offset=-0)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
wb.save(OUT)
print("saved", OUT, "sheets", wb.sheetnames)
