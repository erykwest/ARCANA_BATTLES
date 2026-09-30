import { chromium } from 'playwright-core';
import crypto from 'node:crypto';

const executablePath = process.env.CHROME_BIN || '/usr/bin/google-chrome';
const url = process.env.BRANCH_URL || 'http://127.0.0.1:8001/COFFEE_BATTLES.html';
const seed = Number(process.env.BASELINE_SEED || 1);
const expectedHash = process.env.EXPECTED_HASH || '';

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
      alive: run.blue?.alive, destroyed: run.blue?.destroyed, routedOut: run.blue?.routedOut,
      routing: run.blue?.routing, hp: run.blue?.hp, brain: run.blue?.brain, energy: run.blue?.energy,
      damageV: run.blue?.damageV, damageB: run.blue?.damageB, kills: run.blue?.kills,
      routsOut: run.blue?.routsOut, pointsLost: run.blue?.pointsLost, types: run.blue?.types
    },
    red: {
      alive: run.red?.alive, destroyed: run.red?.destroyed, routedOut: run.red?.routedOut,
      routing: run.red?.routing, hp: run.red?.hp, brain: run.red?.brain, energy: run.red?.energy,
      damageV: run.red?.damageV, damageB: run.red?.damageB, kills: run.red?.kills,
      routsOut: run.red?.routsOut, pointsLost: run.red?.pointsLost, types: run.red?.types
    }
  };
}

function stable(value) {
  if (Array.isArray(value)) return '[' + value.map(stable).join(',') + ']';
  if (value && typeof value === 'object') {
    return '{' + Object.keys(value).sort().map(k => JSON.stringify(k) + ':' + stable(value[k])).join(',') + '}';
  }
  return JSON.stringify(value);
}

const browser = await chromium.launch({ headless:true, executablePath, args:['--no-sandbox'] });
const page = await browser.newPage();
try {
  await page.goto(url, { waitUntil:'domcontentloaded', timeout:60000 });
  await page.addScriptTag({ url:new URL('/sim-lab.js', url).href });
  await page.waitForFunction(() => !!window.__COFFEE_BATTLES_SIM__, null, { timeout:30000 });
  const run = await page.evaluate((seed) => window.__COFFEE_BATTLES_SIM__.runOne({
    seed, points:1000, dt:1/30, maxTime:600, reverseUnits:false, silent:true
  }), seed);
  const fp = fingerprint(run);
  const hash = crypto.createHash('sha256').update(stable(fp)).digest('hex');
  console.log(JSON.stringify({ seed, winner:run.winner, simTime:run.simTime, hash, expectedHash, exact:hash===expectedHash }, null, 2));
  if (expectedHash && hash !== expectedHash) process.exitCode = 2;
} finally {
  await page.close();
  await browser.close();
}
