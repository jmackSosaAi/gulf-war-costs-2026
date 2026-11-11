"""Pull IMF PortWatch daily chokepoint transit calls and rebuild strait_traffic_daily.csv and strait_traffic_summary.json.
Public ArcGIS feature service, no key. Run: python3 -I refresh_strait_traffic.py [--no-pull]
Baseline rule: "same day of 2025" = the same calendar date one year earlier (date minus 365 days).
Windows are inclusive. Counts are AIS-derived ship transit calls (UTC days); capacity = estimated deadweight (metric tons)."""
import urllib.request, urllib.parse, json, hashlib, sys, time, os, datetime
import pandas as pd, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, "portwatch_raw")
SVC = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0"
PORTS = {"chokepoint6": "Strait of Hormuz", "chokepoint4": "Bab el-Mandeb Strait", "chokepoint1": "Suez Canal", "chokepoint7": "Cape of Good Hope"}
TYPES = ["tanker", "container", "dry_bulk", "general_cargo", "roro"]
P10_HORMUZ_WEEKLY = 69.18571428571428   # weekly 10th percentile of 2024-25 Hormuz transits
OLD_END = "2026-10-25"                   # end date of the earlier (28 Oct) pull and the brief's -93.5% window
os.makedirs(RAW, exist_ok=True)

def pull():
    meta = json.loads(urllib.request.urlopen(urllib.request.Request(SVC + "?f=json", headers={"User-Agent": "Mozilla/5.0 research"}), timeout=60).read())
    edit = datetime.datetime.fromtimestamp(meta["editingInfo"]["dataLastEditDate"] / 1000, datetime.timezone.utc).isoformat()
    man = {"service": SVC, "dataLastEditDate_utc": edit, "pulled_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "files": {}}
    for pid in PORTS:
        rows, off = [], 0
        while True:
            q = {"where": f"portid='{pid}' AND date>=DATE '2024-01-01'", "outFields": "*", "returnGeometry": "false", "orderByFields": "date", "resultOffset": off, "resultRecordCount": 1000, "f": "json"}
            req = urllib.request.Request(SVC + "/query?" + urllib.parse.urlencode(q), headers={"User-Agent": "Mozilla/5.0 research"})
            d = json.loads(urllib.request.urlopen(req, timeout=60).read())
            if "error" in d:
                time.sleep(65); continue          # rate limit: 6000 request units per minute
            fs = [f["attributes"] for f in d["features"]]; rows += fs; off += len(fs)
            if not d.get("exceededTransferLimit") or not fs: break
        b = json.dumps(rows).encode(); open(os.path.join(RAW, pid + ".json"), "wb").write(b)
        man["files"][pid] = dict(rows=len(rows), first=rows[0]["date"], last=rows[-1]["date"], sha256=hashlib.sha256(b).hexdigest())
    json.dump(man, open(os.path.join(RAW, "MANIFEST.json"), "w"), indent=1)

def load():
    out = {}
    for pid, name in PORTS.items():
        d = pd.DataFrame(json.load(open(os.path.join(RAW, pid + ".json")))); d["date"] = pd.to_datetime(d["date"]); d = d.set_index("date").sort_index()
        assert d.index.is_unique and len(d) == (d.index[-1] - d.index[0]).days + 1, "gap in days"
        out[name] = d
    return out

def daily_csv(raw):
    parts = []
    for name, d in raw.items():
        x = d[["n_total"] + ["n_" + t for t in TYPES] + ["n_cargo", "capacity"]].copy()
        x["tot7"] = x.n_total.rolling(7).mean(); prev = x.shift(365, freq="D")
        for src, dst in [("n_total", "total_same_day_2025"), ("n_tanker", "tanker_same_day_2025"), ("capacity", "capacity_dwt_same_day_2025"), ("tot7", "total_7d_mean_same_days_2025")]:
            x[dst] = prev[src].reindex(x.index)
        x["pct_of_2025_7d"] = (100 * x.tot7 / x.total_7d_mean_same_days_2025).round(1)
        x = x["2025-01-01":].copy()
        c25 = ["total_same_day_2025", "tanker_same_day_2025", "capacity_dwt_same_day_2025", "total_7d_mean_same_days_2025", "pct_of_2025_7d"]
        x.loc[x.index < "2026-01-01", c25] = np.nan     # 2025 rows have no 2025 comparator
        x["tot7"] = x.tot7.round(2); x["total_7d_mean_same_days_2025"] = x.total_7d_mean_same_days_2025.round(2)
        x = x.rename(columns={"n_total": "total_transits", "n_tanker": "tanker", "n_container": "container", "n_dry_bulk": "dry_bulk", "n_general_cargo": "general_cargo", "n_roro": "roro", "n_cargo": "cargo_all_nontanker", "capacity": "capacity_dwt", "tot7": "total_7d_mean"})
        x.insert(0, "chokepoint", name); parts.append(x)
    o = pd.concat(parts).reset_index(); o["date"] = o.date.dt.strftime("%Y-%m-%d")
    o = o[["date", "chokepoint", "total_transits", "tanker", "container", "dry_bulk", "general_cargo", "roro", "cargo_all_nontanker", "capacity_dwt", "total_7d_mean", "total_same_day_2025", "tanker_same_day_2025", "capacity_dwt_same_day_2025", "total_7d_mean_same_days_2025", "pct_of_2025_7d"]]
    o.to_csv(os.path.join(HERE, "strait_traffic_daily.csv"), index=False)

def win(s, a, z):
    a, z = pd.Timestamp(a), pd.Timestamp(z); o = pd.Timedelta(days=365)
    m26, m25 = s[a:z].mean(), s[a - o:z - o].mean()
    return dict(window_2026=f"{a.date()}..{z.date()}", window_2025=f"{(a - o).date()}..{(z - o).date()}", days=int((z - a).days + 1),
                mean_2026=round(float(m26), 2), mean_2025=round(float(m25), 2), change_pct=round(float(100 * (m26 / m25 - 1)), 1), pct_of_2025=round(float(100 * m26 / m25), 1))

def summary(raw):
    H = raw["Strait of Hormuz"]; B = raw["Bab el-Mandeb Strait"]; last = H.index.max(); L = str(last.date())
    S = {"latest_date_in_data": L, "convention": "same days of 2025 = same calendar dates one year earlier; change_pct = 2026 mean / 2025 mean - 1; counts are AIS ship transit calls per UTC day", "source": SVC}
    for key, d in [("hormuz", H), ("bab_el_mandeb", B), ("suez", raw["Suez Canal"]), ("cape_of_good_hope", raw["Cape of Good Hope"])]:
        S[key] = dict(
            pre_war_1Jan_27Feb=win(d.n_total, "2026-01-01", "2026-02-27"),
            war_8Mar_to_25Oct_same_window_as_brief=win(d.n_total, "2026-03-08", OLD_END),
            war_8Mar_to_latest=win(d.n_total, "2026-03-08", L),
            tanker_8Mar_to_25Oct=win(d.n_tanker, "2026-03-08", OLD_END),
            tanker_8Mar_to_latest=win(d.n_tanker, "2026-03-08", L),
            capacity_dwt_8Mar_to_latest=win(d.capacity, "2026-03-08", L),
            by_type_8Mar_to_latest={t: win(d["n_" + t], "2026-03-08", L) for t in TYPES})
    S["hormuz"]["start_date_sensitivity_change_pct_to_25Oct"] = {a: win(H.n_total, a, OLD_END)["change_pct"] for a in ["2026-02-28", "2026-03-01", "2026-03-02", "2026-03-08", "2026-03-09"]}
    S["hormuz"]["war_28Feb_to_latest"] = win(H.n_total, "2026-02-28", L)
    S["hormuz"]["calendar_week_2_8_Mar"] = win(H.n_total, "2026-03-02", "2026-03-08")
    r7 = H.n_total.rolling(7).mean()["2026-03-08":]; w = r7.idxmin(); b25 = H.n_total[w - pd.Timedelta(days=371):w - pd.Timedelta(days=365)].mean()
    S["hormuz"]["lowest_7_day_window"] = dict(window=f"{(w - pd.Timedelta(days=6)).date()}..{w.date()}", mean_2026=round(float(r7[w]), 2), mean_same_days_2025=round(float(b25), 2), change_pct=round(float(100 * (r7[w] / b25 - 1)), 1))
    m28 = H.n_total.rolling(28).mean(); p28 = (100 * m28 / m28.shift(365, freq="D")).dropna()["2026-03-01":]
    S["hormuz"]["pct_of_2025_28d_mean"] = dict(min=round(float(p28.min()), 1), min_date=str(p28.idxmin().date()), latest=round(float(p28.iloc[-1]), 1), latest_date=str(p28.index[-1].date()))
    wk = H.n_total.resample("W-SUN").mean()["2026-03-01":]; wk = wk[wk.index <= last]
    S["hormuz"]["weeks_below_2024_25_weekly_p10"] = dict(p10_per_day=round(P10_HORMUZ_WEEKLY, 1), count_complete_weeks_since_1Mar=int((wk[wk.index <= last] < P10_HORMUZ_WEEKLY).sum()), note="weeks ending Sunday; last week counted only if it ends on or before the latest date")
    S["hormuz"]["days_with_zero_transits_since_1Mar"] = int((H.n_total["2026-03-01":] == 0).sum())
    S["hormuz"]["share_of_days_5_or_fewer_since_8Mar"] = round(float((H.n_total["2026-03-08":] <= 5).mean()), 3)
    mon = {}
    for key, d in [("hormuz", H), ("bab_el_mandeb", B)]:
        mon[key] = {}
        for p in pd.period_range("2026-01", str(last.to_period("M")), freq="M"):
            a = max(p.start_time, pd.Timestamp("2026-01-01")); z = min(p.end_time.normalize(), last); x = win(d.n_total, a, z); t = win(d.n_tanker, a, z)
            mon[key][str(p)] = dict(days=x["days"], mean_2026=x["mean_2026"], mean_same_days_2025=x["mean_2025"], pct_of_2025=x["pct_of_2025"], tanker_mean_2026=t["mean_2026"], tanker_pct_of_2025=t["pct_of_2025"])
    S["monthly"] = mon
    wk = []
    for e in pd.date_range("2026-06-07", "2026-08-30", freq="W-SUN"):
        a = e - pd.Timedelta(days=6); x = win(H.n_total, a, e); t = win(H.n_tanker, a, e); wk.append(dict(week=f"{a.date()}..{e.date()}", mean_2026=x["mean_2026"], pct_of_2025=x["pct_of_2025"], tanker_pct_of_2025=t["pct_of_2025"]))
    S["hormuz"]["partial_reopening_weekly_jun_aug"] = wk
    ph = win(H.n_total, "2026-06-20", "2026-07-08"); S["hormuz"]["partial_reopening_20Jun_8Jul"] = ph
    S["hormuz"]["partial_reopening_peak_day"] = dict(date=str(H.n_total["2026-06-01":"2026-08-01"].idxmax().date()), transits=int(H.n_total["2026-06-01":"2026-08-01"].max()))
    S["bab_el_mandeb"]["mar_jul_vs_2025"] = win(B.n_total, "2026-03-01", "2026-07-31"); S["bab_el_mandeb"]["aug_to_latest_vs_2025"] = win(B.n_total, "2026-08-01", L)
    json.dump(S, open(os.path.join(HERE, "strait_traffic_summary.json"), "w"), indent=1)
    return S

if __name__ == "__main__":
    if "--no-pull" not in sys.argv: pull()
    raw = load(); daily_csv(raw); S = summary(raw); print(json.dumps({k: S[k] for k in ["latest_date_in_data"]}))
