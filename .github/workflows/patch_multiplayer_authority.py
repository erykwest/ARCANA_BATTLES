from pathlib import Path
p=Path('COFFEE_BATTLES.html')
s=p.read_text(encoding='utf-8')

def one(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1 anchor, found {n}')
    s=s.replace(old,new,1)

def between(start,end,new,label):
    global s
    a=s.find(start)
    if a<0: raise SystemExit(f'{label}: start not found')
    b=s.find(end,a)
    if b<0: raise SystemExit(f'{label}: end not found')
    s=s[:a]+new+s[b:]

# CSS: no player time controls online
one("  body.deployment-active #timeControls,body.deployment-active #victoryBar{display:none}\n",
    "  body.deployment-active #timeControls,body.deployment-active #victoryBar{display:none}\n  body.multiplayer-active #timeControls{display:none!important}\n",
    'multiplayer time css')

# Red/blue deployment zone: online shows only own zone
between("    deploymentOverlay() {", "    orders(u) {", r'''    deploymentOverlay() {
      if (!State.deployment.active) return;
      const multiplayer = Deployment.multiplayerActive();
      const playerSide = Deployment.multiplayerSide();
      const bz = Deployment.zone('blue');
      const rz = Deployment.zone('red');
      ctx.save();

      const drawZone = side => {
        const z = side === 'blue' ? bz : rz;
        const blue = side === 'blue';
        ctx.fillStyle = blue ? 'rgba(91,143,209,.12)' : 'rgba(217,86,58,.12)';
        ctx.fillRect(z.x, z.y, z.w, z.h);
        ctx.setLineDash([7,6]);
        ctx.lineWidth = 2;
        ctx.strokeStyle = blue ? 'rgba(128,170,224,.70)' : 'rgba(232,120,92,.70)';
        ctx.strokeRect(z.x, z.y, z.w, z.h);
        ctx.setLineDash([]);
        ctx.font = 'bold 13px Segoe UI, Arial';
        ctx.textBaseline = 'top';
        ctx.fillStyle = blue ? 'rgba(176,204,238,.88)' : 'rgba(246,184,160,.88)';
        ctx.fillText(I18n.t(blue ? 'deploy.zoneBlue' : 'deploy.zoneRed'), z.x + 8, z.y + 8);
      };

      if (multiplayer) drawZone(playerSide);
      else { drawZone('blue'); if (!Deployment.enemyHiddenDuringSetup()) drawZone('red'); }

      const d = State.deployment.drag;
      if (d?.kind === 'catalog' && d.ghost) {
        const pts = Geometry.corners(d.ghost);
        ctx.beginPath();
        pts.forEach((p,i) => i ? ctx.lineTo(p.x,p.y) : ctx.moveTo(p.x,p.y));
        ctx.closePath();
        ctx.fillStyle = d.valid ? 'rgba(94,200,113,.30)' : 'rgba(218,75,75,.30)';
        ctx.strokeStyle = d.valid ? 'rgba(126,239,145,.95)' : 'rgba(255,116,116,.95)';
        ctx.lineWidth = 2;
        ctx.fill(); ctx.stroke();
        const dms = Geometry.dims(d.ghost);
        const nx = -Math.sin(d.ghost.pose.angle), ny = Math.cos(d.ghost.pose.angle);
        ctx.beginPath();
        ctx.moveTo(d.ghost.pose.x - nx * dms.front/2, d.ghost.pose.y - ny * dms.front/2);
        ctx.lineTo(d.ghost.pose.x + nx * dms.front/2, d.ghost.pose.y + ny * dms.front/2);
        ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 3; ctx.stroke();
        ctx.font = 'bold 11px Segoe UI, Arial';
        ctx.fillStyle = '#fff'; ctx.textAlign='center'; ctx.textBaseline='bottom';
        ctx.fillText(`${I18n.unit(d.type)} · ${Deployment.spec(d.type).cost} PT`, d.ghost.pose.x, d.ghost.pose.y - 12);
      }
      ctx.restore();
    },

''', 'deployment overlay')

# Online player can never switch side
one("    switchSide(side) {\n      State.selectedSide = side;",
    "    switchSide(side) {\n      if (window.__CB_MULTIPLAYER_ACTIVE__ && side !== window.__CB_MULTIPLAYER_SIDE__) return false;\n      State.selectedSide = side;",
    'side lock')

# Semantic commands
between("    moveGroup(point, append = false) {", "    lockGroup(enemy, append = false) {", r'''    moveGroup(point, append = false) {
      const group = this.current().filter(u => !u.status.routing && !Engagements.hasAny(u) && u.stats.energy > 0.0001);
      if (!group.length) return;
      const cx = group.reduce((sum,u) => sum + u.pose.x, 0) / group.length;
      const cy = group.reduce((sum,u) => sum + u.pose.y, 0) / group.length;
      const targets = [];
      for (const u of group) {
        const target = { x:point.x + u.pose.x - cx, y:point.y + u.pose.y - cy };
        Orders.setManual(u, target, append);
        targets.push({ id:u.id, x:target.x, y:target.y });
      }
      if (window.__CB_MULTIPLAYER_ACTIVE__ && !window.__CB_MULTIPLAYER_APPLYING__) window.__CB_MULTIPLAYER_SEND_COMMAND__?.({type:'move', units:targets, append:!!append});
      Log.add(`SELEZIONE (${group.length}): ${append ? 'waypoint concatenato' : 'nuovo ordine di movimento'}.`);
    },

''', 'move command')

between("    lockGroup(enemy, append = false) {", "    setStance(type) {", r'''    lockGroup(enemy, append = false) {
      const group = this.current();
      for (const u of group) {
        const hasManualChain = u.order.kind === 'manual' && (!!u.order.target || u.order.queue.length > 0);
        if (append || hasManualChain) Orders.appendAttack(u, enemy);
        else Orders.setLock(u, enemy);
      }
      if (group.length && enemy && window.__CB_MULTIPLAYER_ACTIVE__ && !window.__CB_MULTIPLAYER_APPLYING__) window.__CB_MULTIPLAYER_SEND_COMMAND__?.({type:'attack', unitIds:group.map(u=>u.id), targetId:enemy.id, append:!!append});
      UI.updateSelectedInfo();
    },

''', 'attack command')

between("    setStance(type) {", "    setFormation(type) {", r'''    setStance(type) {
      const group = this.current();
      for (const u of group) {
        if (!u.status.alive || u.status.routing) continue;
        u.behavior.stance = type;
        if (u.order.kind === 'ai') Orders.clear(u);
      }
      if (group.length && window.__CB_MULTIPLAYER_ACTIVE__ && !window.__CB_MULTIPLAYER_APPLYING__) window.__CB_MULTIPLAYER_SEND_COMMAND__?.({type:'stance', unitIds:group.map(u=>u.id), value:type});
      Log.add(`SELEZIONE (${group.length}): stance ${type.toUpperCase()}`);
      UI.updateSelectedInfo();
    },

''', 'stance command')

between("    setFormation(type) {", "    toggleCharge() {", r'''    setFormation(type) {
      const group = this.current();
      let changed = 0;
      for (const u of group) if (Formations.set(u, type)) changed++;
      if (group.length && window.__CB_MULTIPLAYER_ACTIVE__ && !window.__CB_MULTIPLAYER_APPLYING__) window.__CB_MULTIPLAYER_SEND_COMMAND__?.({type:'formation', unitIds:group.map(u=>u.id), value:type});
      if (changed) Log.add(`SELEZIONE (${changed}): formazione → ${CFG.FORMATIONS[type].label} | 2s`);
      UI.updateSelectedInfo();
    },

''', 'formation command')

between("    toggleCharge() {", "    retreat() {", r'''    toggleCharge() {
      const group = this.current().filter(u => u.status.alive && !Engagements.hasAny(u) && !u.status.routing && u.order.kind !== 'retreat' && u.stats.energy > 0.0001);
      if (!group.length) return;
      const enable = group.some(u => !u.motion.chargeMode);
      for (const u of group) {
        u.motion.chargeOverride = enable;
        u.motion.chargeMode = enable;
        u.motion.moveMult = enable ? u.profile.chargeMult : u.profile.marchMult;
      }
      if (window.__CB_MULTIPLAYER_ACTIVE__ && !window.__CB_MULTIPLAYER_APPLYING__) window.__CB_MULTIPLAYER_SEND_COMMAND__?.({type:'charge', unitIds:group.map(u=>u.id), value:enable});
      const speeds = group.map(u => `${u.name}:M${u.motion.moveMult}`).join(' · ');
      Log.add(`SELEZIONE (${group.length}): ${enable ? 'CARICA MANUALE ON' : 'CARICA MANUALE OFF'} | ${speeds}`);
      UI.updateSelectedInfo();
    },

''', 'charge command')

between("    retreat() {", "    toggleFireAtWill() {", r'''    retreat() {
      let started = 0;
      const ids = [];
      for (const u of this.current()) if (Orders.startRetreat(u)) { started++; ids.push(u.id); }
      if (ids.length && window.__CB_MULTIPLAYER_ACTIVE__ && !window.__CB_MULTIPLAYER_APPLYING__) window.__CB_MULTIPLAYER_SEND_COMMAND__?.({type:'retreat', unitIds:ids});
      if (started) Log.add(`SELEZIONE (${started}): RITIRATA a ≥${CFG.RETREAT_DISTANCE_U}U`);
      UI.updateSelectedInfo();
    },

''', 'retreat command')

between("    toggleFireAtWill() {", "  };\n\n  // ============================================================\n  // 11. VIEW + RENDERER", r'''    toggleFireAtWill() {
      const archers = this.current().filter(u => u.status.alive && u.ranged);
      if (!archers.length) return;
      const enable = archers.some(u => !u.ranged.fireAtWill);
      for (const u of archers) {
        u.ranged.fireAtWill = enable;
        u.ranged.clock = 0;
        u.ranged.active = false;
        u.ranged.targetId = null;
        if (enable && !Engagements.hasAny(u) && u.order.kind === 'ai') {
          u.order.target = null; u.order.queue = []; u.order.approach = null;
          if (u.motion.turn?.kind === 'flip') u.motion.turn = null;
          u.ranged.approachTargetId = null;
        }
        if (!enable && u.order.kind !== 'lock') u.ranged.approachTargetId = null;
      }
      if (window.__CB_MULTIPLAYER_ACTIVE__ && !window.__CB_MULTIPLAYER_APPLYING__) window.__CB_MULTIPLAYER_SEND_COMMAND__?.({type:'fire', unitIds:archers.map(u=>u.id), value:enable});
      Log.add(`RANGED (${archers.length}): FUOCO A VOLONTÀ ${enable ? 'ON' : 'OFF'}`);
      UI.updateSelectedInfo();
    }
  };

  // ============================================================
  // 11. VIEW + RENDERER''', 'fire command')

# Fixed multiplayer clock, host simulates, red follows authority snapshots
between("    setTimeScale(scale) {", "    effectiveFrontageDisplay(u) {", r'''    setTimeScale(scale) {
      if (window.__CB_MULTIPLAYER_ACTIVE__ && State.battle.active && !State.battle.ended) scale = window.__CB_MULTIPLAYER_AUTHORITY__ ? 1 : 0;
      State.timeScale = scale;
      Object.values(DOM.time).forEach(b => b.classList.remove('active'));
      if (scale === 0) DOM.time.pause.classList.add('active');
      if (scale === 1) DOM.time.x1.classList.add('active');
      if (scale === 2) DOM.time.x2.classList.add('active');
      if (scale === 3) DOM.time.x3.classList.add('active');
    },

''', 'fixed clock')

one("    show() {\n      if (this.open) return;",
    "    show() {\n      if (window.__CB_MULTIPLAYER_ACTIVE__ && State.battle.active && !State.battle.ended) return;\n      if (this.open) return;",
    'source pause guard')

# FOW regression: active battle, correct side, no Army AI
between("    finishMultiplayer(snapshot) {", "    pointerWorld(e) {", r'''    finishMultiplayer(snapshot) {
      if (!Array.isArray(snapshot) || !snapshot.length) return false;
      const blue = snapshot.filter(d => d.side === 'blue').length;
      const red = snapshot.filter(d => d.side === 'red').length;
      if (!blue || !red) return false;
      State.deployment.snapshot = snapshot.map(d => ({...d}));
      State.units = snapshot.map(d => {
        const u = makeUnit(d.id,d.name,d.side,d.x,d.y,d.angle,d.color,d.type);
        u.formation.type = d.formation || 'base';
        u.deployCost = d.deployCost || this.spec(d.type).cost;
        u.deployPairId = d.deployPairId || null;
        return u;
      });
      State.deployment.active = false;
      State.deployment.drag = null;
      document.body.classList.remove('deployment-active');
      document.body.classList.add('multiplayer-active');
      const side = this.multiplayerSide();
      State.armyAI.enabled = false;
      State.battle.playerSide = side;
      State.selectedSide = side;
      Battle.reset(true);
      State.battle.playerSide = side;
      Intel.reset();
      const first = State.units.find(u => u.side === side) || null;
      State.selectedIds = new Set(first ? [first.id] : []);
      State.primaryId = first?.id || null;
      if (DOM.sideBlueBtn) DOM.sideBlueBtn.disabled = true;
      if (DOM.sideRedBtn) DOM.sideRedBtn.disabled = true;
      if (DOM.resetBtn) DOM.resetBtn.disabled = true;
      if (DOM.newBattleBtn) DOM.newBattleBtn.disabled = true;
      UI.setTimeScale(window.__CB_MULTIPLAYER_AUTHORITY__ ? 1 : 0);
      Log.add(`🌐 MULTIPLAYER START · BLU ${blue} unità / ROSSO ${red} unità · ${window.__CB_MULTIPLAYER_AUTHORITY__ ? 'CLIENT AUTOREVOLE' : 'CLIENT SINCRONIZZATO'}`);
      this.updateUI();
      UI.updateSelectedInfo();
      return true;
    },

''', 'finish multiplayer')

one("  let activeMatch = null, deploymentPollTimer = null, deploymentFinalizing = false;",
    "  let activeMatch = null, deploymentPollTimer = null, deploymentFinalizing = false;\n  let matchChannel = null, authoritySnapshotTimer = null, commandSeq = 0, lastRemoteSeq = 0;",
    'network vars')

marker="  function stopDeploymentPolling(){"
insert=r'''  function clonePlain(value){
    return value == null ? value : JSON.parse(JSON.stringify(value, (_k,v) => v instanceof Set ? [...v] : v));
  }

  async function stopMatchChannel(){
    if (matchChannel && client) await client.removeChannel(matchChannel);
    matchChannel = null;
  }

  function stopAuthoritySnapshots(){ clearInterval(authoritySnapshotTimer); authoritySnapshotTimer = null; }

  function commandUnits(dbg, ids, side){
    return (Array.isArray(ids) ? ids : []).map(id => dbg.Units.byId(id)).filter(u => u?.status?.alive && u.side === side);
  }

  function applyAuthorityCommand(envelope){
    if (!activeMatch || activeMatch.side !== 'blue') return;
    if (!envelope || envelope.match_id !== activeMatch.id || envelope.side !== 'red') return;
    if ((envelope.seq || 0) <= lastRemoteSeq) return;
    lastRemoteSeq = envelope.seq || lastRemoteSeq;
    const cmd = envelope.command || {};
    const dbg = deploymentDebug();
    if (!dbg) return;
    window.__CB_MULTIPLAYER_APPLYING__ = true;
    try {
      if (cmd.type === 'move') {
        for (const t of Array.isArray(cmd.units) ? cmd.units : []) {
          const u = dbg.Units.byId(t.id);
          if (!u?.status?.alive || u.side !== 'red') continue;
          dbg.Orders.setManual(u,{x:Number(t.x)||0,y:Number(t.y)||0},!!cmd.append);
        }
      } else if (cmd.type === 'attack') {
        const enemy = dbg.Units.byId(cmd.targetId);
        if (!enemy?.status?.alive || enemy.side === 'red') return;
        for (const u of commandUnits(dbg,cmd.unitIds,'red')) {
          const chain = u.order.kind === 'manual' && (!!u.order.target || u.order.queue.length>0);
          if (cmd.append || chain) dbg.Orders.appendAttack(u,enemy); else dbg.Orders.setLock(u,enemy);
        }
      } else if (cmd.type === 'stance') {
        for (const u of commandUnits(dbg,cmd.unitIds,'red')) { u.behavior.stance=cmd.value; if (u.order.kind==='ai') dbg.Orders.clear(u); }
      } else if (cmd.type === 'formation') {
        for (const u of commandUnits(dbg,cmd.unitIds,'red')) dbg.Formations.set(u,cmd.value);
      } else if (cmd.type === 'charge') {
        for (const u of commandUnits(dbg,cmd.unitIds,'red')) { const en=!!cmd.value; u.motion.chargeOverride=en; u.motion.chargeMode=en; u.motion.moveMult=en?u.profile.chargeMult:u.profile.marchMult; }
      } else if (cmd.type === 'retreat') {
        for (const u of commandUnits(dbg,cmd.unitIds,'red')) dbg.Orders.startRetreat(u);
      } else if (cmd.type === 'fire') {
        for (const u of commandUnits(dbg,cmd.unitIds,'red')) {
          if (!u.ranged) continue;
          const en=!!cmd.value; u.ranged.fireAtWill=en; u.ranged.clock=0; u.ranged.active=false; u.ranged.targetId=null;
          if (en && !dbg.Engagements.hasAny(u) && u.order.kind==='ai') { u.order.target=null;u.order.queue=[];u.order.approach=null;if(u.motion.turn?.kind==='flip')u.motion.turn=null;u.ranged.approachTargetId=null; }
          if (!en && u.order.kind!=='lock') u.ranged.approachTargetId=null;
        }
      }
    } finally { window.__CB_MULTIPLAYER_APPLYING__ = false; }
  }

  function serializeAuthorityState(){
    const dbg=deploymentDebug(); if(!dbg||!activeMatch)return null;
    const st=dbg.State;
    return {
      match_id:activeMatch.id, side:'blue', simTime:st.simTime,
      battle:{ended:!!st.battle.ended,result:st.battle.result||null,armyCollapse:clonePlain(st.battle.armyCollapse)},
      projectiles:clonePlain(st.projectiles),
      units:st.units.map(u=>{
        const status={...u.status}; delete status.friendlyFleeImpactVictims;
        return {id:u.id,pose:clonePlain(u.pose),stats:clonePlain(u.stats),battleRecord:clonePlain(u.battleRecord),formation:clonePlain(u.formation),behavior:clonePlain(u.behavior),order:clonePlain(u.order),motion:clonePlain(u.motion),engagement:clonePlain(u.engagement),ranged:clonePlain(u.ranged),status:clonePlain(status)};
      })
    };
  }

  function applyAuthorityState(snapshot){
    if(!activeMatch||activeMatch.side!=='red'||!snapshot||snapshot.match_id!==activeMatch.id||snapshot.side!=='blue')return;
    const dbg=deploymentDebug(); if(!dbg)return;
    const st=dbg.State;
    for(const row of Array.isArray(snapshot.units)?snapshot.units:[]){
      const u=dbg.Units.byId(row.id); if(!u)continue;
      Object.assign(u.pose,row.pose||{}); Object.assign(u.stats,row.stats||{}); Object.assign(u.battleRecord,row.battleRecord||{});
      if(row.formation)u.formation=clonePlain(row.formation);
      if(row.behavior)u.behavior=clonePlain(row.behavior);
      if(row.order)u.order=clonePlain(row.order);
      if(row.motion)u.motion=clonePlain(row.motion);
      if(row.engagement)u.engagement=clonePlain(row.engagement);
      if(u.ranged&&row.ranged)u.ranged=clonePlain(row.ranged);
      if(row.status)Object.assign(u.status,row.status);
      if(!(u.status.friendlyFleeImpactVictims instanceof Set))u.status.friendlyFleeImpactVictims=new Set();
    }
    st.simTime=Number(snapshot.simTime)||0;
    st.projectiles=clonePlain(snapshot.projectiles)||[];
    dbg.Intel.update(); dbg.Battle.updateVictoryBar();
    if(snapshot.battle?.ended&&!st.battle.ended){
      const hr=snapshot.battle.result; const lr=hr==='victory'?'defeat':(hr==='defeat'?'victory':'draw');
      dbg.Battle.showResult(lr,'Risultato sincronizzato dal client autorevole.');
    }
  }

  async function sendBattleCommand(command){
    if(!activeMatch||!matchChannel||activeMatch.side!=='red')return;
    commandSeq+=1;
    await matchChannel.send({type:'broadcast',event:'battle-command',payload:{match_id:activeMatch.id,side:'red',seq:commandSeq,command}});
  }

  async function sendAuthoritySnapshot(){
    if(!activeMatch||activeMatch.side!=='blue'||!matchChannel)return;
    const snap=serializeAuthorityState(); if(!snap)return;
    await matchChannel.send({type:'broadcast',event:'battle-state',payload:snap});
    if(snap.battle?.ended)stopAuthoritySnapshots();
  }

  function startAuthoritySnapshots(){
    stopAuthoritySnapshots();
    if(!activeMatch||activeMatch.side!=='blue')return;
    sendAuthoritySnapshot();
    authoritySnapshotTimer=setInterval(sendAuthoritySnapshot,100);
  }

  async function startMatchChannel(matchId){
    await stopMatchChannel(); lastRemoteSeq=0; commandSeq=0;
    matchChannel=client.channel(`coffee-battles-match-${matchId}`,{config:{broadcast:{self:false,ack:false}}});
    matchChannel.on('broadcast',{event:'battle-command'},({payload})=>applyAuthorityCommand(payload)).on('broadcast',{event:'battle-state'},({payload})=>applyAuthorityState(payload)).subscribe();
  }

'''
if marker not in s: raise SystemExit('transport marker missing')
s=s.replace(marker,insert+marker,1)

one("    stopDeploymentPolling();\n    window.__CB_MULTIPLAYER_DEPLOYMENT_LOCKED__ = false;\n    UI.matchTitle.textContent = 'DEPLOYMENT SYNCED';\n    UI.matchStatus.textContent = 'Both clients now have the same battlefield and both armies.';\n    UI.searchLine.style.display = 'none';\n    UI.side.className = activeMatch.side;\n    UI.side.textContent = `YOU ARE ${activeMatch.side.toUpperCase()}`;\n    UI.matchId.textContent = `MATCH ${activeMatch.id}`;\n    UI.proceed.hidden = true;\n    UI.cancel.textContent = 'CLOSE';\n    UI.note.textContent = 'M0 deployment sync complete. Battle remains paused: command/state synchronization is the next layer.';\n    UI.matchOverlay.classList.add('open');\n    deploymentFinalizing = false;",
    "    stopDeploymentPolling();\n    window.__CB_MULTIPLAYER_DEPLOYMENT_LOCKED__ = false;\n    UI.matchOverlay.classList.remove('open');\n    if (activeMatch.side === 'blue') startAuthoritySnapshots();\n    deploymentFinalizing = false;",
    'finalize starts match')

one("    window.__CB_MULTIPLAYER_ACTIVE__ = true;\n    window.__CB_MULTIPLAYER_SIDE__ = side;\n    window.__CB_MULTIPLAYER_SETUP__ = setup;",
    "    window.__CB_MULTIPLAYER_ACTIVE__ = true;\n    window.__CB_MULTIPLAYER_SIDE__ = side;\n    window.__CB_MULTIPLAYER_AUTHORITY__ = side === 'blue';\n    window.__CB_MULTIPLAYER_SETUP__ = setup;",
    'authority flag')

one("    window.__CB_MULTIPLAYER_SUBMIT_DEPLOYMENT__ = submitDeployment;",
    "    window.__CB_MULTIPLAYER_SUBMIT_DEPLOYMENT__ = submitDeployment;\n    window.__CB_MULTIPLAYER_SEND_COMMAND__ = sendBattleCommand;",
    'sender bridge')

one("    activeMatch = { id:matchId, side, setup };\n    searching = false;",
    "    activeMatch = { id:matchId, side, setup };\n    await startMatchChannel(matchId);\n    searching = false;",
    'channel before deploy')

p.write_text(s,encoding='utf-8')
print('multiplayer authority patch applied')