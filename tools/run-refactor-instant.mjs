import fs from 'node:fs';
import { chromium } from 'playwright-core';
const executablePath=process.env.CHROME_BIN||'/usr/bin/google-chrome';
const targets=[['baseline','http://127.0.0.1:8000/COFFEE_BATTLES.html'],['branch','http://127.0.0.1:8001/COFFEE_BATTLES.html']];
const browser=await chromium.launch({headless:true,executablePath,args:['--no-sandbox']});
async function run([name,url]){
 const page=await browser.newPage();
 try{
  await page.goto(url,{waitUntil:'domcontentloaded',timeout:60000});
  await page.addScriptTag({url:new URL('/sim-lab.js',url).href});
  await page.waitForFunction(()=>!!window.__COFFEE_BATTLES_SIM__,null,{timeout:30000});
  const r=await page.evaluate(()=>window.__COFFEE_BATTLES_SIM__.runOne({points:1000,seed:1,dt:0.05,maxTime:120,reverseUnits:false,silent:true}));
  return [name,{seed:r.seed,winner:r.winner,result:r.result,ended:r.ended,truncated:r.truncated,stuck:r.stuck,simTime:r.simTime,roles:r.roles,biome:r.biome,collapse:r.collapse,blue:r.blue,red:r.red,doctrine:r.doctrine}];
 } finally {await page.close();}
}
let entries;
try{entries=await Promise.all(targets.map(run));}finally{await browser.close();}
const x=Object.fromEntries(entries); const exact=JSON.stringify(x.baseline)===JSON.stringify(x.branch);
const out={baselineCommit:process.env.BASELINE_COMMIT,branchCommit:process.env.BRANCH_COMMIT,exact,baseline:x.baseline,branch:x.branch};
fs.mkdirSync('results',{recursive:true}); fs.writeFileSync('results/instant.json',JSON.stringify(out,null,2));
console.log(JSON.stringify(out,null,2)); if(!exact) process.exitCode=2;
