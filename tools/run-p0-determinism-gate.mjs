import fs from 'node:fs';
import { chromium } from 'playwright-core';

const executablePath = process.env.CHROME_BIN || '/usr/bin/google-chrome';
const url = process.env.BRANCH_URL || 'http://127.0.0.1:8001/COFFEE_BATTLES.html';
const seed = Number(process.env.BASELINE_SEED || 1);
const points = Number(process.env.BASELINE_POINTS || 1000);
const maxTime = Number(process.env.BASELINE_MAX_TIME || 600);

const scenarios = [
  { key:'20hz', dt:0.05, reverseUnits:false },
  { key:'20hz-reverse', dt:0.05, reverseUnits:true },
  { key:'30hz', dt:1/30, reverseUnits:false },
  { key:'30hz-reverse', dt:1/30, reverseUnits:true },
  { key:'60hz', dt:1/60, reverseUnits:false },
  { key:'60hz-reverse', dt:1/60, reverseUnits:true }
];

function fingerprint(run) {
  return {
    seed: run.seed,
    winner: run.winner,
    result: run.result,
    endReason: run.endReason,
    ended: run.ended,
    timedOut: run.timedOut,
    truncated: run.truncated,
    stuck: run.stuck,
    simTime: run.simTime,
    collapse: run.collapse,
    roles: run.roles,
    biome: run.biome,
    coast: run.coast,
    requestedComposition: run.requestedComposition,
    doctrine: run.doctrine,
    blue: {
      alive: run.blue?.alive,
      destroyed: run.blue?.destroyed,
      routedOut: run.blue?.routedOut,
      routing: run.blue?.routing,
      hp: run.blue?.hp,
      brain: run.blue?.brain,
      energy: run.blue?.energy,
      damageV: run.blue?.damageV,
      damageB: run.blue?.damageB,
      kills: run.blue?.kills,
      routsOut: run.blue?.routsOut,
      pointsLost: run.blue?.pointsLost,
      types: run.blue?.types
    },
    red: {
      alive: run.red?.alive,
      destroyed: run.red?.destroyed,
      routedOut: run.red?.routedOut,
      routing: run.red?.routing,
      hp: run.red?.hp,
      brain: run.red?.brain,
      energy: run.red?.energy,
      damageV: run.red?.damageV,
      damageB: run.red?.damageB,
      kills: run.red?.kills,
      routsOut: run.red?.routsOut,
      pointsLost: run.red?.pointsLost,
      types: run.red?.types
    }
  };
}

const browser = await chromium.launch({ headless:true, executablePath, args:['--no-sandbox'] });
const page = await browser.newPage();
const results = {};
try {
  await page.goto(url, { waitUntil:'domcontentloaded', timeout:60000 });
  await page.addScriptTag({ url:new URL('/sim-lab.js', url).href });
  await page.waitForFunction(() => !!window.__COFFEE_BATTLES_SIM__, null, { timeout:30000 });

  for (const s of scenarios) {
    console.log(`RUN ${s.key}`);
    const run = await page.evaluate(({ seed, points, maxTime, dt, reverseUnits }) =>
      window.__COFFEE_BATTLES_SIM__.runOne({ seed, points, maxTime, dt, reverseUnits, silent:true }),
      { seed, points, maxTime, ...s }
    );
    results[s.key] = run;
    console.log(`DONE ${s.key}: ${run.winner || 'unresolved'} @ ${run.simTime}s`);
  }
} finally {
  await page.close();
  await browser.close();
}

const referenceKey = '30hz';
const reference = fingerprint(results[referenceKey]);
const comparisons = {};
let mismatches = 0;
for (const s of scenarios) {
  const fp = fingerprint(results[s.key]);
  const exact = JSON.stringify(fp) === JSON.stringify(reference);
  comparisons[s.key] = { exact, fingerprint: fp };
  if (!exact) mismatches++;
}

const out = {
  generatedAt: new Date().toISOString(),
  branchCommit: process.env.BRANCH_COMMIT || null,
  fixedDt: results[referenceKey]?.fixedDt ?? null,
  seed,
  points,
  maxTime,
  referenceKey,
  mismatches,
  comparisons,
  results
};
fs.mkdirSync('results', { recursive:true });
fs.writeFileSync('results/p0-determinism-gate.json', JSON.stringify(out, null, 2));

let md = '# P0 determinism gate\n\n';
md += `- Branch: \`${out.branchCommit}\`\n`;
md += `- Seed: **${seed}** · Points: **${points}** · maxTime: **${maxTime}s**\n`;
md += `- Reference: **${referenceKey}**\n`;
md += `- Mismatches: **${mismatches}/6**\n\n`;
md += '| Scenario | Winner | Sim time | Exact vs 30 Hz |\n|---|---|---:|---:|\n';
for (const s of scenarios) {
  const r = results[s.key];
  md += `| ${s.key} | ${r.winner || 'unresolved'} | ${r.simTime} | ${comparisons[s.key].exact ? 'YES' : 'NO'} |\n`;
}
fs.writeFileSync('results/p0-determinism-gate.md', md);
console.log('\n' + md);

if (mismatches > 0) {
  console.error(`P0 determinism gate failed: ${mismatches} scenario(s) diverged.`);
  process.exitCode = 2;
}
