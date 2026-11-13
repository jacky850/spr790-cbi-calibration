# Parameter Definitions

Detailed definitions and formulas for every parameter in
[`results/calibration_table.csv`](../results/calibration_table.csv), the
[dashboard](https://jacky850.github.io/spr790-cbi-calibration/) and the
[README](../README.md).

All definitions follow the ADOT Corridor Reliability progress report
(October 2026) and its code,
[adot-corridor-reliability](https://github.com/jacky850/adot-corridor-reliability).

- **Section 1 — speed-based parameters.** Measured directly from INRIX probe
  speeds.
- **Section 2 — flow parameters.** Derived from speed through the S3 model.
  These are estimates and have not been validated against counts.

**Contents**

- [Notation](#notation)
- [1. Speed-based parameters](#1-speed-based-parameters)
- [2. Flow parameters derived from speed](#2-flow-parameters-derived-from-speed)
- [Column reference](#column-reference)

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

The **average weekday profile** uses the mean over the 64 weekdays before smoothing:

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

Let $t_f$ be the first bin and $t_r$ the last bin at which the queue tail is
at its most upstream position, $\min_t x_{\text{tail}}(t)$. Fit straight lines
to the queue-tail position over time ($t$ in hours from the first bin):

```math
w_f = \frac{d\,x_{\text{tail}}}{dt}\Big|_{\,t \le t_f} , \qquad
w_r = \frac{d\,x_{\text{tail}}}{dt}\Big|_{\,t \ge t_r} \qquad (\text{mph, ordinary least squares})
```

- **Why the tail and not $L_{\max}$.** The fit windows end and start where
  the tail turns, not at $L_{\max}$. On I-10 WB PM, for example, the tail
  stops moving after about an hour while the queue keeps growing at its head.
  A window ending at $L_{\max}$ would mix hours of a stationary tail into
  the formation fit.
- **Not reported** (empty) when the tail reaches the upstream end of the
  study corridor, because the true tail is outside the data.
- At least two bins are needed on each side; otherwise the value is empty.

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

The per-day records behind the medians (`bottleneck_days.csv`) are kept locally and not published, in line with the INRIX license.
