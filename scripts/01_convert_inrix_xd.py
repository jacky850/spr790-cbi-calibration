"""
01_convert_inrix_xd.py
Convert INRIX Roadway Analytics XD exports (Jun 1 - Sep 1, 2025, 5-min, km/h)
into mph speed readings (Readings.csv + TMC_Identification.csv, INRIX TMC layout),
one folder per corridor-direction.

Segment set + ordering come from the ADOT Corridor Reliability run
(output/<corridor>/segments.csv: road_order increases in direction of travel).

Run:  python 01_convert_inrix_xd.py
"""
from pathlib import Path
import pandas as pd

J = Path(__file__).resolve().parents[2]            # .../Jinxi Wu
REL = J / "ADOT Corridor Reliability"
OUT = Path(__file__).resolve().parents[1] / "inputs"

EXCLUDE_DATES = {"2025-07-04", "2025-09-01"}       # same holidays as the reliability run
KMH_TO_MPH = 1 / 1.609344

CORRIDORS = {
    "i10_phoenix": {
        "data_dir": "Only-I-10-0601-to-0901_2025-06-01_to_2025-09-02_5_min_part_1",
        "region_contains": "Only-I-10",
        "dirs": {"Eastbound": "I-10_EB", "Westbound": "I-10_WB"},
    },
    "i17_phoenix": {
        "data_dir": "Only-I-17-0601-to-0901_2025-06-01_to_2025-09-02_5_min_part_1",
        "region_contains": "i-17-tti",
        "dirs": {"Northbound": "I-17_NB", "Southbound": "I-17_SB"},
    },
}

USECOLS = ["Date Time", "Segment ID", "Speed(km/hour)", "Ref Speed(km/hour)",
           "Pct Score30", "Corridor/Region Name"]


def convert(key, cfg):
    seg = pd.read_csv(REL / "output" / key / "segments.csv")
    seg_ids = set(seg["tmc_code"].astype("int64"))
    parts = []
    src = REL / cfg["data_dir"] / "data.csv"
    print(f"[{key}] reading {src.name} ...")
    for ch in pd.read_csv(src, usecols=USECOLS, chunksize=2_000_000):
        ch = ch[ch["Segment ID"].isin(seg_ids)
                & ch["Corridor/Region Name"].str.contains(cfg["region_contains"], regex=False)]
        parts.append(ch)
    df = pd.concat(parts, ignore_index=True)
    df = df.drop_duplicates(["Segment ID", "Date Time"])
    # local Phoenix time (no DST, all -07:00) -> naive "YYYY-MM-DD HH:MM:SS"
    df["measurement_tstamp"] = df["Date Time"].str.slice(0, 19).str.replace("T", " ")
    df = df[~df["measurement_tstamp"].str.slice(0, 10).isin(EXCLUDE_DATES)]
    df["speed"] = (df["Speed(km/hour)"] * KMH_TO_MPH).round(2)
    df["reference_speed"] = df["Ref Speed(km/hour)"] * KMH_TO_MPH
    # INRIX confidence semantics: 30 = real-time probe; <30 = historical/reference fill
    df["confidence_score"] = (df["Pct Score30"] >= 50).map({True: 30, False: 10})
    df = df.rename(columns={"Segment ID": "tmc_code"})

    for dname, corr in cfg["dirs"].items():
        s = seg[seg["direction"] == dname].sort_values("road_order")
        d = df[df["tmc_code"].isin(set(s["tmc_code"]))]
        ref = d.groupby("tmc_code")["reference_speed"].median()
        meta = pd.DataFrame({
            "tmc": s["tmc_code"].values,
            "road": corr,
            "direction": dname,
            "intersection": s["intersection"].values,
            "miles": s["miles"].values,
            "road_order": s["road_order"].values,
            "dist_start_mi": s["dist_start_mi"].values,
            "reference_speed": s["tmc_code"].map(ref).round(1).values,
        })
        od = OUT / corr
        od.mkdir(parents=True, exist_ok=True)
        meta.to_csv(od / "TMC_Identification.csv", index=False)
        d[["tmc_code", "measurement_tstamp", "speed", "confidence_score"]] \
            .sort_values(["tmc_code", "measurement_tstamp"]) \
            .to_csv(od / "Readings.csv", index=False)
        days = d["measurement_tstamp"].str.slice(0, 10).nunique()
        print(f"  {corr}: {len(meta)} segments, {len(d):,} readings, {days} days, "
              f"{meta['miles'].sum():.1f} mi, real-time share "
              f"{(d['confidence_score'] == 30).mean():.4f}")


if __name__ == "__main__":
    for k, c in CORRIDORS.items():
        convert(k, c)
