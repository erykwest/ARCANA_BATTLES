(() => {
  'use strict';

  const DEFAULT_DTS = Object.freeze([0.05, 1 / 30, 1 / 60]);

  function round(n, digits = 4) {
    if (!Number.isFinite(n)) return null;
    const p = 10 ** digits;
    return Math.round(n * p) / p;
  }

  function rate(n, d) {
    return d > 0 ? round(n / d, 4) : 0;
  }

  function compactRun(r) {
    return {
      seed: r.seed,
      winner: r.winner,
      result: r.result,
      simTime: r.simTime,
      timedOut: !!r.timedOut,
      truncated: !!r.truncated,
      stuck: !!r.stuck,
      roles: r.roles ? { ...r.roles } : null,
      collapse: r.collapse ? { ...r.collapse } : null
    };
  }

  function compactBatch(batch) {
    const s = batch.summary;
    return {
      requested: batch.requested,
      completed: batch.completed,
      stopped: batch.stopped,
      options: {
        points: batch.options.points,
        seed: batch.options.seed,
        biome: batch.options.biome,
        role: batch.options.role,
        coast: batch.options.coast,
        terrain: batch.options.terrain,
        mirrorComposition: batch.options.mirrorComposition,
        dt: batch.options.dt,
        maxTime: batch.options.maxTime,
        aiRefresh: batch.options.aiRefresh,
        reverseUnits: batch.options.reverseUnits,
        deployOrder: batch.options.deployOrder
      },
      summary: {
        total: s.total,
        wins: { ...s.wins },
        winRates: {
          blue: rate(s.wins.blue, s.total),
          red: rate(s.wins.red, s.total),
          draw: rate(s.wins.draw, s.total),
          unresolved: rate(s.wins.unresolved, s.total)
        },
        timedOut: s.timedOut,
        truncated: s.truncated,
        stuck: s.stuck,
        collapse: { ...s.collapse },
        meanSimTime: s.meanSimTime,
        medianSimTime: s.medianSimTime,
        meanWallMs: s.meanWallMs,
        meanSpeedFactor: s.meanSpeedFactor,
        biomes: s.biomes,
        unitUsage: s.unitUsage,
        doctrines: s.doctrines
      },
      runs: batch.runs.map(compactRun)
    };
  }

  function comparePaired(normal, reversed) {
    if (!normal || !reversed) return null;
    const n = Math.min(normal.runs.length, reversed.runs.length);
    let changedWinner = 0;
    let changedStuck = 0;
    let changedTimeout = 0;
    let sameWinner = 0;
    const changedSeeds = [];

    for (let i = 0; i < n; i++) {
      const a = normal.runs[i];
      const b = reversed.runs[i];
      if (a.seed !== b.seed) continue;
      if (a.winner === b.winner) sameWinner++;
      else {
        changedWinner++;
        if (changedSeeds.length < 50) {
          changedSeeds.push({ seed: a.seed, normal: a.winner, reversed: b.winner });
        }
      }
      if (!!a.stuck !== !!b.stuck) changedStuck++;
      if (!!a.timedOut !== !!b.timedOut) changedTimeout++;
    }

    const blueNormal = normal.summary.winRates.blue;
    const blueReversed = reversed.summary.winRates.blue;

    return {
      pairedRuns: n,
      sameWinner,
      changedWinner,
      changedWinnerRate: rate(changedWinner, n),
      blueWinRateNormal: blueNormal,
      blueWinRateReversed: blueReversed,
      blueWinRateDelta: round(blueReversed - blueNormal, 4),
      changedStuck,
      changedTimeout,
      changedSeeds
    };
  }

  function compareDtCases(cases) {
    const out = [];
    if (!cases.length) return out;
    const ref = cases[0];
    for (const c of cases.slice(1)) {
      out.push({
        referenceDt: ref.dt,
        candidateDt: c.dt,
        blueWinRateDelta: round(c.normal.summary.winRates.blue - ref.normal.summary.winRates.blue, 4),
        redWinRateDelta: round(c.normal.summary.winRates.red - ref.normal.summary.winRates.red, 4),
        drawRateDelta: round(c.normal.summary.winRates.draw - ref.normal.summary.winRates.draw, 4),
        unresolvedRateDelta: round(c.normal.summary.winRates.unresolved - ref.normal.summary.winRates.unresolved, 4),
        meanSimTimeDelta: round(c.normal.summary.meanSimTime - ref.normal.summary.meanSimTime, 3),
        medianSimTimeDelta: round(c.normal.summary.medianSimTime - ref.normal.summary.medianSimTime, 3),
        stuckDelta: c.normal.summary.stuck - ref.normal.summary.stuck,
        timedOutDelta: c.normal.summary.timedOut - ref.normal.summary.timedOut
      });
    }
    return out;
  }

  const BaselineMatrix = {
    version: '0.1',
    running: false,
    lastReport: null,

    async ensureSimLab() {
      if (!window.__COFFEE_BATTLES_SIM__) await import('/sim-lab.js');
      const sim = window.__COFFEE_BATTLES_SIM__;
      if (!sim) throw new Error('SIM Lab non disponibile. Apri prima /play.');
      return sim;
    },

    async run(options = {}) {
      if (this.running) throw new Error('Baseline matrix già in esecuzione.');
      this.running = true;

      try {
        const sim = await this.ensureSimLab();
        const count = Math.max(1, Math.floor(Number(options.count) || 300));
        const seed = (Number(options.seed) || 1) >>> 0;
        const dts = (Array.isArray(options.dts) && options.dts.length ? options.dts : DEFAULT_DTS)
          .map(Number)
          .filter(dt => Number.isFinite(dt) && dt > 0);
        const reverseCheck = options.reverseCheck !== false;

        const common = {
          points: options.points ?? 1000,
          seed,
          biome: options.biome ?? 'random',
          role: options.role ?? 'random',
          coast: options.coast ?? 'random',
          terrain: options.terrain !== false,
          mirrorComposition: !!options.mirrorComposition,
          maxTime: options.maxTime,
          aiRefresh: options.aiRefresh,
          deployOrder: options.deployOrder ?? 'alternate',
          silent: options.silent !== false,
          yieldEvery: options.yieldEvery ?? 1
        };

        Object.keys(common).forEach(k => common[k] === undefined && delete common[k]);

        const cases = [];
        for (const dt of dts) {
          console.info(`[COFFEE BATTLES] baseline dt=${dt} normal · ${count} run`);
          const normalRaw = await sim.runBatch(count, { ...common, dt, reverseUnits: false });
          const normal = compactBatch(normalRaw);

          let reversed = null;
          if (reverseCheck) {
            console.info(`[COFFEE BATTLES] baseline dt=${dt} reverse-order · ${count} run`);
            const reversedRaw = await sim.runBatch(count, { ...common, dt, reverseUnits: true });
            reversed = compactBatch(reversedRaw);
          }

          cases.push({
            dt,
            hz: round(1 / dt, 3),
            normal,
            reversed,
            orderBias: comparePaired(normal, reversed)
          });
        }

        const report = {
          tool: 'COFFEE BATTLES baseline-matrix',
          toolVersion: this.version,
          simLabVersion: sim.version,
          generatedAt: new Date().toISOString(),
          pageTitle: document.title,
          location: location.pathname,
          userAgent: navigator.userAgent,
          config: {
            count,
            seed,
            dts,
            reverseCheck,
            common
          },
          cases,
          timestepComparison: compareDtCases(cases)
        };

        this.lastReport = report;
        console.info('[COFFEE BATTLES] baseline matrix completata', report);
        return report;
      } finally {
        this.running = false;
      }
    },

    exportJSON(report = this.lastReport) {
      if (!report) throw new Error('Nessun report baseline disponibile.');
      return JSON.stringify(report, null, 2);
    },

    downloadJSON(filename = null, report = this.lastReport) {
      if (!report) throw new Error('Nessun report baseline disponibile.');
      const stamp = new Date().toISOString().replace(/[:.]/g, '-');
      const name = filename || `coffee-battles-baseline-${stamp}.json`;
      const blob = new Blob([this.exportJSON(report)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = name;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 0);
      return name;
    },

    help() {
      return {
        load: "await import('/tools/baseline-matrix.js')",
        run300: "await __COFFEE_BATTLES_BASELINE__.run({count:300, seed:1})",
        run500: "await __COFFEE_BATTLES_BASELINE__.run({count:500, seed:1})",
        export: "__COFFEE_BATTLES_BASELINE__.exportJSON()",
        download: "__COFFEE_BATTLES_BASELINE__.downloadJSON()",
        dts: DEFAULT_DTS
      };
    }
  };

  window.__COFFEE_BATTLES_BASELINE__ = BaselineMatrix;
  console.info(`[COFFEE BATTLES] Baseline Matrix v${BaselineMatrix.version} ready`, BaselineMatrix.help());
})();
