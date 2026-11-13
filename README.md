# SPR-790 Corridor Calibration Table — I-10 and I-17 Phoenix

Per-corridor congestion bottleneck parameters for I-10 and I-17 in Phoenix, on
one common analysis window: **64 weekdays, June 1 – September 1, 2025**.
All definitions follow the ADOT Corridor Reliability progress report (October
2026) and its code,
[adot-corridor-reliability](https://github.com/jacky850/adot-corridor-reliability).

The parameters fall into two groups:

- **Speed-based (observed).** Bottleneck location, congestion episode, duration
  P, lowest speed v_t2 and queue extent QE, measured directly from INRIX probe
  speeds.
- **Estimated (model-based).** D/C, D, V and corridor VMT/VHT/VHD, computed from
  speed through the S3 speed–flow relation. There is **no independent count
  validation** yet.

**Files**

- [`results/calibration_table.csv`](results/calibration_table.csv): one row
  per corridor × direction × peak.
- [`results/bottleneck_days.csv`](results/bottleneck_days.csv): one row per
  congested weekday at each bottleneck.

## Results

| Corridor, peak | Bottleneck | Episode (avg weekday) | P avg (h) | P median (p85), h | Congested days | v_t2 median (mph) | QE mean (p95), mi | D/C avg (h) | D / V avg (veh/lane) |
|---|---|---|---|---|---|---|---|---|---|
| I-10 EB AM | I-10 Exit 139 / 51st Ave (mi 16.8) | 04:28–10:44 | 6.25 | 5.71 (6.85) | 63/64 | 18.1 | 12.9 (20.7) | 5.45 | 10,092 / 10,092 |
| I-10 WB AM | I-17 Exit 194 / I-10 Exit 150 (mi 13.2) | 07:20–08:36 | 1.28 | 1.52 (1.86) | 50/64 | 33.2 | 1.8 (3.2) | 1.23 | 2,281 / 5,240 |
| I-10 EB PM | I-10 Exit 130 / Fairway Dr (mi 6.8) | 13:11–16:11 | 2.99 | 3.00 (3.63) | 56/64 | 31.0 | 5.5 (7.7) | 2.85 | 5,518 / 8,652 |
| I-10 WB PM | I-10 Exits 144, 144A / 7th Ave (mi 17.5) | 12:04–18:48 | 6.74 | 6.45 (7.21) | 62/64 | 21.5 | 14.3 (17.2) | 6.02 | 10,157 / 10,157 |
| I-17 NB AM | I-17 Exit 195A / Maricopa Fwy (mi 0.0)¹ | 07:22–08:44 | 1.37 | 1.66 (2.31) | 50/64 | 40.0 | 1.0 (3.2) | 1.24 | 2,099 / 4,881 |
| I-17 SB AM | I-17 Exit 196 / 6th Ave (mi 24.5) | 05:24–09:13 | 3.82 | 3.40 (4.08) | 58/64 | 23.3 | 7.5 (13.8) | 3.53 | 6,537 / 6,537 |
| I-17 NB PM | I-17 Exit 195A / Maricopa Fwy (mi 0.0)¹ | 12:17–18:10 | 5.89 | 5.92 (7.16) | 63/64 | 30.2 | 7.7 (11.4) | 5.44 | 9,177 / 9,177 |
| I-17 SB PM | I-17 Exit 195B / Maricopa Fwy (mi 25.5)¹ | 14:23–17:24 | 3.02 | 2.33 (3.68) | 61/64 | 24.7 | 5.1 (9.7) | 2.95 | 4,984 / 6,654 |

How to read the table:

- The peak-direction rows (I-10 EB AM, I-10 WB PM, I-17 SB AM, I-17 NB PM)
  reproduce the progress report's slide 17.
- "avg" columns are measured on the average weekday speed profile.
- "median (p85)" columns are the distribution over congested weekdays at the
  same bottleneck.
- Mile = distance from the start of the corridor in the direction of travel.

¹ The bottleneck is the first or last segment of the analyzed corridor (the
I-10/I-17 split). The queue may extend beyond the study limits, so QE is a
lower bound.

## Definitions

| Item | Definition |
|---|---|
| Days | Weekdays, June 1 – September 1, 2025; July 4 and Labor Day removed (64 days) |
| Periods | AM 06:00–09:00, PM 14:00–18:00. The episode may start before or end after the period |
| Speed | INRIX XD 5-minute speed, averaged to 15 minutes and smoothed with a centred 3-bin mean |
| Free-flow speed v_f | Weekday night (21:00–05:00) 85th-percentile speed of each segment |
| Capacity speed v_c | v_f · 2^(−2/m), with m = 4 (≈ 0.71 v_f) |
| Congestion episode, P | Longest run below v_c whose slowest point falls in the period, lasting ≥ 0.5 h; P is its duration in hours |
| Bottleneck | Segment with the longest episode on the average weekday |
| v_t2 | Lowest smoothed 15-minute speed in the episode at the bottleneck |
| Queue extent QE | Longest continuous length below v_c at any 15 minutes, from 2 h before to 2 h after the period; mean over weekdays and 95th-percentile day |
| P length-weighted | Σ L·P / Σ L over all segments, with uncongested segments counted as 0 |
| q/C | Flow over capacity from speed through the S3 relation. **Capacity cancels**, so q/C needs only v_f and m |
| D/C (h) | Σ (q/C)·Δt over the episode, in hours. It does not depend on C |
| D, V (veh/lane) | D = D/C × C (episode volume); V = Σ q·Δt over the period and episode |
| C | AZTDM DTA network (GMNS `link.csv`), general-purpose lanes; 1,688 / 1,851 / 1,935 veh/h/lane by area type. Each XD segment is matched to the nearest same-direction freeway link |
| VMT, VHT, VHD | Corridor totals over the period: N = q × lanes × Δt per segment and 15 minutes. VHD = VHT − VMT / v_f |

### What depends on C

- P, v_t2, QE and D/C (h) do not depend on capacity.
- C only scales the vehicle counts D, V, VMT and VHT.
- The progress report found that speed-based flows run 1.4–1.6× above AZTDM ATR
  daily counts. D, V, VMT and VHT should therefore be read as upper estimates
  until the S3 relation is calibrated with counts.

## Columns of `calibration_table.csv`

| Column | Meaning |
|---|---|
| `bottleneck_section`, `bottleneck_location`, `bottleneck_segment`, `bottleneck_mile` | Corridor section, nearest named interchange at or upstream, INRIX XD segment ID, corridor mile |
| `lanes`, `v_f_mph`, `v_c_mph` | Bottleneck lanes (AZTDM GMNS), free-flow speed and capacity speed |
| `avg_episode_start`, `avg_episode_end`, `avg_P_h` | Episode on the average weekday |
| `P_length_weighted_h`, `QE_mi_mean`, `QE_mi_p95` | Corridor-level duration and queue extent |
| `congested_days`, `share_days_congested` | Weekdays with an episode at the bottleneck |
| `P_h_median`, `P_h_p15`, `P_h_p85`, `P_h_p95` | Distribution of daily P at the bottleneck |
| `episode_start_median`, `episode_end_median` | Median daily onset and end |
| `v_t2_mph_median`, `v_t2_mph_p15` | Lowest speed in the daily episode |
| `avg_DC_h`, `DC_h_median`, `DC_h_p85` | D/C in hours (average weekday; daily distribution) — estimated |
| `C_vphpl`, `capacity_source` | Per-lane capacity used for D and V |
| `avg_D_veh_per_lane`, `avg_V_veh_per_lane`, `D_over_V` | Episode and period volume per lane — estimated |
| `VMT`, `VHT`, `VHD`, `avg_speed_mph`, `TTI_VMT` | Corridor totals for the period — estimated |

## Reproduce

```bash
pip install pandas numpy
# 1. corridor_reliability.py and corridor_moe.py in adot-corridor-reliability (needs the licensed INRIX data)
# 2. convert the INRIX XD download to mph readings per corridor-direction
python scripts/01_convert_inrix_xd.py
# 3. build the table
python scripts/02_calibration_table.py
```

The scripts expect `adot-corridor-reliability`, with its INRIX downloads, in
the sibling folder `../ADOT Corridor Reliability`. The INRIX data is licensed
and not included.

## Limitations and next steps

- **D/C ≈ P by construction.** During congestion, S3 places flow close to the
  assumed capacity. D/C becomes an independent measure only after the S3
  relation (v_f, k_c, m, C) is calibrated against counts, such as AZTDM ATR
  daily counts or ADOT detector data.
- **One bottleneck per corridor-direction-peak.** Secondary bottlenecks are not
  summarized.
- **I-17 bottlenecks at the I-10 split** sit at the study-area limit.
- **QVDF shape parameters** (n, s, α, β) and backward/recovery wave speeds are
  not part of this release.
