"""
export_data.py — data for the CBI dashboard (dashboard/data.json).

Public build (default) — aggregates only, no single-day INRIX speeds:
  speed profiles over the 64 weekdays, per segment and 15-min bin, then smoothed
  with a centred 3-bin mean (same processing as corridor_reliability.loading):
    avg  average weekday (mean speed)
    p50  median weekday  (50th-percentile speed of each cell)
    p15  bad day         (15th-percentile speed of each cell)
    p05  worst days      (5th-percentile speed of each cell)
  daily P and L_max at each bottleneck as quantiles only (box plots)

Full build (local only, never publish): CBI_FULL=1 python dashboard/export_data.py
  adds the 64 single-day speed grids and per-day bottleneck records.

Speeds are stored as int mph x 10 (-1 = missing), 03:00-22:00, [segment][bin].
"""
import json
import os
from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
REL = BASE.parent / "ADOT Corridor Reliability" / "output"
OUT = Path(__file__).resolve().parent / "data.json"
FULL = os.environ.get("CBI_FULL") == "1"
M = 4.0
T0, T1 = 3 * 60, 22 * 60
CORR = {
    "i10_phoenix": ("I-10", {"Eastbound": "EB", "Westbound": "WB"}),
    "i17_phoenix": ("I-17", {"Northbound": "NB", "Southbound": "SB"}),
}
XD_META = {
    "i10_phoenix": "Only-I-10-0601-to-0901_2025-06-01_to_2025-09-02_5_min_part_1",
    "i17_phoenix": "Only-I-17-0601-to-0901_2025-06-01_to_2025-09-02_5_min_part_1",
}
PROFILES = [("avg", "Average weekday (mean of 64)", "mean"), ("p50", "Median weekday (p50 speed)", 0.50),
            ("p15", "Bad day (p15 speed)", 0.15), ("p05", "Worst days (p5 speed)", 0.05)]
sm = lambda x: x.rolling(3, center=True, min_periods=1).mean()


def grids(corr_dir, codes):
    rd = pd.read_csv(BASE / "inputs" / corr_dir / "Readings.csv")
    rd = rd[rd["confidence_score"] >= 30]
    rd["ts"] = pd.to_datetime(rd["measurement_tstamp"])
    rd = rd[rd["ts"].dt.weekday < 5]
    rd["tb"] = rd["ts"].dt.floor("15min")
    s = rd.groupby(["tmc_code", "tb"], as_index=False)["speed"].mean()
    s["date"] = s["tb"].dt.date.astype(str)
    s["minute"] = s["tb"].dt.hour * 60 + s["tb"].dt.minute
    s = s.sort_values(["tmc_code", "tb"])
    mins = list(range(T0, T1, 15))

    def pack(df, col="smooth"):
        g = df.pivot_table(index="minute", columns="tmc_code", values=col).reindex(index=mins, columns=codes)
        a = np.where(np.isnan(g.to_numpy()), -1, np.round(g.to_numpy() * 10)).astype(int)
        return a.T.tolist()

    out = {}
    gb = s.groupby(["tmc_code", "minute"])["speed"]
    for key, _, how in PROFILES:
        prof = (gb.mean() if how == "mean" else gb.quantile(how)).rename("speed").reset_index()
        prof = prof.sort_values(["tmc_code", "minute"])
        prof["smooth"] = prof.groupby("tmc_code")["speed"].transform(sm)
        out[key] = pack(prof)
    if FULL:
        s["smooth"] = s.groupby(["tmc_code", "date"])["speed"].transform(sm)
        for d, g in s.groupby("date"):
            out[d] = pack(g)
    return out


data = {"meta": {"m": M, "bin_min": 15, "t0_min": T0, "t1_min": T1, "full": FULL,
                 "window": "64 weekdays, Jun 1 - Sep 1, 2025 (July 4 and Labor Day removed)",
                 "periods": {"AM": [360, 540], "PM": [840, 1080]},
                 "profiles": [[k, lbl] for k, lbl, _ in PROFILES]},
        "corridors": {}}
for cid, (name, dirs) in CORR.items():
    seg = pd.read_csv(REL / cid / "segments.csv")
    cap = pd.read_csv(REL / cid / "segment_capacity.csv")
    day = pd.read_csv(REL / cid / "segment_day_loading.csv")
    vf = day.groupby("tmc_code")["vf_mph"].first()
    geo = pd.read_csv(REL.parent / XD_META[cid] / "metadata.csv").drop_duplicates("Segment ID").set_index("Segment ID")
    for dname, code in dirs.items():
        sd = seg[seg["direction"] == dname].sort_values("road_order").merge(cap, on="tmc_code", how="left")
        codes = sd["tmc_code"].tolist()
        g = grids(f"{name}_{code}", codes)
        days = sorted(d for d in g if d[:2] == "20")
        key = f"{name} {code}"
        data["corridors"][key] = {
            "corridor": name, "direction": code, "direction_name": dname,
            "segments": [{"id": int(r.tmc_code), "x0": round(r.dist_start_mi, 3), "x1": round(r.dist_end_mi, 3),
                          "name": r.intersection if isinstance(r.intersection, str) else "",
                          "section": r.section, "vf": round(float(vf[r.tmc_code]), 2),
                          "lanes": int(r.lanes), "C": int(r.capacity_vphpl),
                          "lat": [round(geo.at[r.tmc_code, "Start Latitude"], 5), round(geo.at[r.tmc_code, "End Latitude"], 5)],
                          "lon": [round(geo.at[r.tmc_code, "Start Longitude"], 5), round(geo.at[r.tmc_code, "End Longitude"], 5)]}
                         for r in sd.itertuples()],
            "days": days,
            "speed": g,
        }
        print(key, len(codes), "segments,", "profiles", [p[0] for p in PROFILES], f"+ {len(days)} days" if days else "")

cal = pd.read_csv(BASE / "results" / "calibration_table.csv")
bd = pd.read_csv(BASE / "results" / "bottleneck_days.csv")
data["calibration"] = json.loads(cal.to_json(orient="records"))
# daily spread at each bottleneck as box-plot quantiles (no per-day values)
dist = {}
for (c, d, p), g in bd.groupby(["corridor", "direction", "period"]):
    dist[f"{c} {d} {p}"] = {col: [round(float(g[col].quantile(q)), 3) for q in (0, .25, .5, .75, 1)]
                            for col in ("P_h", "L_max_mi")}
data["dist"] = dist
if FULL:
    data["bottleneck_days"] = json.loads(bd.to_json(orient="records"))
OUT.write_text(json.dumps(data, separators=(",", ":")))
print(f"wrote {OUT} ({OUT.stat().st_size / 1e6:.1f} MB, {'FULL - do not publish' if FULL else 'public'})")
