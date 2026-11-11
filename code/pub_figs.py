"""New figures for the public report: export losses by state, by quarter, the revenue-to-margin layers,
ship traffic through the straits with war-risk premiums, and oil routes.
Run: python3 -I pub_figs.py   (from this folder). Reads ../data/*.csv|json, writes ../figures and ../data/pub_figs_numbers.json.
Every number drawn is also written to ../data/pub_figs_numbers.json with its source."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from style import *
import pandas as pd, numpy as np
import matplotlib.dates as mdates

REP = os.path.dirname(HERE)
FIG = os.path.join(REP, "figures"); DAT = os.path.join(REP, "data")
NUM = {}
RED = ORANGE          # losses
GAIN = BLUE           # price gain
DARK = "#3a4149"


def bn(x, sign=False):
    s = f"{abs(x):.1f}"
    pre = ("+" if x > 0 else "–") if sign else ""
    return f"{pre}${s}bn"



# ---------------------------------------------------------------- 0. strike damage by weapon and by state
def damage():
    w = json.load(open(os.path.join(DAT, "strike_damage_by_weapon.json")))["by_weapon_usd_bn"]
    d = pd.read_csv(os.path.join(DAT, "strike_damage_by_site.csv"))
    st = (d.groupby("state").base_usd_m.sum() / 1e3).sort_values(ascending=False)
    tot = d.base_usd_m.sum() / 1e3
    weap = [("Ballistic missiles", w["ballistic"]["base"], DARK), ("Unknown", w["unknown"]["base"] + w["cruise"]["base"], NEUTRAL),
            ("Drones", w["one_way_drone"]["base"], RED)]
    cols = {"Qatar": DARK, "UAE": BLUE, "Kuwait": "#6ea6e6", "Bahrain": NEUTRAL, "Saudi Arabia": NEUTRAL_LIGHT}
    fig, ax = plt.subplots(figsize=(10.0, 1.7))
    def row(y, parts, head, sub):
        x0 = 0
        for i, (lab, v, col) in enumerate(parts):
            ax.barh(y, v, left=x0, color=col, height=0.42, zorder=3, edgecolor="white", lw=1.2)
            dark = col in (DARK, RED, BLUE)
            ax.text(x0 + 0.06, y + 0.3, lab, ha="left", va="center", fontsize=9.4, fontweight="bold", color=INK)
            if v >= 1.2:
                ax.text(x0 + v / 2, y, f"${v:.1f}bn", ha="center", va="center", fontsize=11.5, fontweight="bold", color="white" if dark else INK)
            else:
                ax.text(x0 + v + 0.12, y, f"${v:.1f}bn", ha="left", va="center", fontsize=11.5, fontweight="bold", color=INK)
            x0 += v
        ax.text(-4.1, y + 0.08, head, ha="left", va="center", fontsize=11, fontweight="bold", color=INK)
        ax.text(-4.1, y - 0.2, sub, ha="left", va="center", fontsize=8, color=INK2)
    row(1.0, weap, "By weapon", f"${tot:.1f}bn · 61 priced strikes")
    row(0.0, [(k, float(v), cols[k]) for k, v in st.items()], "By state", "where the struck site is")
    ax.set_xlim(-4.1, tot + 1.6); ax.set_ylim(-0.36, 1.5)
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    for sp in ax.spines.values(): sp.set_visible(False)
    save(fig, os.path.join(FIG, "fig_damage"))
    NUM["fig_damage"] = dict(total_bn=round(float(tot), 2), by_weapon={a: round(float(b), 2) for a, b, _ in weap}, by_state={k: round(float(v), 2) for k, v in st.items()},
                             top_sites=d.head(6)[["state", "site", "base_usd_m"]].to_dict("records"),
                             _source="data/strike_damage_by_site.csv and strike_damage_by_weapon.json (author's cost model as of 2 Nov 2026; base case; inputs largely assumptions)")

# ---------------------------------------------------------------- 1. export losses by state
def exports_state():
    d = pd.read_csv(os.path.join(DAT, "export_losses_by_state.csv"))
    s = d[d.scope == "state"].set_index("state")
    order = ["Qatar", "Kuwait", "Bahrain", "Saudi", "UAE", "Oman"]
    names = {"Saudi": "Saudi Arabia"}
    loss = (s.loss_usd_base / 1e9).reindex(order); gain = (s.price_windfall_usd / 1e9).reindex(order)
    net = gain - loss; share = s.loss_pct_of_2025_baseline.reindex(order)
    tc = pd.read_csv(os.path.join(DAT, "trade_check_by_state.csv")).set_index("state")
    def trade(st):
        k = names.get(st, st)
        c, lo, hi = tc.loc[k, "trade_data_net_central_usd_bn"], tc.loc[k, "trade_data_net_low_usd_bn"], tc.loc[k, "trade_data_net_high_usd_bn"]
        if pd.isna(c): return "not published", MUTED
        if hi - lo > 10: return f"–${abs(lo):.0f} to –{abs(hi):.0f}bn", INK
        return ("+" if c > 0 else "–") + f"${int(abs(c) + 0.5)}bn", INK
    fig, ax = plt.subplots(figsize=(7.0, 3.75))
    ax.axvspan(124, 171, color="#f3f4f6", lw=0, zorder=0)
    sb = lambda v: ("+" if v > 0 else "–") + (f"${abs(v):.1f}bn" if abs(v) < 10 else f"${int(abs(v) + 0.5)}bn")
    y = np.arange(len(order))[::-1]
    ax.barh(y, -loss, color=RED, height=0.56, zorder=3)
    ax.barh(y, gain, color=GAIN, height=0.56, zorder=3)
    ax.axvline(0, color=INK, lw=1.0, zorder=4)
    for yi, st in zip(y, order):
        l, g, n = loss[st], gain[st], net[st]
        if l > 0.05:
            ax.text(-l - 1.5, yi, sb(-l), ha="right", va="center", fontsize=10.5, fontweight="bold", color=RED)
        else:
            ax.text(-1.2, yi, "no loss", ha="right", va="center", fontsize=9.5, color=MUTED)
        ax.text(g + 1.5, yi, sb(g), ha="left", va="center", fontsize=10.5, fontweight="bold", color=GAIN)
        ax.text(-112, yi + 0.07, names.get(st, st), ha="left", va="center", fontsize=11.5, fontweight="bold", color=INK)
        sub = f"lost {share[st]:.0f}% of normal value" if l > 0.05 else "exports outside the strait"
        ax.text(-112, yi - 0.27, sub, ha="left", va="center", fontsize=7.8, color=INK2)
        ax.text(110, yi, ("+" if n > 0 else "–") + f"${abs(n):.0f}bn", ha="right", va="center", fontsize=12.5, fontweight="bold", color=RED if n < 0 else GAIN)
        tt, tcol = trade(st)
        ax.text(168, yi, tt, ha="right", va="center", fontsize=10.5 if len(tt) > 8 else 12.5, fontweight="bold" if tcol == INK else "normal", color=tcol)
    top = len(order) - 0.42
    ax.text(-3, top, "Output lost, at 2025 prices", ha="right", va="bottom", fontsize=8.6, color=RED, fontweight="bold")
    ax.text(3, top, "Gained from higher prices", ha="left", va="bottom", fontsize=8.6, color=GAIN, fontweight="bold")
    ax.text(168, top, "Trade data", ha="right", va="bottom", fontsize=8.6, color=INK, fontweight="bold")
    ax.text(110, top, "Our net", ha="right", va="bottom", fontsize=8.6, color=INK, fontweight="bold")
    ax.set_xlim(-112, 170); ax.set_ylim(-0.55, len(order) - 0.05)
    ax.set_yticks([]); ax.set_xticks([]); ax.grid(False)
    for sp in ax.spines.values(): sp.set_visible(False)
    for yi in y[:-1]:
        ax.axhline(yi - 0.5, color=GRID, lw=0.7, zorder=1)
    save(fig, os.path.join(FIG, "fig_exports_state"))
    NUM["fig_exports_state"] = {st: dict(loss_bn=round(float(loss[st]), 2), price_gain_bn=round(float(gain[st]), 2), net_bn=round(float(net[st]), 2),
                                         loss_pct_of_2025_baseline=float(share[st])) for st in order}
    NUM["fig_exports_state"]["_source"] = "data/export_losses_by_state.csv (our calculation on EIA production estimates and 2025 prices)"


# ---------------------------------------------------------------- 2. by quarter and product
def exports_time():
    d = pd.read_csv(os.path.join(DAT, "export_losses_tidy.csv"))
    d = d[d.in_headline_base == "yes"].copy()
    def q(p):
        if "Q" in p: return p[-2:]
        m = int(p[5:7]); return "Q%d" % ((m - 1) // 3 + 1)
    d["q"] = d.period.map(q)
    d["grp"] = np.where(d.commodity == "LNG", "LNG", "Oil and liquids")
    t = d.groupby(["q", "grp"]).loss_usd_base.sum().unstack(fill_value=0) / 1e9
    t = t.reindex(["Q1", "Q2", "Q3"])
    fig, ax = plt.subplots(figsize=(4.7, 2.9))
    x = np.arange(3)
    oil, lng = t["Oil and liquids"].values, t["LNG"].values
    ax.bar(x, oil, color=DARK, width=0.58, zorder=3)
    ax.bar(x, lng, bottom=oil, color=RED, width=0.58, zorder=3)
    for xi, o, l in zip(x, oil, lng):
        ax.text(xi, o + l + 1.0, bn(o + l), ha="center", va="bottom", fontsize=12.5, fontweight="bold", color=INK)
        if o > 6: ax.text(xi, o / 2, f"oil\n{bn(o)}", ha="center", va="center", fontsize=8.6, color="white", linespacing=1.15)
        if l > 4: ax.text(xi, o + l / 2, f"gas {bn(l)}", ha="center", va="center", fontsize=8.6, color="white")
    ax.set_xticks(x); ax.set_xticklabels(["Jan–Mar\n(war from 28 Feb)", "Apr–Jun", "Jul–Sep"], fontsize=9.5, color=INK)
    ax.set_ylim(0, 58); ax.set_yticks([]); ax.grid(False)
    ax.spines["left"].set_visible(False); ax.tick_params(axis="x", length=0, pad=5)
    save(fig, os.path.join(FIG, "fig_exports_time"))
    NUM["fig_exports_time"] = {k: {g: round(float(t.loc[k, g]), 2) for g in t.columns} for k in t.index}
    NUM["fig_exports_time"]["_source"] = "data/export_losses_tidy.csv, rows in the headline; monthly LNG rows mapped to quarters"


# ---------------------------------------------------------------- 3. revenue -> value -> margin -> state take
def layers():
    d = pd.read_csv(os.path.join(DAT, "export_losses_by_state.csv"))
    r = d[d.scope == "total"].iloc[0]
    rows = [("Sales not made", r.loss_usd_base / 1e9, "lost volume × 2025 price", DARK),
            ("Value lost for good", r.economic_value_lost_usd_base / 1e9, "if half the oil is sold later", DARK),
            ("Profit lost", r.margin_lost_usd_base / 1e9, "after costs not incurred", DARK),
            ("State revenue lost", r.fiscal_take_lost_usd_base / 1e9, "excludes Bahrain", RED)]
    fig, ax = plt.subplots(figsize=(4.7, 2.9))
    y = np.arange(len(rows))[::-1] * 1.0
    for yi, (lab, v, sub, col) in zip(y, rows):
        ax.barh(yi - 0.14, v, color=col, height=0.36, zorder=3)
        ax.text(v + 1.6, yi - 0.14, bn(v), ha="left", va="center", fontsize=12.5, fontweight="bold", color=col if col == RED else INK)
        ax.text(0, yi + 0.2, lab, ha="left", va="center", fontsize=10, fontweight="bold", color=INK)
        ax.text(99, yi + 0.2, sub, ha="right", va="center", fontsize=7.8, color=INK2)
    ax.set_xlim(0, 122); ax.set_ylim(-0.5, len(rows) - 0.55)
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    for sp in ax.spines.values(): sp.set_visible(False)
    save(fig, os.path.join(FIG, "fig_layers"))
    NUM["fig_layers"] = {lab: round(float(v), 2) for lab, v, _, _ in rows}
    NUM["fig_layers"]["_source"] = "data/export_losses_by_state.csv total row; layers rest on assumed deferral shares (0.5 oil, 0.15 LNG), time value and avoidable cost"


# ---------------------------------------------------------------- 4. straits: traffic + war-risk premium
PREM = [  # date, low, high, label, source (all broker or trade-press quotes; each quote's source is in the last field)
    ("2026-03-10", 1.0, 3.0, "1–3%", "Reuters 6 Mar (3% on most tankers); Caixin 7 Mar (1%)"),
    ("2026-06-25", 2.0, 4.0, "2–4%", "FT-cited brokers via Insurance Business 25 Jun (about 2%); Marsh via S&P 23 Jun (3–4%)"),
    ("2026-07-10", 2.0, 6.0, "2–6%", "Marsh (Baker) via Insurance Business 10 Jul"),
    ("2026-07-22", 7.5, 10.0, "7.5–10%", "S&P Global 22 Jul, quoted by Al Jazeera 23 Jul"),
    ("2026-10-07", 6.0, 10.0, "6–10%", "FT-cited brokers, week of 5–9 Oct, via Insurance Business 14 Oct"),
]

def straits():
    d = pd.read_csv(os.path.join(DAT, "strait_traffic_daily.csv"), parse_dates=["date"])
    out = {}
    def pct(name, col):
        s = d[d.chokepoint == name].set_index("date")[col].astype(float)
        m = s.rolling(7).mean()
        base = m.shift(365, freq="D")
        return (100 * m / base).dropna()
    hz = pct("Strait of Hormuz", "total_transits"); tk = pct("Strait of Hormuz", "tanker")
    bm28 = None
    s = d[d.chokepoint == "Bab el-Mandeb Strait"].set_index("date")["total_transits"].astype(float)
    m = s.rolling(28).mean(); bm = (100 * m / m.shift(365, freq="D")).dropna()
    A, Z = pd.Timestamp("2026-01-01"), d.date.max()
    WAR = pd.Timestamp("2026-02-28")
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(6.9, 5.2), gridspec_kw=dict(height_ratios=[1.55, 1], hspace=0.38))
    ax.axhline(100, color=MUTED, lw=0.8, ls=(0, (2, 2)), zorder=1)
    ax.plot(bm[A:Z].index, bm[A:Z].values, color=NEUTRAL, lw=1.8, zorder=2)
    ax.plot(hz[A:Z].index, hz[A:Z].values, color=BLUE, lw=2.2, zorder=3)
    ax.axvline(WAR, color=INK, lw=1.0, zorder=4)
    ax.text(WAR - pd.Timedelta(days=3), 42, "war starts\n28 Feb", ha="right", va="center", fontsize=8.2, color=INK, linespacing=1.15)
    ax.text(Z, 104, "2025 level", ha="right", va="bottom", fontsize=7.8, color=MUTED)
    ax.text(pd.Timestamp("2026-04-12"), 126, "Bab el-Mandeb (Red Sea)", ha="left", va="center", fontsize=8.6, color=INK2)
    pk = hz["2026-06-10":"2026-07-20"]
    pkd, pkv = pk.idxmax(), pk.max()
    ax.annotate(f"brief reopening:\n{pkv:.0f}% on {pkd.day} {pkd.strftime('%b')}", (pkd, pkv), xytext=(pkd - pd.Timedelta(days=4), 66),
                fontsize=8.6, color=BLUE, ha="center", va="bottom", linespacing=1.15,
                arrowprops=dict(arrowstyle="-", color=BLUE, lw=0.7, shrinkA=1, shrinkB=3))
    ax.text(pd.Timestamp("2026-08-24"), 20, "Strait of Hormuz", ha="left", va="center", fontsize=9.6, color=BLUE, fontweight="bold")
    ax.set_ylim(0, 142); ax.set_yticks([0, 50, 100]); ax.set_yticklabels(["0%", "50%", "100%"])
    ax.set_xlim(A, Z + pd.Timedelta(days=4))
    ax.xaxis.set_major_locator(mdates.MonthLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax.grid(axis="x", visible=False); ax.tick_params(axis="x", length=0)
    ax.set_title("Ships seen by trackers each day, % of the same days in 2025", fontsize=9.3, fontweight="bold", loc="left", pad=6, color=INK)

    ax2.hlines(0.25, A, WAR, color=INK, lw=3, zorder=3)
    ax2.text(pd.Timestamp("2026-01-06"), 1.1, "0.25%, pre-war", ha="left", va="bottom", fontsize=8.4, color=INK)
    for dt, lo, hi, lab, src in PREM:
        x = pd.Timestamp(dt)
        ax2.vlines(x, lo, hi, color=RED, lw=5, zorder=3)
        ax2.text(x, hi + 0.55, lab, ha="center", va="bottom", fontsize=8.6, color=INK, fontweight="bold")
    ax2.axvline(WAR, color=INK, lw=1.0, zorder=2, ymax=0.2)
    ax2.set_ylim(0, 13.4); ax2.set_yticks([0, 5, 10]); ax2.set_yticklabels(["0%", "5%", "10%"])
    ax2.set_xlim(A, Z + pd.Timedelta(days=4))
    ax2.xaxis.set_major_locator(mdates.MonthLocator()); ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax2.grid(axis="x", visible=False); ax2.tick_params(axis="x", length=0)
    ax2.set_title("Extra war insurance for one passage, % of the ship's value (broker quotes)", fontsize=9.3, fontweight="bold", loc="left", pad=6, color=INK)
    save(fig, os.path.join(FIG, "fig_straits"))
    def avg(series_name, col, a, z):
        s = d[d.chokepoint == series_name].set_index("date")[col].astype(float)
        a, z = pd.Timestamp(a), pd.Timestamp(z)
        m26 = s[a:z].mean(); m25 = s[a - pd.Timedelta(days=365):z - pd.Timedelta(days=365)].mean()
        return dict(mean_2026=round(m26, 2), mean_2025=round(m25, 2), change_pct=round(100 * (m26 / m25 - 1), 1))
    z = str(Z.date())
    NUM["fig_straits"] = dict(latest_date=z, hormuz_all_8Mar_latest=avg("Strait of Hormuz", "total_transits", "2026-03-08", z),
                              hormuz_tanker_8Mar_latest=avg("Strait of Hormuz", "tanker", "2026-03-08", z),
                              hormuz_july=avg("Strait of Hormuz", "total_transits", "2026-07-01", "2026-07-31"),
                              hormuz_aug=avg("Strait of Hormuz", "total_transits", "2026-08-01", "2026-08-31"),
                              hormuz_oct=avg("Strait of Hormuz", "total_transits", "2026-10-01", "2026-10-31"),
                              babm_mar_jul=avg("Bab el-Mandeb Strait", "total_transits", "2026-03-01", "2026-07-31"),
                              babm_aug_latest=avg("Bab el-Mandeb Strait", "total_transits", "2026-08-01", z),
                              reopening_peak_7d=dict(date=str(pkd.date()), pct_of_2025=round(float(pkv), 1)),
                              premiums=[dict(date=a, low=b, high=c, source=e) for a, b, c, _, e in PREM],
                              _source="IMF PortWatch daily chokepoint transit calls (data/strait_traffic_daily.csv); 7-day mean for Hormuz, 28-day for Bab el-Mandeb")


# ---------------------------------------------------------------- 5. oil routes
def routes():
    rows = [("Through Hormuz, before the war", 21.6, "Oct–Dec 2025", DARK),
            ("Through Hormuz, Apr–Jun 2026", 4.9, "down 77%", RED),
            ("Through Hormuz, September 2026", 10.9, "includes cargoes moved ship to ship off Oman", RED),
            ("Saudi pipeline to the Red Sea", 5.0, "before a September attack", GAIN),
            ("UAE pipeline to Fujairah", 1.8, "April loadings", GAIN),
            ("Oil not produced at all", 10.9, "May peak; 2.5 by October", NEUTRAL)]
    fig, ax = plt.subplots(figsize=(4.7, 4.6))
    y = np.arange(len(rows))[::-1] * 1.0
    for yi, (lab, v, sub, col) in zip(y, rows):
        ax.barh(yi - 0.15, v, color=col, height=0.36, zorder=3)
        ax.text(v + 0.4, yi - 0.15, f"{v:.1f}" + ("+" if "pipeline to the Red" in lab else ""), ha="left", va="center", fontsize=13, fontweight="bold", color=INK)
        ax.text(0, yi + 0.2, lab, ha="left", va="center", fontsize=9.8, fontweight="bold", color=INK)
        ax.text(0, yi - 0.47, sub, ha="left", va="center", fontsize=8.2, color=INK2)
    ax.set_xlim(0, 26); ax.set_ylim(-0.62, len(rows) - 0.6)
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    for sp in ax.spines.values(): sp.set_visible(False)
    save(fig, os.path.join(FIG, "fig_routes"))
    NUM["fig_routes"] = dict(rows=[dict(label=a, mbd=b, note=c) for a, b, c, _ in rows],
                             _source="EIA Short-Term Energy Outlook Aug 2026 (21.6 and 4.9 mb/d), IEA Oil Market Report Oct 2026 (10.9 mb/d in September, a different method that counts ship-to-ship transfers), Oct 2026 (Saudi East-West pipeline, more than 5.0 mb/d), Nov 2026 (shut-ins 10.9 mb/d May, 2.5 mb/d Oct); Kpler (Fujairah loadings 1.82 mb/d, April). Different months and methods: bars are not additive.")


# ---------------------------------------------------------------- 6. outlook: what Iran has left, and the three paths
def outlook():
    fig, ax = plt.subplots(figsize=(4.6, 1.25))
    rows = [("Missiles", 70), ("Drones", 40)]   # US assessments, spring 2026, as reported by ISW (13 May) and CSIS (23 Jun)
    for i, (lab, left) in enumerate(rows):
        y = 1 - i
        ax.barh(y, 100, height=0.6, color=NEUTRAL_LIGHT, zorder=2)
        ax.barh(y, left, height=0.6, color=INK2, zorder=3)
        ax.text(left - 2, y, f"~{left}% left", va="center", ha="right", fontsize=11, fontweight="bold", color="white", zorder=5)
        ax.text(103, y, f"~{100-left}% used or destroyed", va="center", ha="left", fontsize=10, color=INK2, zorder=5)
    ax.set_yticks([1, 0]); ax.set_yticklabels([r[0] for r in rows], fontsize=11, fontweight="bold")
    ax.set_xlim(0, 178); ax.set_ylim(-0.55, 1.55); ax.set_xticks([]); ax.grid(False)
    for sp in ("left", "bottom"): ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", length=0, pad=8)
    save(fig, os.path.join(FIG, "fig_next_stock"))
    fig, ax = plt.subplots(figsize=(10.1, 0.48)); ax.axis("off"); ax.set_xlim(0, 100); ax.set_ylim(0, 1)
    x = 0
    for lab, w, col in [("Renewed war", 35, ORANGE), ("Harassment", 50, INK2), ("Calm", 15, NEUTRAL)]:
        ax.add_patch(plt.Rectangle((x, 0.15), w, 0.7, color=col, lw=0))
        ax.text(x + w / 2, 0.5, f"{lab}  ~{w}%", ha="center", va="center", fontsize=11.5, fontweight="bold", color="white" if col != NEUTRAL else INK)
        x += w
    save(fig, os.path.join(FIG, "fig_next_paths"))
    NUM["fig_outlook"] = dict(missiles_left_pct=70, drones_left_pct=40, odds=dict(renewed_war=35, harassment=50, calm=15),
                              _source="US assessments reported by ISW (13 May 2026) and CSIS (23 Jun 2026); odds are the author's judgment (27 Oct 2026)")


if __name__ == "__main__":
    setup()
    damage(); exports_state(); exports_time(); layers(); straits(); routes(); outlook()
    json.dump(NUM, open(os.path.join(REP, "data/pub_figs_numbers.json"), "w"), indent=1)
    print(json.dumps(NUM, indent=1)[:3000])
