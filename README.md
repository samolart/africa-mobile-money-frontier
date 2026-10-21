# Africa's mobile-money frontier: where should a Kenyan operator expand next?

A consulting-style market-selection case. A hypothetical Kenya-based mobile-money operator has near-saturated its home market. Which sub-Saharan markets should it enter by 2030, in what order, and what would have to be true?

**Answer.** Enter **Tanzania** first, hold **DR Congo** as a gated option, and commit to a second market only after a 2028 checkpoint. The business case is thin (Tanzania Base NPV about $13m, break-even if the operator wins about 14% of new users against 15% assumed), so the plan is gated, not a flat "enter two markets".

**[![View Presentation](https://shields.io)](https://samolart.github.io/africa-mobile-money-frontier/deck/mobile_money_frontier_deck.html)**

## Open these first
| File | What it is |
|---|---|
| `deck/mobile_money_frontier_deck.html` | 15-slide deck plus appendix (open in any browser; arrow keys to move; light/dark) |
| `docs/executive_summary.pdf` | One-page summary |
| `model/africa_mobile_money_model.xlsx` | Excel model with live formulas, scenarios, sensitivities and integrity checks |
| `docs/methods_appendix.md` | Method, results, limitations, how to reproduce |
| `docs/cv_and_application_kit.md` | CV bullets, 60-second pitch, interview Q&A |

## Headline findings
1. Kenya is at 87.5% mobile-money adoption; most large candidates are at half that or less.
2. Tanzania ranks first on attractiveness x ease; it is in the top two in about half of 5,000 random weightings. Rankings beyond the top two are unstable.
3. Nigeria has the largest revenue pool on paper but ranks 20th of 25 (conflict-affected, bank-led, low revenue per user).
4. Economic fundamentals do **not** predict adoption out-of-sample (25.5 vs 21.0 points of error), so every entry needs a diligence gate.

## Repository layout
```
data/raw/         Global Findex 2025, WDI extract and series metadata (as downloaded)
data/processed/   cleaned panel and market table
analysis/         prepare.py, model.py (Python reference), build_workbook.py, export_results.py, build_deck.py, build_docs.py
model/            Excel model
outputs/          py_results.json (Python reference), results.json (exported from the recalculated workbook)
deck/             HTML deck
docs/             executive summary, methods appendix, CV and interview kit
```

## Reproduce
```
pip install -r requirements.txt
python analysis/prepare.py
python analysis/model.py
python analysis/build_workbook.py          # then recalculate in Excel or LibreOffice (soffice --headless --convert-to xlsx)
python analysis/export_results.py
python analysis/build_deck.py
python analysis/build_docs.py
```
The workbook is reconciled to the Python reference on its **Checks** sheet (23 checks).

## Data and sources
- S1 World Bank, Global Findex Database 2025 (survey year 2024).
- S2 World Bank, World Development Indicators (DataBank extract).
- S3, S4 Safaricom and Airtel Africa FY2026 results, as reported, used to calibrate revenue per user.
- S5 World Bank FY26 list of fragile and conflict-affected situations.

## Limitations (stated plainly)
Governance indicators (WGI) were not in the data supplied, so stability uses the World Bank fragility list. No Findex codebook was available. Rwanda, Burundi, Somalia and South Sudan have no 2024 result. Revenue per user rests on two press-reported company disclosures; operator share, margin, fixed cost and launch spend are analyst assumptions tested by sensitivity and break-even analysis. The business case is an entry screen, not a valuation. The client is hypothetical.
