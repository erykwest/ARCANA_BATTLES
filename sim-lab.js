(() => {
  'use strict';

  const D = window.__COFFEE_BATTLES_DEBUG__;
  if (!D) throw new Error('COFFEE BATTLES debug API non disponibile.');

  const {
    State, Units, ArmyAI, Simulation, CFG,
    Battle, BattleSetup, Deployment, DoctrineEngine
  } = D;

  const BIOMES = new Set(['random','plains','hills','valley','river','forest','mountains','village']);
  const ROLES = new Set(['random','attack','defend']);
  const DEPLOY_ORDERS = new Set(['alternate','blue-first','red-first']);
  const COAST_MODES = new Set(['random','none','gulf','landing']);

  const SimLab = {
    version: '0.2',
    running: false,
    batchRunning: false,
    stopRequested: false,
    lastResult: null,
    lastBatch: null,
    _endLead: null,

    DEFAULTS: Object.freeze({
      points: 1000,
      seed: 1,
      biome: 'random',
      role: 'random',
      coast: 'random',
      terrain: true,
      mirrorComposition: false,
      dt: 0.05,
      maxTime: CFG.BATTLE_TIME_LIMIT_S,
      aiRefresh: CFG.ARMY_AI_REFRESH_S,
      reverseUnits: false,
      deployOrder: 'alternate',
      silent: true,
      yieldEvery: 1
    }),

    rng(seed = 1) {
      let a = (Number(seed) || 1) >>> 0;
      return function mulberry32() {
        a |= 0;
        a = a + 0x6D2B79F5 | 0;
        let t = Math.imul(a ^ a >>> 15, 1 | a);
        t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
        return ((t ^ t >>> 14) >>> 0) / 4294967296;
      };
    },

    normalizeOptions(input = {}) {
      const o = { ...this.DEFAULTS, ...input };
      o.points = BattleSetup.sanitizePoints(o.points);
      o.seed = (Number(o.seed) || 1) >>> 0;
      o.dt = Math.max(0.005, Math.min(0.10, Number(o.dt) || 0.05));
      o.maxTime = Math.max(o.dt, Math.min(3600, Number(o.maxTime) || CFG.BATTLE_TIME_LIMIT_S));
      o.aiRefresh = Math.max(o.dt, Number(o.aiRefresh) || CFG.ARMY_AI_REFRESH_S);
      o.yieldEvery = Math.max(1, Math.floor(Number(o.yieldEvery) || 1));
      if (!BIOMES.has(o.biome)) o.biome = 'random';
      if (!ROLES.has(o.role)) o.role = 'random';
      if (!DEPLOY_ORDERS.has(o.deployOrder)) o.deployOrder = 'alternate';
      if (!COAST_MODES.has(o.coast)) o.coast = 'random';
      o.terrain = o.terrain !== false;
      o.mirrorComposition = !!o.mirrorComposition;
      o.reverseUnits = !!o.reverseUnits;
      o.silent = o.silent !== false;
      return o;
    },

    beginRuntime(o) {
      const logEl = document.getElementById('log');
      const saved = {
        random: Math.random,
        updateVictoryBar: Battle.updateVictoryBar,
        showResult: Battle.showResult,
        armyEnabled: State.armyAI.enabled,
        timeScale: State.timeScale,
        logEl,
        logShadowed: false
      };

      Math.random = this.rng(o.seed);
      this._endLead = null;

      if (o.silent && logEl) {
        try {
          Object.defineProperty(logEl, 'textContent', {
            configurable: true,
            get: () => '',
            set: () => {}
          });
          saved.logShadowed = true;
        } catch (_) {}
      }

      Battle.updateVictoryBar = () => {};
      Battle.showResult = (result, leadOverride = null) => {
        if (State.battle.ended) return;
        State.battle.ended = true;
        State.battle.active = false;
        State.battle.result = result;
        State.timeScale = 0;
        this._endLead = leadOverride || null;
      };

      State.armyAI.enabled = false;
      State.timeScale = 0;
      return saved;
    },

    endRuntime(saved) {
      Math.random = saved.random;
      Battle.updateVictoryBar = saved.updateVictoryBar;
      Battle.showResult = saved.showResult;
      State.armyAI.enabled = saved.armyEnabled;
      State.timeScale = 0;

      if (saved.logShadowed && saved.logEl) {
        try { delete saved.logEl.textContent; } catch (_) {}
      }
    },

    sideOrder(o) {
      if (o.deployOrder === 'blue-first') return ['blue','red'];
      if (o.deployOrder === 'red-first') return ['red','blue'];
      return o.seed % 2 ? ['blue','red'] : ['red','blue'];
    },

    setupBattle(o) {
      State.battleSetup.points = o.points;
      State.battleSetup.mode = 'auto';
      State.battleSetup.role = o.role;
      State.battleSetup.biome = o.biome;
      State.battleSetup.resolvedBiome = null;
      State.battleSetup.mirrorArmy = false;
      State.battleSetup.mirrorDeployment = false;
      State.battleSetup.configured = true;
      State.battleSetup.coastMode = o.coast === 'random' ? null : o.coast;
      State.battleSetup.coast = null;

      State.doctrine.roles = { blue:null, red:null };
      State.doctrine.selected = { blue:null, red:null };
      State.doctrine.scores = { blue:[], red:[] };
      State.doctrine.terrain = { blue:null, red:null };
      State.doctrine.compositions = { blue:[], red:[] };

      BattleSetup.resolveRoles();

      // Usa il vero setup del gioco per inizializzare mappa, stato e contatori.
      Deployment.start();
      State.deployment.active = false;
      document.body.classList.remove('deployment-active');
      if (!o.terrain) {
        State.terrain = [];
        State.battleSetup.coast = null;
      }

      const order = this.sideOrder(o);
      const comps = {};
      for (const side of order) {
        if (o.mirrorComposition && comps[this.opposite(side)]) {
          const src = comps[this.opposite(side)];
          comps[side] = { ...src, types:[...src.types] };
        } else {
          comps[side] = DoctrineEngine.generateComposition(o.points);
        }
      }
      if (o.mirrorComposition && !comps.blue) comps.blue = { ...comps.red, types:[...comps.red.types] };
      if (o.mirrorComposition && !comps.red) comps.red = { ...comps.blue, types:[...comps.blue.types] };

      State.doctrine.compositions.blue = [...comps.blue.types];
      State.doctrine.compositions.red = [...comps.red.types];

      const docs = {};
      for (const side of order) {
        docs[side] = DoctrineEngine.chooseDoctrine(
          comps[side].types,
          side,
          State.doctrine.roles[side]
        );
      }

      for (const side of order) {
        DoctrineEngine.deployComposition(
          side,
          comps[side].types,
          docs[side],
          State.doctrine.roles[side]
        );
      }

      Deployment.recount();
      State.deployment.snapshot = null;
      if (o.reverseUnits) State.units.reverse();

      Battle.reset(true);
      State.battle.playerSide = 'blue';
      State.battle.active = true;
      State.battle.ended = false;
      State.battle.result = null;
      State.armyAI.enabled = false;
      State.timeScale = 0;

      return {
        order,
        requestedComposition: {
          blue: [...comps.blue.types],
          red: [...comps.red.types]
        }
      };
    },

    opposite(side) { return side === 'blue' ? 'red' : 'blue'; },

    issueBothSides() {
      Simulation.canonicalizeUnitOrder?.();
      const report = { new:0, same:0, none:0, skip:0 };
      for (const u of State.units) {
        if (!u.status.alive) continue;
        const key = ArmyAI.issueAttackNearest(u);
        report[key] = (report[key] || 0) + 1;
      }
      return report;
    },

    typeCounts(side) {
      const out = {};
      for (const u of State.units) {
        if (u.side !== side) continue;
        out[u.type] = (out[u.type] || 0) + 1;
      }
      return out;
    },

    sideStats(side) {
      const units = State.units.filter(u => u.side === side);
      const alive = units.filter(u => u.status.alive);
      const sum = fn => units.reduce((n,u) => n + (Number(fn(u)) || 0), 0);
      return {
        initial: units.length,
        alive: alive.length,
        destroyed: units.filter(u => u.status.exitReason === 'destroyed').length,
        routedOut: units.filter(u => u.status.exitReason === 'rout').length,
        routing: alive.filter(u => u.status.routing).length,
        hp: Number(sum(u => u.stats.hp).toFixed(2)),
        brain: Number(sum(u => u.stats.brain).toFixed(2)),
        energy: Number(sum(u => u.stats.energy).toFixed(2)),
        damageV: Number(sum(u => u.battleRecord?.damageV).toFixed(2)),
        damageB: Number(sum(u => u.battleRecord?.damageB).toFixed(2)),
        kills: sum(u => u.battleRecord?.kills),
        routsOut: sum(u => u.battleRecord?.routsOut),
        pointsInitial: Battle.initialPoints(side),
        pointsLost: Battle.lostPoints(side),
        types: this.typeCounts(side)
      };
    },

    doctrineSnapshot(side) {
      const d = State.doctrine.selected[side];
      if (!d) return null;
      return {
        id: d.id,
        label: d.label,
        total: Number((d.total || 0).toFixed(3)),
        army: Number((d.army || 0).toFixed(3)),
        terrain: Number((d.terrain || 0).toFixed(3)),
        role: Number((d.role || 0).toFixed(3))
      };
    },

    winner() {
      if (!State.battle.ended) return null;
      if (State.battle.result === 'draw') return 'draw';
      if (State.battle.result === 'victory') return State.battle.playerSide;
      if (State.battle.result === 'defeat') return this.opposite(State.battle.playerSide);
      return null;
    },

    collectResult(o, meta, aiRefreshCount, wallMs, driverTime = State.simTime) {
      const truncated = !State.battle.ended && driverTime >= o.maxTime - 1e-9;
      const timedOut = /Tempo massimo/i.test(this._endLead || '');
      return {
        simVersion: this.version,
        seed: o.seed,
        points: o.points,
        biome: State.battleSetup.resolvedBiome || o.biome,
        coast: State.battleSetup.coast || null,
        terrain: o.terrain,
        roles: { ...State.doctrine.roles },
        winner: this.winner(),
        result: State.battle.result,
        endReason: this._endLead,
        ended: State.battle.ended,
        timedOut,
        truncated,
        stuck: truncated && o.maxTime >= CFG.BATTLE_TIME_LIMIT_S,
        simTime: Number(State.simTime.toFixed(3)),
        driverTime: Number(driverTime.toFixed(3)),
        fixedDt: Number((CFG.SIM_FIXED_DT || o.dt).toFixed(9)),
        wallMs: Number(wallMs.toFixed(1)),
        speedFactor: wallMs > 0 ? Number((State.simTime / (wallMs / 1000)).toFixed(1)) : null,
        collapse: { ...State.battle.armyCollapse },
        aiRefreshCount,
        deployOrder: [...meta.order],
        reverseUnits: o.reverseUnits,
        requestedComposition: meta.requestedComposition,
        doctrine: {
          blue: this.doctrineSnapshot('blue'),
          red: this.doctrineSnapshot('red')
        },
        blue: this.sideStats('blue'),
        red: this.sideStats('red')
      };
    },

    _runOne(input = {}) {
      if (this.running) throw new Error('SIM già in esecuzione.');
      const o = this.normalizeOptions(input);
      const saved = this.beginRuntime(o);
      const wallStart = performance.now();
      this.running = true;

      try {
        const meta = this.setupBattle(o);
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

        const result = this.collectResult(o, meta, aiRefreshCount, performance.now() - wallStart, driverTime);
        this.lastResult = result;
        return result;
      } finally {
        this.running = false;
        this.endRuntime(saved);
      }
    },

    runOne(options = {}) {
      if (this.batchRunning) throw new Error('Batch SIM già in esecuzione.');
      return this._runOne(options);
    },

    median(values) {
      if (!values.length) return 0;
      const s = [...values].sort((a,b) => a-b);
      const m = Math.floor(s.length / 2);
      return s.length % 2 ? s[m] : (s[m-1] + s[m]) / 2;
    },

    summarize(runs) {
      const s = {
        total: runs.length,
        wins: { blue:0, red:0, draw:0, unresolved:0 },
        timedOut: 0,
        truncated: 0,
        stuck: 0,
        collapse: { blue:0, red:0, both:0 },
        meanSimTime: 0,
        medianSimTime: 0,
        meanWallMs: 0,
        meanSpeedFactor: 0,
        biomes: {},
        unitUsage: { blue:{}, red:{} },
        doctrines: { blue:{}, red:{} }
      };

      for (const r of runs) {
        if (r.winner === 'blue') s.wins.blue++;
        else if (r.winner === 'red') s.wins.red++;
        else if (r.winner === 'draw') s.wins.draw++;
        else s.wins.unresolved++;
        if (r.timedOut) s.timedOut++;
        if (r.truncated) s.truncated++;
        if (r.stuck) s.stuck++;
        if (r.collapse.blue) s.collapse.blue++;
        if (r.collapse.red) s.collapse.red++;
        if (r.collapse.blue && r.collapse.red) s.collapse.both++;

        const b = s.biomes[r.biome] || (s.biomes[r.biome] = { n:0, blue:0, red:0, draw:0, unresolved:0 });
        b.n++;
        if (r.winner === 'blue') b.blue++;
        else if (r.winner === 'red') b.red++;
        else if (r.winner === 'draw') b.draw++;
        else b.unresolved++;

        for (const side of ['blue','red']) {
          for (const [type,count] of Object.entries(r[side].types || {})) {
            const u = s.unitUsage[side][type] || (s.unitUsage[side][type] = { fielded:0, winningArmy:0 });
            u.fielded += count;
            if (r.winner === side) u.winningArmy += count;
          }
          const d = r.doctrine?.[side]?.id;
          if (d) {
            const x = s.doctrines[side][d] || (s.doctrines[side][d] = { used:0, wins:0 });
            x.used++;
            if (r.winner === side) x.wins++;
          }
        }
      }

      if (runs.length) {
        s.meanSimTime = Number((runs.reduce((n,r) => n + r.simTime, 0) / runs.length).toFixed(2));
        s.medianSimTime = Number(this.median(runs.map(r => r.simTime)).toFixed(2));
        s.meanWallMs = Number((runs.reduce((n,r) => n + r.wallMs, 0) / runs.length).toFixed(1));
        const speeds = runs.map(r => r.speedFactor).filter(Number.isFinite);
        s.meanSpeedFactor = speeds.length
          ? Number((speeds.reduce((a,b) => a+b, 0) / speeds.length).toFixed(1))
          : 0;
      }
      return s;
    },

    async runBatch(count = 100, options = {}) {
      if (this.running || this.batchRunning) throw new Error('SIM già in esecuzione.');
      const n = Math.max(1, Math.floor(Number(count) || 1));
      const base = this.normalizeOptions(options);
      const runs = [];
      this.stopRequested = false;
      this.batchRunning = true;

      try {
        for (let i = 0; i < n; i++) {
          if (this.stopRequested) break;
          runs.push(this._runOne({ ...base, seed: (base.seed + i) >>> 0 }));
          if ((i + 1) % base.yieldEvery === 0) {
            await new Promise(resolve => setTimeout(resolve, 0));
          }
        }

        const batch = {
          requested: n,
          completed: runs.length,
          stopped: this.stopRequested,
          options: base,
          summary: this.summarize(runs),
          runs
        };
        this.lastBatch = batch;
        return batch;
      } finally {
        this.batchRunning = false;
        this.stopRequested = false;
      }
    },

    stop() {
      this.stopRequested = true;
      return true;
    },

    exportJSON(value = this.lastBatch || this.lastResult) {
      return JSON.stringify(value, null, 2);
    },

    help() {
      return {
        load: "await import('/sim-lab.js')",
        one: "__COFFEE_BATTLES_SIM__.runOne({points:1000, seed:1})",
        batch: "await __COFFEE_BATTLES_SIM__.runBatch(100, {points:1000, seed:1})",
        biasCheck: "await __COFFEE_BATTLES_SIM__.runBatch(100, {points:1000, seed:1, reverseUnits:true})",
        coreNoTerrain: "await __COFFEE_BATTLES_SIM__.runBatch(100, {points:1000, terrain:false})",
        stop: "__COFFEE_BATTLES_SIM__.stop()",
        export: "__COFFEE_BATTLES_SIM__.exportJSON()",
        note: 'La fisica usa CFG.SIM_FIXED_DT fisso; option dt controlla solo la cadenza del driver headless. Il loop gira non throttled alla massima velocità CPU.'
      };
    }
  };

  window.__COFFEE_BATTLES_SIM__ = SimLab;
  console.info(`[COFFEE BATTLES] SIM Lab v${SimLab.version} ready`, SimLab.help());
})();
