"""Step 6. Write the executive summary, methods appendix and CV/interview kit from outputs/results.json (no hand-typed results)."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(ROOT, "outputs", "results.json")))
M = {m["iso"]: m for m in D["markets"]}
S = {s["iso"]: s for s in D["summary"]}
C = sorted([m for m in D["markets"] if m["cand"] == 1], key=lambda m: m["rank"])
inp = D["inputs"]
K, T, CI, U, DR, NG, ET = (M[i] for i in ("KEN", "TZA", "CIV", "UGA", "COD", "NGA", "ETH"))
sT, sC, sU, sD = S["TZA"], S["CIV"], S["UGA"], S["COD"]
p = lambda v, d=0: f"{v*100:.{d}f}%"
m_ = lambda v, d=0: ("−$" if v < 0 else "$") + f"{abs(v):,.{d}f}m"
SN = inp["Operator's share of NEW users by 2030"]["base"]
bt = {round(b["w"], 2): b for b in D["backtest"]}
rm, rn = D["reg"]["loco_rmse_pp"], D["reg"]["loco_rmse_naive_pp"]
mc = D["mc"]; nc = len(C)
npass = sum(1 for c in D["checks"] if c[1] is True)
B1 = D["blocks"]["1|Base"]["rows"]
LIB = M["LBR"]

ES = f"""# Africa's mobile-money frontier: where should a Kenyan operator expand next?

**Question.** A hypothetical Kenya-based mobile-money operator has {p(K['mm24'],1)} of Kenyan adults already using mobile money. Which sub-Saharan markets should it enter by 2030, in what order, and what would have to be true?

**Answer.** Enter **Tanzania** first. Hold **DR Congo** as a gated option and take a diligence view on **Côte d'Ivoire** before committing a second market. Do not commit to two markets up front.

## What the analysis shows

1. **The home market is close to full.** Kenya is at {p(K['mm24'])}; Tanzania, Côte d'Ivoire and Uganda are at {p(T['mm24'])}, {p(CI['mm24'])} and {p(U['mm24'])}. Of {len(D['markets'])} markets with 2024 data, {nc} pass a size screen.
2. **Tanzania ranks first** on a two-axis score (attractiveness {T['A']:.0f}, ease {T['E']:.0f}, priority {T['priority']:.0f}/100), with a 2030 revenue pool of {m_(T['pool30'][1])} and no fragility flag. It is in the top two in {p(mc['TZA']['top2'])} of {D['n_draws']:,} random weightings. DR Congo ({p(mc['COD']['top2'])}) is next; beyond the top two the ranking is not stable.
3. **Size alone misleads.** Nigeria has the largest pool ({m_(NG['pool30'][1])}) but ranks {NG['rank']} of {nc}: it is conflict-affected on the World Bank list, bank-led, and revenue per user is {p(1-NG['arpu'][1]/K['arpu'][1])} below Kenya's even after adjustment (Airtel Money Nigeria discloses about $3). Ethiopia ranks {ET['rank']}.
4. **The business case is thin.** Tanzania's Base NPV is {m_(sT['npv'][1],1)} (Low {m_(sT['npv'][0])}, High {m_(sT['npv'][2])}), peak funding {m_(sT['peak'])}, payback {sT['payback']}. DR Congo is {m_(sD['npv'][1],1)}; Côte d'Ivoire {m_(sC['npv'][1],1)}; Uganda {m_(sU['npv'][1],1)}.
5. **What you need to believe.** Tanzania breaks even if the operator wins {p(sT['be_share'],1)} of new users against {p(SN)} assumed. Côte d'Ivoire needs {p(sC['be_share'],1)} and Uganda {p(sU['be_share'],1)}.
6. **Fundamentals do not predict winners.** A model using income, urbanisation, phones, electricity and remittances misses 2024 adoption by {rm:.1f} points on held-out countries, worse than a benchmark that ignores them ({rn:.1f}). Kenya sits about {(K['mm24']-D['loco']['KEN']['expected'])*100:.0f} points above what fundamentals imply. Ecosystem, regulation and execution decide, hence a diligence gate.

## Recommendation

- **Gate 0 (2026):** diligence on Tanzania's licence and partner route and agent economics; screen DR Congo and Côte d'Ivoire. Go if the entry route fits the {m_(D['blocks']['1|Base']['capex'])} launch budget.
- **2027:** launch Tanzania. Base plan {B1['users'][1]/1e6:.2f}m users in year one, reaching {B1['users'][4]/1e6:.1f}m by 2030 and {m_(sT['rev30'])} revenue.
- **Gate 1 (end-2028):** continue only if users are within 20% of the Base plan and the share of new users is tracking towards {p(sT['be_share'])} or better.
- **2029 to 2030:** choose DR Congo or Côte d'Ivoire on diligence evidence, preferably through a partnership.

## Confidence and limits

Revenue per user is calibrated on two company disclosures reported in the press; operator share, margin, fixed cost and launch spend are analyst assumptions, each tested in the sensitivity and break-even analysis. Governance indicators (WGI) were not available, so institutional stability uses the World Bank fragility list. Rwanda, Burundi, Somalia and South Sudan have no 2024 data. The business case is an entry screen, not a valuation. The back-test showed the adoption forecast ran {bt[0.0]['bias_pp']:.1f} points high, which is why the Low scenario matters.

*Every figure comes from `model/africa_mobile_money_model.xlsx` ({npass} of {len(D['checks'])} integrity checks pass against an independent Python implementation). Method and sources: `docs/methods_appendix.md`.*
"""
open(os.path.join(ROOT, "docs", "executive_summary.md"), "w").write(ES)

rowsA = "\n".join(f"| {c['rank']} | {c['country']} | {c['A']:.0f} | {c['E']:.0f} | {c['priority']:.1f} | {c['quad']} | {p(c['mm24'])} | {p(c['a30'][1])} | {c['pool30'][1]:,.0f} | {c['win_rev'][1]:,.1f} |" for c in C)
MA = f"""# Methods appendix: Africa's mobile-money frontier

## 1. Question and structure
**Governing question:** Which markets should a Kenya-based mobile-money operator enter by 2030, and in what order?
Issue tree: (1) Is the home market saturated? (2) Which markets are attractive? (3) Which are feasible to enter? (4) Does the business case work, and what must be true? (5) What sequence manages the risk?

## 2. Data
| ID | Source | Used for |
|---|---|---|
""" + "\n".join(f"| {s[0]} | {s[1]} ({s[2]}) | {s[4]} |" for s in D["sources"]) + f"""

Data were cleaned in `analysis/prepare.py`. The Global Findex 'all adults' group is used for headline measures; segment results (gender, income, rural) come from the same file. WDI values use the latest observation up to two years before the reference year; inflation, currency depreciation and GDP growth are 2022 to 2024 averages.

## 3. Method
**Screen.** Kenya (home) is excluded; markets under {inp['Minimum market size to be a candidate']['base']/1e6:.0f} million adults are dropped. {nc} candidates remain of {len(D['markets'])} markets with 2024 data.

**Forecast.** Adoption follows a logistic curve: logit(adoption) rises at a common {D['g0']:.3f} a year, multiplied by 0.5, 1.0 and 1.5 for the Low, Base and High scenarios, with a ceiling of {p(inp['Adoption ceiling in forecasts']['base'])}. Adults grow at each country's population growth rate. A back-test forecasting 2024 from data to the 2022 round compared five weights on each country's own trend. The common rate (weight 0) had the lowest error ({bt[0.0]['mae_pp']:.1f} points against {bt[1.0]['mae_pp']:.1f} for pure country trends and {bt[0.0]['naive_mae_pp']:.1f} for no growth) but a bias of +{bt[0.0]['bias_pp']:.1f} points, which motivates the Low scenario.

**Pools.** Pool = users × revenue per user. Revenue per user in market *i* = reference revenue (Low $15, Base $25, High $32) × min/max-capped (GDP per capita / Kenya's)^0.35 × capped (mobile-led share / Kenya's)^1.0, where the mobile-led share is the ratio of mobile-money to any-account adoption. The reference revenue is calibrated on Safaricom M-Pesa (about $32 per active user) and Airtel Money East Africa (about $25 per customer); Airtel Money Nigeria is about $3.

**Winnable revenue.** The operator wins a share of existing users ({p(inp['Operator\'s share of EXISTING users']['base'] if 'Operator\'s share of EXISTING users' in inp else 0.03,1)} Base) and of new users above 2024 penetration ({p(SN)} Base; 8% Low, 22% High).

**Scoring.** Attractiveness = size 35%, pool growth 20%, merchant-payment gap to Kenya 15%, remittances 15%, inclusion gap 15%. Ease = digital readiness 20%, macro stability 20%, fragility 20%, mobile-led structure 15%, proximity to Kenya 15%, momentum 10%. Each component is min-max scaled to 0 to 100 across candidates; gaps are filled with the cross-market median. **Priority = √(Attractiveness × Ease)**, which penalises a weak side. Fragility uses the World Bank FY26 list (conflict-affected 0, institutional fragility 40, not listed 100).

**Business case (top five).** Launch spend in 2026; revenue from 2027 with a ramp of 10%, 35%, 65% and 100% of the target user base in 2027 to 2030; contribution margin 50%; acquisition cost $3 per new user; fixed cost $12m a year; launch investment $20m; costs scaled by (adults / 20m)^0.4 within 0.6x to 2.0x. Discount rate = 12% + 4% × (1 − macro score) + 4% × (1 − stability score). Terminal value is 5× 2035 EBITDA. Because NPV is linear in the operator's share, the break-even share is solved in closed form and cross-checked by bisection in Python.

**Robustness.** (a) Back-test above. (b) A leave-one-country-out regression of adoption on fundamentals shows they do not predict out-of-sample ({rm:.1f} against {rn:.1f} points); the regression is reported but not used in scoring. (c) {D['n_draws']:,} random draws of all scoring weights (flat Dirichlet) record how often each market is first, or in the top two or three.

## 4. Results
| Rank | Market | Attract. | Ease | Priority | Quadrant | Adoption 2024 | Adoption 2030 Base | Pool 2030 Base ($m) | Winnable 2030 Base ($m) |
|---|---|---|---|---|---|---|---|---|---|
{rowsA}

| Market | NPV Low | NPV Base | NPV High | Expected NPV | Peak funding | Payback | Break-even share of new users |
|---|---|---|---|---|---|---|---|
""" + "\n".join(f"| {s['country']} | {m_(s['npv'][0])} | {m_(s['npv'][1],1)} | {m_(s['npv'][2])} | {m_(s['exp_npv'],1)} | {m_(s['peak'])} | {s['payback']} | {p(s['be_share'],1)} |" for s in D["summary"]) + f"""

## 5. Integrity checks ({D['overall']})
""" + "\n".join(f"- {a}: {'pass' if b is True else 'FAIL'}" for a, b in D["checks"]) + """

## 6. Limitations
""" + "\n".join(f"{i+1}. {t}" for i, t in enumerate(D["limits"])) + """

## 7. Reproduce
```
pip install -r requirements.txt
python analysis/prepare.py        # clean raw data
python analysis/model.py          # Python reference model, back-test, regressions, Monte Carlo
python analysis/build_workbook.py # build the Excel model (then recalculate in Excel or LibreOffice)
python analysis/export_results.py # export results from the recalculated workbook
python analysis/build_deck.py     # HTML deck
python analysis/build_docs.py     # documents
```
"""
open(os.path.join(ROOT, "docs", "methods_appendix.md"), "w").write(MA)

KIT = f"""# CV, application and interview kit: Africa's mobile-money frontier

## CV bullets (pick two or three)
- Built a market-selection model for a hypothetical Kenyan mobile-money operator across {len(D['markets'])} sub-Saharan markets (Global Findex 2025, World Bank WDI); ranked {nc} candidates on attractiveness and ease of entry and recommended a gated Tanzania-first entry, with DR Congo held as an option.
- Back-tested the adoption forecast (error {bt[0.0]['mae_pp']:.1f} points against {bt[1.0]['mae_pp']:.1f} for country-specific trends), found that economic fundamentals fail out-of-sample ({rm:.1f} against {rn:.1f} points of error), and used the result to design a diligence gate rather than over-trust a model.
- Built a live-formula Excel model with scenarios, break-even analysis and a {D['n_draws']:,}-draw weight-robustness test, reconciled to an independent Python implementation ({npass} of {len(D['checks'])} checks pass), plus an interactive HTML deck.

## LinkedIn / GitHub one-liner
Market-selection case for a Kenyan mobile-money operator: which African markets to enter, in what order, and what you would need to believe. Findex + WDI data, Excel model, HTML deck.

## 60-second pitch
"A Kenyan mobile-money operator has {p(K['mm24'])} adoption at home, so growth has to come from abroad. I scored {nc} sub-Saharan markets on attractiveness and how easy they are to enter, then built business cases for the top five. Tanzania comes first. It has a {m_(T['pool30'][1])} revenue pool by 2030, adoption of {p(T['mm24'])} against Kenya's {p(K['mm24'])}, and no fragility flag. But the case is thin: the Base NPV is {m_(sT['npv'][1],1)}, and it only breaks even if the operator wins {p(sT['be_share'],1)} of new users. The most interesting finding was that economic fundamentals don't predict who wins, so my recommendation is a gated plan: diligence, a Tanzania launch, a 2028 checkpoint, and a second market only on evidence."

## Likely interview questions and answers
**1. Why this topic?** Mobile money is where African financial inclusion is being decided, and it is a classic market-entry problem with real data. It lets me show structuring, quantitative work and judgement.

**2. What is your recommendation in one sentence?** Enter Tanzania first, hold DR Congo as a gated option, and commit to a second market only after a 2028 checkpoint.

**3. Why Tanzania over Nigeria, which is much bigger?** Nigeria's pool is the largest on paper ({m_(NG['pool30'][1])}) but it is conflict-affected on the World Bank list, mostly bank-led so revenue per user is lower (Airtel Money Nigeria discloses about $3), and it ranks {NG['rank']} of {nc}. A big prize you cannot reach profitably is not the best first move.

**4. How did you pick the weights?** They are my judgement (35% on size within attractiveness; 20% each on readiness, macro and fragility within ease). I tested them with {D['n_draws']:,} random weightings: Tanzania stays top-two in {p(mc['TZA']['top2'])}, and I say plainly that positions beyond the top two are unstable.

**5. How do you know the forecast is any good?** I back-tested it. Forecasting 2024 from data to 2022, the common growth rate had {bt[0.0]['mae_pp']:.1f} points of average error versus {bt[1.0]['mae_pp']:.1f} for country-specific trends. It ran {bt[0.0]['bias_pp']:.1f} points high, so I built a Low scenario at half the growth.

**6. What is the biggest weakness?** Revenue per user and operator share are assumptions. Revenue per user is calibrated on two press-reported company disclosures; operator share is a judgement. I handled this with a break-even share ({p(sT['be_share'],1)} for Tanzania against {p(SN)} assumed) and sensitivity grids rather than claiming precision.

**7. Your fundamentals model failed. Why report it?** Because it is a real finding. Income, urbanisation, phones, electricity and remittances don't predict adoption for countries the model hasn't seen ({rm:.1f} points of error against {rn:.1f} for a benchmark). Kenya is about {(K['mm24']-D['loco']['KEN']['expected'])*100:.0f} points above its fundamentals. It tells the client that local ecosystem and execution matter, which is why the plan has gates.

**8. The NPV is only {m_(sT['npv'][1],1)}. Why recommend it?** The Base case is thin and the Low case is {m_(sT['npv'][0])}, so I recommend a staged bet: diligence first, a launch only if the entry route fits the budget, and a gate at end-2028. Expected NPV across scenarios is {m_(sT['exp_npv'],1)}, but I would not present that as the headline.

**9. What would change your answer?** If diligence showed an entry route above budget, if the 2028 share of new users stalled below about {p(sT['be_share'])}, or if a partnership made DR Congo's or Côte d'Ivoire's economics better than stand-alone.

**10. What data was missing?** Governance indicators (WGI) and the Findex codebook. I used the World Bank fragility list as a coarse stability proxy and disclosed it. Adding WGI is the first extension.

**11. What would you do with more time?** Add WGI; model regulation and interoperability explicitly; use operator-level data on agents and revenue; run country diligence on Tanzania and DR Congo.

**12. How did you check the work?** The Excel model is built from live formulas and reconciled to an independent Python implementation: {npass} of {len(D['checks'])} checks pass, including a closed-form NPV tie-out and a break-even cross-check.

## Application notes (McKinsey Business Associate and Young Leaders Program)
- Lead with the question and the answer, then the one finding that surprised you (fundamentals don't predict winners).
- Say what you assumed and how you tested it. Consulting interviewers reward honest limits more than polish.
- Be ready to walk the Tanzania slide: pool, share, break-even, gate.
- The client is hypothetical; the data and calculations are real and reproducible.
"""
open(os.path.join(ROOT, "docs", "cv_and_application_kit.md"), "w").write(KIT)
print("docs written")
