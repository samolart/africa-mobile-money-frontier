"""Source register and limitations, shared by the workbook, deck and docs."""
SOURCES = [
    ("S1", "Global Findex Database 2025 (survey year 2024; earlier rounds 2011-2021/22)", "World Bank / Gates Foundation / Gallup",
     "https://www.worldbank.org/en/publication/globalfindex", "Mobile money, account and merchant-payment adoption; gender, income and rural gaps; adult population"),
    ("S2", "World Development Indicators (DataBank extract, last updated 8 Oct 2026)", "World Bank",
     "https://databank.worldbank.org/source/world-development-indicators", "GDP per capita, urbanisation, mobile subscriptions, internet, electricity, remittances, inflation, exchange rate, population growth"),
    ("S3", "Safaricom FY2026 results (year to March 2026), M-Pesa revenue and active customers", "Safaricom PLC, as reported by HapaKenya",
     "https://hapakenya.com", "Calibration of revenue per active user in the home market"),
    ("S4", "Airtel Africa FY2026 final results: Airtel Money revenue and customers by region", "Airtel Africa plc",
     "https://www.airtel.africa/", "Calibration of revenue per customer in East Africa and Nigeria; low-revenue bank-led markets"),
    ("S5", "Harmonized List of Fragile and Conflict-Affected Situations, FY26", "World Bank",
     "https://www.worldbank.org/en/topic/fragilityconflictviolence/brief/harmonized-list-of-fragile-situations", "Institutional stability score (conflict = 0, institutional/social fragility = 40, not listed = 100)"),
]
LIMITS = [
    "Governance indicators (WGI: government effectiveness GE.EST, regulatory quality RQ.EST) were not in the data supplied. Institutional stability is therefore proxied by the World Bank FY26 fragility list, which is coarse (three levels). Adding WGI is the first extension.",
    "No Findex codebook was available. Variable meanings were taken from names and checked against published headline figures (for example Kenya's mobile-money adoption).",
    "Rwanda, Burundi, Somalia and South Sudan have no 2024 Findex mobile-money result, so they cannot be scored.",
    "Findex measures the share of adults reporting a mobile money account. Operator-reported 'active users' are defined differently and are not comparable one-to-one.",
    "Revenue per user is calibrated on two company disclosures reported in the press (S3, S4), not audited filings. It is scaled to other markets by income and by how mobile-led the market is. The Low/High range spans the uncertainty.",
    "Judgement inputs, flagged [A] in the workbook: proximity to Kenya, operator share of new and existing users, margin, fixed cost, launch investment, terminal multiple and discount-rate premia. Each is tested in the Sensitivity sheet or through the break-even share.",
    "A cross-country regression of adoption on economic fundamentals does not predict adoption out-of-sample (leave-one-country-out error 25.5 points against 21.0 for a no-fundamentals benchmark). The regression is therefore reported, not used in scoring.",
    "The adoption forecast over-predicted 2024 levels by 2.8 points on average in a back-test from 2022. The Low scenario halves the trend to cover this.",
    "Ranks beyond the top two are sensitive to the scoring weights (see Robustness). The recommendation rests on the top of the ranking and on the gate sequence, not on a precise ordering.",
    "Business-case values are an illustrative, entry-level screen (no tax, no working capital, no currency path beyond the discount-rate premium). They are not a valuation.",
]
