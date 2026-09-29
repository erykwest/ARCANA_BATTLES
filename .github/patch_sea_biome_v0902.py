from pathlib import Path
import re

p = Path('COFFEE_BATTLES.html')
s = p.read_text(encoding='utf-8')


def replace_once(old, new, label):
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected 1 occurrence, found {count}')
    s = s.replace(old, new, 1)


def sub_once(pattern, repl, label, flags=0):
    global s
    s2, count = re.subn(pattern, repl, s, count=1, flags=flags)
    if count != 1:
        raise SystemExit(f'{label}: expected 1 match, found {count}')
    s = s2

# Version: preserve concurrent v0.90.1 work and advance only this fix.
if 'v0.90.1' not in s:
    raise SystemExit('expected current v0.90.1 base')
s = s.replace('v0.90.1', 'v0.90.2')

# Sea is a real selectable biome, not a random overlay on every biome.
replace_once(
    '          <option value="village">Villaggio</option>\n',
    '          <option value="village">Villaggio</option>\n          <option value="sea">Mare</option>\n',
    'sea select option'
)
replace_once(
    "      village:   Object.freeze({ label:'Villaggio', field:'#29261d' })\n",
    "      village:   Object.freeze({ label:'Villaggio', field:'#29261d' }),\n      sea:       Object.freeze({ label:'Mare',       field:'#1b281c' })\n",
    'sea biome catalog'
)
replace_once('    COAST_CHANCE: .30,\n', '', 'remove universal coast chance')

# Coast helpers + coast scenario. Ships are sampled from the real coastline,
# offset along the normal that points into the sea, and accepted only when the
# whole hull footprint is inside the sea polygon.
new_coast = r'''coastFrame(coastline,q){
  if(!coastline?.length)return null;
  const n=coastline.length;
  const f=this.clamp(q,0,1)*(n-1),i=Math.min(n-2,Math.floor(f)),t=f-i;
  const a=coastline[i],b=coastline[i+1];
  const point={x:a.x+(b.x-a.x)*t,y:a.y+(b.y-a.y)*t};
  const prev=coastline[Math.max(0,i-1)],next=coastline[Math.min(n-1,i+2)];
  const angle=Math.atan2(next.y-prev.y,next.x-prev.x);
  return {point,angle};
},

coastSeaNormal(sea,frame){
  const a=frame.angle;
  const normals=[{x:-Math.sin(a),y:Math.cos(a)},{x:Math.sin(a),y:-Math.cos(a)}];
  const probes=[1.0,2.0,3.0].map(u=>u*CFG.U);
  let best=normals[0],bestScore=-1;
  for(const n of normals){
    let score=0;
    for(const d of probes){
      const p={x:frame.point.x+n.x*d,y:frame.point.y+n.y*d};
      if(this.worldPolygonContains(sea.points,p,0))score++;
    }
    if(score>bestScore){best=n;bestScore=score;}
  }
  return best;
},

shipInsideSea(ship,sea){
  const wb=Geometry.worldBounds();
  const footprint=this.shapeSamples(ship)||[];
  return footprint.length===4 && footprint.every(p=>
    p.x>=wb.minX&&p.x<=wb.maxX&&p.y>=wb.minY&&p.y<=wb.maxY&&
    this.worldPolygonContains(sea.points,p,0)
  );
},

makeLandingShips(sea,count){
  const ships=[];
  const qOffsets=[0,.018,-.018,.036,-.036,.06,-.06,.085,-.085];
  const offsetsU=[2.6,3.2,3.8,4.5,5.2,6.0,7.0,8.0];
  for(let i=0;i<count;i++){
    const baseQ=(i+1)/(count+1);
    let ship=null;
    const tryAtQ=q=>{
      const frame=this.coastFrame(sea.coastline,this.clamp(q,.035,.965));
      if(!frame)return null;
      const normal=this.coastSeaNormal(sea,frame);
      for(const offU of offsetsU){
        const candidate={
          id:`ship-${i+1}`,type:'ship',
          x:frame.point.x+normal.x*offU*CFG.U,
          y:frame.point.y+normal.y*offU*CFG.U,
          angle:frame.angle+this.rand(-.045,.045),
          w:4.2*CFG.U,h:1.35*CFG.U,fill:'#4a382b',edge:'#dfcfaa'
        };
        if(this.shipInsideSea(candidate,sea))return candidate;
      }
      return null;
    };
    for(const dq of qOffsets){ship=tryAtQ(baseQ+dq);if(ship)break;}
    if(!ship){
      for(let k=1;k<=48&&!ship;k++)ship=tryAtQ(k/49);
    }
    if(ship)ships.push(ship);
  }
  return ships;
},

makeCoastScenario(){
  const forced=State.battleSetup.coastMode;
  const mode=(forced==='gulf'||forced==='landing')?forced:(Math.random()<.5?'gulf':'landing');
  const b=Geometry.battlefieldBounds(),wb=Geometry.worldBounds(),U=CFG.U,phase=this.rand(0,Math.PI*2);
  const coast=[];
  let points=[],side=null,attackerSide=null;

  if(mode==='gulf'){
    side=Math.random()<.5?'left':'right';
    const n=16;
    for(let i=0;i<=n;i++){
      const y=wb.minY+(wb.maxY-wb.minY)*(i/n);
      const depthU=this.coastDepthProfile(i,n,6,18,phase);
      const x=side==='left'?b.minX+depthU*U:b.maxX-depthU*U;
      coast.push({x,y});
    }
    points=side==='left'
      ? [{x:wb.minX,y:wb.minY},...coast,{x:wb.minX,y:wb.maxY}]
      : [{x:wb.maxX,y:wb.minY},...coast,{x:wb.maxX,y:wb.maxY}];
  }else{
    attackerSide=State.doctrine.roles.blue==='attack'?'blue':'red';
    side=attackerSide==='blue'?'bottom':'top';
    const maxU=this.COAST_MAX_LANDING_DEPTH_U;
    const n=20;
    for(let i=0;i<=n;i++){
      const x=wb.minX+(wb.maxX-wb.minX)*(i/n);
      const depthU=this.coastDepthProfile(i,n,3.2,maxU,phase);
      const y=side==='top'?b.minY+depthU*U:b.maxY-depthU*U;
      coast.push({x,y});
    }
    points=side==='top'
      ? [{x:wb.minX,y:wb.minY},{x:wb.maxX,y:wb.minY},...coast.slice().reverse()]
      : [...coast,{x:wb.maxX,y:wb.maxY},{x:wb.minX,y:wb.maxY}];
  }

  const sea={
    id:'sea-1',type:'sea',mode,side,attackerSide,points,coastline:coast,
    fill:'#245d78',edge:'#8bcbdc'
  };
  const shipCount=mode==='landing'?Math.max(1,Math.ceil(State.battleSetup.points/500)):0;
  const ships=mode==='landing'?this.makeLandingShips(sea,shipCount):[];
  return {sea,ships,meta:{mode,side,attackerSide,shipCount:ships.length,maxLandingDepthU:this.COAST_MAX_LANDING_DEPTH_U}};
},

clampToLand(point){'''
sub_once(r'makeCoastScenario\(\)\{.*?\n\},\n\nclampToLand\(point\)\{', new_coast, 'coast scenario', re.S)

# Village roads: the smaller junction angle is 40–60 degrees, never 90.
# Reserve the actual angled branch corridor so buildings still precede roads.
new_village = r'''makeVillagePlan(spawn){
  const baseAngle=this.rand(-Math.PI,Math.PI),topology=Math.random()<.5?'cross':'T',branchSign=Math.random()<.5?-1:1;
  const junctionDelta=this.rand(40,60)*Math.PI/180;
  const branchAngle=Geometry.normalizeAngle(baseAngle+branchSign*junctionDelta);
  return {spawn:{...spawn},baseAngle,branchAngle,topology,branchSign,junctionAngleDeg:junctionDelta*180/Math.PI};
},

streetCorridorReserved(plan,x,y,clearanceU=4.0){
  if(!plan)return false;
  const dx=x-plan.spawn.x,dy=y-plan.spawn.y,clear=clearanceU*CFG.U;
  const mc=Math.cos(plan.baseAngle),ms=Math.sin(plan.baseAngle);
  const mainSide=-dx*ms+dy*mc;
  if(Math.abs(mainSide)<clear)return true;

  const bc=Math.cos(plan.branchAngle),bs=Math.sin(plan.branchAngle);
  const branchAlong=dx*bc+dy*bs,branchSide=-dx*bs+dy*bc;
  if(Math.abs(branchSide)>=clear)return false;
  return plan.topology==='cross'||branchAlong>-clear;
},

makeRoadFromControls(id,controls,junction=null,spawn=null){
  return {id,type:'road',controlPoints:controls,samples:Terrain.sampleRoad(controls,.36),width:2*CFG.U,fill:'rgba(176,142,98,.90)',edge:'rgba(222,198,154,.95)',junction,spawn:spawn?{...spawn}:null};
},

makeVillageRoadNetwork(plan){
  const spawn=plan.spawn,[m0,m1]=this.edgePointsThrough(spawn,plan.baseAngle),j=.55*CFG.U;
  const pointBetween=(a,b,t)=>({x:a.x+(b.x-a.x)*t,y:a.y+(b.y-a.y)*t});
  const offset=(p,angle,amount)=>({x:p.x-Math.sin(angle)*amount,y:p.y+Math.cos(angle)*amount});

  // The controls immediately adjacent to the junction stay on the road axes:
  // Catmull-Rom therefore preserves the requested <=60° junction tangent.
  const mn0=pointBetween(spawn,m0,.34),mn1=pointBetween(spawn,m1,.34);
  const mf0=offset(pointBetween(spawn,m0,.72),plan.baseAngle,this.rand(-j,j));
  const mf1=offset(pointBetween(spawn,m1,.72),plan.baseAngle,this.rand(-j,j));
  const main=this.makeRoadFromControls('road-1',[m0,mf0,mn0,{...spawn},mn1,mf1,m1],plan.topology,spawn);

  const [b0,b1]=this.edgePointsThrough(spawn,plan.branchAngle);
  let controls;
  if(plan.topology==='cross'){
    const bn0=pointBetween(spawn,b0,.34),bn1=pointBetween(spawn,b1,.34);
    const bf0=offset(pointBetween(spawn,b0,.72),plan.branchAngle,this.rand(-j,j));
    const bf1=offset(pointBetween(spawn,b1,.72),plan.branchAngle,this.rand(-j,j));
    controls=[b0,bf0,bn0,{...spawn},bn1,bf1,b1];
  }else{
    // edgePointsThrough is ordered by signed t; b1 is the positive ray of branchAngle.
    const end=b1,near=pointBetween(spawn,end,.34),far=offset(pointBetween(spawn,end,.72),plan.branchAngle,this.rand(-j,j));
    controls=[{...spawn},near,far,end];
  }
  return [main,this.makeRoadFromControls('road-2',controls,plan.topology,spawn)];
},

roadConflictScore'''
sub_once(r'makeVillagePlan\(spawn\)\{.*?\nroadConflictScore', new_village, 'village junction block', re.S)

# Coast exists only for the sea biome.
replace_once(
'''    generateCoast(ctx) {
      const scenario=this.makeCoastScenario();
      State.battleSetup.coast=scenario?.meta||null;
      if(!scenario)return;
      ctx.sea=scenario.sea;
      ctx.ships=scenario.ships;
      ctx.placed.push(scenario.sea);
    },
''',
'''    generateCoast(ctx) {
      State.battleSetup.coast=null;
      if(ctx.biome!=='sea')return;
      const scenario=this.makeCoastScenario();
      State.battleSetup.coast=scenario.meta;
      ctx.sea=scenario.sea;
      ctx.ships=scenario.ships;
      ctx.placed.push(scenario.sea);
    },
''',
'generate coast only sea'
)

replace_once(
    "      }else if(ctx.biome==='plains'||ctx.biome==='hills'||ctx.biome==='forest'){\n",
    "      }else if(ctx.biome==='plains'||ctx.biome==='hills'||ctx.biome==='forest'||ctx.biome==='sea'){\n",
    'sea road generation'
)

replace_once(
'''      }else if(ctx.biome==='village'){
        this.addRandom(placed,this.randi(1,2),forest,.16);
        this.addRandom(placed,this.randi(0,1),hill,.16);
      }
''',
'''      }else if(ctx.biome==='village'){
        this.addRandom(placed,this.randi(1,2),forest,.16);
        this.addRandom(placed,this.randi(0,1),hill,.16);
      }else if(ctx.biome==='sea'){
        this.addRandom(placed,1,rough,.22);
        this.addRandom(placed,this.randi(0,1),forest,.22);
      }
''',
'sea tactical filler'
)

replace_once(
    "      const ranges={plains:[2,4],hills:[1,3],valley:[1,3],river:[1,3],forest:[0,2],mountains:[0,1],village:[2,4]};\n",
    "      const ranges={plains:[2,4],hills:[1,3],valley:[1,3],river:[1,3],forest:[0,2],mountains:[0,1],village:[2,4],sea:[1,2]};\n",
    'sea field range'
)

# Setup copy: describe the new biome explicitly.
s=s.replace(
    'Casuale sceglie un bioma coerente. Fiumi: invalicabili salvo ponti/guadi · torrenti: terreno accidentato · montagne/edifici: ostacoli pieni.',
    'Casuale sceglie un bioma coerente. Mare: golfo o sbarco · fiumi: invalicabili salvo ponti/guadi · torrenti: terreno accidentato · montagne/edifici: ostacoli pieni.'
)

p.write_text(s, encoding='utf-8')
print('patched COFFEE_BATTLES.html -> v0.90.2')
