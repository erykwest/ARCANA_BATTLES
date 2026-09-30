import fs from 'node:fs';

const htmlPath = 'COFFEE_BATTLES.html';
const simPath = 'sim-lab.js';

let html = fs.readFileSync(htmlPath, 'utf8');
let sim = fs.readFileSync(simPath, 'utf8');

function replaceOnce(source, search, replacement, label) {
  const idx = source.indexOf(search);
  if (idx < 0) throw new Error(`Patch target not found: ${label}`);
  const second = source.indexOf(search, idx + search.length);
  if (second >= 0) throw new Error(`Patch target is ambiguous: ${label}`);
  return source.slice(0, idx) + replacement + source.slice(idx + search.length);
}

function replaceRegexOnce(source, regex, replacement, label) {
  const flags = regex.flags.includes('g') ? regex.flags : regex.flags + 'g';
  const matches = [...source.matchAll(new RegExp(regex.source, flags))];
  if (matches.length !== 1) throw new Error(`Expected exactly one ${label} match, found ${matches.length}`);
  return source.replace(regex, replacement);
}

// ---------------------------------------------------------------------------
// COFFEE_BATTLES.html — fixed physics cadence + canonical unit iteration.
// ---------------------------------------------------------------------------
if (!html.includes('SIM_FIXED_DT:')) {
  html = replaceOnce(
    html,
    '    BATTLE_TIME_LIMIT_S: 600,\n',
    '    BATTLE_TIME_LIMIT_S: 600,\n    SIM_FIXED_DT: 1 / 30,\n',
    'CFG.SIM_FIXED_DT'
  );
}

if (!html.includes('simAccumulator: 0,')) {
  html = replaceOnce(
    html,
    '    simTime: 0,\n    lastFrameAt: performance.now(),\n',
    '    simTime: 0,\n    simAccumulator: 0,\n    lastFrameAt: performance.now(),\n',
    'State.simAccumulator'
  );
}

// Any fresh simulation timeline must also flush fractional elapsed time.
html = html.replace(
  /      State\.simTime = 0;\n      State\.combatClocks\.clear\(\);/g,
  '      State.simTime = 0;\n      State.simAccumulator = 0;\n      State.combatClocks.clear();'
);

if (!html.includes('canonicalizeUnitOrder()')) {
  const simStart = html.indexOf('  const Simulation = {');
  if (simStart < 0) throw new Error('Simulation object not found');

  const updateStart = html.indexOf('    update(dt) {\n', simStart);
  if (updateStart < 0) throw new Error('Simulation.update not found');

  const updateBodyStart = updateStart + '    update(dt) {\n'.length;
  const updateEndMarker = '\n    },\n\n    frame(now) {';
  const updateEnd = html.indexOf(updateEndMarker, updateBodyStart);
  if (updateEnd < 0) throw new Error('Simulation.update end marker not found');

  const originalBody = html.slice(updateBodyStart, updateEnd);
  const fixedBody = `      // Canonical order makes pair resolution independent from insertion/reversal order.\n      this.canonicalizeUnitOrder();\n      if (this.preStepHook) this.preStepHook(dt);\n\n${originalBody}`;

  const replacement = `    preStepHook: null,\n\n    canonicalizeUnitOrder() {\n      State.units.sort((a, b) => {\n        const ai = String(a?.id ?? '');\n        const bi = String(b?.id ?? '');\n        return ai < bi ? -1 : ai > bi ? 1 : 0;\n      });\n    },\n\n    setPreStepHook(fn = null) {\n      this.preStepHook = typeof fn === 'function' ? fn : null;\n      return this.preStepHook;\n    },\n\n    fixedStep(dt = CFG.SIM_FIXED_DT) {\n${fixedBody}\n    },\n\n    advance(elapsedDt) {\n      const elapsed = Math.max(0, Number(elapsedDt) || 0);\n      if (elapsed <= 0 || State.battle.ended) return 0;\n\n      const step = CFG.SIM_FIXED_DT;\n      State.simAccumulator += elapsed;\n      let steps = 0;\n\n      while (!State.battle.ended && State.simAccumulator + 1e-12 >= step) {\n        State.simAccumulator -= step;\n        if (Math.abs(State.simAccumulator) < 1e-12) State.simAccumulator = 0;\n        State.simTime += step;\n        this.fixedStep(step);\n        steps++;\n      }\n      return steps;\n    },\n\n    // Compatibility entry point for debug tooling. Physics remains fixed-step.\n    update(dt) {\n      return this.advance(dt);\n    }`;

  html = html.slice(0, updateStart) + replacement + html.slice(updateEnd + '\n    },'.length);

  html = replaceOnce(
    html,
    '      State.simTime += dt;\n      if (dt > 0) Simulation.update(dt);\n',
    '      if (dt > 0) Simulation.advance(dt);\n',
    'Simulation.frame fixed-step advance'
  );
}

// ---------------------------------------------------------------------------
// sim-lab.js — dt becomes driver cadence, never physics cadence.
// AI refresh happens on fixed-step boundaries, not on driver boundaries.
// ---------------------------------------------------------------------------
sim = sim.replace("    version: '0.1',", "    version: '0.2',");

if (!sim.includes('Simulation.canonicalizeUnitOrder?.();')) {
  sim = replaceOnce(
    sim,
    "    issueBothSides() {\n      const report = { new:0, same:0, none:0, skip:0 };\n",
    "    issueBothSides() {\n      Simulation.canonicalizeUnitOrder?.();\n      const report = { new:0, same:0, none:0, skip:0 };\n",
    'SimLab.issueBothSides canonicalization'
  );
}

if (!sim.includes('driverTime: Number(driverTime.toFixed(3))')) {
  sim = replaceOnce(
    sim,
    '    collectResult(o, meta, aiRefreshCount, wallMs) {\n      const truncated = !State.battle.ended && State.simTime >= o.maxTime - o.dt * 0.51;\n',
    '    collectResult(o, meta, aiRefreshCount, wallMs, driverTime = State.simTime) {\n      const truncated = !State.battle.ended && driverTime >= o.maxTime - 1e-9;\n',
    'SimLab.collectResult signature'
  );

  sim = replaceOnce(
    sim,
    '        simTime: Number(State.simTime.toFixed(3)),\n        wallMs: Number(wallMs.toFixed(1)),\n',
    '        simTime: Number(State.simTime.toFixed(3)),\n        driverTime: Number(driverTime.toFixed(3)),\n        fixedDt: Number((CFG.SIM_FIXED_DT || o.dt).toFixed(9)),\n        wallMs: Number(wallMs.toFixed(1)),\n',
    'SimLab fixed timestep result metadata'
  );
}

if (!sim.includes('let driverTime = 0;')) {
  const runLoopRegex = /        const meta = this\.setupBattle\(o\);\n        let nextAI = 0;\n        let aiRefreshCount = 0;\n\n        this\.issueBothSides\(\);\n        aiRefreshCount\+\+;\n        nextAI = o\.aiRefresh;\n\n        while \(!State\.battle\.ended && State\.simTime \+ 1e-9 < o\.maxTime\) \{\n          const dt = Math\.min\(o\.dt, o\.maxTime - State\.simTime\);\n          State\.simTime \+= dt;\n\n          if \(State\.simTime \+ 1e-9 >= nextAI\) \{\n            this\.issueBothSides\(\);\n            aiRefreshCount\+\+;\n            while \(nextAI <= State\.simTime \+ 1e-9\) nextAI \+= o\.aiRefresh;\n          \}\n\n          Simulation\.update\(dt\);\n        \}\n\n        const result = this\.collectResult\(o, meta, aiRefreshCount, performance\.now\(\) - wallStart\);/;

  const runLoopReplacement = `        const meta = this.setupBattle(o);\n        let nextAI = o.aiRefresh;\n        let aiRefreshCount = 0;\n        let driverTime = 0;\n\n        this.issueBothSides();\n        aiRefreshCount++;\n\n        const previousPreStepHook = Simulation.preStepHook || null;\n        Simulation.setPreStepHook?.(() => {\n          if (State.simTime + 1e-9 < nextAI) return;\n          this.issueBothSides();\n          aiRefreshCount++;\n          while (nextAI <= State.simTime + 1e-9) nextAI += o.aiRefresh;\n        });\n\n        try {\n          while (!State.battle.ended && driverTime + 1e-9 < o.maxTime) {\n            const dt = Math.min(o.dt, o.maxTime - driverTime);\n            driverTime += dt;\n            Simulation.advance(dt);\n          }\n        } finally {\n          Simulation.setPreStepHook?.(previousPreStepHook);\n        }\n\n        const result = this.collectResult(o, meta, aiRefreshCount, performance.now() - wallStart, driverTime);`;

  sim = replaceRegexOnce(sim, runLoopRegex, runLoopReplacement, 'SimLab driver loop');
}

sim = sim.replace(
  "        note: 'Il motore usa dt fisso; il loop gira non throttled alla massima velocità CPU. speedFactor misura il rapporto rispetto al realtime.'",
  "        note: 'La fisica usa CFG.SIM_FIXED_DT fisso; option dt controlla solo la cadenza del driver headless. Il loop gira non throttled alla massima velocità CPU.'"
);

fs.writeFileSync(htmlPath, html);
fs.writeFileSync(simPath, sim);
console.log('P0 deterministic core patch applied successfully.');
