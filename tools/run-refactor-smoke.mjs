import fs from 'node:fs';
import { chromium } from 'playwright-core';

const executablePath = process.env.CHROME_BIN || '/usr/bin/google-chrome';
const seed = Number(process.env.BASELINE_SEED || 1);
const points = Number(process.env.BASELINE_POINTS || 1000);
const targets = [
  { name:'baseline', url:'http://127.0.0.1:8000/COFFEE_BATTLES.html' },
  { name:'branch', url:'http://127.0.0.1:8001/COFFEE_BATTLES.html' }
];
const series = [0.05, 1/30, 1/60].flatMap(dt => [false,true].map(reverseUnits => ({dt,reverseUnits})));
const keyFor = (dt,r) => `${Math.round(1/dt)}hz${r?'-reverse':''}`;

function fp(r){
  return {
    seed:r.seed,winner:r.winner,result:r.result,ended:r.ended,timedOut:r.timedOut,truncated:r.truncated,stuck:r.stuck,
    simTime:r.simTime,collapse:r.collapse,roles:r.roles,biome:r.biome,
    blue:{pointsLost:r.blue?.pointsLost,hp:r.blue?.hp,brain:r.blue?.brain,energy:r.blue?.energy,kills:r.blue?.kills,routsOut:r.blue?.routsOut},
    red:{pointsLost:r.red?.pointsLost,hp:r.red?.hp,brain:r.red?.brain,energy:r.red?.energy,kills:r.red?.kills,routsOut:r.red?.routsOut}
  };
}

const browser = await chromium.launch({headless:true,executablePath,args:['--no-sandbox']});
const all={};
async function one(target,s){
  const page=await browser.newPage();
  const key=keyFor(s.dt,s.reverseUnits);
  try{
    await page.goto(target.url,{waitUntil:'domcontentloaded',timeout:60000});
    await page.addScriptTag({url:new URL('/sim-lab.js',target.url).href});
    await page.waitForFunction(()=>!!window.__COFFEE_BATTLES_SIM__,null,{timeout:30000});
    const r=await page.evaluate(({seed,points,dt,reverseUnits})=>window.__COFFEE_BATTLES_SIM__.runOne({seed,points,dt,reverseUnits,silent:true}),{seed,points,dt:s.dt,reverseUnits:s.reverseUnits});
    console.log(`${target.name} ${key}: ${r.winner} ${r.simTime}s`);
    return [key,fp(r)];
  } finally { await page.close(); }
}
try{
  for(const target of targets) all[target.name]=Object.fromEntries(await Promise.all(series.map(s=>one(target,s))));
} finally { await browser.close(); }

const rows=[]; let mismatches=0;
for(const s of series){
  const key=keyFor(s.dt,s.reverseUnits),a=all.baseline[key],b=all.branch[key];
  const exact=JSON.stringify(a)===JSON.stringify(b); if(!exact)mismatches++;
  rows.push({key,exact,baseline:a,branch:b});
}
const out={baselineCommit:process.env.BASELINE_COMMIT,branchCommit:process.env.BRANCH_COMMIT,seed,points,mismatches,rows};
fs.mkdirSync('results',{recursive:true});
fs.writeFileSync('results/refactor-p0-smoke.json',JSON.stringify(out,null,2));
let md=`# Exact single-seed baseline vs branch smoke\n\n- Seed: **${seed}**\n- Mismatches: **${mismatches}/6**\n\n| Series | Baseline | Branch | sim time B/branch | Exact |\n|---|---|---|---:|---:|\n`;
for(const r of rows) md+=`| ${r.key} | ${r.baseline.winner ?? '—'} | ${r.branch.winner ?? '—'} | ${r.baseline.simTime}/${r.branch.simTime} | ${r.exact?'YES':'NO'} |\n`;
fs.writeFileSync('results/refactor-p0-smoke.md',md); console.log(md);
if(mismatches) process.exitCode=2;
