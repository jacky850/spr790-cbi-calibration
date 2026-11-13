// cbi_core.js — CBI analysis on a 15-min smoothed speed grid.
// Same definitions as scripts/02_calibration_table.py and corridor_reliability.py
// (README sections 1 and 2). Pure functions; used by the dashboard and by test_core.js.
(function (root) {
  'use strict';
  const HYST_BINS = 2;          // 30 min at or above v_c ends an event
  const MIN_EVENT_H = 0.5;
  const DT_H = 0.25;

  const vcOf = (vf, m) => vf * Math.pow(2, -2 / m);

  // S3: flow / capacity from speed (capacity cancels)
  function qOverC(v, vf, m) {
    const vc = vcOf(vf, m);
    const vv = Math.min(Math.max(v, 1.0), 0.99 * vf);
    const ratio = Math.max(Math.pow(vf / vv, m / 2) - 1, 1e-8);
    return Math.min((vv / vc) * Math.pow(ratio, 1 / m), 1.0);
  }

  // decode one segment's series: int x10, -1 = missing
  const dec = a => a.map(x => (x < 0 ? NaN : x / 10));

  // Runs below cutoff with hysteresis; times interpolated at the crossings.
  // minute[k] = start minute of bin k. Mirrors corridor_reliability.find_episodes.
  function findEvents(minute, v, cutoff, stepMin) {
    const out = [], n = v.length;
    const below = k => !(v[k] >= cutoff) && !Number.isNaN(v[k]);
    const cross = (l, r) => {
      if (v[r] === v[l]) return minute[r];
      const f = Math.min(Math.max((cutoff - v[l]) / (v[r] - v[l]), 0), 1);
      return minute[l] + f * (minute[r] - minute[l]);
    };
    let i = 0;
    while (i < n) {
      if (!below(i)) { i++; continue; }
      const s = i; let e = i;
      while (e < n - 1) {
        const nx = e + 1;
        let stays = true;
        for (let k = nx; k < Math.min(nx + HYST_BINS, n); k++) if (below(k) || Number.isNaN(v[k])) { stays = false; break; }
        if (!below(nx) && stays) break;
        e++;
      }
      const t0 = s > 0 ? cross(s - 1, s) : minute[0];
      const t3 = e < n - 1 ? cross(e, e + 1) : minute[n - 1] + stepMin;
      let tr = s;
      for (let k = s; k <= e; k++) if (v[k] < v[tr]) tr = k;
      out.push({ s, e, t0, t3, P_h: (t3 - t0) / 60, trough: minute[tr] });
      i = e + 1;
    }
    return out;
  }

  // Event of segment i for a peak: longest run with trough in [a, b), P >= 0.5 h
  function peakEvent(minute, v, vc, a, b, stepMin) {
    const c = findEvents(minute, v, vc, stepMin).filter(ev => ev.trough >= a && ev.trough < b && ev.P_h >= MIN_EVENT_H);
    if (!c.length) return null;
    return c.reduce((x, y) => (y.P_h > x.P_h ? y : x));
  }

  const fit = (t, x) => {
    const n = t.length; if (n < 2) return NaN;
    let st = 0, sx = 0, stt = 0, stx = 0;
    for (let k = 0; k < n; k++) { st += t[k]; sx += x[k]; stt += t[k] * t[k]; stx += t[k] * x[k]; }
    const d = n * stt - st * st; if (Math.abs(d) < 1e-12) return NaN;
    return (n * stx - st * sx) / d;
  };
  const median = a => { const s = a.filter(Number.isFinite).sort((p, q) => p - q); if (!s.length) return NaN; const m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };

  // Full CBI analysis of an event on segment i.
  // grid: [segment][bin] speeds (mph); segs: [{x0,x1,vf,C,lanes}]; ev: event on segment i
  function analyze(grid, segs, minute, i, ev, m) {
    const vf = segs[i].vf, vc = vcOf(vf, m), C = segs[i].C;
    const v = grid[i];
    // lowest speed: bins with start in [t0 - 15, t3]
    let vt2 = Infinity, tvt2 = null;
    for (let k = 0; k < minute.length; k++) if (minute[k] >= ev.t0 - 15 && minute[k] <= ev.t3 && v[k] < vt2) { vt2 = v[k]; tvt2 = minute[k]; }
    // D/C: bins with start in [t0, t3]
    let dc = 0;
    for (let k = 0; k < minute.length; k++) if (minute[k] >= ev.t0 && minute[k] <= ev.t3 && Number.isFinite(v[k])) dc += qOverC(v[k], vf, m) * DT_H;
    // queue through i at bins overlapping (t0, t3)
    const vcs = segs.map(s => vcOf(s.vf, m));
    const q = [];
    for (let k = 0; k < minute.length; k++) {
      if (!(minute[k] > ev.t0 - 15 && minute[k] < ev.t3)) continue;
      const bl = j => grid[j][k] < vcs[j];
      if (!bl(i)) continue;
      let u = i, d = i;
      while (u > 0 && bl(u - 1)) u--;
      while (d < segs.length - 1 && bl(d + 1)) d++;
      q.push({ minute: minute[k], tail: segs[u].x0, head: segs[d].x1, L: segs[d].x1 - segs[u].x0, u, d });
    }
    let res = { vf, vc, C, lanes: segs[i].lanes, t0: ev.t0, t3: ev.t3, P_h: ev.P_h, v_t2: vt2, t_vt2: tvt2,
      DC_h: dc, mean_qC: dc / ev.P_h, mu_hat: dc / ev.P_h * C, D_lane: dc * C, D_all: dc * C * segs[i].lanes, queue: q };
    if (q.length) {
      let kmax = 0; q.forEach((r, k) => { if (r.L > q[kmax].L) kmax = k; });
      const th = q.map(r => (r.minute - q[0].minute) / 60), tl = q.map(r => r.tail);
      // formation: onset -> first time the tail reaches its most upstream point;
      // recovery: last time there -> end. NaN when the tail sits at the upstream study limit.
      const tmin = Math.min(...tl);
      const kf = tl.findIndex(x => Math.abs(x - tmin) < 1e-9);
      let kr = kf; tl.forEach((x, k) => { if (Math.abs(x - tmin) < 1e-9) kr = k; });
      const censored = tmin <= segs[0].x0 + 1e-9;
      res = Object.assign(res, {
        L_max: q[kmax].L, L_avg: q.reduce((s, r) => s + r.L, 0) / q.length,
        head: median(q.map(r => r.head)), tail_min: tmin, t_Lmax: q[kmax].minute,
        w_f: censored ? NaN : fit(th.slice(0, kf + 1), tl.slice(0, kf + 1)),
        w_r: censored ? NaN : fit(th.slice(kr), tl.slice(kr)), kmax, kf, kr, censored,
      });
    }
    return res;
  }

  // Bottleneck for a peak: segment with the longest peak event on this grid
  function bottleneck(grid, segs, minute, a, b, m, stepMin) {
    let best = null;
    segs.forEach((s, i) => {
      const ev = peakEvent(minute, grid[i], vcOf(s.vf, m), a, b, stepMin);
      if (ev && (!best || ev.P_h > best.ev.P_h)) best = { i, ev };
    });
    return best;
  }

  // Event containing bin k on segment i (any time of day)
  function eventAt(minute, v, vc, k, stepMin) {
    return findEvents(minute, v, vc, stepMin).find(ev => k >= ev.s && k <= ev.e) || null;
  }

  const api = { qOverC, vcOf, dec, findEvents, peakEvent, analyze, bottleneck, eventAt, median };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.CBI = api;
})(this);
