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
  const matches = [...source.matchAll(new RegExp(regex.source, regex.flags.includes('g') ? regex.flags : regex.flags + 'g'))];
  if (matches.length !== 1) throw new Error(`Expected exactly one ${label} match, found ${matches.length}`);
  return source.replace(regex, replacement);
}

// ---------------------------------------------------------------------------
// COFFEE_BATTLES.html — physics cadence and stable iteration order
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

// Reset the accumulator wherever a fresh simulation timeline is created.
html = html.replace(
  /      State\.simTime = 0;\n      State\.combatClocks\.clear\(\);/g,
  '      State.simTime = 0;\n      State.simAccumulator = 0;\n      State.combatClocks.clear();'
);

if (!html.includes('canonicalizeUnitOrder()')) {
  const simulationRegex = /    update\(dt\) \{\n      ArmyAI\.update\(\);[\s\S]*?      Battle\.checkTimeLimit\(\);\n    \},\n\n    frame\(now\) \{\n      const realDt = Math\.min\(0\.05, \(now - State\.lastFrameAt\) \/ 1000\);\n      State\.lastFrameAt = now;\n      const dt = realDt \* State\.timeScale;\n      State\.simTime \+= dt;\n      if \(dt > 0\) Simulation\.update\(dt\);\n      UI\.updateSelectedInfo\(\);\n      Battle\.updateVictoryBar\(\);\n      Renderer\.draw\(\);\n      requestAnimationFrame\(Simulation\.frame\);\n    \}/;

  const replacement = `    preStepHook: null,

    canonicalizeUnitOrder() {
      State.units.sort((a, b) => {
        const ai = String(a?.id ?? '');
        const bi = String(b?.id ?? '');
        return ai < bi ? -1 : ai > bi ? 1 : 0;
      });
    },

    setPreStepHook(fn = null) {
      this.preStepHook = typeof fn === 'function' ? fn : null;
      return this.preStepHook;
    },

    fixedStep(dt = CFG.SIM_FIXED_DT) {
      // Every physics tick starts from the same canonical unit ordering.
      // This removes array insertion/reversal order from combat, collision,
      // targeting and resource resolution without changing unit identities.
      this.canonicalizeUnitOrder();
      if (this.preStepHook) this.preStepHook(dt);

      ArmyAI.update();
      State.units.forEach(Formations.update);
      State.units.forEach(AI.update.bind(AI));
      State.units.forEach(u => Movement.update(u, dt));
      State.units.forEach(u => Engagements.updateDefensiveState(u, dt));
      Collision.solveGlobal();
      State.units.forEach(u => Engagements.maintain(u, dt));
      Collision.solveGlobal();
      this.updateFreeContacts();
      Ranged.update(dt);

      for (const u of State.units) {
        if (u.status.chargeUntil && State.simTime >= u.status.chargeUntil) {
          u.status.chargeUntil = 0;
          u.motion.chargeMode = false;
          u.motion.chargeOverride = null;
          if (u.order.kind !== 'retreat' && !u.status.routing) {
            u.motion.moveMult = u.profile.marchMult;
          }
        }
        Resources.update(u, dt);
      }
      Combat.update(dt);
      Battle.checkArmyCollapse();
      Battle.checkOutcome();
      Battle.checkTimeLimit();
    },

    advance(elapsedDt) {
      const elapsed = Math.max(0, Number(elapsedDt) || 0);
      if (elapsed <= 0 || State.battle.ended) return 0;

      const step = CFG.SIM_FIXED_DT;
      State.simAccumulator += elapsed;
      let steps = 0;

      while (!State.battle.ended && State.simAccumulator + 1e-12 >= step) {
        State.simAccumulator -= step;
        if (Math.abs(State.simAccumulator) < 1e-12) State.simAccumulator = 0;
        State.simTime += step;
        this.fixedStep(step);
        steps++;
      }
      return steps;
    },

    // Compatibility entry point for debug tooling: update() now means
    // "advance elapsed time", never "run one variable physics step".
    update(dt) {
      return this.advance(dt);
    },

    frame(now) {
      const realDt = Math.min(0.05, (now - State.lastFrameAt) / 1000);
      State.lastFrameAt = now;
      const dt = realDt * State.timeScale;
      if (dt > 0) Simulation.advance(dt);
      UI.updateSelectedInfo();
      Battle.updateVictoryBar();
      Renderer.draw();
      requestAnimationFrame(Simulation.frame);
    }`;

  html = replaceRegexOnce(html, simulationRegex, replacement, 'Simulation.update/frame block');
}

// ---------------------------------------------------------------------------
// sim-lab.js — outer cadence is now a driver cadence, physics stays fixed.
// AI refresh is injected at fixed-step boundaries so 20/30/60 Hz drivers
// cannot shift the command timing.
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

  const runLoopReplacement = `        const meta = this.setupBattle(o);
        let nextAI = o.aiRefresh;
        let aiRefreshCount = 0;
        let driverTime = 0;

        this.issueBothSides();
        aiRefreshCount++;

        const previousPreStepHook = Simulation.preStepHook || null;
        Simulation.setPreStepHook?.(() => {
          if (State.simTime + 1e-9 < nextAI) return;
          this.issueBothSides();
          aiRefreshCount++;
          while (nextAI <= State.simTime + 1e-9) nextAI += o.aiRefresh;
        });

        try {
          while (!State.battle.ended && driverTime + 1e-9 < o.maxTime) {
            const dt = Math.min(o.dt, o.maxTime - driverTime);
            driverTime += dt;
            Simulation.advance(dt);
          }
        } finally {
          Simulation.setPreStepHook?.(previousPreStepHook);
        }

        const result = this.collectResult(o, meta, aiRefreshCount, performance.now() - wallStart, driverTime);`;

  sim = replaceRegexOnce(sim, runLoopRegex, runLoopReplacement, 'SimLab driver loop');
}

sim = sim.replace(
  "        note: 'Il motore usa dt fisso; il loop gira non throttled alla massima velocità CPU. speedFactor misura il rapporto rispetto al realtime.'",
  "        note: 'La fisica usa CFG.SIM_FIXED_DT fisso; option dt controlla solo la cadenza del driver headless. Il loop gira non throttled alla massima velocità CPU.'"
);

fs.writeFileSync(htmlPath, html);
fs.writeFileSync(simPath, sim);
console.log('P0 deterministic core patch applied successfully.');
