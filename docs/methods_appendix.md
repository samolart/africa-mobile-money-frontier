# Methods appendix: Africa's mobile-money frontier

## 1. Question and structure
**Governing question:** Which markets should a Kenya-based mobile-money operator enter by 2030, and in what order?
Issue tree: (1) Is the home market saturated? (2) Which markets are attractive? (3) Which are feasible to enter? (4) Does the business case work, and what must be true? (5) What sequence manages the risk?

## 2. Data
| ID | Source | Used for |
|---|---|---|
| S1 | Global Findex Database 2025 (survey year 2024; earlier rounds 2011-2021/22) (World Bank / Gates Foundation / Gallup) | Mobile money, account and merchant-payment adoption; gender, income and rural gaps; adult population |
| S2 | World Development Indicators (DataBank extract, last updated 8 Oct 2026) (World Bank) | GDP per capita, urbanisation, mobile subscriptions, internet, electricity, remittances, inflation, exchange rate, population growth |
| S3 | Safaricom FY2026 results (year to March 2026), M-Pesa revenue and active customers (Safaricom PLC, as reported by HapaKenya) | Calibration of revenue per active user in the home market |
| S4 | Airtel Africa FY2026 final results: Airtel Money revenue and customers by region (Airtel Africa plc) | Calibration of revenue per customer in East Africa and Nigeria; low-revenue bank-led markets |
| S5 | Harmonized List of Fragile and Conflict-Affected Situations, FY26 (World Bank) | Institutional stability score (conflict = 0, institutional/social fragility = 40, not listed = 100) |

Data were cleaned in `analysis/prepare.py`. The Global Findex 'all adults' group is used for headline measures; segment results (gender, income, rural) come from the same file. WDI values use the latest observation up to two years before the reference year; inflation, currency depreciation and GDP growth are 2022 to 2024 averages.

## 3. Method
**Screen.** Kenya (home) is excluded; markets under 3 million adults are dropped. 25 candidates remain of 34 markets with 2024 data.

**Forecast.** Adoption follows a logistic curve: logit(adoption) rises at a common 0.179 a year, multiplied by 0.5, 1.0 and 1.5 for the Low, Base and High scenarios, with a ceiling of 92%. Adults grow at each country's population growth rate. A back-test forecasting 2024 from data to the 2022 round compared five weights on each country's own trend. The common rate (weight 0) had the lowest error (7.4 points against 10.8 for pure country trends and 11.4 for no growth) but a bias of +2.8 points, which motivates the Low scenario.

**Pools.** Pool = users × revenue per user. Revenue per user in market *i* = reference revenue (Low $15, Base $25, High $32) × min/max-capped (GDP per capita / Kenya's)^0.35 × capped (mobile-led share / Kenya's)^1.0, where the mobile-led share is the ratio of mobile-money to any-account adoption. The reference revenue is calibrated on Safaricom M-Pesa (about $32 per active user) and Airtel Money East Africa (about $25 per customer); Airtel Money Nigeria is about $3.

**Winnable revenue.** The operator wins a share of existing users (3.0% Base) and of new users above 2024 penetration (15% Base; 8% Low, 22% High).

**Scoring.** Attractiveness = size 35%, pool growth 20%, merchant-payment gap to Kenya 15%, remittances 15%, inclusion gap 15%. Ease = digital readiness 20%, macro stability 20%, fragility 20%, mobile-led structure 15%, proximity to Kenya 15%, momentum 10%. Each component is min-max scaled to 0 to 100 across candidates; gaps are filled with the cross-market median. **Priority = √(Attractiveness × Ease)**, which penalises a weak side. Fragility uses the World Bank FY26 list (conflict-affected 0, institutional fragility 40, not listed 100).

**Business case (top five).** Launch spend in 2026; revenue from 2027 with a ramp of 10%, 35%, 65% and 100% of the target user base in 2027 to 2030; contribution margin 50%; acquisition cost $3 per new user; fixed cost $12m a year; launch investment $20m; costs scaled by (adults / 20m)^0.4 within 0.6x to 2.0x. Discount rate = 12% + 4% × (1 − macro score) + 4% × (1 − stability score). Terminal value is 5× 2035 EBITDA. Because NPV is linear in the operator's share, the break-even share is solved in closed form and cross-checked by bisection in Python.

**Robustness.** (a) Back-test above. (b) A leave-one-country-out regression of adoption on fundamentals shows they do not predict out-of-sample (25.5 against 21.0 points); the regression is reported but not used in scoring. (c) 5,000 random draws of all scoring weights (flat Dirichlet) record how often each market is first, or in the top two or three.

## 4. Results
| Rank | Market | Attract. | Ease | Priority | Quadrant | Adoption 2024 | Adoption 2030 Base | Pool 2030 Base ($m) | Winnable 2030 Base ($m) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Tanzania | 54 | 79 | 65.7 | Prioritise | 53% | 77% | 673 | 45.2 |
| 2 | Cote d'Ivoire | 51 | 72 | 60.6 | Prioritise | 53% | 77% | 409 | 27.3 |
| 3 | Uganda | 47 | 77 | 60.5 | Prioritise | 68% | 86% | 516 | 28.6 |
| 4 | Congo, Dem. Rep. | 64 | 57 | 60.3 | Big but hard | 35% | 61% | 620 | 50.4 |
| 5 | Benin | 43 | 71 | 55.5 | Easy but small | 45% | 70% | 129 | 9.5 |
| 6 | Senegal | 41 | 74 | 55.4 | Easy but small | 67% | 86% | 224 | 12.5 |
| 7 | Zambia | 40 | 76 | 54.8 | Easy but small | 69% | 87% | 258 | 14.0 |
| 8 | Togo | 45 | 67 | 54.8 | Easy but small | 48% | 73% | 82 | 5.9 |
| 9 | Madagascar | 54 | 55 | 54.2 | Big but hard | 19% | 41% | 118 | 11.0 |
| 10 | Liberia | 47 | 62 | 53.8 | Prioritise | 48% | 73% | 41 | 2.9 |
| 11 | Ghana | 39 | 69 | 52.0 | Easy but small | 78% | 91% | 584 | 27.5 |
| 12 | Guinea | 46 | 59 | 51.8 | Prioritise | 26% | 50% | 80 | 7.0 |
| 13 | Malawi | 44 | 58 | 50.5 | Easy but small | 47% | 72% | 162 | 11.6 |
| 14 | Cameroon | 48 | 52 | 50.0 | Big but hard | 55% | 78% | 331 | 21.6 |
| 15 | South Africa | 41 | 59 | 49.3 | Easy but small | 32% | 57% | 377 | 31.7 |
| 16 | Mozambique | 50 | 46 | 48.1 | Big but hard | 46% | 71% | 211 | 15.4 |
| 17 | Mali | 50 | 45 | 47.5 | Big but hard | 48% | 73% | 198 | 14.0 |
| 18 | Sierra Leone | 41 | 53 | 46.9 | Deprioritise | 32% | 58% | 59 | 4.9 |
| 19 | Congo, Rep. | 37 | 59 | 46.8 | Easy but small | 52% | 76% | 78 | 5.3 |
| 20 | Nigeria | 69 | 30 | 45.8 | Big but hard | 33% | 59% | 1,321 | 109.7 |
| 21 | Burkina Faso | 47 | 39 | 42.6 | Big but hard | 44% | 70% | 175 | 13.0 |
| 22 | Chad | 45 | 36 | 40.0 | Deprioritise | 13% | 31% | 52 | 5.1 |
| 23 | Ethiopia | 58 | 27 | 39.6 | Big but hard | 9% | 23% | 104 | 10.5 |
| 24 | Zimbabwe | 43 | 36 | 39.1 | Deprioritise | 43% | 69% | 159 | 11.9 |
| 25 | Niger | 45 | 25 | 33.8 | Deprioritise | 6% | 15% | 17 | 1.7 |

| Market | NPV Low | NPV Base | NPV High | Expected NPV | Peak funding | Payback | Break-even share of new users |
|---|---|---|---|---|---|---|---|
| Tanzania | −$102m | $13.5m | $194m | $29.8m | $56m | 2035 | 13.6% |
| Cote d'Ivoire | −$81m | −$10.3m | $99m | −$0.6m | $44m | none | 16.7% |
| Uganda | −$96m | −$29.9m | $65m | −$22.7m | $54m | none | 20.2% |
| Congo, Dem. Rep. | −$112m | $2.2m | $209m | $25.4m | $70m | 2035 | 14.8% |
| Benin | −$67m | −$40.7m | $2m | −$36.3m | $50m | none | 33.9% |

## 5. Integrity checks (ALL CHECKS PASS)
- Attractiveness weights sum to 100%: pass
- Ease weights sum to 100%: pass
- Adoption forecast 2030 (Base) equals Python: total absolute difference: pass
- Revenue pool 2030 (Base) equals Python: pass
- Winnable revenue 2030 (Base) equals Python: pass
- Attractiveness score equals Python: pass
- Ease score equals Python: pass
- Priority score equals Python: pass
- Rank equals Python: pass
- Discount rate equals Python: pass
- Number of ranked candidates equals count of candidate flags: pass
- Home market (Kenya) is excluded from candidates: pass
- Closed-form NPV equals year-by-year NPV in all 15 case blocks (total gap): pass
- NPV (Low, Base, High) for the top five equals Python: total absolute difference: pass
- Break-even share multiple for the top five equals Python's bisection: pass
- Sensitivity grid centre cells equal Base NPV (total difference): pass
- No error values on Data: pass
- No error values on Forecast: pass
- No error values on Pools: pass
- No error values on Scorecard: pass
- No error values on Cases: pass
- No error values on Sensitivity: pass
- No error values on Summary: pass

## 6. Limitations
1. Governance indicators (WGI: government effectiveness GE.EST, regulatory quality RQ.EST) were not in the data supplied. Institutional stability is therefore proxied by the World Bank FY26 fragility list, which is coarse (three levels). Adding WGI is the first extension.
2. No Findex codebook was available. Variable meanings were taken from names and checked against published headline figures (for example Kenya's mobile-money adoption).
3. Rwanda, Burundi, Somalia and South Sudan have no 2024 Findex mobile-money result, so they cannot be scored.
4. Findex measures the share of adults reporting a mobile money account. Operator-reported 'active users' are defined differently and are not comparable one-to-one.
5. Revenue per user is calibrated on two company disclosures reported in the press (S3, S4), not audited filings. It is scaled to other markets by income and by how mobile-led the market is. The Low/High range spans the uncertainty.
6. Judgement inputs, flagged [A] in the workbook: proximity to Kenya, operator share of new and existing users, margin, fixed cost, launch investment, terminal multiple and discount-rate premia. Each is tested in the Sensitivity sheet or through the break-even share.
7. A cross-country regression of adoption on economic fundamentals does not predict adoption out-of-sample (leave-one-country-out error 25.5 points against 21.0 for a no-fundamentals benchmark). The regression is therefore reported, not used in scoring.
8. The adoption forecast over-predicted 2024 levels by 2.8 points on average in a back-test from 2022. The Low scenario halves the trend to cover this.
9. Ranks beyond the top two are sensitive to the scoring weights (see Robustness). The recommendation rests on the top of the ranking and on the gate sequence, not on a precise ordering.
10. Business-case values are an illustrative, entry-level screen (no tax, no working capital, no currency path beyond the discount-rate premium). They are not a valuation.

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
