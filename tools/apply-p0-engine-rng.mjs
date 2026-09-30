import fs from 'node:fs';

const enginePath = 'COFFEE_BATTLES.html';
const simPath = 'sim-lab.js';

let html = fs.readFileSync(enginePath, 'utf8');
let sim = fs.readFileSync(simPath, 'utf8');

if (!html.includes('const Random = {')) {
  const anchor = '\n  const worldPx = () => ({';
  if (!html.includes(anchor)) throw new Error('Random insertion anchor not found');

  const randomBlock = `
  // ============================================================
  // GAMEPLAY RNG — explicit runtime-owned random source
  // ============================================================
  const Random = {
    _systemSource: Math.random.bind(Math),
    _source: null,
    _seed: null,

    next() {
      return (this._source || this._systemSource)();
    },

    create(seed = 1) {
      let a = (Number(seed) || 1) >>> 0;
      return function mulberry32() {
        a |= 0;
        a = a + 0x6D2B79F5 | 0;
        let t = Math.imul(a ^ a >>> 15, 1 | a);
        t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
        return ((t ^ t >>> 14) >>> 0) / 4294967296;
      };
    },

    setSeed(seed = 1) {
      const normalized = (Number(seed) || 1) >>> 0;
      this._seed = normalized;
      this._source = this.create(normalized);
      return normalized;
    },

    useSystem() {
      this._seed = null;
      this._source = this._systemSource;
    },

    capture() {
      return { source: this._source, seed: this._seed };
    },

    restore(snapshot = null) {
      if (snapshot && typeof snapshot.source === 'function') {
        this._source = snapshot.source;
        this._seed = snapshot.seed ?? null;
      } else {
        this.useSystem();
      }
    },

    get seed() {
      return this._seed;
    }
  };
  Random.useSystem();
`;

  html = html.replace(anchor, `\n${randomBlock}${anchor}`);
}

const randomCallCount = (html.match(/Math\.random\(\)/g) || []).length;
if (randomCallCount < 10) {
  throw new Error(`Expected gameplay Math.random() calls before migration; found ${randomCallCount}`);
}
html = html.replace(/Math\.random\(\)/g, 'Random.next()');
if (html.includes('Math.random()')) throw new Error('Gameplay Math.random() call remains in engine');

const debugOld = 'window.__COFFEE_BATTLES_DEBUG__ = { State, Units, Intel,';
const debugNew = 'window.__COFFEE_BATTLES_DEBUG__ = { State, Random, Units, Intel,';
if (!html.includes(debugNew)) {
  if (!html.includes(debugOld)) throw new Error('Debug API anchor not found');
  html = html.replace(debugOld, debugNew);
}

const destructureOld = `  const {\n    State, Units, ArmyAI, Simulation, CFG,\n    Battle, BattleSetup, Deployment, DoctrineEngine\n  } = D;`;
const destructureNew = `  const {\n    State, Random, Units, ArmyAI, Simulation, CFG,\n    Battle, BattleSetup, Deployment, DoctrineEngine\n  } = D;`;
if (!sim.includes(destructureNew)) {
  if (!sim.includes(destructureOld)) throw new Error('SimLab debug destructuring anchor not found');
  sim = sim.replace(destructureOld, destructureNew);
}

sim = sim.replace("version: '0.2'", "version: '0.3'");

const rngMethod = /\n    rng\(seed = 1\) \{[\s\S]*?\n    \},\n\n    normalizeOptions/;
if (rngMethod.test(sim)) {
  sim = sim.replace(rngMethod, '\n    normalizeOptions');
}

if (sim.includes('random: Math.random,')) {
  sim = sim.replace('random: Math.random,', 'randomState: Random.capture(),');
}
if (sim.includes('Math.random = this.rng(o.seed);')) {
  sim = sim.replace('Math.random = this.rng(o.seed);', 'Random.setSeed(o.seed);');
}
if (sim.includes('Math.random = saved.random;')) {
  sim = sim.replace('Math.random = saved.random;', 'Random.restore(saved.randomState);');
}

if (sim.includes('Math.random =')) throw new Error('Global Math.random monkey-patch remains in SimLab');
if (sim.includes('this.rng(')) throw new Error('Legacy SimLab RNG helper still used');
if (!sim.includes('Random.setSeed(o.seed);')) throw new Error('SimLab engine RNG seed injection missing');
if (!sim.includes('Random.restore(saved.randomState);')) throw new Error('SimLab engine RNG restore missing');

fs.writeFileSync(enginePath, html);
fs.writeFileSync(simPath, sim);

console.log(JSON.stringify({
  migratedGameplayRandomCalls: randomCallCount,
  engineHasExplicitRandom: html.includes('const Random = {'),
  simLabUsesEngineRandom: sim.includes('Random.setSeed(o.seed);'),
  simLabGlobalRandomPatch: sim.includes('Math.random =')
}, null, 2));
