"""Step 1. Clean the two raw downloads into analysis-ready tables.

Inputs  (data/raw):  GlobalFindexDatabase2025.csv (World Bank), WDI_selected_indicators.csv (World Bank DataBank)
Outputs (data/processed): panel.csv, segments_2024.csv
Run from the repository root:  python analysis/prepare.py
"""
import os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW, PROC = os.path.join(ROOT, "data", "raw"), os.path.join(ROOT, "data", "processed")

# ---- Global Findex 2025 (survey years 2011, 2014, 2017, 2021, 2024; 2022 is a small extra round) ----
fx = pd.read_csv(os.path.join(RAW, "GlobalFindexDatabase2025.csv"), low_memory=False)
fx = fx.rename(columns={"countrynewwb": "country", "codewb": "iso3", "regionwb24_hi": "region", "incomegroupwb24": "income_group"})
ssa = fx[fx["region"].str.contains("Sub-Saharan", na=False)].copy()
KEEP = {  # Findex variable -> analysis name (all are shares of adults, 0-1)
    "account_t_d": "account",             # has an account (financial institution or mobile money)
    "fiaccount_t_d": "fi_account",        # has a financial-institution account
    "mobileaccount_t_d": "mobile_money",  # has a mobile money account
    "g20_made": "digital_pay_made",       # made a digital payment
    "g20_received": "digital_pay_recv",   # received a digital payment
    "merchant_pay": "merchant_pay",       # made a digital merchant payment (2021 and 2024 only)
    "internet": "internet_access",        # has internet access
}
allg = ssa[ssa["group"] == "all"][["country", "iso3", "year", "pop_adult", "income_group"] + list(KEEP)].rename(columns=KEEP)

# ---- WDI selected indicators ----
w = pd.read_csv(os.path.join(RAW, "WDI_selected_indicators.csv"), na_values=["..", ""])
w = w[w["Series Code"].notna() & w["Country Code"].notna()]
ycols = [c for c in w.columns if "[YR" in c]
w = w.melt(id_vars=["Country Name", "Country Code", "Series Code"], value_vars=ycols, var_name="y", value_name="value")
w["year"] = w["y"].str.extract(r"(\d{4})").astype(int)
WNAME = {"SP.POP.TOTL": "pop_total", "SP.POP.GROW": "pop_growth", "SP.URB.TOTL.IN.ZS": "urban_pct", "NY.GDP.PCAP.PP.KD": "gdppc_ppp",
         "NY.GDP.PCAP.CD": "gdppc_usd", "NY.GDP.MKTP.KD.ZG": "gdp_growth", "IT.CEL.SETS.P2": "mobile_subs_100",
         "IT.NET.USER.ZS": "internet_users_pct", "FP.CPI.TOTL.ZG": "inflation", "PA.NUS.FCRF": "fx_lcu_usd",
         "BX.TRF.PWKR.DT.GD.ZS": "remit_gdp", "EG.ELC.ACCS.ZS": "electricity_pct"}
w["var"] = w["Series Code"].map(WNAME)
wide = w.pivot_table(index=["Country Code", "year"], columns="var", values="value", aggfunc="first").reset_index().rename(columns={"Country Code": "iso3"})

# FX change: log change in local currency per USD (positive = local currency weakened)
wide = wide.sort_values(["iso3", "year"])
wide["fx_dep_pct"] = wide.groupby("iso3")["fx_lcu_usd"].transform(lambda s: np.log(s).diff() * 100)

wide.to_csv(os.path.join(PROC, "wdi_wide.csv"), index=False)
panel = allg.merge(wide, on=["iso3", "year"], how="left")
panel = panel.sort_values(["iso3", "year"]).reset_index(drop=True)
panel.to_csv(os.path.join(PROC, "panel.csv"), index=False)

# ---- 2024 segment gaps (mobile money account, by group) ----
seg = ssa[(ssa["year"] == 2024) & (ssa["group"] != "all")][["country", "iso3", "group", "group2", "mobileaccount_t_d", "account_t_d", "fiaccount_t_d"]]
seg = seg.rename(columns={"mobileaccount_t_d": "mobile_money", "account_t_d": "account", "fiaccount_t_d": "fi_account"})
seg.to_csv(os.path.join(PROC, "segments_2024.csv"), index=False)

print("panel rows", len(panel), "countries", panel.iso3.nunique(), "years", sorted(panel.year.unique()))
print("2024 SSA with mobile money:", panel[(panel.year == 2024) & panel.mobile_money.notna()].shape[0])
print("missing share of key WDI vars in 2024 SSA rows:")
p24 = panel[panel.year == 2024]
print(p24[["gdppc_ppp", "urban_pct", "mobile_subs_100", "internet_users_pct", "electricity_pct", "remit_gdp", "inflation", "fx_lcu_usd", "pop_growth"]].isna().mean().round(2).to_string())
