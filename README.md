# SPR-790 Bottleneck Calibration Table — I-10 and I-17 Phoenix

This repository gives one calibration record per **corridor × direction × weekday
peak** for I-10 and I-17 in Phoenix. The common analysis window is **64
weekdays, June 1 – September 1, 2025**, using INRIX XD probe speeds.

The parameters fall into two groups:

1. **Speed-based parameters.** These are measured directly from the
   time–space speed field: bottleneck location, congestion event window,
   duration P, lowest speed, queue length, queue head, and the formation and
   recovery speeds of the queue.
2. **Flow parameters derived from speed.** Speed is converted to flow through
   the S3 speed–density model, which gives D/C, the mean flow during the event,
   the volumes D and V, and corridor VMT, VHT and VHD. These are **model
   estimates**; they have not been validated against counts.

All definitions follow the ADOT Corridor Reliability progress report (October
2026) and its code,
[adot-corridor-reliability](https://github.com/jacky850/adot-corridor-reliability).
The peak-direction rows reproduce slide 17 of that report.

**Outputs**

- [`results/calibration_table.csv`](results/calibration_table.csv): one row
  per corridor × direction × peak (8 rows).
- [`results/bottleneck_days.csv`](results/bottleneck_days.csv): one row per
  congested weekday at each bottleneck (463 rows).

---

## Key results

Peaks are weekday AM 06:00–09:00 and PM 14:00–18:00. **Bold rows** are the
peak directions. "Median (p85)" is taken over congested weekdays at the
bottleneck.

### A. Speed-based parameters

| Corridor, peak | Bottleneck | Event window (avg weekday) | P avg (h) | P median (p85), h | Lowest speed v_t2 (mph) | Max queue L_max, median (p85), mi | Avg queue L_avg (mi) | Queue head (mi) | Formation / recovery w_f / w_r (mph) | Corridor QE mean (p95), mi |
|---|---|---|---|---|---|---|---|---|---|---|
| **I-10 EB AM** | 51st Ave, mi 16.8 | 04:28–10:44 | 6.25 | 5.71 (6.85) | 18.1 | 12.7 (20.2) | 6.6 | 18.5 | −2.5 / +2.0 | 12.9 (20.7) |
| I-10 WB AM | I-17 / I-10 Exit 150, mi 13.2 | 07:20–08:36 | 1.28 | 1.52 (1.86) | 33.2 | 1.7 (2.6) | 1.4 | 13.9 | −2.4 / +0.9 | 1.8 (3.2) |
| I-10 EB PM | Fairway Dr, mi 6.8 | 13:11–16:11 | 2.99 | 3.00 (3.63) | 31.0 | 4.8 (5.7) | 3.7 | 7.7 | −2.1 / +1.4 | 5.5 (7.7) |
| **I-10 WB PM** | 7th Ave, mi 17.5 | 12:04–18:48 | 6.74 | 6.45 (7.21) | 21.5 | 14.9 (17.1) | 7.4 | 20.3 | −0.3 / +0.7 | 14.3 (17.2) |
| I-17 NB AM ¹ | Exit 195A, mi 0.0 | 07:22–08:44 | 1.37 | 1.66 (2.31) | 40.0 | 0.5 (0.5) | 0.5 | 0.5 | — / 0.0 | 1.0 (3.2) |
| **I-17 SB AM** ¹ | 6th Ave, mi 24.5 | 05:24–09:13 | 3.82 | 3.40 (4.08) | 23.3 | 3.2 (4.5) | 2.5 | 25.9 | −0.8 / +0.9 | 7.5 (13.8) |
| **I-17 NB PM** ¹ | Exit 195A, mi 0.0 | 12:17–18:10 | 5.89 | 5.92 (7.16) | 30.2 | 4.8 (11.0) | 1.6 | 0.5 | 0.0 / 0.0 | 7.7 (11.4) |
| I-17 SB PM ¹ | Exit 195B, mi 25.5 | 14:23–17:24 | 3.02 | 2.33 (3.68) | 24.7 | 2.6 (3.2) | 1.3 | 25.9 | −1.7 / +0.8 | 5.1 (9.7) |

### B. Flow parameters derived from speed (estimated)

| Corridor, peak | Lanes × C (veh/h/lane) | D/C avg (h) | D/C median (p85), h | Mean q/C in event | Mean event flow (veh/h/lane) | D per lane (veh) | D all lanes (veh) | V per lane (veh) | D/V | VMT (veh-mi) | VHT (veh-h) | VHD (veh-h) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **I-10 EB AM** | 4 × 1,851 | 5.45 | 4.67 (5.68) | 0.84 | 1,546 | 10,092 | 40,368 | 10,092 | 1.00 | 682,617 | 14,481 | 5,020 |
| I-10 WB AM | 3 × 1,851 | 1.23 | 1.43 (1.86) | 0.97 | 1,794 | 2,281 | 6,842 | 5,240 | 0.44 | 658,123 | 10,001 | 863 |
| I-10 EB PM | 4 × 1,935 | 2.85 | 2.75 (3.47) | 0.94 | 1,815 | 5,518 | 22,071 | 8,652 | 0.64 | 891,108 | 15,720 | 3,370 |
| **I-10 WB PM** | 4 × 1,688 | 6.02 | 5.47 (6.23) | 0.87 | 1,473 | 10,157 | 40,627 | 10,157 | 1.00 | 937,735 | 21,944 | 8,923 |
| I-17 NB AM ¹ | 3 × 1,688 | 1.24 | 1.72 (2.21) | 0.99 | 1,674 | 2,099 | 6,298 | 4,881 | 0.43 | 354,060 | 5,551 | 577 |
| **I-17 SB AM** ¹ | 3 × 1,851 | 3.53 | 3.04 (3.79) | 0.90 | 1,657 | 6,537 | 19,611 | 6,537 | 1.00 | 354,154 | 6,892 | 1,950 |
| **I-17 NB PM** ¹ | 3 × 1,688 | 5.44 | 5.57 (6.67) | 0.94 | 1,589 | 9,177 | 27,530 | 9,177 | 1.00 | 486,060 | 9,518 | 2,686 |
| I-17 SB PM ¹ | 3 × 1,688 | 2.95 | 2.07 (3.27) | 0.90 | 1,526 | 4,984 | 14,952 | 6,654 | 0.75 | 486,728 | 8,367 | 1,577 |

Notes:

- D, V, VMT and VHT scale with C. In the progress report, speed-based flows were
  1.4–1.6× the AZTDM ATR daily counts, so read these columns as upper estimates.
- D/V = 1.00 means the event covers the whole peak period.

¹ The bottleneck is the first or last segment of the analyzed I-17 corridor
(the I-10/I-17 split at Exit 195). The queue head or tail lies at the study
limit, so the queue length and wave speeds are truncated (`flags` column).

---

## Notation

| Symbol | Meaning |
|---|---|
| $i = 1,\dots,N$ | INRIX XD segments of one direction, numbered in the direction of travel |
| $x_i^{0}, x_i^{1}$ | Start and end of segment $i$, in miles from the start of the corridor (increasing downstream) |
| $\ell_i = x_i^{1}-x_i^{0}$ | Segment length (mi) |
| $n_i$ | Number of general-purpose lanes on segment $i$ (AZTDM GMNS) |
| $d \in \mathcal{D}$ | Weekdays, $\lvert\mathcal{D}\rvert = 64$ |
| $t$ | 15-minute bins, $\Delta t = 0.25$ h |
| $[T_a, T_b]$ | Peak period: AM $[06{:}00, 09{:}00]$, PM $[14{:}00, 18{:}00]$ |
| $b$ | Bottleneck segment |

---

## 1. Speed-based parameters

### 1.1 Speed processing

The INRIX 5-minute speeds (records with score 30 only) are averaged to 15
minutes, giving $u_{i,d}(t)$. They are then smoothed with a centred 3-bin mean:

```math
v_{i,d}(t) = \tfrac{1}{3}\big[u_{i,d}(t-1) + u_{i,d}(t) + u_{i,d}(t+1)\big]
```

The **average weekday profile** uses the mean over days before smoothing:

```math
\bar v_i(t) = \mathrm{smooth}\Big(\tfrac{1}{|\mathcal{D}|}\textstyle\sum_{d} u_{i,d}(t)\Big)
```

### 1.2 Free-flow speed and capacity speed

```math
v_{f,i} = P_{85}\big\{u_{i,d}(t) : d \in \mathcal{D},\; t \in [21{:}00, 05{:}00)\big\}
```

```math
v_{c,i} = v_{f,i}\, 2^{-2/m}, \qquad m = 4 \;\Rightarrow\; v_{c,i} \approx 0.707\, v_{f,i}
```

$v_{c,i}$ is the speed at capacity in the S3 model (Section 2.1). It is the
congestion threshold for every speed-based parameter.

### 1.3 Congestion event and duration P

On segment $i$ and day $d$, a congestion event is a run of bins with
$v_{i,d}(t) < v_{c,i}$.

- **Hysteresis.** A run ends only when the speed stays at or above $v_{c,i}$
  for 30 minutes (2 bins).
- **Start and end times.** The start $t_0$ and end $t_3$ are interpolated
  linearly at the crossings of $v_{c,i}$:

```math
t_0 = t_{s-1} + \frac{v_{c,i} - v(t_{s-1})}{v(t_s) - v(t_{s-1})}\,(t_s - t_{s-1})
```

and analogously for $t_3$ at the end of the run.

- **Which run is the event for a peak.** The event of segment $i$ for a peak
  is the **longest** run that:
  - has its slowest bin (the trough) inside $[T_a, T_b]$, and
  - lasts at least 0.5 h.

  The event may start before $T_a$ and end after $T_b$.
- **Duration.**

```math
P_{i,d} = t_3 - t_0 \quad (\text{h}), \qquad P_{i,d} = 0 \text{ if no event}
```

The same rule applied to $\bar v_i(t)$ gives the average-weekday event
$[\bar t_0, \bar t_3]$ and $\bar P_i$.

**Columns.** `event_start_avg`, `event_end_avg` and `P_h_avg` come from the
average weekday. `event_start_median`, `event_end_median`, `P_h_median`,
`P_h_p85` and `P_h_p95` are taken over congested days, where $P_{b,d} > 0$.
`congested_days` counts those days, and `share_days_congested` divides by 64.

### 1.4 Bottleneck

```math
b = \arg\max_i \; \bar P_i
```

The bottleneck is the segment with the longest event on the average weekday.
`bottleneck_mile` is $x_b^{0}$. `bottleneck_location` is the nearest named
interchange at or upstream of $b$.

### 1.5 Lowest speed

```math
v_{t2,d} = \min_{t \in [t_0,\, t_3]} v_{b,d}(t), \qquad \text{speed drop} = v_{t2}/v_{f,b}
```

### 1.6 Queue length and queue head (dashboard parameters)

At each bin $t$ of day $d$'s event at $b$ where $v_{b,d}(t) < v_{c,b}$, grow
the run of congested segments outward from $b$:

```math
\underline{i}(t) = \min\{\, j \le b : v_{k,d}(t) < v_{c,k}\ \ \forall k \in [j, b] \,\}
```

```math
\overline{i}(t) = \max\{\, j \ge b : v_{k,d}(t) < v_{c,k}\ \ \forall k \in [b, j] \,\}
```

This gives the queue tail (upstream end), the queue head (downstream end, the
active bottleneck) and the queue length:

```math
x_{\text{tail}}(t) = x^{0}_{\underline{i}(t)}, \qquad
x_{\text{head}}(t) = x^{1}_{\overline{i}(t)}, \qquad
L(t) = x_{\text{head}}(t) - x_{\text{tail}}(t)
```

Over the event, with $\mathcal{T}_d$ the bins with a queue:

```math
L_{\max,d} = \max_{t \in \mathcal{T}_d} L(t), \qquad
L_{\text{avg},d} = \frac{1}{|\mathcal{T}_d|}\sum_{t \in \mathcal{T}_d} L(t), \qquad
x_{\text{head},d} = \mathrm{median}_{t} \, x_{\text{head}}(t)
```

**Columns.** `L_max_mi_median`, `L_max_mi_p85`, `L_avg_mi_median` and
`queue_head_mi_median`.

### 1.7 Queue formation and recovery speeds

Let $t^{*}$ be the bin with the largest $L(t)$. Fit straight lines to the
queue-tail position over time ($t$ in hours from the first bin):

```math
w_f = \frac{d\,x_{\text{tail}}}{dt}\Big|_{\,t \le t^{*}} , \qquad
w_r = \frac{d\,x_{\text{tail}}}{dt}\Big|_{\,t \ge t^{*}} \qquad (\text{mph, ordinary least squares})
```

- A negative value means the tail moves upstream; a positive value means it
  moves downstream.
- $w_f$ is how fast the queue grows backward. $w_r$ is how fast it clears.
- These are rates of growth and clearance at 15-minute and segment
  resolution. They are not the kinematic waves inside stop-and-go traffic
  (about 10–12 mph), which this resolution cannot capture.

**Columns.** `w_f_mph_median` and `w_r_mph_median`.

### 1.8 Corridor-wide measures

**Queue extent QE.** For every day and bin from $T_a - 2$ h to $T_b + 2$ h,
find the longest run of consecutive congested segments anywhere on the
corridor. Take the daily maximum:

```math
QE_d = \max_{t \in [T_a-2,\;T_b+2]} \;\; \max_{\text{runs } R(t)} \sum_{i \in R(t)} \ell_i
```

`QE_mi_mean` is the mean of $QE_d$ over weekdays, and `QE_mi_p95` is its 95th
percentile. Unlike $L$, QE is not tied to the bottleneck.

**Length-weighted duration.** Uncongested segments count as 0:

```math
P_{\ell} = \frac{\sum_i \ell_i\, \bar P_i}{\sum_i \ell_i}
```

---

## 2. Flow parameters derived from speed

### 2.1 S3 speed–density model and the speed-to-flow conversion

```math
v(k) = \frac{v_f}{\big[1 + (k/k_c)^{m}\big]^{2/m}}, \qquad q = k\,v
```

At the critical density $k = k_c$, the speed is $v_c = v_f\,2^{-2/m}$ and the
flow is at capacity, $C = k_c v_c$. Inverting $v(k)$ and dividing by $C$ gives
flow relative to capacity as a function of speed alone:

```math
\frac{q}{C}(v) = \min\left\{ \frac{v}{v_c}\Big[\Big(\frac{v_f}{v}\Big)^{m/2} - 1\Big]^{1/m},\; 1 \right\},
\qquad v \in [1,\; 0.99\,v_f]
```

**$C$ and $k_c$ cancel**, so $q/C$ needs only $v_f$ and $m$. Every quantity
below that is a ratio to $C$, including D/C and the mean $q/C$, is therefore
**independent of the capacity value**. $C$ only sets the scale of vehicle
counts.

### 2.2 Demand-to-capacity ratio D/C (hours)

```math
\Big(\frac{D}{C}\Big)_{d} = \sum_{t \in [t_0,\, t_3]} \frac{q}{C}\big(v_{b,d}(t)\big)\,\Delta t \quad (\text{h})
```

D/C is the equivalent number of hours of capacity flow that passed the
bottleneck during the event.

- The sum runs over the 15-minute bins whose start lies in $[t_0, t_3]$.
- Because $q/C \le 1$, D/C ≤ P up to bin rounding. P uses the interpolated
  $t_0$ and $t_3$, so on single days D/C can exceed P by at most one bin
  (0.25 h).

**Columns.** `DC_h_avg` (average weekday) and `DC_h_median`, `DC_h_p85`.

### 2.3 Mean flow during the event (S3 discharge rate)

```math
\overline{q/C} = \frac{(D/C)}{P}, \qquad \hat\mu = \overline{q/C}\cdot C \quad (\text{veh/h/lane})
```

$\hat\mu$ is the speed-implied queue discharge rate at the bottleneck. It is
the quantity that counts would calibrate.

**Columns.** `mean_qC_in_event` and `mean_event_flow_vphpl` (median over days).

### 2.4 Capacity C and volumes D, V

$C_b$ is the per-lane capacity of the AZTDM DTA network link matched to segment
$b$. It depends only on the area type: 1,688, 1,851 or 1,935 veh/h/lane.

```math
D = C_b\,(D/C), \qquad D_{\text{all lanes}} = n_b\,D, \qquad
V = C_b \sum_{t \in [T_a,T_b]\,\cup\,[t_0,t_3]} \frac{q}{C}\big(\bar v_b(t)\big)\,\Delta t
```

- $D$ is the volume per lane during the event.
- $V$ is the volume per lane over the peak period and the event together.
- $D/V$ is the share of peak volume that travels in congestion.

**Columns.** `D_veh_per_lane_avg`, `D_veh_all_lanes_avg`, `V_veh_per_lane_avg`
and `D_over_V`.

### 2.5 Corridor VMT, VHT and delay

For segment $i$ and bin $t$ in the peak, use the unsmoothed 15-minute speed
$u_{i,d}(t)$:

```math
N_{i,d}(t) = \frac{q}{C}\big(u_{i,d}(t)\big)\, C_i\, n_i\, \Delta t
```

```math
\text{VMT}_d = \sum_{i,t} N\,\ell_i, \qquad
\text{VHT}_d = \sum_{i,t} \frac{N\,\ell_i}{u_{i,d}(t)}, \qquad
\text{VHD}_d = \text{VHT}_d - \sum_{i,t} \frac{N\,\ell_i}{v_{f,i}}
```

```math
\text{TTI}_{\text{VMT},d} = \frac{\sum_{i,t} N\,\ell_i\, v_{f,i}/u_{i,d}(t)}{\text{VMT}_d}, \qquad
\bar v = \frac{\overline{\text{VMT}}}{\overline{\text{VHT}}}
```

The table reports means over the 64 weekdays.

### 2.6 What these flow parameters can and cannot say

- **D/C ≈ P by construction.** During congestion the speed is below $v_c$, and
  S3 maps those speeds to $q/C$ close to 1 (median mean $q/C$ in the event:
  0.84–0.99). D/C therefore adds
  little information beyond P until the S3 relation ($v_f$, $k_c$, $m$, $C$)
  is calibrated against counts.
- **Volume scale.** The scale of D, V and VMT rests on the assumed $C$. The
  progress report found speed-based flows 1.4–1.6× above the AZTDM ATR daily
  counts, mainly from speeds near $v_f$.
- **Next step.** Calibrate S3 with the AZTDM ATR counts (105 matched segments)
  and ADOT detector counts at the bottlenecks. Then compare $\hat\mu$ with the
  measured discharge rate.

---

## Column reference

`calibration_table.csv`:

| Column | Symbol / section |
|---|---|
| `corridor`, `direction`, `period`, `weekdays` | — |
| `bottleneck_section`, `bottleneck_location`, `bottleneck_segment`, `bottleneck_mile` | $b$, $x_b^0$ (1.4) |
| `lanes`, `v_f_mph`, `v_c_mph` | $n_b$, $v_{f,b}$, $v_{c,b}$ (1.2) |
| `event_start_avg`, `event_end_avg`, `P_h_avg` | $\bar t_0$, $\bar t_3$, $\bar P_b$ (1.3) |
| `congested_days`, `share_days_congested` | (1.3) |
| `event_start_median`, `event_end_median`, `P_h_median`, `P_h_p85`, `P_h_p95` | $t_0$, $t_3$, $P_{b,d}$ (1.3) |
| `v_t2_mph_median`, `v_t2_mph_p15`, `speed_drop_vt2_over_vf` | $v_{t2}$ (1.5) |
| `L_max_mi_median`, `L_max_mi_p85`, `L_avg_mi_median`, `queue_head_mi_median` | $L_{\max}$, $L_{\text{avg}}$, $x_{\text{head}}$ (1.6) |
| `w_f_mph_median`, `w_r_mph_median` | $w_f$, $w_r$ (1.7) |
| `QE_mi_mean`, `QE_mi_p95`, `P_length_weighted_h` | $QE$, $P_\ell$ (1.8) |
| `C_vphpl`, `capacity_source` | $C_b$ (2.4) |
| `DC_h_avg`, `DC_h_median`, `DC_h_p85` | $D/C$ (2.2) |
| `mean_qC_in_event`, `mean_event_flow_vphpl` | $\overline{q/C}$, $\hat\mu$ (2.3) |
| `D_veh_per_lane_avg`, `D_veh_all_lanes_avg`, `V_veh_per_lane_avg`, `D_over_V` | $D$, $V$ (2.4) |
| `VMT`, `VHT`, `VHD`, `avg_speed_mph`, `TTI_VMT` | (2.5) |
| `flags` | `bottleneck_at_study_limit`, `queue_reaches_upstream_limit` |

`bottleneck_days.csv` has the same quantities for each congested weekday.

## Data

| Corridor | Limits | Length per direction | XD segments |
|---|---|---|---|
| I-10 Phoenix | Exit 122 (Perryville Rd) – Exit 162 (Wild Horse Pass Blvd) | 39.3 mi | 89 EB, 89 WB |
| I-17 Phoenix | Exit 194 (I-10 split) – Exit 223 (Loop 303) | 26.3 mi NB, 25.9 mi SB | 56 NB, 50 SB |

- INRIX Roadway Analytics XD download, 5-minute speeds, Arizona local time
  (UTC−7). At least 99.7% of records are real-time probe data.
- Segment order, lanes and capacity come from `adot-corridor-reliability`.
- The INRIX data is licensed and is **not** included in this repository.

## Reproduce

```bash
pip install -r requirements.txt
# 1. In ../ADOT Corridor Reliability: corridor_reliability.py and corridor_moe.py for both corridors
python scripts/01_convert_inrix_xd.py   # INRIX XD download -> mph readings per corridor-direction
python scripts/02_calibration_table.py  # -> results/
```
