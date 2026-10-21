"""SVG chart helpers for the 'Kanga' deck. Colours are CSS variables so charts follow light/dark themes."""
from html import escape

IND, SAF, VERM, TEAL, PLUM = "var(--ind)", "var(--saf)", "var(--verm)", "var(--teal)", "var(--plum)"
INK, MUTE, RULE, SOFT, PAPER = "var(--ink)", "var(--mute)", "var(--rule)", "var(--soft)", "var(--paper)"


def esc(t):
    return escape(str(t), quote=True)


def svg(w, h, inner, label=""):
    return f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}" xmlns="http://www.w3.org/2000/svg">{inner}</svg>'


def T(x, y, s, size=12, anchor="start", weight=400, fill=INK, extra=""):
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" fill="{fill}" {extra}>{esc(s)}</text>'


class Sc:
    def __init__(s, d0, d1, r0, r1):
        s.d0, s.d1, s.r0, s.r1 = d0, d1, r0, r1

    def __call__(s, v):
        return s.r0 + (v - s.d0) / (s.d1 - s.d0) * (s.r1 - s.r0)


def pct(v, d=0):
    return f"{v*100:.{d}f}%"


def usd(v, d=0):
    s = f"{abs(v):,.{d}f}"
    return ("−$" if v < 0 else "$") + s


def grid_x(sx, y0, y1, vals, fmt, mt, ph, out):
    for v in vals:
        out.append(f'<line x1="{sx(v):.1f}" x2="{sx(v):.1f}" y1="{mt}" y2="{mt+ph}" stroke="{RULE}"/>')
        out.append(T(sx(v), mt + ph + 18, fmt(v), 11, "middle", fill=MUTE))


def trends(w, h, series, x0=2011, x1=2025, colors=None, hi="Kenya"):
    """series: {label: {year: value}}. Highlight one series."""
    ml, mr, mt, mb = 44, 96, 16, 30
    pw, ph = w - ml - mr, h - mt - mb
    sx, sy = Sc(x0, x1, ml, ml + pw), Sc(0, 1, mt + ph, mt)
    out = []
    for v in (0, .25, .5, .75, 1):
        out.append(f'<line x1="{ml}" x2="{ml+pw}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" stroke="{RULE}"/>')
        out.append(T(ml - 8, sy(v) + 4, pct(v), 11, "end", fill=MUTE))
    for yv in (2014, 2017, 2021, 2024):
        out.append(T(sx(yv), mt + ph + 20, yv, 11, "middle", fill=MUTE))
    ends = []
    for lab, d in series.items():
        pts = sorted(d.items())
        col = colors.get(lab, MUTE) if colors else MUTE
        isk = lab == hi
        poly = " ".join(f"{sx(a):.1f},{sy(b):.1f}" for a, b in pts)
        out.append(f'<polyline points="{poly}" fill="none" stroke="{col}" stroke-width="{4 if isk else 2.2}" stroke-linejoin="round" stroke-linecap="round"/>')
        for a, b in pts:
            out.append(f'<circle cx="{sx(a):.1f}" cy="{sy(b):.1f}" r="{4.5 if isk else 3}" fill="{col}"/>')
        ends.append((sy(pts[-1][1]), lab, col, pts[-1][1]))
    ends.sort()
    last = -99
    for y, lab, col, val in ends:
        y = max(y, last + 14)
        out.append(T(sx(x1 - 1) + 10, y + 4, f"{lab} {pct(val)}", 12, "start", 700, col))
        last = y
    return svg(w, h, "".join(out), "Mobile-money adoption over time")


def dumbbell(w, rows, cols, xmax=1.0, label=""):
    """rows: [(label, [v1,v2,v3], highlight)] ; cols: [(name,color)] values joined by a line."""
    ml, mr, mt, rh = 150, 40, 30, 30
    h = mt + rh * len(rows) + 30
    pw = w - ml - mr
    sx = Sc(0, xmax, ml, ml + pw)
    out = []
    for v in [i / 4 for i in range(0, int(xmax * 4) + 1)]:
        out.append(f'<line x1="{sx(v):.1f}" x2="{sx(v):.1f}" y1="{mt-6}" y2="{h-30}" stroke="{RULE}"/>')
        out.append(T(sx(v), h - 12, pct(v), 11, "middle", fill=MUTE))
    for i, (lab, vals, hl) in enumerate(rows):
        y = mt + rh * i + rh / 2
        out.append(T(ml - 12, y + 4, lab, 12, "end", 700 if hl else 500, INK))
        out.append(f'<line x1="{sx(min(vals)):.1f}" x2="{sx(max(vals)):.1f}" y1="{y:.1f}" y2="{y:.1f}" stroke="{RULE}" stroke-width="5" stroke-linecap="round"/>')
        for v, (nm, col) in zip(vals, cols):
            out.append(f'<circle cx="{sx(v):.1f}" cy="{y:.1f}" r="6" fill="{col}"/>')
    # column legend at top
    return svg(w, h, "".join(out), label)


def hbars(w, rows, fmt, color=IND, xmax=None, ml=150, bar=20, gap=11, whisk=None, label="", hl=None):
    """rows: [(label, value, color_override)]; whisk: dict label->(lo,hi)."""
    mt, mr = 10, 70
    h = mt + (bar + gap) * len(rows) + 8
    xm = xmax or max([r[1] for r in rows] + [x[1] for x in (whisk or {}).values()]) * 1.05
    sx = Sc(0, xm, ml, w - mr)
    out = [f'<line x1="{ml}" x2="{ml}" y1="{mt}" y2="{h-4}" stroke="{INK}"/>']
    for i, r in enumerate(rows):
        lab, val = r[0], r[1]
        col = r[2] if len(r) > 2 and r[2] else color
        y = mt + (bar + gap) * i
        out.append(T(ml - 10, y + bar / 2 + 4, lab, 12, "end", 700 if (hl and lab in hl) else 500))
        out.append(f'<rect x="{ml}" y="{y}" width="{max(sx(val)-ml,1):.1f}" height="{bar}" fill="{col}" rx="2"/>')
        if whisk and lab in whisk:
            lo, hi = whisk[lab]
            yc = y + bar / 2
            out.append(f'<line x1="{sx(lo):.1f}" x2="{sx(hi):.1f}" y1="{yc}" y2="{yc}" stroke="{INK}" stroke-width="1.6"/>')
            for v in (lo, hi):
                out.append(f'<line x1="{sx(v):.1f}" x2="{sx(v):.1f}" y1="{yc-5}" y2="{yc+5}" stroke="{INK}" stroke-width="1.6"/>')
            out.append(T(sx(hi) + 8, yc + 4, fmt(val), 12, "start", 700))
        else:
            out.append(T(sx(val) + 8, y + bar / 2 + 4, fmt(val), 12, "start", 700))
    return svg(w, h, "".join(out), label)


def bubble(w, h, pts, xr=(0, 100), yr=(0, 100), xl="", yl="", xmid=None, ymid=None, label="", labels=()):
    """pts: dict(x,y,r,color,label,show)"""
    ml, mr, mt, mb = 56, 24, 20, 46
    pw, ph = w - ml - mr, h - mt - mb
    sx, sy = Sc(*xr, ml, ml + pw), Sc(*yr, mt + ph, mt)
    out = []
    if xmid is not None:
        out.append(f'<rect x="{sx(xmid):.1f}" y="{mt}" width="{ml+pw-sx(xmid):.1f}" height="{sy(ymid)-mt:.1f}" fill="{SAF}" opacity=".13"/>')
        out.append(f'<line x1="{sx(xmid):.1f}" x2="{sx(xmid):.1f}" y1="{mt}" y2="{mt+ph}" stroke="{MUTE}" stroke-dasharray="4 4"/>')
        out.append(f'<line x1="{ml}" x2="{ml+pw}" y1="{sy(ymid):.1f}" y2="{sy(ymid):.1f}" stroke="{MUTE}" stroke-dasharray="4 4"/>')
        out.append(T(ml + pw - 8, mt + 16, "PRIORITISE", 11, "end", 700, MUTE))
        out.append(T(ml + 8, mt + 16, "EASY BUT SMALL", 11, "start", 700, MUTE, 'opacity=".8"').replace("start", "start"))
        out.append(T(ml + pw - 8, mt + ph - 8, "BIG BUT HARD", 11, "end", 700, MUTE))
        out.append(T(ml + 8, mt + ph - 8, "DEPRIORITISE", 11, "start", 700, MUTE))
    out.append(f'<rect x="{ml}" y="{mt}" width="{pw}" height="{ph}" fill="none" stroke="{RULE}"/>')
    for v in range(int(xr[0]), int(xr[1]) + 1, 20):
        out.append(T(sx(v), mt + ph + 18, v, 11, "middle", fill=MUTE))
    for v in range(int(yr[0]), int(yr[1]) + 1, 20):
        out.append(T(ml - 8, sy(v) + 4, v, 11, "end", fill=MUTE))
    out.append(T(ml + pw / 2, h - 6, xl, 12, "middle", 600, INK))
    out.append(f'<text transform="translate(14,{mt+ph/2}) rotate(-90)" font-size="12" text-anchor="middle" font-weight="600" fill="{INK}">{esc(yl)}</text>')
    for p in sorted(pts, key=lambda p: -p["r"]):
        out.append(f'<circle cx="{sx(p["x"]):.1f}" cy="{sy(p["y"]):.1f}" r="{p["r"]:.1f}" fill="{p["color"]}" fill-opacity=".78" stroke="{PAPER}" stroke-width="1.5"/>')
    for p in pts:
        if p.get("show"):
            dx, dy = p.get("dx", p["r"] + 5), p.get("dy", 4)
            out.append(T(sx(p["x"]) + dx, sy(p["y"]) + dy, p["label"], 12, p.get("anchor", "start"), 700, INK))
    return svg(w, h, "".join(out), label)


def range_dots(w, rows, label="", xmin=-130, xmax=230):
    """rows: [(label,[low,base,high],exp,hl)] NPV with zero line."""
    ml, mr, mt, rh = 150, 30, 24, 46
    h = mt + rh * len(rows) + 34
    sx = Sc(xmin, xmax, ml, w - mr)
    out = []
    for v in range(-100, xmax + 1, 50):
        out.append(f'<line x1="{sx(v):.1f}" x2="{sx(v):.1f}" y1="{mt-6}" y2="{h-30}" stroke="{RULE}"/>')
        out.append(T(sx(v), h - 12, usd(v), 11, "middle", fill=MUTE))
    out.append(f'<line x1="{sx(0):.1f}" x2="{sx(0):.1f}" y1="{mt-10}" y2="{h-30}" stroke="{INK}" stroke-width="2"/>')
    for i, (lab, (lo, ba, hi), hl) in enumerate(rows):
        y = mt + rh * i + rh / 2
        out.append(T(ml - 12, y + 4, lab, 12, "end", 700 if hl else 500))
        out.append(f'<line x1="{sx(lo):.1f}" x2="{sx(hi):.1f}" y1="{y}" y2="{y}" stroke="{RULE}" stroke-width="8" stroke-linecap="round"/>')
        out.append(f'<circle cx="{sx(lo):.1f}" cy="{y}" r="5.5" fill="{VERM}"/><circle cx="{sx(hi):.1f}" cy="{y}" r="5.5" fill="{TEAL}"/>')
        out.append(f'<rect x="{sx(ba)-8:.1f}" y="{y-8}" width="16" height="16" fill="{IND}" transform="rotate(45 {sx(ba):.1f} {y})"/>')
        out.append(T(sx(ba), y - 14, usd(ba), 12, "middle", 700, INK))
    return svg(w, h, "".join(out), label)


def cash_chart(w, h, years, rev, ebitda, cum, label=""):
    ml, mr, mt, mb = 52, 20, 18, 30
    pw, ph = w - ml - mr, h - mt - mb
    lo, hi = -70, 80
    sy = Sc(lo, hi, mt + ph, mt)
    n = len(years)
    slot = pw / n
    out = []
    for v in range(-60, 81, 20):
        out.append(f'<line x1="{ml}" x2="{ml+pw}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" stroke="{RULE}"/>')
        out.append(T(ml - 8, sy(v) + 4, v, 11, "end", fill=MUTE))
    out.append(f'<line x1="{ml}" x2="{ml+pw}" y1="{sy(0):.1f}" y2="{sy(0):.1f}" stroke="{INK}" stroke-width="1.5"/>')
    bw = slot * 0.34
    for i, y in enumerate(years):
        cx = ml + slot * i + slot / 2
        for dx, val, col in ((-bw / 2 - 1, rev[i] or 0, SAF), (bw / 2 + 1, ebitda[i] or 0, IND)):
            top, hh = (sy(val), sy(0) - sy(val)) if val >= 0 else (sy(0), sy(val) - sy(0))
            out.append(f'<rect x="{cx+dx-bw/2:.1f}" y="{top:.1f}" width="{bw:.1f}" height="{max(hh,0.5):.1f}" fill="{col}"/>')
        out.append(T(cx, mt + ph + 20, y, 11, "middle", fill=MUTE))
    pts = " ".join(f"{ml+slot*i+slot/2:.1f},{sy(c):.1f}" for i, c in enumerate(cum))
    out.append(f'<polyline points="{pts}" fill="none" stroke="{VERM}" stroke-width="3" stroke-linejoin="round"/>')
    for i, c in enumerate(cum):
        out.append(f'<circle cx="{ml+slot*i+slot/2:.1f}" cy="{sy(c):.1f}" r="3.6" fill="{VERM}"/>')
    k = min(range(n), key=lambda i: cum[i])
    out.append(T(ml + slot * k + slot / 2, sy(cum[k]) + 20, f"low point {usd(cum[k])}m", 12, "middle", 700, VERM))
    return svg(w, h, "".join(out), label)


def vbars_pair(w, h, cats, a, b, ymax, fa, names, label=""):
    """grouped bars: a (indigo) and b (saffron)."""
    ml, mr, mt, mb = 44, 14, 16, 54
    pw, ph = w - ml - mr, h - mt - mb
    sy = Sc(0, ymax, mt + ph, mt)
    slot = pw / len(cats)
    out = []
    for v in range(0, int(ymax) + 1, 4):
        out.append(f'<line x1="{ml}" x2="{ml+pw}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" stroke="{RULE}"/>')
        out.append(T(ml - 8, sy(v) + 4, v, 11, "end", fill=MUTE))
    bw = slot * 0.3
    for i, c in enumerate(cats):
        cx = ml + slot * i + slot / 2
        for dx, val, col in ((-bw / 2 - 1, a[i], IND), (bw / 2 + 1, b[i], SAF)):
            out.append(f'<rect x="{cx+dx-bw/2:.1f}" y="{sy(val):.1f}" width="{bw:.1f}" height="{sy(0)-sy(val):.1f}" fill="{col}"/>')
            out.append(T(cx + dx, sy(val) - 5, fa(val), 11, "middle", 700))
        for q, ln in enumerate(str(c).split("\n")):
            out.append(T(cx, mt + ph + 18 + 14 * q, ln, 11.5, "middle", 500, MUTE))
    return svg(w, h, "".join(out), label)


def scatter_loco(w, h, pts, label=""):
    ml, mr, mt, mb = 56, 20, 16, 46
    pw, ph = w - ml - mr, h - mt - mb
    sx, sy = Sc(0, 1, ml, ml + pw), Sc(0, 1, mt + ph, mt)
    out = [f'<rect x="{ml}" y="{mt}" width="{pw}" height="{ph}" fill="none" stroke="{RULE}"/>']
    for v in (0, .25, .5, .75, 1):
        out.append(T(sx(v), mt + ph + 18, pct(v), 11, "middle", fill=MUTE)); out.append(T(ml - 8, sy(v) + 4, pct(v), 11, "end", fill=MUTE))
    out.append(f'<line x1="{sx(0)}" y1="{sy(0)}" x2="{sx(1)}" y2="{sy(1)}" stroke="{MUTE}" stroke-dasharray="5 4"/>')
    out.append(T(sx(1) - 4, sy(1) + 16, "perfect prediction", 11, "end", fill=MUTE))
    for p in pts:
        col = VERM if p.get("hl") else IND
        out.append(f'<circle cx="{sx(p["x"]):.1f}" cy="{sy(p["y"]):.1f}" r="{6 if p.get("hl") else 4.2}" fill="{col}" fill-opacity=".8"/>')
        if p.get("label"):
            out.append(T(sx(p["x"]) - 10, sy(p["y"]) + 4, p["label"], 12, "end", 700, col))
    out.append(T(ml + pw / 2, h - 6, "Adoption predicted from fundamentals (country held out)", 12, "middle", 600))
    out.append(f'<text transform="translate(14,{mt+ph/2}) rotate(-90)" font-size="12" text-anchor="middle" font-weight="600" fill="{INK}">Actual adoption 2024</text>')
    return svg(w, h, "".join(out), label)
