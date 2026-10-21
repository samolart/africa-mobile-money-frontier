"""Step 5. Build the HTML deck ('Kanga' theme) from outputs/results.json. No hand-typed results: every figure is read from the recalculated workbook."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from deck_lib2 import *  # noqa
from html import escape as esc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(ROOT, "outputs", "results.json")))
MK = {m["iso"]: m for m in D["markets"]}
CAND = sorted([m for m in D["markets"] if m["cand"] == 1], key=lambda m: m["rank"])
S = {s["iso"]: s for s in D["summary"]}
KEN = MK["KEN"]
TZA, CIV, UGA, COD, NGA, ETH = (MK[i] for i in ("TZA", "CIV", "UGA", "COD", "NGA", "ETH"))
B1 = D["blocks"]["1|Base"]["rows"]
YRS = list(range(2026, 2036))
inp = D["inputs"]
def I(name): return inp[name]
SN = pct(inp["Operator's share of NEW users by 2030"]["base"])
def money(v, d=0): return usd(v, d) + "m"
SL = []
def slide(sec, body, src="", cls=""):
    n = len(SL) + 1
    SL.append(f'<section class="slide {cls}" id="s{n}"><div class="rail"><span class="no">{n:02d}</span><span class="sec">{esc(sec)}</span></div><div class="main">{body}'
              + (f'<p class="src">{esc(src)}</p>' if src else "") + "</div></section>")
def tile(big, small, cls=""): return f'<div class="tile {cls}"><b>{big}</b><span>{small}</span></div>'
def call(h, p): return f'<div class="call"><b>{h}</b><p>{p}</p></div>'
def legend(items): return '<div class="legend">' + "".join(f'<span class="lg"><i class="{c}" style="background:{col}"></i>{esc(t)}</span>' for t, col, c in items) + "</div>"

n_all = len(D["markets"]); n_c = len(CAND)
ken_pool = KEN["pool24"]
best = CAND[0]; sb = S["TZA"]; sd = S["COD"]; sc = S["CIV"]; su = S["UGA"]
top2_tza = D["mc"]["TZA"]["top2"]; top1_tza = D["mc"]["TZA"]["top1"]
npvB = lambda iso: S[iso]["npv"][1]
bt = {round(b["w"], 2): b for b in D["backtest"]}
rm, rn = D["reg"]["loco_rmse_pp"], D["reg"]["loco_rmse_naive_pp"]
ken_exp = D["loco"]["KEN"]["expected"]

# 1 cover
motif = '<svg class="motif" viewBox="0 0 360 360" aria-hidden="true"><g fill="none" stroke-width="10">' + "".join(
    f'<rect x="{180-r}" y="{180-r}" width="{2*r}" height="{2*r}" transform="rotate(45 180 180)" stroke="{c}"/>' for r, c in ((150, "var(--saf)"), (115, "var(--verm)"), (80, "var(--teal)"), (45, "var(--on-ind)"))) + "</g></svg>"
slide("Strategy case", f"""{motif}<span class="kick">Market selection for a hypothetical Kenyan mobile-money operator</span>
<h1>Africa's mobile-money frontier: where to expand next, and what you would need to believe</h1>
<p class="lede">Kenya's home market is close to full. We scored {n_c} sub-Saharan markets on attractiveness and ease of entry, built business cases for the top five, and tested what would have to be true for each to pay back.</p>
<div class="foot"><span>Data: Global Findex 2025 (survey 2024), World Development Indicators, World Bank FY26 fragility list</span><span>Independent analysis, October 2026</span></div>""", cls="cover")

# 2 exec summary
slide("Answer first", f"""<h2>Enter Tanzania first, hold DR Congo as a gated option, and do not commit to a second market until the Tanzania gate is passed</h2>
<div class="tiles">{tile(pct(KEN['mm24'],1),"of Kenyan adults use mobile money: little room left at home")}
{tile(f"#{best['rank']} {best['country']}",f"top priority score ({best['priority']:.0f}/100) and the only large market that is also easy")}
{tile(money(sb['npv'][1],1),f"Tanzania Base-case NPV; range {money(sb['npv'][0])} to {money(sb['npv'][2])}","ok")}
{tile(pct(sb['be_share'],1),f"share of new users Tanzania needs to break even, against {SN} assumed","hot")}</div>
<div class="cols2"><div class="call"><b>Why Tanzania</b><p>Highest priority score, a Base revenue pool of {money(TZA['pool30'][1])} in 2030, adoption of {pct(TZA['mm24'])} against Kenya's {pct(KEN['mm24'])}, and no fragility flag. It is the only market where the Base case is positive and the downside is survivable.</p></div>
<div class="call"><b>Why not a flat "enter two markets"</b><p>Only Tanzania and DR Congo are positive in the Base case, and both only just. {CIV['country']} and Uganda need more than the assumed share to break even. Fundamentals also fail to predict who wins locally, so each entry needs a diligence gate.</p></div></div>
<p class="ans"><b>The ask:</b> approve a gated Tanzania entry with a peak funding need of about {money(sb['peak'])}, and a diligence study on DR Congo and {CIV['country']} to decide the second move by the 2028 gate.</p>""",
      "Excel model: Summary and Cases sheets")

# 3 context chart
cols = {"Kenya": VERM, "Tanzania": IND, "Uganda": TEAL, "Nigeria": SAF, "Ethiopia": PLUM, "Cote d'Ivoire": MUTE}
nm = {"KEN": "Kenya", "TZA": "Tanzania", "UGA": "Uganda", "NGA": "Nigeria", "ETH": "Ethiopia", "CIV": "Cote d'Ivoire"}
ser = {nm[i]: {int(y): v for y, v in D["trend"][i].items()} for i in nm}
slide("Context", f"""<h2>Kenya's home market is near its ceiling at {pct(KEN['mm24'])} adoption, while most of the region is at half that or less</h2>
<div class="split"><div class="chart">{trends(760,380,ser,colors=cols)}<p class="note">Share of adults with a mobile money account, Global Findex survey rounds.</p></div>
<div class="side">{call("Growth at home has to slow",f"Kenya's adult population is {KEN['adults']/1e6:.1f} million and {pct(KEN['mm24'])} already use mobile money. Further growth is mostly revenue per user, not new users.")}
{call("The runway is elsewhere",f"Tanzania, Cote d'Ivoire and Uganda sit at {pct(TZA['mm24'])}, {pct(CIV['mm24'])} and {pct(UGA['mm24'])}. DR Congo and Nigeria are at {pct(COD['mm24'])} and {pct(NGA['mm24'])} with far larger populations.")}
{call("The question for the board","Which two markets, in what order, and on what evidence? The next slides answer that.")}</div></div>""",
      "Global Findex 2025 (S1). Adoption = adults with a mobile money account (2014 to 2024 rounds)")

# 4 approach funnel
slide("Approach", f"""<h2>We screened {n_all} markets down to {n_c} candidates, scored them two ways, and stress-tested only the top five in a business case</h2>
<div class="funnel">
<div class="fstep"><span class="fnum">{n_all}</span><div class="fbar"><span>Sub-Saharan markets with 2024 Findex mobile-money data</span><span>Findex + WDI</span></div></div>
<div class="fstep"><span class="fnum">{n_c}</span><div class="fbar" style="background:var(--teal);color:#fff"><span>Candidates after removing Kenya and markets under {I('Minimum market size to be a candidate')['base']/1e6:.0f}m adults</span><span>Size screen</span></div></div>
<div class="fstep"><span class="fnum">2</span><div class="fbar" style="background:var(--saf);color:#16184F"><span>Scores: attractiveness (size, growth, merchant gap, remittances, inclusion) and ease (readiness, macro, mobile-led, proximity, momentum, stability)</span><span>Priority = √(A×E)</span></div></div>
<div class="fstep"><span class="fnum">5</span><div class="fbar" style="background:var(--verm);color:#fff"><span>Business cases in Low, Base and High scenarios, with break-even share and sensitivities</span><span>NPV, funding, payback</span></div></div>
<div class="fstep"><span class="fnum">1+1</span><div class="fbar" style="background:var(--plum);color:#fff"><span>Gated recommendation: one entry now, one option held</span><span>Roadmap</span></div></div></div>
<p class="note">Every number in this deck is read from the Excel model after recalculation; {len([c for c in D['checks'] if c[1] is True])} of {len(D['checks'])} integrity checks pass against an independent Python implementation.</p>""",
      "analysis/ and model/ in the repository")

# 5 dumbbell
top = sorted(CAND, key=lambda m: -m["win_rev"][1])[:10]
rows = [(m["country"].replace("Congo, Dem. Rep.", "DR Congo"), [m["mm17"], m["mm24"], m["a30"][1]], m["rank"] <= 2) for m in top]
slide("Adoption", f"""<h2>Adoption has risen fast but unevenly, and the Base forecast has most large markets still below Kenya's {pct(KEN['mm24'])} in 2030</h2>
<div class="split"><div class="chart">{dumbbell(700,rows,[("2017",MUTE),("2024",IND),("2030 Base",VERM)])}{legend([("2017",MUTE,"c"),("2024 survey",IND,"c"),("2030 Base forecast",VERM,"c")])}</div>
<div class="side">{call("Method",f"Logistic (S-curve) diffusion: each market's log-odds of adoption grows at a common {D['g0']:.2f} a year, with the Low and High scenarios at half and one and a half times that pace, capped at {pct(I('Adoption ceiling in forecasts')['base'])}.")}
{call("Why a common rate",f"A back-test from the 2022 round showed it beat country-specific trends: {bt[0.0]['mae_pp']:.1f} against {bt[1.0]['mae_pp']:.1f} points of average error.")}
{call("Reading","Ten markets with the largest winnable revenue in 2030 (Base).")}</div></div>""",
      "Findex 2025 (S1); Forecast sheet. Dots: 2017, 2024 and 2030 Base forecast")

# 6 backtest
ws_ = [0.0, 0.25, 0.5, 0.75, 1.0]
slide("Forecast credibility", f"""<h2>A single regional growth rate forecast 2024 adoption better than country-specific trends, but ran {bt[0.0]['bias_pp']:.1f} points high, so the Low case matters</h2>
<div class="split"><div class="chart">{vbars_pair(640,330,[f"{int(w*100)}%" for w in ws_],[bt[w]['mae_pp'] for w in ws_],[bt[w]['naive_mae_pp'] for w in ws_],12,lambda v:f"{v:.1f}",("Model","No growth"),"Back-test error")}
{legend([("Forecast error with this weight on the country's own trend (points)",IND,""),("Error if adoption is assumed not to grow",SAF,"")])}<p class="note">Horizontal axis: weight given to each country's own trend. {int(bt[0.0]['n'])} countries; forecasts made from the 2022 round for 2024.</p></div>
<div class="side">{call("What it tells us",f"Country-specific trends add noise: error rises from {bt[0.0]['mae_pp']:.1f} to {bt[1.0]['mae_pp']:.1f} points as they get more weight. We therefore use a common rate.")}
{call("What it cannot do",f"The forecast was {bt[0.0]['bias_pp']:.1f} points too high on average. The Low scenario (half the growth) is the prudent planning case, and it is where Tanzania's NPV is {money(sb['npv'][0])}.")}</div></div>""",
      "Robustness sheet, section C (analysis/model.py)")

# 7 pools
topp = sorted(CAND, key=lambda m: -m["pool30"][1])[:10]
rowsP = [(m["country"].replace("Congo, Dem. Rep.", "DR Congo"), m["pool30"][1], (VERM if m["iso"] in ("NGA", "ETH") else IND)) for m in topp]
wh = {m["country"].replace("Congo, Dem. Rep.", "DR Congo"): (m["pool30"][0], m["pool30"][2]) for m in topp}
slide("Revenue pools", f"""<h2>Nigeria's revenue pool is the largest on paper but the least reliable: revenue per user is already {pct(1-NGA['arpu'][1]/KEN['arpu'][1])} below Kenya's after adjustment, and disclosed Nigerian figures are lower still</h2>
<div class="split"><div class="chart">{hbars(700,rowsP,lambda v:f"${v:,.0f}m",whisk=wh,hl=("Nigeria","Tanzania"))}<p class="note">2030 revenue pool (users × revenue per user), Base, with Low–High whiskers. Red = pools most at risk of being overstated by low or uncertain revenue per user.</p></div>
<div class="side">{tile(f"${KEN['arpu'][1]:.0f}","a year per user at Kenyan income and structure (Base)")}
{tile(f"${NGA['arpu'][1]:.0f}","Nigeria after adjusting for income and bank-led structure (Airtel Money Nigeria reports about $3)","hot")}
{tile(f"${ETH['arpu'][1]:.0f}","Ethiopia, same adjustment","hot")}
<p class="note">Calibration: Airtel Money East Africa earns about $25 per customer, Airtel Money Nigeria about $3.</p></div></div>""",
      "Pools sheet; company figures S3 and S4. Revenue per user scaled by income (elasticity 0.35) and mobile-led structure")

# 8 bubble
pts = []
for m in CAND:
    col = VERM if m["fcs"] == 0 else (SAF if m["fcs"] == 40 else IND)
    show = m["rank"] <= 5 or m["iso"] in ("NGA", "ETH", "GHA")
    lab = m["country"].replace("Congo, Dem. Rep.", "DR Congo").replace("Cote d'Ivoire", "C. d'Ivoire")
    dx = {"UGA": -12, "CIV": 12}.get(m["iso"]); dy = {"UGA": -10}.get(m["iso"])
    p = dict(x=m["A"], y=m["E"], r=4 + (m["win_rev"][1] ** .5) * 1.5, color=col, label=lab, show=show)
    if m["iso"] == "UGA": p.update(dx=-16, dy=-12, anchor="end")
    if m["iso"] == "CIV": p.update(dx=14, dy=-6)
    pts.append(p)
amed = sorted(m["A"] for m in CAND)[len(CAND) // 2]; emed = sorted(m["E"] for m in CAND)[len(CAND) // 2]
slide("Scorecard", f"""<h2>Tanzania is the only market that is both large and easy to enter; Nigeria and Ethiopia are attractive but hard</h2>
<div class="split"><div class="chart">{bubble(700,470,pts,(20,80),(20,90),"Attractiveness (0 to 100)","Ease of entry (0 to 100)",amed,emed,"Attractiveness and ease")}
{legend([("Not on the fragility list",IND,"c"),("Institutional fragility",SAF,"c"),("Conflict-affected (World Bank FY26)",VERM,"c")])}<p class="note">Bubble area = winnable revenue in 2030, Base. Shaded quadrant = above the median on both axes.</p></div>
<div class="side">{call("Attractiveness",f"Winnable revenue (35%), pool growth (20%), merchant-payment gap, remittances and inclusion gap (15% each).")}
{call("Ease",f"Digital readiness and macro stability (20% each), fragility (20%), mobile-led structure and proximity to Kenya (15% each), momentum (10%).")}
{call("Priority score","Square root of attractiveness × ease, so a market cannot score well by being strong on one side only.")}</div></div>""",
      "Scorecard sheet; weights are analyst judgement (tag [A]) and are tested on the next-but-one slide")

# 9 ranking heat table
def hc(v):
    t = max(0, min(1, v / 100))
    return f"background:color-mix(in srgb,var(--saf) {int(t*85)}%,var(--paper))"
cols_h = [("Size", "s_size"), ("Growth", "s_growth"), ("Merch.", "s_merch"), ("Remit.", "s_remit"), ("Incl.", "s_incl"), ("Ready", "s_ready"), ("Macro", "s_macro"), ("Mobile-led", "s_led"), ("Prox.", "s_prox"), ("Momentum", "s_mom"), ("Stability", "s_fcs")]
trs = "".join(f'<tr class="{"hl" if m["rank"]<=2 else ""}"><td>{m["rank"]}</td><td>{esc(m["country"])}</td><td class="n"><b>{m["priority"]:.0f}</b></td>' + "".join(f'<td class="n" style="{hc(m[k])}">{m[k]:.0f}</td>' for _, k in cols_h) + "</tr>" for m in CAND[:10])
slide("Ranking", f"""<h2>Tanzania leads on a balance of size and ease; DR Congo is nearly as attractive as Nigeria but is held back by fragility and weak infrastructure</h2>
<div class="scroll"><table class="heat"><thead><tr><th>#</th><th>Market</th><th class="n">Priority</th>{''.join(f'<th class="n">{a}</th>' for a,_ in cols_h)}</tr></thead><tbody>{trs}</tbody></table></div>
<p class="note">Component scores 0 to 100 (min-max across the {n_c} candidates). The first five columns make up attractiveness, the last six ease. Top 10 of {n_c}; full table in Appendix D.</p>""",
      "Scorecard sheet")

# 10 robustness
mc = sorted(CAND, key=lambda m: -D["mc"][m["iso"]]["top2"])[:8]
rowsM = [(m["country"].replace("Congo, Dem. Rep.", "DR Congo"), D["mc"][m["iso"]]["top2"], (VERM if m["iso"] == "TZA" else IND)) for m in mc]
slide("Robustness", f"""<h2>Tanzania and DR Congo are the most frequent top-two markets across {D['n_draws']:,} random weightings; beyond them the ranking is unstable, so we recommend a sequence</h2>
<div class="split"><div class="chart">{hbars(680,rowsM,lambda v:pct(v),xmax=0.62,hl=("Tanzania",))}<p class="note">Share of {D['n_draws']:,} draws, with all attractiveness and ease weights re-drawn at random (Dirichlet), in which the market ranks in the top two.</p></div>
<div class="side">{call("What is robust",f"Tanzania ranks first in {pct(top1_tza)} of draws and DR Congo is the next most frequent top-two market ({pct(D['mc']['COD']['top2'])}).")}
{call("What is not",f"Positions three to ten swap easily. Liberia appears in the top two in {pct(D['mc']['LBR']['top2'])} of draws on ease alone, but its 2030 pool is only {money(MK['LBR']['pool30'][1])} and it covers {MK['LBR']['cover']:.1f}× its fixed cost, so the business-case screen would remove it.")}
{call("Implication","Use the score to shortlist, then decide on the business case and on diligence evidence.")}</div></div>""",
      "Robustness sheet, section D (analysis/model.py, 5,000 draws, fixed seed)")

# 11 NPV range
top5 = D["summary"]
rowsN = [(s["country"].replace("Congo, Dem. Rep.", "DR Congo"), s["npv"], s["iso"] == "TZA") for s in top5]
slide("Business case", f"""<h2>Only Tanzania and DR Congo are positive in the Base case, and the Low case is negative for all five, so this is a staged bet and not a sure thing</h2>
<div class="split"><div class="chart">{range_dots(700,rowsN,xmin=-130,xmax=230)}{legend([("Low",VERM,"c"),("Base",IND,"d"),("High",TEAL,"c")])}<p class="note">NPV at 2026 in $m, launch 2027, 2035 terminal value at {I('Terminal value multiple on 2035 EBITDA')['base']:.0f}× EBITDA. Discount rates {min(s['wacc'] for s in top5)*100:.0f}% to {max(s['wacc'] for s in top5)*100:.0f}% by market risk.</p></div>
<div class="side">{call("Tanzania",f"Base {money(sb['npv'][1],1)}, expected {money(sb['exp_npv'],1)} across scenarios, peak funding {money(sb['peak'])}, payback {sb['payback']}.")}
{call("DR Congo",f"Base {money(sd['npv'][1],1)} and the widest range, with a {sd['wacc']*100:.0f}% discount rate for fragility. It is an option, not a commitment.")}
{call(CIV['country'],f"Base {money(sc['npv'][1],1)}. Strong revenue per user but a smaller market; a partnership or acquisition route may change the maths.")}</div></div>""",
      "Cases sheet. Not a valuation: ignores tax, working capital and detailed currency paths")

# 12 Tanzania cash
slide("Tanzania", f"""<h2>Tanzania needs about {money(sb['peak'])} of funding before cash turns, with payback in {sb['payback']} on the Base case</h2>
<div class="split"><div class="chart">{cash_chart(700,370,YRS,B1['rev'],B1['ebitda'],B1['cum'],"Tanzania cash profile")}{legend([("Revenue",SAF,""),("EBITDA",IND,""),("Cumulative cash incl. launch spend",VERM,"c")])}<p class="note">$m. Base scenario.</p></div>
<div class="side">{tile(f"{sb['users30']/1e6:.1f}m",f"operator users in 2030 (about {sb['users30']/B1['adults'][4]*100:.0f}% of adults)")}
{tile(money(sb['rev30'],0),"operator revenue in 2030","")}
{tile(money(sb['ebitda30'],1),"EBITDA in 2030: the first positive year","ok")}
<p class="note">Launch spend {money(D['blocks']['1|Base']['capex'])} in 2026; fixed cost {money(I('Fixed operating cost per year (reference-size market)')['base'])} a year scaled for market size.</p></div></div>""",
      "Cases sheet, rank 1 Base block")

# 13 what you need to believe
g = D["grids"]["1"]["g1"]
r8 = g['vals'][1]; be80 = g['cols'][2] + (g['cols'][3]-g['cols'][2]) * (-r8[2]) / (r8[3]-r8[2])
def cellc(v):
    if v < 0: return "background:color-mix(in srgb,var(--verm) 38%,var(--paper))"
    return "background:color-mix(in srgb,var(--teal) 30%,var(--paper))"
trs = "".join(f'<tr><th class="n">{r:.1f}×</th>' + "".join(f'<td class="n" style="{cellc(v)}">{v:,.0f}</td>' for v in row) + "</tr>" for r, row in zip(g["rows"], g["vals"]))
slide("What you need to believe", f"""<h2>Tanzania breaks even if the operator wins {pct(sb['be_share'],1)} of new users, against the {SN} we assume: the margin for error is thin</h2>
<div class="split"><div><h3>Tanzania NPV ($m): share won × revenue per user</h3><div class="scroll"><table class="heat"><thead><tr><th>Revenue per user ↓ / Share →</th>{''.join(f'<th class="n">{c:.2f}×</th>' for c in g['cols'])}</tr></thead><tbody>{trs}</tbody></table></div>
<p class="note">Multiples of the Base assumptions. Green = positive NPV. Centre cell = Base.</p></div>
<div class="side">{call("Break-even share of new users",f"Tanzania {pct(sb['be_share'],1)}, DR Congo {pct(sd['be_share'],1)}, {CIV['country']} {pct(sc['be_share'],1)}, Uganda {pct(su['be_share'],1)}, assumed {SN}.")}
{call("What must be true",f"A well-funded challenger takes roughly one in seven new mobile-money users, at Kenyan-style revenue per user adjusted for Tanzanian income. A 20% shortfall in revenue per user needs about {pct(be80-1)} more share to still break even.")}</div></div>""",
      "Sensitivity sheet; Cases sheet break-even columns")

# 14 fundamentals do not predict
loco = D["loco"]
ptsL = [dict(x=v["expected"], y=v["actual"], hl=(k == "KEN"), label=("Kenya" if k == "KEN" else None)) for k, v in loco.items()]
slide("Risks", f"""<h2>Economic fundamentals do not predict who wins locally, which is why every entry needs a diligence gate</h2>
<div class="split"><div class="chart">{scatter_loco(520,420,ptsL,"Predicted vs actual adoption")}<p class="note">Each dot is a country, predicted by a model that never saw it (income, urbanisation, phones, electricity, remittances).</p></div>
<div class="side">{tile(f"{rm:.1f} pts","prediction error of the fundamentals model, held-out countries","hot")}{tile(f"{rn:.1f} pts","error of a benchmark that ignores fundamentals entirely")}
{call("Reading",f"The fundamentals model is no better than the benchmark. Kenya is about {(KEN['mm24']-ken_exp)*100:.0f} points above what its fundamentals imply: the operator, regulation and agent network matter.")}
{call("Gate items","Licensing path, interoperability rules, agent economics, incumbent response, FX convertibility and conflict exposure. For DR Congo add security and rail access.")}</div></div>""",
      "Robustness sheet, sections A and B (leave-one-country-out)")

# 15 roadmap
slide("Recommendation", f"""<h2>Recommended sequence: diligence, Tanzania launch, a 2028 gate, then a second market only on evidence</h2>
<div class="tl">
<div class="g"><div class="h">Gate 0 · 2026</div><p><b>Diligence study</b></p><p>Tanzania licence and partner route, agent economics, DR Congo and {CIV['country']} screening.</p><p><span class="tag">GO IF</span>entry route cost within {money(D['blocks']['1|Base']['capex'])} launch budget.</p></div>
<div><div class="h">2027 · Launch Tanzania</div><p><b>{B1['users'][1]/1e6:.2f}m users</b> and {money(B1['rev'][1],1)} revenue in the Base plan.</p><p>EBITDA {money(B1['ebitda'][1],1)}: the investment phase.</p></div>
<div class="g"><div class="h">Gate 1 · end 2028</div><p><b>Is Tanzania on the Base path?</b></p><p><span class="tag">GO IF</span>users within 20% of the Base plan ({B1['users'][2]/1e6:.1f}m at end-2028, so at least {0.8*B1['users'][2]/1e6:.1f}m) and revenue per user near ${TZA['arpu'][1]:.0f}.</p><p><span class="tag">STOP IF</span>share of new users stalls well below {pct(sb['be_share'],0)}.</p></div>
<div><div class="h">2029 to 2030 · Second market</div><p>Choose DR Congo or {CIV['country']} on diligence evidence, ideally by partnership, since stand-alone peak funding is {money(sd['peak'])} for DR Congo and {money(sc['peak'])} for {CIV['country']}.</p><p>Uganda and Nigeria revisited only if the unit economics change.</p></div></div>
<div class="tiles">{tile(money(sb['peak']),"Tanzania peak funding, Base case")}{tile(money(sb['exp_npv'],1),"Tanzania expected NPV across scenarios","ok")}{tile(money(sb['npv'][0]),"Tanzania NPV if the Low case happens: the cost of being wrong","hot")}{tile("Gate 1","end-2028: no second market is committed before it")}</div>
<p class="note">Thresholds are read from the Base business case; they are planning triggers, not forecasts.</p>""",
      "Cases sheet; roadmap is analyst judgement")

# Appendix A inputs
rowsA = "".join(f'<tr><td>{esc(k)}</td><td class="n">{(v["low"] if v["low"] is not None else "")}</td><td class="n">{v["base"]}</td><td class="n">{(v["high"] if v["high"] is not None else "")}</td><td>{esc(v["tag"] or "")}</td></tr>'
                for k, v in D["inputs"].items() if v["tag"] in ("[A]", "[S]", "[S/A]", "[E]") and not k.startswith("c_") and not k.startswith("Cap") and not k.startswith("Floor"))
def fmtv(x):
    if isinstance(x, float): return f"{x:.4g}"
    return x
rowsA = "".join(f'<tr><td>{esc(k)}</td><td class="n">{fmtv(v["low"]) if v["low"] is not None else ""}</td><td class="n">{fmtv(v["base"])}</td><td class="n">{fmtv(v["high"]) if v["high"] is not None else ""}</td><td>{esc(v["tag"] or "")}</td></tr>'
                for k, v in D["inputs"].items() if v["tag"] in ("[A]", "[S]", "[S/A]", "[E]") and not k.startswith(("Cap", "Floor")))
slide("Appendix A", f"""<h2>Appendix A. Assumptions: every input is tagged by how it was obtained</h2>
<div class="scroll"><table class="small"><thead><tr><th>Input</th><th class="n">Low</th><th class="n">Base</th><th class="n">High</th><th>Tag</th></tr></thead><tbody>{rowsA}</tbody></table></div>
<p class="note">[S] sourced, [A] analyst assumption, [E] estimated in Python, [S/A] sourced with analyst adjustment. All can be changed on the Inputs sheet.</p>""", "Excel model, Inputs sheet", cls="appendix")

# Appendix B method + checks
ck = "".join(f'<li>{esc(a)}: <b class="{"ok" if b is True else "bad"}">{"pass" if b is True else "FAIL"}</b></li>' for a, b in D["checks"])
slide("Appendix B", f"""<h2>Appendix B. Method and integrity checks</h2>
<div class="cols2"><div><h3>Method in six lines</h3><ol class="srcs"><li>Screen: Kenya excluded, markets under {I('Minimum market size to be a candidate')['base']/1e6:.0f}m adults dropped ({n_c} candidates).</li>
<li>Forecast: logit-space diffusion, common growth {D['g0']:.3f} a year, ceiling {pct(I('Adoption ceiling in forecasts')['base'])}; Low, Base and High scenarios.</li>
<li>Pools: users × revenue per user; revenue per user adjusted for income and mobile-led structure.</li>
<li>Winnable revenue: share of existing and of new users.</li>
<li>Score: min-max across candidates; attractiveness and ease; priority = √(A×E).</li>
<li>Case: NPV at risk-adjusted discount rates; closed-form break-even share; 5,000-draw weight robustness.</li></ol></div>
<div><h3>Integrity checks ({D['overall']})</h3><ol class="srcs">{ck}</ol></div></div>""", "model/ and analysis/model.py", cls="appendix")

# Appendix C sources/limits
srcs = "".join(f'<li><b>{s[0]}</b> {esc(s[1])} ({esc(s[2])}). <i>Used for:</i> {esc(s[4])}</li>' for s in D["sources"])
lims = "".join(f"<li>{esc(t)}</li>" for t in D["limits"])
slide("Appendix C", f"""<h2>Appendix C. Sources and limitations</h2><div class="cols2"><div><h3>Sources</h3><ol class="srcs">{srcs}</ol></div><div><h3>Limitations we are open about</h3><ol class="srcs">{lims}</ol></div></div>""", "Sources sheet", cls="appendix")

# Appendix D full table
trs = "".join(f'<tr class="{"hl" if m["rank"]<=2 else ""}"><td>{m["rank"]}</td><td>{esc(m["country"])}</td><td class="n">{m["A"]:.0f}</td><td class="n">{m["E"]:.0f}</td><td class="n">{m["priority"]:.1f}</td><td>{m["quad"]}</td><td class="n">{pct(m["mm24"])}</td><td class="n">{pct(m["a30"][1])}</td><td class="n">{m["pool30"][1]:,.0f}</td><td class="n">{m["win_rev"][1]:,.1f}</td><td class="n">{m["wacc"]*100:.1f}%</td></tr>' for m in CAND)
slide("Appendix D", f"""<h2>Appendix D. All {n_c} candidate markets</h2><div class="scroll"><table class="small"><thead><tr><th>#</th><th>Market</th><th class="n">Attract.</th><th class="n">Ease</th><th class="n">Priority</th><th>Quadrant</th><th class="n">Adopt. 2024</th><th class="n">Adopt. 2030 B</th><th class="n">Pool 2030 $m</th><th class="n">Winnable $m</th><th class="n">Disc. rate</th></tr></thead><tbody>{trs}</tbody></table></div>""", "Scorecard, Pools and Forecast sheets", cls="appendix")

CSS = open(os.path.join(os.path.dirname(__file__), "deck2.css")).read()
JS = """(function(){var s=[].slice.call(document.querySelectorAll('.slide')),n=s.length,c=document.getElementById('ctr');
function cur(){var y=window.innerHeight*0.35,b=0;s.forEach(function(e,i){if(e.getBoundingClientRect().top<y)b=i;});return b;}
function upd(){if(c)c.textContent=(cur()+1)+' / '+n;}
function go(d){var i=Math.max(0,Math.min(n-1,cur()+d));s[i].scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});}
window.addEventListener('scroll',upd,{passive:true});
document.addEventListener('keydown',function(e){var t=e.target&&e.target.tagName;if(t==='INPUT'||t==='TEXTAREA')return;
if(e.key==='ArrowRight'||e.key==='PageDown'||(e.key===' '&&!e.shiftKey)){e.preventDefault();go(1);}
else if(e.key==='ArrowLeft'||e.key==='PageUp'||(e.key===' '&&e.shiftKey)){e.preventDefault();go(-1);}});
var b=document.getElementById('thm');if(b){b.addEventListener('click',function(){var r=document.documentElement,d=r.getAttribute('data-theme');
var dark=d?d==='dark':window.matchMedia('(prefers-color-scheme: dark)').matches;r.setAttribute('data-theme',dark?'light':'dark');});}
upd();})();"""
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=Figtree:wght@400;500;600&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">'
HEAD = '<title>Mobile Money Frontier</title><meta name="claude:viewport-fit-sides" content="cover">' + FONTS + f"<style>{CSS}</style>"
BODY = f'<main class="deck">{"".join(SL)}</main><button class="theme" id="thm" type="button">Light / dark</button><div class="counter" id="ctr" aria-live="off"></div><script>{JS}</script>'
os.makedirs(os.path.join(ROOT, "deck"), exist_ok=True)
std = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">' + HEAD + '</head><body>' + BODY + '</body></html>')
open(os.path.join(ROOT, "deck", "mobile_money_frontier_deck.html"), "w").write(std)
open(os.path.join(ROOT, "deck", "mobile_money_frontier_deck.fragment.html"), "w").write(HEAD + BODY)
print("slides", len(SL), "bytes", len(std))
