from pathlib import Path
import re

p = Path('COFFEE_BATTLES.html')
s = p.read_text(encoding='utf-8')


def once(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        raise SystemExit(f'{label}: expected 1 match, found {n}')
    s = s.replace(old, new, 1)

# version
if 'v0.89.2' not in s:
    raise SystemExit('expected v0.89.2 base')
s = s.replace('v0.89.2', 'v0.89.3')

once(
"    GENERATION_PHASES: Object.freeze(['Orography','Hydrology','Settlement','Buildings','Roads','Crossings','Tactical','Fields']),",
"    GENERATION_PHASES: Object.freeze(['Coast','Orography','Hydrology','Settlement','Buildings','Roads','Crossings','Tactical','Fields']),",
'phase order')

once(
"    pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; },\n    clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); },",
"    pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; },\n    clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); },\n    COAST_CHANCE: .30,\n    COAST_MAX_LANDING_DEPTH_U: CFG.DEPLOYMENT_DEPTH_U * .5,",
'coast constants')

old_zone = """    mapZone() {
      const b = Geometry.battlefieldBounds();
      return {
        minX: b.minX + 8 * CFG.U,
        maxX: b.maxX - 8 * CFG.U,
        minY: b.minY + 10 * CFG.U,
        maxY: b.maxY - 10 * CFG.U,
        cx: (b.minX + b.maxX) / 2,
        cy: (b.minY + b.maxY) / 2
      };
    },
"""
new_zone = """    worldZone() {
      const b = Geometry.worldBounds();
      return { minX:b.minX, maxX:b.maxX, minY:b.minY, maxY:b.maxY, cx:(b.minX+b.maxX)/2, cy:(b.minY+b.maxY)/2 };
    },

    gameplayContainsPoint(point, pad = 0) {
      const b = Geometry.battlefieldBounds();
      return point.x >= b.minX - pad && point.x <= b.maxX + pad && point.y >= b.minY - pad && point.y <= b.maxY + pad;
    },

    mapZone() {
      // I centri restano legati al campo operativo, ma possono stare vicino al limite:
      // le forme possono quindi proseguire naturalmente nei 10U di bordocampo.
      const b = Geometry.battlefieldBounds();
      return {
        minX: b.minX + 2 * CFG.U,
        maxX: b.maxX - 2 * CFG.U,
        minY: b.minY + 2 * CFG.U,
        maxY: b.maxY - 2 * CFG.U,
        cx: (b.minX + b.maxX) / 2,
        cy: (b.minY + b.maxY) / 2
      };
    },
"""
once(old_zone, new_zone, 'map/world zones')

# Water reaches the outer visual world, not only the 90x60 operational rectangle.
once(
"    makeWatercourse(type = 'stream', id = null) {\n      const b = Geometry.battlefieldBounds();",
"    makeWatercourse(type = 'stream', id = null) {\n      const b = Geometry.worldBounds();",
'watercourse world bounds')

# Coast geometry + ships. Sea is gameplay geometry; ships are visual only.
anchor = """},

edgePointsThrough(point,angle){
"""
coast_code = r'''},

worldPolygonBoundaryDistance(points,point){
  if(!points?.length)return Infinity;
  let best=Infinity;
  for(let i=0;i<points.length;i++)best=Math.min(best,Geometry.pointSegmentDistance(point,points[i],points[(i+1)%points.length]));
  return best;
},

worldPolygonContains(points,point,pad=0){
  if(!points?.length)return false;
  let inside=false;
  for(let i=0,j=points.length-1;i<points.length;j=i++){
    const a=points[i],b=points[j];
    const hit=((a.y>point.y)!==(b.y>point.y)) && (point.x < (b.x-a.x)*(point.y-a.y)/((b.y-a.y)||1e-9)+a.x);
    if(hit)inside=!inside;
  }
  return inside || (pad>0 && this.worldPolygonBoundaryDistance(points,point)<=pad);
},

coastDepthProfile(i,n,minU,maxU,phase){
  const q=n?i/n:0;
  const wave=Math.sin(q*Math.PI*2+phase)*1.6 + Math.sin(q*Math.PI*5+phase*.7)*.65;
  return this.clamp(this.rand(minU,maxU)+wave,minU,maxU);
},

makeCoastScenario(){
  const forced=State.battleSetup.coastMode;
  if(forced==='none')return null;
  let mode;
  if(forced==='gulf'||forced==='landing')mode=forced;
  else{
    if(Math.random()>=this.COAST_CHANCE)return null;
    mode=Math.random()<.5?'gulf':'landing';
  }

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
  const ships=[];
  if(mode==='landing'){
    const count=Math.max(1,Math.ceil(State.battleSetup.points/500));
    for(let i=0;i<count;i++){
      const x=b.minX+b.w*(i+1)/(count+1)+this.rand(-1.2,1.2)*U;
      const y=side==='top'?b.minY-3.5*U:b.maxY+3.5*U;
      ships.push({id:`ship-${i+1}`,type:'ship',x,y,angle:side==='top'?0:Math.PI,w:4.2*U,h:1.35*U,fill:'#4a382b',edge:'#dfcfaa'});
    }
  }
  return {sea,ships,meta:{mode,side,attackerSide,shipCount:ships.length,maxLandingDepthU:this.COAST_MAX_LANDING_DEPTH_U}};
},

clampToLand(point){
  const b=Geometry.battlefieldBounds();
  const base={x:this.clamp(point.x,b.minX,b.maxX),y:this.clamp(point.y,b.minY,b.maxY)};
  const sea=State.terrain.find(t=>t.type==='sea');
  if(!sea||!this.containsPoint(sea,base,0))return base;
  const step=.5*CFG.U;
  for(let r=step;r<=24*CFG.U;r+=step){
    for(let i=0;i<32;i++){
      const a=Math.PI*2*i/32,p={x:base.x+Math.cos(a)*r,y:base.y+Math.sin(a)*r};
      if(p.x<b.minX||p.x>b.maxX||p.y<b.minY||p.y>b.maxY)continue;
      if(!this.containsPoint(sea,p,.15*CFG.U))return p;
    }
  }
  return base;
},

edgePointsThrough(point,angle){
'''
once(anchor, coast_code, 'coast helpers')

# Roads must treat sea as a hard spatial constraint.
s = s.replace("if(o.type!=='mountain'&&o.type!=='building')continue;", "if(o.type!=='mountain'&&o.type!=='building'&&o.type!=='sea')continue;")

# Shape adapters for sea/ship.
once(
"""    shapeSamples(t,steps=32) {
      if (!t) return null;
      if (['road','river','stream'].includes(t.type)) {""",
"""    shapeSamples(t,steps=32) {
      if (!t) return null;
      if (t.type==='sea') return t.points||[];
      if (t.type==='ship') {
        const hw=t.w/2,hh=t.h/2;
        return [[-hw,-hh],[hw,-hh],[hw,hh],[-hw,hh]].map(([x,y])=>Terrain.localToWorld(t,{x,y}));
      }
      if (['road','river','stream'].includes(t.type)) {""",
'shape sea')

once(
"""    containsPoint(t,point,pad=0) {
      if (!t || !point) return null;
      if (t.type==='river'||t.type==='stream') return Terrain.pointPolylineDistance(point,t.samples)<=t.width/2+pad;""",
"""    containsPoint(t,point,pad=0) {
      if (!t || !point) return null;
      if (t.type==='sea') return this.worldPolygonContains(t.points,point,pad);
      if (t.type==='ship') return false;
      if (t.type==='river'||t.type==='stream') return Terrain.pointPolylineDistance(point,t.samples)<=t.width/2+pad;""",
'contains sea')

once(
"""    boundaryDistance(t,point) {
      if (!t || !point) return Infinity;
      if (t.type==='building') {""",
"""    boundaryDistance(t,point) {
      if (!t || !point) return Infinity;
      if (t.type==='sea') return this.containsPoint(t,point,0)?0:this.worldPolygonBoundaryDistance(t.points,point);
      if (t.type==='building') {""",
'boundary sea')

once(
"""    overlaps(a,b,marginU=.35) {
      if(!a||!b)return false;
      const pad=marginU*CFG.U;
      const as=Terrain.shapeSamples(a),bs=Terrain.shapeSamples(b);
      if(as.some(p=>Terrain.containsPoint(b,p,pad)))return true;
      if(bs.some(p=>Terrain.containsPoint(a,p,pad)))return true;
      return false;
    },

    fitsZone(t) {
      if (['road','river','stream'].includes(t.type)) return true;
      const z=this.mapZone();
      return Terrain.shapeSamples(t).every(p=>p.x>=z.minX&&p.x<=z.maxX&&p.y>=z.minY&&p.y<=z.maxY);
    },""",
"""    overlaps(a,b,marginU=.35) {
      if(!a||!b)return false;
      const pad=marginU*CFG.U;
      const as=Terrain.shapeSamples(a)||[],bs=Terrain.shapeSamples(b)||[];
      if(!as.length||!bs.length)return false;
      if(as.some(p=>Terrain.containsPoint(b,p,pad)))return true;
      if(bs.some(p=>Terrain.containsPoint(a,p,pad)))return true;
      return false;
    },

    fitsZone(t) {
      if (['road','river','stream','sea','ship'].includes(t.type)) return true;
      const z=this.worldZone(),pad=.35*CFG.U;
      return (Terrain.shapeSamples(t)||[]).every(p=>p.x>=z.minX+pad&&p.x<=z.maxX-pad&&p.y>=z.minY+pad&&p.y<=z.maxY-pad);
    },""",
'overlap/world fit')

# Phase 0 and mountain filtering.
once(
"""    generateOrography(ctx) {
      if(ctx.biome==='valley')ctx.placed.push(...this.makeMountainSectorChain(3,5));
      else if(ctx.biome==='mountains')ctx.placed.push(...this.makeMountainSectorChain(4,7));
    },""",
"""    generateCoast(ctx) {
      const scenario=this.makeCoastScenario();
      State.battleSetup.coast=scenario?.meta||null;
      if(!scenario)return;
      ctx.sea=scenario.sea;
      ctx.ships=scenario.ships;
      ctx.placed.push(scenario.sea);
    },

    generateOrography(ctx) {
      let chain=[];
      if(ctx.biome==='valley')chain=this.makeMountainSectorChain(3,5);
      else if(ctx.biome==='mountains')chain=this.makeMountainSectorChain(4,7);
      if(chain.length){
        chain=chain.filter(m=>!ctx.placed.some(o=>o.type==='sea'&&this.overlaps(m,o,.20)));
        ctx.placed.push(...chain);
      }
    },""",
'coast phase')

# Village roads: if literal +/T route hits coast, keep the village anchor but solve a land route.
once(
"""        for(const r of roads){
          const score=this.roadConflictScore(r,ctx.placed,.25);
          if(score>0)r.generationFallback=true;
          ctx.placed.push(r);
        }""",
"""        for(const r of roads){
          const score=this.roadConflictScore(r,ctx.placed,.25);
          if(score>0){
            const safe=this.makeRoadAvoiding(ctx.placed,r.id,ctx.villagePlan.spawn,120);
            safe.junction=ctx.villagePlan.topology;
            safe.spawn={...ctx.villagePlan.spawn};
            safe.generationFallback=true;
            ctx.placed.push(safe);
          }else ctx.placed.push(r);
        }""",
'village coast roads')

once(
"""    makeBiomeTerrain(biome) {
      const ctx={biome,z:this.mapZone(),placed:[],river:null,bridgeQ:null,fordQ:null,villagePlan:null,village:null};
      for(const phase of this.GENERATION_PHASES){
        const fn=this[`generate${phase}`];
        if(typeof fn==='function')fn.call(this,ctx);
      }
      return ctx.placed;
    },""",
"""    makeBiomeTerrain(biome) {
      const ctx={biome,z:this.mapZone(),placed:[],sea:null,ships:[],river:null,bridgeQ:null,fordQ:null,villagePlan:null,village:null};
      for(const phase of this.GENERATION_PHASES){
        const fn=this[`generate${phase}`];
        if(typeof fn==='function')fn.call(this,ctx);
      }
      return [...ctx.placed,...ctx.ships];
    },""",
'biome context')

# Drawing: sea behind everything, ships on top.
insert_draw = r'''    drawSea(items) {
      for(const t of items){
        if(!t.points?.length)continue;
        ctx.save();
        ctx.beginPath();
        t.points.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));
        ctx.closePath();ctx.fillStyle=t.fill;ctx.fill();
        if(t.coastline?.length){
          ctx.beginPath();t.coastline.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));
          ctx.strokeStyle=t.edge;ctx.lineWidth=3;ctx.stroke();
          ctx.globalAlpha=.28;ctx.strokeStyle='#d8f2f4';ctx.lineWidth=1;
          for(let k=1;k<=2;k++){
            ctx.beginPath();
            t.coastline.forEach((p,i)=>{
              const q={x:p.x,y:p.y+(t.side==='top'?k*5:(t.side==='bottom'?-k*5:0)),};
              if(t.side==='left')q.x+=k*5;
              if(t.side==='right')q.x-=k*5;
              i?ctx.lineTo(q.x,q.y):ctx.moveTo(q.x,q.y);
            });
            ctx.stroke();
          }
        }
        ctx.restore();
      }
    },

    drawShips(items) {
      for(const t of items){
        ctx.save();ctx.translate(t.x,t.y);ctx.rotate(t.angle||0);
        ctx.fillStyle=t.fill;ctx.strokeStyle=t.edge;ctx.lineWidth=1.5;
        ctx.beginPath();ctx.moveTo(-t.w/2,-t.h*.28);ctx.lineTo(t.w*.42,-t.h*.28);ctx.lineTo(t.w/2,0);ctx.lineTo(t.w*.42,t.h*.28);ctx.lineTo(-t.w/2,t.h*.28);ctx.closePath();ctx.fill();ctx.stroke();
        ctx.beginPath();ctx.moveTo(-t.w*.05,0);ctx.lineTo(-t.w*.05,-t.h*1.25);ctx.stroke();
        ctx.beginPath();ctx.moveTo(-t.w*.03,-t.h*1.18);ctx.lineTo(t.w*.20,-t.h*.45);ctx.lineTo(-t.w*.03,-t.h*.45);ctx.closePath();ctx.fillStyle='rgba(224,213,181,.78)';ctx.fill();ctx.stroke();
        ctx.restore();
      }
    },

'''
once("    drawFields(items) {", insert_draw + "    drawFields(items) {", 'sea/ship drawing')

old_draw = """      Terrain.draw=()=>{
        const all=State.terrain;
        this.drawFields(all.filter(t=>t.type==='field'));
        State.terrain=all.filter(t=>['road','hill','forest','rough','pond','wall'].includes(t.type)&&!(t.type==='hill'&&t.blob));
        try{legacyDraw();}finally{State.terrain=all;}
        this.drawExtras(all.filter(t=>['river','stream','bridge','ford','mountain','building'].includes(t.type)||(t.type==='hill'&&t.blob)));
      };"""
new_draw = """      Terrain.draw=()=>{
        const all=State.terrain;
        this.drawSea(all.filter(t=>t.type==='sea'));
        this.drawFields(all.filter(t=>t.type==='field'));
        State.terrain=all.filter(t=>['road','hill','forest','rough','pond','wall'].includes(t.type)&&!(t.type==='hill'&&t.blob));
        try{legacyDraw();}finally{State.terrain=all;}
        this.drawExtras(all.filter(t=>['river','stream','bridge','ford','mountain','building'].includes(t.type)||(t.type==='hill'&&t.blob)));
        this.drawShips(all.filter(t=>t.type==='ship'));
      };"""
once(old_draw,new_draw,'draw layering')

# Runtime adapters: sea hard-blocks; border overflow of normal terrain is visual-only for routed units.
old_blocks = """      Terrain.blocksUnit=(u,t)=>{
        if(t?.type==='river')return Terrain.unitSamplePoints(u).some(p=>Terrain.containsPoint(t,p,0)&&!this.crossingAt(p,0));
        if(t?.type==='building'||t?.type==='mountain')return Terrain.unitSamplePoints(u).some(p=>Terrain.containsPoint(t,p,0));
        return legacyBlocksUnit(u,t);
      };"""
new_blocks = """      Terrain.blocksUnit=(u,t)=>{
        const samples=Terrain.unitSamplePoints(u);
        if(t?.type==='sea')return samples.some(p=>Terrain.containsPoint(t,p,0));
        if(u?.status?.routing){
          const active=samples.filter(p=>this.gameplayContainsPoint(p));
          if(!active.length)return false;
          if(t?.type==='river')return active.some(p=>Terrain.containsPoint(t,p,0)&&!this.crossingAt(p,0));
          if(t?.type==='building'||t?.type==='mountain')return active.some(p=>Terrain.containsPoint(t,p,0));
          if(t?.type==='pond')return active.some(p=>Terrain.insideHardCore(t,p));
          if(t?.type==='forest'&&u.type==='cavalry')return active.some(p=>Terrain.insideHardCore(t,p));
          return false;
        }
        if(t?.type==='river')return samples.some(p=>Terrain.containsPoint(t,p,0)&&!this.crossingAt(p,0));
        if(t?.type==='building'||t?.type==='mountain')return samples.some(p=>Terrain.containsPoint(t,p,0));
        return legacyBlocksUnit(u,t);
      };"""
once(old_blocks,new_blocks,'sea blocks unit')

once(
"""      Terrain.distanceToBlockingTerrain=(t,point)=>{
        if(t?.type==='building'||t?.type==='mountain')return this.boundaryDistance(t,point);""",
"""      Terrain.distanceToBlockingTerrain=(t,point)=>{
        if(t?.type==='sea'||t?.type==='building'||t?.type==='mountain')return this.boundaryDistance(t,point);""",
'distance sea')

old_point = """      Terrain.blocksPoint=(u,point,clearancePx=0)=>{
        for(const t of State.terrain){
          if(t.type==='river'){
            if(Terrain.pointPolylineDistance(point,t.samples)<=t.width/2+clearancePx&&!this.crossingAt(point,clearancePx))return true;
          } else if(t.type==='building'||t.type==='mountain'){
            if(Terrain.distanceToBlockingTerrain(t,point)<=clearancePx)return true;
          }
        }
        return legacyBlocksPoint(u,point,clearancePx);
      };"""
new_point = """      Terrain.blocksPoint=(u,point,clearancePx=0)=>{
        const routingBorder=!!u?.status?.routing&&!this.gameplayContainsPoint(point,clearancePx);
        for(const t of State.terrain){
          if(t.type==='sea'){
            if(Terrain.distanceToBlockingTerrain(t,point)<=clearancePx)return true;
          } else if(routingBorder) continue;
          else if(t.type==='river'){
            if(Terrain.pointPolylineDistance(point,t.samples)<=t.width/2+clearancePx&&!this.crossingAt(point,clearancePx))return true;
          } else if(t.type==='building'||t.type==='mountain'){
            if(Terrain.distanceToBlockingTerrain(t,point)<=clearancePx)return true;
          }
        }
        if(routingBorder)return false;
        return legacyBlocksPoint(u,point,clearancePx);
      };"""
once(old_point,new_point,'sea blocks point')

once(
"""      Terrain.movementMultiplier=(u)=>{
        let mult=legacyMovement(u);
        if(!u?.status?.alive)return mult;
        const c=Geometry.center(u);""",
"""      Terrain.movementMultiplier=(u)=>{
        if(!u?.status?.alive)return legacyMovement(u);
        const c=Geometry.center(u);
        if(u.status.routing&&!this.gameplayContainsPoint(c))return 1;
        let mult=legacyMovement(u);""",
'rout border visual only')

# Land-clamp all normal targets, including manual movement and voluntary retreat.
once(
"  MapEngine.installTerrainAdapters();\n\n  const Pathfinder = {",
"  MapEngine.installTerrainAdapters();\n  const __baseClampPointToBattlefield=Geometry.clampPointToBattlefield.bind(Geometry);\n  Geometry.clampPointToBattlefield=(point)=>MapEngine.clampToLand(__baseClampPointToBattlefield(point));\n\n  const Pathfinder = {",
'land target clamp')

# ROUT cannot exit through sea, even though ordinary outer edges remain valid exits.
old_rout = """      // ROUT: il bordocampo è percorribile, ma il bordo esterno è uscita definitiva.
      // RETREAT volontaria non arriva mai qui ed è già confinata nel battlefield centrale.
      if (Geometry.crossesOuterWorld(u)) {
        Battle.removeRoutedUnit(u);
        return;
      }

      Geometry.clampToWorld(u);"""
new_rout = """      // Il mare ha priorità sul bordo esterno: non è mai una direzione valida di fuga.
      const seaHit=State.terrain.some(t=>t.type==='sea'&&Terrain.blocksUnit(u,t));
      if(seaHit){
        u.pose.x=old.x;u.pose.y=old.y;
        const previous=u.status.routAngle;
        const next=Terrain.findRoutDeflection(u,previous);
        u.status.routAngle=next;u.pose.angle=next;u.motion.moving=false;
        if(Math.abs(Geometry.shortestDelta(previous,next))>.01)Log.add(`${u.name}: ROUT devia dalla costa`);
        return;
      }

      // ROUT: il bordocampo è percorribile, ma il bordo esterno di TERRA resta uscita definitiva.
      // RETREAT volontaria non arriva mai qui ed è già confinata nel battlefield centrale.
      if (Geometry.crossesOuterWorld(u)) {
        Battle.removeRoutedUnit(u);
        return;
      }

      Geometry.clampToWorld(u);"""
once(old_rout,new_rout,'rout coast')

# Visual continuity: same biome ground under the 10U border; dashed 90x60 line still marks gameplay.
once(
"""      // Fascia esterna: bordocampo, accessibile soltanto alle unità in ROUT.
      ctx.fillStyle = '#0c120e';
      ctx.fillRect(0, 0, w, h);

      // Campo di battaglia operativo 90×60U.
      ctx.fillStyle = MapEngine.fieldColor();
      ctx.fillRect(b.x, b.y, b.w, b.h);""",
"""      // Continuità visiva: il bioma riempie l'intero world 110×80U.
      // Il tratteggio 90×60U resta l'unico confine di gameplay ordinario.
      ctx.fillStyle = MapEngine.fieldColor();
      ctx.fillRect(0, 0, w, h);

      // Campo di battaglia operativo 90×60U: stesso fondo, distinto dal tratteggio.
      ctx.fillStyle = MapEngine.fieldColor();
      ctx.fillRect(b.x, b.y, b.w, b.h);""",
'border background')

# Semantic assertions
required = [
    "['Coast','Orography','Hydrology'",
    "type:'sea'",
    "mode==='landing'",
    "COAST_MAX_LANDING_DEPTH_U: CFG.DEPLOYMENT_DEPTH_U * .5",
    "Math.ceil(State.battleSetup.points/500)",
    "ctx.fillRect(0, 0, w, h)",
    "ROUT devia dalla costa",
]
for token in required:
    if token not in s:
        raise SystemExit(f'missing semantic token: {token}')

p.write_text(s, encoding='utf-8')
print('patched COFFEE_BATTLES.html -> v0.89.3 coast + border continuity')
