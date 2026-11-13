// test_core.js — check the dashboard's JS analysis against results/bottleneck_days.csv
// Needs the full (local) build: CBI_FULL=1 python dashboard/export_data.py && node dashboard/test_core.js
const fs = require('fs');
const path = require('path');
const CBI = require('./cbi_core.js');
const D = JSON.parse(fs.readFileSync(path.join(__dirname, 'data.json')));
const m = D.meta.m, step = D.meta.bin_min;
const minute = []; for (let t = D.meta.t0_min; t < D.meta.t1_min; t += step) minute.push(t);
if (!D.bottleneck_days) { console.log('public build has no per-day data; run CBI_FULL=1 python dashboard/export_data.py first'); process.exit(0); }
const hm = s => { const [h, mm] = s.split(':').map(Number); return h * 60 + mm; };

const err = { P_h: [], DC_h: [], v_t2_mph: [], L_max_mi: [], L_avg_mi: [], w_f_mph: [], w_r_mph: [] };
let n = 0, miss = 0;
for (const r of D.bottleneck_days) {
  const c = D.corridors[`${r.corridor} ${r.direction}`];
  const i = c.segments.findIndex(s => s.id === r.bottleneck_segment);
  const grid = c.speed[r.date].map(CBI.dec);
  const per = D.meta.periods[r.period];
  const ev = CBI.peakEvent(minute, grid[i], CBI.vcOf(c.segments[i].vf, m), per[0], per[1], step);
  if (!ev) { miss++; continue; }
  const a = CBI.analyze(grid, c.segments, minute, i, ev, m);
  const js = { P_h: a.P_h, DC_h: a.DC_h, v_t2_mph: a.v_t2, L_max_mi: a.L_max, L_avg_mi: a.L_avg, w_f_mph: a.w_f, w_r_mph: a.w_r };
  for (const k in err) if (Number.isFinite(js[k]) && Number.isFinite(r[k])) err[k].push(Math.abs(js[k] - r[k]));
  n++;
}
console.log(`compared ${n} bottleneck-days, ${miss} with no JS event`);
for (const k in err) {
  const e = err[k].sort((x, y) => x - y);
  const q = p => e[Math.min(e.length - 1, Math.floor(p * e.length))];
  console.log(`${k.padEnd(10)} n=${e.length}  median |diff|=${q(0.5).toFixed(3)}  p90=${q(0.9).toFixed(3)}  exact(<0.01)=${(e.filter(x => x < 0.01).length / e.length * 100).toFixed(0)}%`);
}
