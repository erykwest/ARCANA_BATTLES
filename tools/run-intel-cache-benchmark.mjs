import { chromium } from 'playwright-core';

const executablePath = process.env.CHROME_BIN || '/usr/bin/google-chrome';
const url = process.env.BRANCH_URL || 'http://127.0.0.1:8001/COFFEE_BATTLES.html';
const seed = Number(process.env.BASELINE_SEED || 1);
const points = Number(process.env.BASELINE_POINTS || 1000);

const browser = await chromium.launch({ headless:true, executablePath, args:['--no-sandbox'] });
const page = await browser.newPage();
try {
  await page.goto(url, { waitUntil:'domcontentloaded', timeout:60000 });
  await page.addScriptTag({ url:new URL('/sim-lab.js', url).href });
  await page.waitForFunction(() => !!window.__COFFEE_BATTLES_SIM__ && !!window.__COFFEE_BATTLES_DEBUG__?.Intel, null, { timeout:30000 });

  const result = await page.evaluate(async ({ seed, points }) => {
    const sim = window.__COFFEE_BATTLES_SIM__;
    const Intel = window.__COFFEE_BATTLES_DEBUG__.Intel;
    Intel.resetVisibilityCache?.(true);
    const t0 = performance.now();
    const run = await sim.runOne({ seed, points, dt:1/30, maxTime:600, reverseUnits:false, silent:true });
    const wallMs = performance.now() - t0;
    return {
      seed,
      winner:run.winner,
      simTime:run.simTime,
      wallMs,
      intel:Intel.visibilityStats?.() || null
    };
  }, { seed, points });

  console.log(JSON.stringify(result, null, 2));
} finally {
  await page.close();
  await browser.close();
}
