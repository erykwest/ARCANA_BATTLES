import fs from 'node:fs';

const path = 'sim-lab.js';
let src = fs.readFileSync(path, 'utf8');

const before = `        try {
          while (!State.battle.ended && driverTime + 1e-9 < o.maxTime) {
            const dt = Math.min(o.dt, o.maxTime - driverTime);
            driverTime += dt;
            Simulation.advance(dt);
          }
        } finally {`;

const after = `        try {
          const fixedDt = CFG.SIM_FIXED_DT || o.dt;
          // Stop on canonical simulation time, not on driver elapsed time.
          // This guarantees the final fixed tick is executed identically at
          // 20/30/60 Hz (e.g. the battle-limit tick at exactly 600 s).
          while (!State.battle.ended && State.simTime + fixedDt * 0.5 < o.maxTime) {
            driverTime += o.dt;
            Simulation.advance(o.dt);
          }
        } finally {`;

if (src.includes(after)) {
  console.log('Sim Lab boundary already fixed.');
  process.exit(0);
}

const first = src.indexOf(before);
if (first < 0) throw new Error('Sim Lab driver loop boundary target not found');
if (src.indexOf(before, first + before.length) >= 0) throw new Error('Sim Lab driver loop boundary target is ambiguous');

src = src.slice(0, first) + after + src.slice(first + before.length);
fs.writeFileSync(path, src);
console.log('Sim Lab max-time boundary fixed.');
