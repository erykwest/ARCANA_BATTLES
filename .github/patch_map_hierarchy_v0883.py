from pathlib import Path
import re

p = Path('COFFEE_BATTLES.html')
s = p.read_text(encoding='utf-8')

if 'Campal Battle Lab v0.88.2' not in s:
    raise SystemExit('Unexpected source version; refusing patch')


def repl(start, end, new):
    global s
    a = s.index(start)
    b = s.index(end, a)
    s = s[:a] + new + s[b:]


# Version bump.
s = s.replace('v0.88.2', 'v0.88.3')

# Make the generation hierarchy explicit and executable.
marker = "    labels: null,\n"
if marker not in s:
    raise SystemExit('MapEngine labels marker not found')
s = s.replace(
    marker,
    "    GENERATION_PHASES: Object.freeze(['Orography','Hydrology','Settlement','Buildings','Roads','Crossings','Tactical']),\n\n" + marker,
    1,
)

# Village planning now precedes buildings; actual roads are generated later.
repl(
    "makeVillageRoadNetwork(spawn){",
    "perimeterMountainSectors(){",
    r'''makeVillagePlan(spawn){
  const baseAngle=this.rand(-Math.PI,Math.PI),topology=Math.random()<.5?'cross':'T',branchSign=Math.random()<.5?-1:1;
  return {spawn:{...spawn},baseAngle,branchAngle:baseAngle+Math.PI/2,topology,branchSign};
},

streetCorridorReserved(plan,x,y,clearanceU=4.0){
  if(!plan)return false;
  const dx=x-plan.spawn.x,dy=y-plan.spawn.y,c=Math.cos(plan.baseAngle),sn=Math.sin(plan.baseAngle);
  const along=dx*c+dy*sn,side=-dx*sn+dy*c,clear=clearanceU*CFG.U;
  if(Math.abs(side)<clear)return true;
  if(Math.abs(along)<clear){
    if(plan.topology==='cross')return true;
    if(side*plan.branchSign>-clear)return true;
  }
  return false;
},

makeRoadFromControls(id,controls,junction=null,spawn=null){
  return {id,type:'road',controlPoints:controls,samples:Terrain.sampleRoad(controls,.36),width:2*CFG.U,fill:'rgba(176,142,98,.90)',edge:'rgba(222,198,154,.95)',junction,spawn:spawn?{...spawn}:null};
},

makeVillageRoadNetwork(plan){
  const spawn=plan.spawn,[m0,m1]=this.edgePointsThrough(spawn,plan.baseAngle),j=.65*CFG.U;
  const mc0={x:(m0.x+spawn.x)*.5-Math.sin(plan.baseAngle)*this.rand(-j,j),y:(m0.y+spawn.y)*.5+Math.cos(plan.baseAngle)*this.rand(-j,j)};
  const mc1={x:(m1.x+spawn.x)*.5-Math.sin(plan.baseAngle)*this.rand(-j,j),y:(m1.y+spawn.y)*.5+Math.cos(plan.baseAngle)*this.rand(-j,j)};
  const main=this.makeRoadFromControls('road-1',[m0,mc0,{...spawn},mc1,m1],plan.topology,spawn);
  const [b0,b1]=this.edgePointsThrough(spawn,plan.branchAngle);
  let controls;
  if(plan.topology==='cross'){
    const q0={x:(b0.x+spawn.x)*.5+Math.cos(plan.baseAngle)*this.rand(-j,j),y:(b0.y+spawn.y)*.5+Math.sin(plan.baseAngle)*this.rand(-j,j)};
    const q1={x:(b1.x+spawn.x)*.5+Math.cos(plan.baseAngle)*this.rand(-j,j),y:(b1.y+spawn.y)*.5+Math.sin(plan.baseAngle)*this.rand(-j,j)};
    controls=[b0,q0,{...spawn},q1,b1];
  }else{
    const end=plan.branchSign<0?b0:b1;
    const q={x:(spawn.x+end.x)*.5+Math.cos(plan.baseAngle)*this.rand(-j,j),y:(spawn.y+end.y)*.5+Math.sin(plan.baseAngle)*this.rand(-j,j)};
    controls=[{...spawn},q,end];
  }
  return [main,this.makeRoadFromControls('road-2',controls,plan.topology,spawn)];
},

roadConflictScore(road,placed,marginU=.55){
  if(!road?.samples?.length)return Infinity;
  const pad=road.width/2+marginU*CFG.U;
  let score=0;
  for(let i=0;i<road.samples.length;i+=2){
    const p=road.samples[i];
    for(const o of placed){
      if(o.type!=='mountain'&&o.type!=='building')continue;
      if(Terrain.containsPoint(o,p,pad)){score++;break;}
    }
  }
  return score;
},

makeRoadAvoiding(placed,id='road-1',through=null,attempts=70){
  let best=null,bestScore=Infinity;
  for(let i=0;i<attempts;i++){
    const r=this.makeRoad(id,through),score=this.roadConflictScore(r,placed,.55);
    if(score===0)return r;
    if(score<bestScore){best=r;bestScore=score;}
  }
  const pivot=through||{x:this.mapZone().cx,y:this.mapZone().cy};
  for(let i=0;i<24;i++){
    const angle=Math.PI*i/24,[a,b]=this.edgePointsThrough(pivot,angle),r=this.makeRoadFromControls(id,[a,{...pivot},b]);
    const score=this.roadConflictScore(r,placed,.55);
    if(score===0)return r;
    if(score<bestScore){best=r;bestScore=score;}
  }
  if(best)best.generationFallback=true;
  return best||this.makeRoad(id,through);
},

watercourseConflictScore(water,placed,marginU=.45){
  if(!water?.samples?.length)return Infinity;
  const pad=water.width/2+marginU*CFG.U;
  let score=0;
  for(let i=0;i<water.samples.length;i+=2){
    const p=water.samples[i];
    for(const o of placed){
      if(o.type!=='mountain')continue;
      if(Terrain.containsPoint(o,p,pad)){score++;break;}
    }
  }
  return score;
},

makeWatercourseAvoiding(placed,type='stream',id=null,attempts=120){
  let best=null,bestScore=Infinity;
  for(let i=0;i<attempts;i++){
    const w=this.makeWatercourse(type,id),score=this.watercourseConflictScore(w,placed,.45);
    if(score===0)return w;
    if(score<bestScore){best=w;bestScore=score;}
  }
  if(best)best.generationFallback=true;
  return best||this.makeWatercourse(type,id);
},

perimeterMountainSectors(){'''
)

# Buildings consume only the settlement plan / reserved corridors, not roads.
repl(
    "    makeVillageCluster(placed,count=14,center=null) {",
    "\n\n    makeBiomeTerrain(biome) {",
    r'''    makeVillageCluster(placed,count=14,plan=null) {
      const z=this.mapZone(),center=plan?.spawn||{x:z.cx,y:z.cy},cx=center.x,cy=center.y,base=plan?.baseAngle??0;
      const tx=Math.cos(base),ty=Math.sin(base),nx=-ty,ny=tx;
      const blockCenters=[[-11,-8],[-4,-8],[4,-8],[11,-7],[-11,8],[-4,8],[4,8],[11,7]];
      let made=0;
      for(let bi=0;bi<blockCenters.length&&made<count;bi++){
        const [ba,bs]=blockCenters[bi],bcA=ba+this.rand(-2.5,2.5),bcS=bs+this.rand(-2.0,2.0),blockAngle=base+this.rand(-.38,.38),ct=Math.cos(blockAngle-base),st=Math.sin(blockAngle-base),nBuildings=this.randi(2,4);
        for(let j=0;j<nBuildings&&made<count;j++)for(let tries=0;tries<28;tries++){
          const la=this.rand(-3.8,3.8),ls=this.rand(-3.0,3.0),along=bcA+la*ct-ls*st,side=bcS+la*st+ls*ct;
          const x=cx+tx*along*CFG.U+nx*side*CFG.U,y=cy+ty*along*CFG.U+ny*side*CFG.U;
          if(this.streetCorridorReserved(plan,x,y,4.0))continue;
          const b=this.makeBuilding(`building-${made+1}`,x,y,this.rand(2.5,4.1),this.rand(2.2,3.5),blockAngle+this.rand(-.20,.20));
          if(!this.fitsZone(b)||placed.some(o=>o.type==='building'&&this.overlaps(b,o,.10))||placed.some(o=>o.type==='mountain'&&this.overlaps(b,o,.20)))continue;
          placed.push(b);made++;break;
        }
      }
      for(let tries=0;made<count&&tries<260;tries++){
        const a=this.rand(0,Math.PI*2),r=this.rand(6,16),x=cx+Math.cos(a)*r*CFG.U,y=cy+Math.sin(a)*r*CFG.U;
        if(this.streetCorridorReserved(plan,x,y,4.0))continue;
        const b=this.makeBuilding(`building-${made+1}`,x,y,this.rand(2.4,4.0),this.rand(2.1,3.3),base+this.rand(-.45,.45));
        if(!this.fitsZone(b)||placed.some(o=>o.type==='building'&&this.overlaps(b,o,.10))||placed.some(o=>o.type==='mountain'&&this.overlaps(b,o,.20)))continue;
        placed.push(b);made++;
      }
      return{x:cx,y:cy,buildingCount:made,topology:plan?.topology||null};
    },'''
)

# Replace monolithic biome assembly with ordered generation phases.
repl(
    "    makeBiomeTerrain(biome) {",
    "\n\n    generate(choice=State.battleSetup.biome) {",
    r'''    generateOrography(ctx) {
      if(ctx.biome==='valley')ctx.placed.push(...this.makeMountainSectorChain(3,5));
      else if(ctx.biome==='mountains')ctx.placed.push(...this.makeMountainSectorChain(4,7));
    },

    generateHydrology(ctx) {
      if(ctx.biome==='plains'&&Math.random()<.45)ctx.placed.push(this.makeWatercourseAvoiding(ctx.placed,'stream','stream-1'));
      else if(ctx.biome==='valley'||ctx.biome==='forest'||ctx.biome==='mountains')ctx.placed.push(this.makeWatercourseAvoiding(ctx.placed,'stream','stream-1'));
      else if(ctx.biome==='river'){
        ctx.river=this.makeWatercourseAvoiding(ctx.placed,'river','river-1');
        ctx.placed.push(ctx.river);
        ctx.bridgeQ=this.rand(.30,.42);
        ctx.fordQ=this.rand(.62,.75);
      }
    },

    generateSettlement(ctx) {
      if(ctx.biome!=='village')return;
      const z=ctx.z,spawn={x:this.rand(z.cx-5*CFG.U,z.cx+5*CFG.U),y:this.rand(z.cy-3*CFG.U,z.cy+3*CFG.U)};
      State.battleSetup.mapSpawn={...spawn};
      ctx.villagePlan=this.makeVillagePlan(spawn);
    },

    generateBuildings(ctx) {
      if(ctx.biome==='village')ctx.village=this.makeVillageCluster(ctx.placed,this.randi(12,18),ctx.villagePlan);
    },

    generateRoads(ctx) {
      const z=ctx.z;
      if(ctx.biome==='village'){
        const roads=this.makeVillageRoadNetwork(ctx.villagePlan);
        for(const r of roads){
          const score=this.roadConflictScore(r,ctx.placed,.25);
          if(score>0)r.generationFallback=true;
          ctx.placed.push(r);
        }
      }else if(ctx.biome==='river'){
        const crossing=this.sampleAlong(ctx.river,ctx.bridgeQ);
        ctx.placed.push(this.makeRoadAvoiding(ctx.placed,'road-1',{x:crossing.x,y:crossing.y}));
      }else if(ctx.biome==='valley'||ctx.biome==='mountains'){
        ctx.placed.push(this.makeRoadAvoiding(ctx.placed,'road-1',{x:z.cx,y:z.cy}));
      }else if(ctx.biome==='plains'||ctx.biome==='hills'||ctx.biome==='forest'){
        ctx.placed.push(this.makeRoadAvoiding(ctx.placed,'road-1'));
      }
    },

    generateCrossings(ctx) {
      if(ctx.biome!=='river'||!ctx.river)return;
      ctx.placed.push(this.makeCrossing(ctx.river,'bridge',ctx.bridgeQ,'bridge-1'));
      ctx.placed.push(this.makeCrossing(ctx.river,'ford',ctx.fordQ,'ford-1'));
    },

    generateTactical(ctx) {
      const placed=ctx.placed,pos=(m=0)=>this.randomCenter(m);
      const hill=(i,small=false)=>{const p=pos(small?4:7);return this.makeHill(`hill-${i+1}`,p.x,p.y,small?this.rand(5,7):this.rand(8,10),small?this.rand(3,4):this.rand(4,5.5));};
      const forest=(i,small=false)=>{const p=pos(small?4:7);return this.makeForest(`forest-${i+1}`,p.x,p.y,small?this.rand(5,7):this.rand(8,10),small?this.rand(3,4):this.rand(4,5.5));};
      const rough=i=>{const p=pos(4);return this.makeRough(`rough-${i+1}`,p.x,p.y,this.rand(4.5,6),this.rand(3,4));};
      const pond=i=>{const p=pos(4);return this.makePond(`pond-${i+1}`,p.x,p.y,this.rand(4,5),this.rand(2.5,3.3));};
      if(ctx.biome==='plains'){
        this.addRandom(placed,this.randi(1,2),rough,.30);
        this.addRandom(placed,this.randi(0,1),forest,.30);
      }else if(ctx.biome==='hills'){
        this.addRandom(placed,this.randi(3,4),hill,.20);
        this.addRandom(placed,this.randi(1,2),rough,.25);
        this.addRandom(placed,this.randi(0,1),forest,.25);
      }else if(ctx.biome==='valley'){
        this.addRandom(placed,1,rough,.18);
      }else if(ctx.biome==='river'){
        this.addRandom(placed,this.randi(1,2),forest,.22);
        this.addRandom(placed,this.randi(0,1),hill,.22);
      }else if(ctx.biome==='forest'){
        this.addRandom(placed,this.randi(4,6),i=>forest(i,true),.16);
        this.addRandom(placed,this.randi(0,1),pond,.20);
      }else if(ctx.biome==='mountains'){
        this.addRandom(placed,this.randi(1,2),hill,.10);
      }else if(ctx.biome==='village'){
        this.addRandom(placed,this.randi(1,2),forest,.16);
        this.addRandom(placed,this.randi(0,1),hill,.16);
      }
    },

    makeBiomeTerrain(biome) {
      const ctx={biome,z:this.mapZone(),placed:[],river:null,bridgeQ:null,fordQ:null,villagePlan:null,village:null};
      for(const phase of this.GENERATION_PHASES){
        const fn=this[`generate${phase}`];
        if(typeof fn==='function')fn.call(this,ctx);
      }
      return ctx.placed;
    },'''
)

p.write_text(s, encoding='utf-8')

# Static validation before CI commits anything.
required = [
    'Campal Battle Lab v0.88.3',
    "GENERATION_PHASES: Object.freeze(['Orography','Hydrology','Settlement','Buildings','Roads','Crossings','Tactical'])",
    'generateOrography(ctx)',
    'generateBuildings(ctx)',
    'generateRoads(ctx)',
    'makeVillagePlan(spawn)',
    'makeVillageCluster(placed,count=14,plan=null)',
]
for token in required:
    if token not in s:
        raise SystemExit(f'Missing required token: {token}')

blocks = re.findall(r'<script[^>]*>(.*?)</script>', s, re.S | re.I)
if not blocks:
    raise SystemExit('No script blocks found')
Path('/tmp/coffee-battles.js').write_text('\n'.join(blocks), encoding='utf-8')
