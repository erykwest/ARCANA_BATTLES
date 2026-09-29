from pathlib import Path

p = Path('COFFEE_BATTLES.html')
s = p.read_text(encoding='utf-8')

if 'Campal Battle Lab v0.88.3' not in s:
    raise SystemExit('Unexpected source version; refusing patch')


def once(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f'Missing patch anchor: {label}')
    s = s.replace(old, new, 1)


# Version.
s = s.replace('v0.88.3', 'v0.88.4')

# Wall rules.
once(
"    TERRAIN_SOFT_EDGE_U: 0.75, // fascia visibile esterna: accidentata ma non collider duro\n",
"    TERRAIN_SOFT_EDGE_U: 0.75, // fascia visibile esterna: accidentata ma non collider duro\n    WALL_CROSS_TIME_S: 4,\n    WALL_ADJACENCY_U: 1.6,\n",
'CFG wall constants')

once(
"        detour: null,       // A* runtime path; NON modifica la command chain\n        terrainClearanceBoostUntil: 0\n",
"        detour: null,       // A* runtime path; NON modifica la command chain\n        terrainClearanceBoostUntil: 0,\n        wallCrossing: null,  // { wallId, start, until } · attraversamento atomico 4s\n        wallPassId: null     // muro già pagato: ignorato finché il reparto lo ha completamente superato\n",
'motion wall state')

once(
"      if (t.type === 'wall') {\n        return this.unitSamplePoints(u).some(p => this.containsPoint(t, p, 0));\n      }\n",
"      if (t.type === 'wall') return false; // valicabile: il costo è temporale, non un collider duro\n",
'wall blocksUnit')

once(
"        const blocks = t.type === 'pond' || t.type === 'wall' || (t.type === 'forest' && u.type === 'cavalry');\n",
"        const blocks = t.type === 'pond' || (t.type === 'forest' && u.type === 'cavalry');\n",
'wall blocksPoint')

once(
"    rangedAttackPenalty(attacker,defender) {\n      const ac=Geometry.center(attacker),dc=Geometry.center(defender); let penalty=0;\n      for(const t of State.terrain) if(t.type==='forest'&&(this.containsPoint(t,ac,0)||this.containsPoint(t,dc,0))) penalty=Math.max(penalty,1);\n      return penalty;\n    },\n\n    rangedDefenseBonus(attacker,defender) {\n      const a=Geometry.center(attacker),d=Geometry.center(defender); let bonus=0;\n      for(const t of State.terrain) if(t.type==='wall'&&this.segmentIntersects(t,a,d)&&this.containsPoint(t,d,1.6*CFG.U)) bonus=Math.max(bonus,1);\n      return bonus;\n    },\n",
"    wallProtection(attacker, defender) {\n      if(!attacker?.status?.alive || !defender?.status?.alive) return 0;\n      const a=Geometry.center(attacker),d=Geometry.center(defender);\n      for(const t of State.terrain){\n        if(t.type!=='wall') continue;\n        if(!this.containsPoint(t,d,CFG.WALL_ADJACENCY_U*CFG.U)) continue;\n        if(this.segmentIntersects(t,a,d)) return 1;\n      }\n      return 0;\n    },\n\n    rangedAttackPenalty(attacker,defender) {\n      const ac=Geometry.center(attacker),dc=Geometry.center(defender); let penalty=0;\n      for(const t of State.terrain) if(t.type==='forest'&&(this.containsPoint(t,ac,0)||this.containsPoint(t,dc,0))) penalty=Math.max(penalty,1);\n      penalty=Math.max(penalty,this.wallProtection(attacker,defender));\n      return penalty;\n    },\n\n    rangedDefenseBonus(attacker,defender) {\n      // I muretti non aggiungono armatura: Cover 1 = -1 Mira all'attaccante.\n      return 0;\n    },\n",
'wall directional defense')

once(
"    segmentIntersects(t,a,b) {\n      const len=Math.hypot(b.x-a.x,b.y-a.y),steps=Math.max(10,Math.ceil(len/(0.45*CFG.U)));\n      for(let i=0;i<=steps;i++){const r=i/steps,p={x:a.x+(b.x-a.x)*r,y:a.y+(b.y-a.y)*r};if(this.containsPoint(t,p,0))return true;}\n      return false;\n    },\n",
"    segmentIntersects(t,a,b) {\n      const len=Math.hypot(b.x-a.x,b.y-a.y),steps=Math.max(10,Math.ceil(len/(0.45*CFG.U)));\n      for(let i=0;i<=steps;i++){const r=i/steps,p={x:a.x+(b.x-a.x)*r,y:a.y+(b.y-a.y)*r};if(this.containsPoint(t,p,0))return true;}\n      return false;\n    },\n\n    wallTouchesUnit(u, wall) {\n      if(!u?.status?.alive || wall?.type!=='wall') return false;\n      const a=this.localToWorld(wall,{x:-wall.w/2,y:0});\n      const b=this.localToWorld(wall,{x: wall.w/2,y:0});\n      if(Geometry.pointInUnit(u,a.x,a.y)||Geometry.pointInUnit(u,b.x,b.y)) return true;\n      const pts=Geometry.corners(u);\n      for(let i=0;i<pts.length;i++) if(Geometry.segmentsIntersect(pts[i],pts[(i+1)%pts.length],a,b)) return true;\n      return this.unitSamplePoints(u).some(p=>this.containsPoint(wall,p,0.08*CFG.U));\n    },\n\n    updateWallTraversal(u) {\n      const cross=u?.motion?.wallCrossing;\n      if(cross){\n        if(State.simTime < cross.until){u.motion.moving=false;return true;}\n        u.motion.wallPassId=cross.wallId;\n        u.motion.wallCrossing=null;\n        Log.add(`${u.name}: MURETTO SUPERATO | ${CFG.WALL_CROSS_TIME_S}s`);\n      }\n      if(u?.motion?.wallPassId){\n        const wall=State.terrain.find(t=>t.id===u.motion.wallPassId&&t.type==='wall');\n        if(!wall||!this.wallTouchesUnit(u,wall)) u.motion.wallPassId=null;\n      }\n      return false;\n    },\n\n    interceptWallTraversal(u, oldPose) {\n      if(!u?.status?.alive || !oldPose || u.motion.wallCrossing) return false;\n      const moved=Math.hypot(u.pose.x-oldPose.x,u.pose.y-oldPose.y);\n      if(moved < 0.01*CFG.U) return false;\n      const oldUnit={...u,pose:{...oldPose}};\n      for(const wall of State.terrain){\n        if(wall.type!=='wall'||wall.id===u.motion.wallPassId) continue;\n        if(!this.wallTouchesUnit(u,wall)||this.wallTouchesUnit(oldUnit,wall)) continue;\n        u.pose.x=oldPose.x;u.pose.y=oldPose.y;u.pose.angle=oldPose.angle;\n        u.motion.moving=false;\n        u.motion.wallCrossing={wallId:wall.id,start:State.simTime,until:State.simTime+CFG.WALL_CROSS_TIME_S};\n        Log.add(`${u.name}: SCAVALCA MURETTO | ${CFG.WALL_CROSS_TIME_S}s`);\n        return true;\n      }\n      return false;\n    },\n",
'wall traversal helpers')

once(
"    resolveMover(u, oldPose) {\n      if (Terrain.placementBlocked(u)) {\n",
"    resolveMover(u, oldPose) {\n      if (Terrain.interceptWallTraversal(u, oldPose)) return 'wall-crossing';\n      if (Terrain.placementBlocked(u)) {\n",
'wall traversal collision intercept')

once(
"    update(u, dt) {\n      u.motion.moving = false;\n      if (!u.status.alive) return;\n      if (u.status.routing) {\n",
"    update(u, dt) {\n      u.motion.moving = false;\n      if (!u.status.alive) return;\n      if (Terrain.updateWallTraversal(u)) return;\n      if (u.status.routing) {\n",
'wall traversal movement freeze')

once(
"      const ca = combatA === null ? this.effectiveCombat(a, pair) : Math.max(0, combatA);\n      const cb = combatB === null ? this.effectiveCombat(b, pair) : Math.max(0, combatB);\n      const scoreA = this.battleDie() + ca;\n      const scoreB = this.battleDie() + cb;\n",
"      let ca = combatA === null ? this.effectiveCombat(a, pair) : Math.max(0, combatA);\n      let cb = combatB === null ? this.effectiveCombat(b, pair) : Math.max(0, combatB);\n      if(pair){\n        ca=Math.max(0,ca-Terrain.wallProtection(a,b));\n        cb=Math.max(0,cb-Terrain.wallProtection(b,a));\n      }\n      const scoreA = this.battleDie() + ca;\n      const scoreB = this.battleDie() + cb;\n",
'melee wall combat penalty')

# Fields are the final generation layer.
once(
"    GENERATION_PHASES: Object.freeze(['Orography','Hydrology','Settlement','Buildings','Roads','Crossings','Tactical']),\n",
"    GENERATION_PHASES: Object.freeze(['Orography','Hydrology','Settlement','Buildings','Roads','Crossings','Tactical','Fields']),\n",
'fields generation priority')

once(
"makeBuilding(id,x,y,w=4,h=3,angle=0){return{id,type:'building',x,y,angle,w:w*CFG.U,h:h*CFG.U,fill:'#725647',edge:'#c39a79'};},\n",
"makeBuilding(id,x,y,w=4,h=3,angle=0){return{id,type:'building',x,y,angle,w:w*CFG.U,h:h*CFG.U,fill:'#725647',edge:'#c39a79'};},\nmakeField(id,x,y,wU,hU,angle=0){return{id,type:'field',x,y,angle,w:wU*CFG.U,h:hU*CFG.U,fill:'rgba(203,181,128,.34)',edge:'rgba(232,211,164,.46)'};},\nmakeFieldWalls(field){\n  const hw=field.w/2,hh=field.h/2;\n  const adjacent=[[0,1],[1,2],[2,3],[3,0]],opposite=[[0,2],[1,3]];\n  const chosen=Math.random()<.72?this.pick(adjacent):this.pick(opposite);\n  const defs=[\n    {p:{x:0,y:-hh},len:field.w,a:field.angle},\n    {p:{x:hw,y:0},len:field.h,a:field.angle+Math.PI/2},\n    {p:{x:0,y:hh},len:field.w,a:field.angle},\n    {p:{x:-hw,y:0},len:field.h,a:field.angle+Math.PI/2}\n  ];\n  return chosen.map((side,i)=>{const d=defs[side],p=Terrain.localToWorld(field,d.p);const w=this.makeWall(`${field.id}-wall-${i+1}`,p.x,p.y,d.len/CFG.U,.38,d.a);w.parentFieldId=field.id;w.fieldSide=side;return w;});\n},\n",
'field factories')

once(
"      if (['building','bridge','ford'].includes(t.type)) {\n",
"      if (['building','bridge','ford','field'].includes(t.type)) {\n",
'field shape samples')

once(
"      if (t.type==='building'||t.type==='bridge'||t.type==='ford') return Terrain.rectContains(t,point.x,point.y,pad);\n",
"      if (t.type==='building'||t.type==='bridge'||t.type==='ford'||t.type==='field') return Terrain.rectContains(t,point.x,point.y,pad);\n",
'field contains point')

once(
"    makeBiomeTerrain(biome) {\n",
"    generateFields(ctx) {\n      const ranges={plains:[2,4],hills:[1,3],valley:[1,3],river:[1,3],forest:[0,2],mountains:[0,1],village:[2,4]};\n      const [lo,hi]=ranges[ctx.biome]||[1,2],count=this.randi(lo,hi);\n      for(let i=0;i<count;i++){\n        let field=null;\n        for(let tries=0;tries<320;tries++){\n          const p=this.randomCenter(0),swap=Math.random()<.5;\n          const a=this.rand(4,10),b=this.rand(6,12),wU=swap?b:a,hU=swap?a:b;\n          const candidate=this.makeField(`field-${i+1}`,p.x,p.y,wU,hU,this.rand(-Math.PI,Math.PI));\n          if(!this.fitsZone(candidate)) continue;\n          if(ctx.placed.some(o=>this.overlaps(candidate,o,.20))) continue;\n          field=candidate;break;\n        }\n        if(!field) continue;\n        ctx.placed.push(field,...this.makeFieldWalls(field));\n      }\n    },\n\n    makeBiomeTerrain(biome) {\n",
'generate fields')

once(
"    drawExtras(items) {\n",
"    drawFields(items) {\n      for(const t of items){\n        ctx.save();ctx.translate(t.x,t.y);ctx.rotate(t.angle||0);\n        ctx.fillStyle=t.fill;ctx.strokeStyle=t.edge;ctx.lineWidth=1.2;\n        ctx.fillRect(-t.w/2,-t.h/2,t.w,t.h);ctx.strokeRect(-t.w/2,-t.h/2,t.w,t.h);\n        ctx.globalAlpha=.20;ctx.strokeStyle='#f0dfb8';ctx.lineWidth=1;\n        const step=Math.max(8,1.2*CFG.U);\n        for(let x=-t.w/2+step;x<t.w/2;x+=step){ctx.beginPath();ctx.moveTo(x,-t.h/2+2);ctx.lineTo(x,t.h/2-2);ctx.stroke();}\n        ctx.restore();\n      }\n    },\n\n    drawExtras(items) {\n",
'field renderer')

once(
"      Terrain.draw=()=>{\n        const all=State.terrain;\n        State.terrain=all.filter(t=>['road','hill','forest','rough','pond','wall'].includes(t.type)&&!(t.type==='hill'&&t.blob));\n        try{legacyDraw();}finally{State.terrain=all;}\n",
"      Terrain.draw=()=>{\n        const all=State.terrain;\n        this.drawFields(all.filter(t=>t.type==='field'));\n        State.terrain=all.filter(t=>['road','hill','forest','rough','pond','wall'].includes(t.type)&&!(t.type==='hill'&&t.blob));\n        try{legacyDraw();}finally{State.terrain=all;}\n",
'field draw ordering')

# Basic structural assertions before the CI syntax check.
for needle in [
    "'Tactical','Fields'",
    'WALL_CROSS_TIME_S: 4',
    'wallProtection(attacker, defender)',
    'interceptWallTraversal(u, oldPose)',
    'generateFields(ctx)',
    "type:'field'"
]:
    if needle not in s:
        raise SystemExit(f'Post-patch assertion failed: {needle}')

p.write_text(s, encoding='utf-8')
