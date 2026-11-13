"""
02_calibration_table.py
Per-corridor calibration table on the ADOT Corridor Reliability (progress report)
definitions. Formulas for every column are in README.md.

Inputs
  ../ADOT Corridor Reliability/output/<corridor>/   (corridor_reliability.py, corridor_moe.py)
      segments.csv, segment_capacity.csv, segment_day_loading.csv,
      segment_average_weekday_dv.csv, corridor_moe.csv
  ../inputs/<corridor>_<dir>/Readings.csv           (01_convert_inrix_xd.py; 5-min speed, mph)

Outputs
  ../results/calibration_table.csv   one row per corridor x direction x peak
  ../results/bottleneck_days.csv     one row per congested weekday at each bottleneck

Run:  python 02_calibration_table.py
"""
from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
REL = BASE.parent / "ADOT Corridor Reliability" / "output"
RES = BASE / "results"
M = 4.0                 # S3 shape parameter (progress report)
SMOOTH_BINS = 3         # centred 3-bin mean of 15-min speed
DT_H = 0.25             # 15-min bins
CORR = {
    "i10_phoenix": {"name": "I-10", "dirs": {"Eastbound": "EB", "Westbound": "WB"}},
    "i17_phoenix": {"name": "I-17", "dirs": {"Northbound": "NB", "Southbound": "SB"}},
}


def clock(h):
    if pd.isna(h):
        return ""
    mm = int(round(h * 60))
    return f"{mm // 60:02d}:{mm % 60:02d}"


def pct(s, p):
    s = pd.Series(s, dtype=float).dropna()
    return float(s.quantile(p)) if len(s) else np.nan


def r_(x, n):
    return round(x, n) if pd.notna(x) else np.nan


def speed_grid(corr_dir, seg_codes):
    """Weekday 15-min mean speed, smoothed with a centred 3-bin mean within each
    segment-day (same processing as corridor_reliability.loading)."""
    rd = pd.read_csv(BASE / "inputs" / corr_dir / "Readings.csv")
    rd = rd[rd["confidence_score"] >= 30]
    rd["ts"] = pd.to_datetime(rd["measurement_tstamp"])
    rd = rd[rd["ts"].dt.weekday < 5]
    rd["tb"] = rd["ts"].dt.floor("15min")
    s = rd.groupby(["tmc_code", "tb"], as_index=False)["speed"].mean()
    s["date"] = s["tb"].dt.date.astype(str)
    s = s.sort_values(["tmc_code", "tb"])
    s["smooth"] = s.groupby(["tmc_code", "date"])["speed"].transform(
        lambda x: x.rolling(SMOOTH_BINS, center=True, min_periods=1).mean())
    g = s.pivot_table(index="tb", columns="tmc_code", values="smooth")
    return g.reindex(columns=[int(c) for c in seg_codes])


def slope(t_h, x):
    t_h, x = np.asarray(t_h, float), np.asarray(x, float)
    if len(t_h) < 2 or np.ptp(t_h) == 0:
        return np.nan
    return float(np.polyfit(t_h, x, 1)[0])


def queue_geometry(grid, b, vc, x0, x1, date, t0_h, t3_h):
    """Queue through bottleneck column b at each 15-min bin overlapping [t0, t3].
    Returns L_max, L_avg, head, tail_min, w_f, w_r (see README section 1.6)."""
    day0 = pd.Timestamp(date)
    lo_ts = day0 + pd.Timedelta(hours=t0_h) - pd.Timedelta(minutes=15)
    hi_ts = day0 + pd.Timedelta(hours=t3_h)
    sub = grid[(grid.index > lo_ts) & (grid.index < hi_ts)]
    rows = []
    for ts, v in zip(sub.index, sub.to_numpy()):
        below = v < vc
        if not below[b]:
            continue
        u = d = b
        while u > 0 and below[u - 1]:
            u -= 1
        while d < len(v) - 1 and below[d + 1]:
            d += 1
        rows.append((ts, x0[u], x1[d]))
    if not rows:
        return {}
    qd = pd.DataFrame(rows, columns=["ts", "tail", "head"])
    qd["L"] = qd["head"] - qd["tail"]
    th = (qd["ts"] - qd["ts"].iloc[0]).dt.total_seconds().to_numpy() / 3600
    tl = qd["tail"].to_numpy()
    k = int(qd["L"].to_numpy().argmax())
    # formation: onset -> first time the tail reaches its most upstream point;
    # recovery: last time at that point -> end. Not identifiable when the tail
    # sits at the upstream study limit (the true tail is outside the corridor).
    at_min = np.flatnonzero(np.isclose(tl, tl.min()))
    kf, kr = int(at_min[0]), int(at_min[-1])
    censored = tl.min() <= x0[0] + 1e-9
    return dict(L_max=qd["L"].max(), L_avg=qd["L"].mean(), head=qd["head"].median(),
                tail_min=tl.min(), t_Lmax=qd["ts"].iloc[k],
                w_f=np.nan if censored else slope(th[:kf + 1], tl[:kf + 1]),
                w_r=np.nan if censored else slope(th[kr:], tl[kr:]))


rows, day_rows = [], []
for cid, c in CORR.items():
    seg = pd.read_csv(REL / cid / "segments.csv")
    moe = pd.read_csv(REL / cid / "corridor_moe.csv")
    avg = pd.read_csv(REL / cid / "segment_average_weekday_dv.csv")
    day = pd.read_csv(REL / cid / "segment_day_loading.csv")
    cap = pd.read_csv(REL / cid / "segment_capacity.csv")
    vf_all = day.groupby("tmc_code")["vf_mph"].first()
    for dname, dcode in c["dirs"].items():
        sd = seg[seg["direction"] == dname].sort_values("road_order").reset_index(drop=True)
        codes = sd["tmc_code"].tolist()
        x0 = sd["dist_start_mi"].to_numpy()
        x1 = sd["dist_end_mi"].to_numpy()
        vc_vec = vf_all.reindex(codes).to_numpy() * 2.0 ** (-2.0 / M)
        x_end = float(x1[-1])
        grid = speed_grid(f"{c['name']}_{dcode}", codes)
        for _, r in moe[moe["direction"] == dname].iterrows():
            per = r["period"]
            a = avg[(avg["direction"] == dname) & (avg["period"] == per)]
            b = a.loc[a["P_h"].idxmax()]                     # same rule as corridor_moe.py
            tmc = int(b["tmc_code"])
            bi = codes.index(tmc)
            cp = cap[cap["tmc_code"] == tmc].iloc[0]
            lanes, C = int(cp["lanes"]), float(cp["capacity_vphpl"])
            vf = float(vf_all[tmc])
            vc = vf * 2.0 ** (-2.0 / M)
            dd = day[(day["tmc_code"] == tmc) & (day["period"] == per)]
            cong = dd[dd["P_h"] > 0]
            recs = []
            for _, e in cong.iterrows():
                geo = queue_geometry(grid, bi, vc_vec, x0, x1, e["date"],
                                     e["episode_start"], e["episode_end"])
                g = grid[tmc]
                g = g[(g.index.date.astype(str) == e["date"])]
                h = g.index.hour + g.index.minute / 60
                w = g[(h >= e["episode_start"] - 0.25) & (h <= e["episode_end"])]
                vt2 = float(w.min()) if len(w) else np.nan
                rec = dict(date=e["date"], P_h=e["P_h"], t0=e["episode_start"], t3=e["episode_end"],
                           v_t2=vt2, DC_h=e["DC_h"], D=e["D_veh"], V=e["V_veh"], **geo)
                recs.append(rec)
                day_rows.append(dict(
                    corridor=c["name"], direction=dcode, period=per, date=e["date"],
                    bottleneck_segment=tmc, episode_start=clock(rec["t0"]), episode_end=clock(rec["t3"]),
                    P_h=r_(rec["P_h"], 3), v_t2_mph=r_(vt2, 1),
                    L_max_mi=r_(geo.get("L_max"), 2), L_avg_mi=r_(geo.get("L_avg"), 2),
                    queue_head_mi=r_(geo.get("head"), 2),
                    w_f_mph=r_(geo.get("w_f"), 2), w_r_mph=r_(geo.get("w_r"), 2),
                    DC_h=r_(rec["DC_h"], 3), mean_qC=r_(rec["DC_h"] / rec["P_h"], 3),
                    D_veh_per_lane=r_(rec["D"], 0), V_veh_per_lane=r_(rec["V"], 0)))
            E = pd.DataFrame(recs)
            n_wd = int(r["weekdays"])
            loc = next((x for x in a.sort_values("dist_start_mi", ascending=False)
                        .loc[lambda f: f["dist_start_mi"] <= b["dist_start_mi"], "intersection"]
                        if pd.notna(x) and str(x).strip()), "")
            flags = []
            if bi == 0 or bi == len(codes) - 1 or (pd.notna(pct(E.get("head"), .5))
                                                    and x_end - pct(E.get("head"), .5) < 0.5):
                flags.append("bottleneck_at_study_limit")
            if pd.notna(pct(E.get("tail_min"), .5)) and pct(E.get("tail_min"), .5) < 0.05:
                flags.append("queue_reaches_upstream_limit")
            rows.append(dict(
                corridor=c["name"], direction=dcode, period=per, weekdays=n_wd,
                # ---- bottleneck ----
                bottleneck_section=r["bottleneck_section"], bottleneck_location=loc,
                bottleneck_segment=tmc, bottleneck_mile=r_(b["dist_start_mi"], 2),
                lanes=lanes, v_f_mph=r_(vf, 1), v_c_mph=r_(vc, 1),
                # ---- 1. speed-based ----
                event_start_avg=clock(r["bottleneck_start"]), event_end_avg=clock(r["bottleneck_end"]),
                P_h_avg=r_(r["bottleneck_P_h"], 2),
                congested_days=len(E), share_days_congested=r_(len(E) / n_wd, 2),
                event_start_median=clock(pct(E["t0"], .5)), event_end_median=clock(pct(E["t3"], .5)),
                P_h_median=r_(pct(E["P_h"], .5), 2), P_h_p85=r_(pct(E["P_h"], .85), 2),
                P_h_p95=r_(pct(E["P_h"], .95), 2),
                v_t2_mph_median=r_(pct(E["v_t2"], .5), 1), v_t2_mph_p15=r_(pct(E["v_t2"], .15), 1),
                speed_drop_vt2_over_vf=r_(pct(E["v_t2"], .5) / vf, 2),
                L_max_mi_median=r_(pct(E.get("L_max"), .5), 2), L_max_mi_p85=r_(pct(E.get("L_max"), .85), 2),
                L_avg_mi_median=r_(pct(E.get("L_avg"), .5), 2),
                queue_head_mi_median=r_(pct(E.get("head"), .5), 2),
                w_f_mph_median=r_(pct(E.get("w_f"), .5), 1), w_r_mph_median=r_(pct(E.get("w_r"), .5), 1),
                QE_mi_mean=r_(r["QE_mi_mean"], 1), QE_mi_p95=r_(r["QE_mi_p95"], 1),
                P_length_weighted_h=r_(r["P_length_weighted_h"], 2),
                # ---- 2. flow from speed (S3), estimated ----
                C_vphpl=int(C), capacity_source=cp["capacity_source"],
                DC_h_avg=r_(r["bottleneck_DC_h"], 2),
                DC_h_median=r_(pct(E["DC_h"], .5), 2), DC_h_p85=r_(pct(E["DC_h"], .85), 2),
                mean_qC_in_event=r_(pct(E["DC_h"] / E["P_h"], .5), 3),
                mean_event_flow_vphpl=r_(pct(E["DC_h"] / E["P_h"], .5) * C, 0),
                D_veh_per_lane_avg=r_(b["D_veh"], 0), V_veh_per_lane_avg=r_(b["V_veh"], 0),
                D_veh_all_lanes_avg=r_(b["D_veh"] * lanes, 0),
                D_over_V=r_(b["D_veh"] / b["V_veh"], 2),
                VMT=r_(r["VMT"], 0), VHT=r_(r["VHT"], 0), VHD=r_(r["VHD"], 0),
                avg_speed_mph=r_(r["avg_speed_mph"], 1), TTI_VMT=r_(r["TTI_VMT"], 2),
                flags=";".join(flags),
            ))

RES.mkdir(exist_ok=True)
T = pd.DataFrame(rows)
order = {"EB": 0, "WB": 1, "NB": 2, "SB": 3}
T = T.sort_values(["corridor", "period", "direction"],
                  key=lambda s: s.map(order) if s.name == "direction" else s)
T.to_csv(RES / "calibration_table.csv", index=False)
pd.DataFrame(day_rows).to_csv(RES / "bottleneck_days.csv", index=False)
with pd.option_context("display.width", 250, "display.max_columns", 80):
    print(T.T.to_string())
