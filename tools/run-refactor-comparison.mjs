import fs from 'node:fs';
import { chromium } from 'playwright-core';

const count = Number(process.env.BASELINE_COUNT || 300);
const seed = Number(process.env.BASELINE_SEED || 1);
const points = Number(process.env.BASELINE_POINTS || 1000);
const executablePath = process.env.CHROME_BIN || '/usr/bin/google-chrome';
const targets = [
  { name: 'baseline', url: 'http://127.0.0.1:8000/COFFEE_BATTLES.html' },
  { name: 'branch', url: 'http://127.0.0.1:8001/COFFEE_BATTLES.html' }
];
const dts = [0.05, 1 / 30, 1 / 60];

function keyFor(dt, reverseUnits) {
  const hz = Math.round(1 / dt);
  return `${hz}hz${reverseUnits ? '-reverse' : ''}`;
}

function fingerprint(run) {
  return {
    seed: run.seed,
    winner: run.winner,
    result: run.result,
    ended: run.ended,
    timedOut: run.timedOut,
    truncated: run.truncated,
    stuck: run.stuck,
    simTime: run.simTime,
    collapse: run.collapse,
    roles: run.roles,
    biome: run.biome,
    blue: {
      pointsLost: run.blue?.pointsLost,
      hp: run.blue?.hp,
      brain: run.blue?.brain,
      energy: run.blue?.energy,
      kills: run.blue?.kills,
      routsOut: run.blue?.routsOut
    },
    red: {
      pointsLost: run.red?.pointsLost,
      hp: run.red?.hp,
      brain: run.red?.brain,
      energy: run.red?.energy,
      kills: run.red?.kills,
      routsOut: run.red?.routsOut
    }
  };
}

function diffSummaries(a, b) {
  const aw = a.summary.wins;
  const bw = b.summary.wins;
  return {
    blueWins: bw.blue - aw.blue,
    redWins: bw.red - aw.red,
    draws: bw.draw - aw.draw,
    unresolved: bw.unresolved - aw.unresolved,
    timedOut: b.summary.timedOut - a.summary.timedOut,
    truncated: b.summary.truncated - a.summary.truncated,
    stuck: b.summary.stuck - a.summary.stuck,
    meanSimTime: Number((b.summary.meanSimTime - a.summary.meanSimTime).toFixed(3)),
    medianSimTime: Number((b.summary.medianSimTime - a.summary.medianSimTime).toFixed(3))
  };
}

const browser = await chromium.launch({ headless: true, executablePath, args: ['--no-sandbox'] });
const all = {};
try {
  for (const target of targets) {
    const page = await browser.newPage();
    page.on('console', msg => {
      const text = msg.text();
      if (/SIM Lab|error|warning/i.test(text)) console.log(`[${target.name}] ${text}`);
    });
    await page.goto(target.url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.addScriptTag({ url: new URL('/sim-lab.js', target.url).href });
    await page.waitForFunction(() => !!window.__COFFEE_BATTLES_SIM__, null, { timeout: 30000 });

    all[target.name] = {};
    for (const dt of dts) {
      for (const reverseUnits of [false, true]) {
        const key = keyFor(dt, reverseUnits);
        console.log(`RUN ${target.name} ${key}: ${count} seeds`);
        const result = await page.evaluate(async ({ count, seed, points, dt, reverseUnits }) => {
          const sim = window.__COFFEE_BATTLES_SIM__;
          const batch = await sim.runBatch(count, {
            points,
            seed,
            dt,
            reverseUnits,
            silent: true,
            yieldEvery: 10
          });
          return {
            options: batch.options,
            summary: batch.summary,
            runs: batch.runs
          };
        }, { count, seed, points, dt, reverseUnits });
        all[target.name][key] = {
          options: result.options,
          summary: result.summary,
          fingerprints: result.runs.map(fingerprint)
        };
        console.log(`DONE ${target.name} ${key}:`, JSON.stringify(result.summary));
      }
    }
    await page.close();
  }
} finally {
  await browser.close();
}

const comparison = {};
let totalMismatches = 0;
for (const key of Object.keys(all.baseline)) {
  const base = all.baseline[key];
  const branch = all.branch[key];
  const mismatches = [];
  const n = Math.min(base.fingerprints.length, branch.fingerprints.length);
  for (let i = 0; i < n; i++) {
    if (JSON.stringify(base.fingerprints[i]) !== JSON.stringify(branch.fingerprints[i])) {
      mismatches.push({
        seed: base.fingerprints[i].seed,
        baseline: base.fingerprints[i],
        branch: branch.fingerprints[i]
      });
    }
  }
  totalMismatches += mismatches.length;
  comparison[key] = {
    summaryDelta: diffSummaries(base, branch),
    exactFingerprintMatches: n - mismatches.length,
    compared: n,
    mismatchCount: mismatches.length,
    mismatches: mismatches.slice(0, 25)
  };
}

const output = {
  generatedAt: new Date().toISOString(),
  countPerSeries: count,
  seedStart: seed,
  points,
  baselineCommit: process.env.BASELINE_COMMIT || null,
  branchCommit: process.env.BRANCH_COMMIT || null,
  totalRunsPerTarget: count * dts.length * 2,
  totalMismatches,
  all,
  comparison
};

fs.mkdirSync('results', { recursive: true });
fs.writeFileSync('results/refactor-p0-comparison.json', JSON.stringify(output, null, 2));

let md = `# P0 baseline vs branch comparison\n\n`;
md += `- Baseline: \`${output.baselineCommit}\`\n`;
md += `- Branch: \`${output.branchCommit}\`\n`;
md += `- Seeds per series: **${count}**\n`;
md += `- Series per target: **6** (20/30/60 Hz × normal/reverse)\n`;
md += `- Runs per target: **${output.totalRunsPerTarget}**\n`;
md += `- Fingerprint mismatches: **${totalMismatches}**\n\n`;
md += `| Series | Baseline B/R/D/U | Branch B/R/D/U | Δ mean time | stuck Δ | exact |\n`;
md += `|---|---:|---:|---:|---:|---:|\n`;
for (const key of Object.keys(comparison)) {
  const a = all.baseline[key].summary;
  const b = all.branch[key].summary;
  const c = comparison[key];
  const aw = a.wins, bw = b.wins;
  md += `| ${key} | ${aw.blue}/${aw.red}/${aw.draw}/${aw.unresolved} | ${bw.blue}/${bw.red}/${bw.draw}/${bw.unresolved} | ${c.summaryDelta.meanSimTime} s | ${c.summaryDelta.stuck} | ${c.exactFingerprintMatches}/${c.compared} |\n`;
}
fs.writeFileSync('results/refactor-p0-summary.md', md);
console.log('\n' + md);

if (totalMismatches > 0) {
  console.error(`Detected ${totalMismatches} baseline/branch fingerprint mismatches.`);
  process.exitCode = 2;
}
