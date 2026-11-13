"""
02_calibration_table.py
Per-corridor calibration table on the ADOT Corridor Reliability (progress report)
definitions. Reads the outputs of corridor_reliability.py and corridor_moe.py
(github.com/jacky850/adot-corridor-reliability) and the bottleneck speed series.

Definitions (same as the progress report, slides 3, 6, 12, 17):
  - weekdays Jun 1 - Sep 1, 2025 (64; July 4 and Labor Day removed)
  - periods: AM 06-09, PM 14-18; the episode may run past the period
  - free flow v_f: weekday night (21-05) 85th-percentile speed, per segment
  - capacity speed v_c = v_f * 2^(-2/m), m = 4  (= 0.707 v_f)
  - speed: 15-min mean, centred 3-bin smoothing
  - episode: longest run below v_c whose slowest point is in the period, >= 0.5 h
  - P: episode duration (h)
  - q/C from speed through the S3 relation; C cancels, so D/C needs no capacity
  - D/C (h) = sum (q/C) dt over the episode;  D = D/C * C;  V = sum q dt (veh/lane)
  - C: AZTDM GMNS per-lane capacity (1,688 / 1,851 / 1,935 by area type)
  - bottleneck: segment with the longest episode on the average weekday
  - queue extent QE: longest continuous length below v_c at any 15 min,
    from 2 h before to 2 h after the period

Speed-based (directly observed): bottleneck, episode window, P, v_t2, QE.
Estimated (S3 flow, model-based, no count validation): D/C, D, V.

Run:  python 02_calibration_table.py
Out:  ../results/calibration_table.csv, ../results/bottleneck_days.csv
"""
from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
J = BASE.parent
REL = J / "ADOT Corridor Reliability" / "output"
RES = BASE / "results"
M = 4.0
SMOOTH_BINS = 3

CORR = {
    "i10_phoenix": {"name": "I-10", "dirs": {"Eastbound": "EB", "Westbound": "WB"}},
    "i17_phoenix": {"name": "I-17", "dirs": {"Northbound": "NB", "Southbound": "SB"}},
}


def clock(h):
    if pd.isna(h):
        return ""
    mm = int(round(h * 60))
    return f"{mm // 60:02d}:{mm % 60:02d}"


def q(s, p):
    s = pd.Series(s).dropna()
    return float(s.quantile(p)) if len(s) else np.nan


def load_speed(corr_dir, tmc):
    """15-min smoothed weekday speed of one segment (converted INRIX inputs, mph)."""
    rd = pd.read_csv(BASE / "inputs" / corr_dir / "Readings.csv")
    rd = rd[(rd["tmc_code"] == int(tmc)) & (rd["confidence_score"] >= 30)]
    rd["ts"] = pd.to_datetime(rd["measurement_tstamp"])
    rd = rd[rd["ts"].dt.weekday < 5]
    rd["tb"] = rd["ts"].dt.floor("15min")
    s = rd.groupby("tb")["speed"].mean().reset_index()
    s["date"] = s["tb"].dt.date.astype(str)
    s["h"] = s["tb"].dt.hour + s["tb"].dt.minute / 60
    s["smooth"] = s.groupby("date")["speed"].transform(
        lambda x: x.rolling(SMOOTH_BINS, center=True, min_periods=1).mean())
    return s


rows, day_rows = [], []
for cid, c in CORR.items():
    moe = pd.read_csv(REL / cid / "corridor_moe.csv")
    avg = pd.read_csv(REL / cid / "segment_average_weekday_dv.csv")
    day = pd.read_csv(REL / cid / "segment_day_loading.csv")
    cap = pd.read_csv(REL / cid / "segment_capacity.csv")
    for _, r in moe.iterrows():
        dname, per = r["direction"], r["period"]
        dcode = c["dirs"][dname]
        a = avg[(avg["direction"] == dname) & (avg["period"] == per)]
        b = a.loc[a["P_h"].idxmax()]                       # same rule as corridor_moe.py
        tmc = str(b["tmc_code"])
        assert abs(b["dist_start_mi"] - r["bottleneck_mile"]) < 1e-6, (cid, dname, per)
        cp = cap[cap["tmc_code"].astype(str) == tmc].iloc[0]
        dd = day[(day["tmc_code"].astype(str) == tmc) & (day["period"] == per)].copy()
        cong = dd[dd["P_h"] > 0]
        vf = float(dd["vf_mph"].iloc[0])
        vc = vf * 2.0 ** (-2.0 / M)

        # lowest speed v_t2 in each day's episode at the bottleneck
        sp = load_speed(f"{c['name']}_{dcode}", tmc)
        vt2 = []
        for _, e in cong.iterrows():
            g = sp[(sp["date"] == e["date"]) & (sp["h"] >= e["episode_start"] - 0.25)
                   & (sp["h"] <= e["episode_end"])]
            v = float(g["smooth"].min()) if len(g) else np.nan
            vt2.append(v)
            day_rows.append(dict(corridor=c["name"], direction=dcode, period=per, date=e["date"],
                                 bottleneck_segment=tmc, P_h=round(e["P_h"], 3),
                                 episode_start=clock(e["episode_start"]), episode_end=clock(e["episode_end"]),
                                 v_t2_mph=round(v, 1), DC_h=round(e["DC_h"], 3),
                                 D_veh_per_lane=round(e["D_veh"], 0), V_veh_per_lane=round(e["V_veh"], 0),
                                 daily_TTI=round(e["daily_TTI"], 3)))
        cong = cong.assign(v_t2=vt2)
        n_wd = int(r["weekdays"])
        rows.append(dict(
            corridor=c["name"], direction=dcode, period=per, weekdays=n_wd,
            # --- bottleneck (speed-based) ---
            bottleneck_section=r["bottleneck_section"],
            # nearest named segment at or upstream of the bottleneck
            bottleneck_location=next(
                (x for x in a.sort_values("dist_start_mi", ascending=False)
                 .loc[lambda f: f["dist_start_mi"] <= b["dist_start_mi"], "intersection"]
                 if pd.notna(x) and str(x).strip()), ""),
            bottleneck_segment=tmc, bottleneck_mile=round(r["bottleneck_mile"], 2),
            lanes=int(cp["lanes"]), v_f_mph=round(vf, 1), v_c_mph=round(vc, 1),
            # average weekday (as in progress report slide 17)
            avg_episode_start=clock(r["bottleneck_start"]), avg_episode_end=clock(r["bottleneck_end"]),
            avg_P_h=round(r["bottleneck_P_h"], 2),
            P_length_weighted_h=round(r["P_length_weighted_h"], 2),
            QE_mi_mean=round(r["QE_mi_mean"], 1), QE_mi_p95=round(r["QE_mi_p95"], 1),
            # day-level distribution at the bottleneck
            congested_days=len(cong), share_days_congested=round(len(cong) / n_wd, 2),
            P_h_median=round(q(cong["P_h"], .5), 2), P_h_p15=round(q(cong["P_h"], .15), 2),
            P_h_p85=round(q(cong["P_h"], .85), 2), P_h_p95=round(q(cong["P_h"], .95), 2),
            episode_start_median=clock(q(cong["episode_start"], .5)),
            episode_end_median=clock(q(cong["episode_end"], .5)),
            v_t2_mph_median=round(q(cong["v_t2"], .5), 1), v_t2_mph_p15=round(q(cong["v_t2"], .15), 1),
            # --- estimated (S3 flow; D/C independent of C) ---
            avg_DC_h=round(r["bottleneck_DC_h"], 2),
            DC_h_median=round(q(cong["DC_h"], .5), 2), DC_h_p85=round(q(cong["DC_h"], .85), 2),
            C_vphpl=int(cp["capacity_vphpl"]), capacity_source=cp["capacity_source"],
            avg_D_veh_per_lane=round(b["D_veh"], 0), avg_V_veh_per_lane=round(b["V_veh"], 0),
            D_over_V=round(b["D_veh"] / b["V_veh"], 2),
            # --- corridor MOE (estimated, S3 flow x GMNS lanes/capacity) ---
            VMT=round(r["VMT"]), VHT=round(r["VHT"]), VHD=round(r["VHD"]),
            avg_speed_mph=round(r["avg_speed_mph"], 1), TTI_VMT=round(r["TTI_VMT"], 2),
        ))

RES.mkdir(exist_ok=True)
T = pd.DataFrame(rows)
order = {"EB": 0, "WB": 1, "NB": 2, "SB": 3}
T = T.sort_values(["corridor", "period", "direction"], key=lambda s: s.map(order) if s.name == "direction" else s)
T.to_csv(RES / "calibration_table.csv", index=False)
pd.DataFrame(day_rows).to_csv(RES / "bottleneck_days.csv", index=False)
with pd.option_context("display.width", 250, "display.max_columns", 60):
    print(T.T.to_string())
