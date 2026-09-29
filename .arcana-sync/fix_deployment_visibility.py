from pathlib import Path
p=Path('ARCANA_BATTLES.html')
s=p.read_text(encoding='utf-8')

def rep(old,new,label):
    global s
    n=s.count(old)
    if n!=1: raise SystemExit(f'{label}: expected 1, found {n}')
    s=s.replace(old,new,1)

s=s.replace('v0.86.0','v0.87.0')
s=s.replace('ARCHITETTURA v0.86:','ARCHITETTURA v0.87:')

rep("    unitCost(u) { return Number(u?.deployCost || this.spec(u?.type).cost || 0); },\n\n    recount() {",
"    unitCost(u) { return Number(u?.deployCost || this.spec(u?.type).cost || 0); },\n\n    enemyHiddenDuringSetup() {\n      return State.deployment.active && State.battleSetup.mode === 'auto';\n    },\n\n    visibleInDeployment(u) {\n      return !(this.enemyHiddenDuringSetup() && u?.side === 'red');\n    },\n\n    recount() {",'visibility helpers')

old="""    updateUI() {
      this.recount();
      const side = State.selectedSide;
      const spent = State.deployment.spent[side] || 0;
      DOM.deploySpent.textContent = spent;
      DOM.deployBudget.textContent = State.battleSetup.points;
      DOM.deployBlueBtn.classList.toggle('active', side === 'blue');
      DOM.deployRedBtn.classList.toggle('active', side === 'red');
      DOM.sideBlueBtn?.classList.toggle('active', side === 'blue');
      DOM.sideRedBtn?.classList.toggle('active', side === 'red');
      DOM.deploymentCards.querySelectorAll('.unit-card').forEach(card => {
        const type = card.dataset.unitType;
        const cost = this.spec(type).cost;
        const blockedByMirror = State.battleSetup.mirrorArmy && side === 'red';
        const unaffordable = spent + cost > State.battleSetup.points;
        card.classList.toggle('disabled', blockedByMirror || unaffordable);
        card.disabled = blockedByMirror || unaffordable;
        card.title = blockedByMirror
          ? 'Mirror Army attivo: la composizione ROSSA replica automaticamente il BLU.'
          : (unaffordable ? 'Budget insufficiente.' : `Trascina ${this.spec(type).label} sul campo.`);
      });
    },

    setSide(side) {
      if (!State.deployment.active) return false;
      State.selectedSide = side;
      Selection.clear();
      this.updateUI();
      return true;
    },"""
new="""    updateUI() {
      this.recount();
      const autoPlayerDeploy = State.deployment.active && State.battleSetup.mode === 'auto';
      if (autoPlayerDeploy) State.selectedSide = 'blue';
      const side = State.selectedSide;
      const spent = State.deployment.spent[side] || 0;
      DOM.deploySpent.textContent = spent;
      DOM.deployBudget.textContent = State.battleSetup.points;
      DOM.deployBlueBtn.classList.toggle('active', side === 'blue');
      DOM.deployRedBtn.classList.toggle('active', side === 'red');
      DOM.deployRedBtn.style.display = autoPlayerDeploy ? 'none' : '';
      if (DOM.sideRedBtn) DOM.sideRedBtn.disabled = autoPlayerDeploy;
      if (DOM.sideBlueBtn) DOM.sideBlueBtn.disabled = false;
      DOM.sideBlueBtn?.classList.toggle('active', side === 'blue');
      DOM.sideRedBtn?.classList.toggle('active', side === 'red');
      if (DOM.removeDeployUnitBtn) DOM.removeDeployUnitBtn.disabled = autoPlayerDeploy;
      DOM.deploymentCards.querySelectorAll('.unit-card').forEach(card => {
        const type = card.dataset.unitType;
        const cost = this.spec(type).cost;
        const blockedByMirror = State.battleSetup.mirrorArmy && side === 'red';
        const unaffordable = spent + cost > State.battleSetup.points;
        const lockedRoster = autoPlayerDeploy;
        card.classList.toggle('disabled', blockedByMirror || unaffordable || lockedRoster);
        card.disabled = blockedByMirror || unaffordable || lockedRoster;
        card.title = lockedRoster
          ? 'AUTO: composizione BLU già generata. Riposiziona le unità esistenti.'
          : blockedByMirror
            ? 'Mirror Army attivo: la composizione ROSSA replica automaticamente il BLU.'
            : (unaffordable ? 'Budget insufficiente.' : `Trascina ${this.spec(type).label} sul campo.`);
      });
    },

    setSide(side) {
      if (!State.deployment.active) return false;
      if (State.battleSetup.mode === 'auto' && side !== 'blue') return false;
      State.selectedSide = side;
      Selection.clear();
      this.updateUI();
      return true;
    },"""
rep(old,new,'deployment ui')

rep("    placeFromCatalog(side, type, x, y) {\n      const spec = this.spec(type);",
"    placeFromCatalog(side, type, x, y) {\n      if (State.deployment.active && State.battleSetup.mode === 'auto') return false;\n      const spec = this.spec(type);",'catalog guard')
rep("    removeSelected() {\n      if (!State.deployment.active) return;",
"    removeSelected() {\n      if (!State.deployment.active || State.battleSetup.mode === 'auto') return;",'remove guard')
rep("    beginCatalogDrag(type, e) {\n      if (!State.deployment.active) return;",
"    beginCatalogDrag(type, e) {\n      if (!State.deployment.active || State.battleSetup.mode === 'auto') return;",'drag catalog guard')
rep("    beginUnitDrag(u, e) {\n      if (!State.deployment.active || !u) return;",
"    beginUnitDrag(u, e) {\n      if (!State.deployment.active || !u) return;\n      if (State.battleSetup.mode === 'auto' && u.side !== 'blue') return;",'drag red guard')

rep("    hitUnit(worldPoint) {\n      return [...State.units].reverse().find(u => u.status.alive && Geometry.pointInUnit(u, worldPoint.x, worldPoint.y)) || null;\n    },",
"    hitUnit(worldPoint) {\n      return [...State.units].reverse().find(u =>\n        u.status.alive && Deployment.visibleInDeployment(u) && Geometry.pointInUnit(u, worldPoint.x, worldPoint.y)\n      ) || null;\n    },",'hit hidden red')

rep("      const rz = Deployment.zone('red');\n      ctx.save();",
"      const rz = Deployment.zone('red');\n      const hideRed = Deployment.enemyHiddenDuringSetup();\n      ctx.save();",'overlay hide flag')
rep("      ctx.fillStyle = 'rgba(207,77,77,.10)';\n      ctx.fillRect(rz.x, rz.y, rz.w, rz.h);",
"      if (!hideRed) {\n        ctx.fillStyle = 'rgba(207,77,77,.10)';\n        ctx.fillRect(rz.x, rz.y, rz.w, rz.h);\n      }",'overlay red fill')
rep("      ctx.strokeStyle = 'rgba(235,104,104,.70)';\n      ctx.strokeRect(rz.x, rz.y, rz.w, rz.h);",
"      if (!hideRed) {\n        ctx.strokeStyle = 'rgba(235,104,104,.70)';\n        ctx.strokeRect(rz.x, rz.y, rz.w, rz.h);\n      }",'overlay red stroke')
rep("      ctx.fillStyle = 'rgba(255,170,170,.85)';\n      ctx.fillText('ZONA SCHIERAMENTO ROSSO', rz.x + 8, rz.y + 8);",
"      if (!hideRed) {\n        ctx.fillStyle = 'rgba(255,170,170,.85)';\n        ctx.fillText('ZONA SCHIERAMENTO ROSSO', rz.x + 8, rz.y + 8);\n      }",'overlay red label')

old="""      this.deploymentOverlay();
      State.units.forEach(u => this.orders(u));
      const p = Selection.primary();
      if (p) this.lock(p);
      State.units.forEach(u => this.unit(u));
      this.projectiles();"""
new="""      this.deploymentOverlay();
      const visibleUnits = State.units.filter(u => Deployment.visibleInDeployment(u));
      visibleUnits.filter(u => u.side === State.battle.playerSide).forEach(u => this.orders(u));
      const p = Selection.primary();
      if (p && Deployment.visibleInDeployment(p)) this.lock(p);
      visibleUnits.forEach(u => this.unit(u));
      this.projectiles();"""
rep(old,new,'renderer visible units')
rep("      State.units.forEach(u => this.hud(u));\n      this.selectionBox();",
"      const hudUnits = State.units.filter(u => Deployment.visibleInDeployment(u));\n      hudUnits.forEach(u => this.hud(u));\n      this.selectionBox();",'hud hidden red')

insert="""
    stagePlayerComposition(types) {
      for (const type of types) {
        const pose = Deployment.stagingPose('blue', type);
        if (!pose) continue;
        const u = Deployment.makeDeployUnit('blue', type, pose.x, pose.y, pose.angle);
        if (Deployment.validPlacement(u)) State.units.push(u);
        else State.deployment.counters.blue -= 1;
      }
    },

"""
rep("    autoSetup() {\n      State.units = [];",insert+"    autoSetup() {\n      State.units = [];",'stage player composition')

old="""      for (const side of ['blue','red']) {
        const composition = this.generateComposition(State.battleSetup.points);
        State.doctrine.compositions[side] = [...composition.types];
        const chosen = this.chooseDoctrine(composition.types, side, State.doctrine.roles[side]);
        this.deployComposition(side, composition.types, chosen, State.doctrine.roles[side]);
      }

      Deployment.recount();"""
new="""      // ROSSO viene risolto per primo e quindi non può reagire allo schieramento BLU.
      const redComposition = this.generateComposition(State.battleSetup.points);
      State.doctrine.compositions.red = [...redComposition.types];
      const redDoctrine = this.chooseDoctrine(redComposition.types, 'red', State.doctrine.roles.red);
      this.deployComposition('red', redComposition.types, redDoctrine, State.doctrine.roles.red);

      // BLU: composizione e dottrina esistono, ma lo schieramento resta al giocatore.
      const blueComposition = this.generateComposition(State.battleSetup.points);
      State.doctrine.compositions.blue = [...blueComposition.types];
      this.chooseDoctrine(blueComposition.types, 'blue', State.doctrine.roles.blue);
      this.stagePlayerComposition(blueComposition.types);

      Deployment.recount();"""
rep(old,new,'auto setup order')
rep("      DOM.deployHint.textContent = `AUTO · BLU ${State.doctrine.roles.blue.toUpperCase()}: ${blueD} · ROSSO ${State.doctrine.roles.red.toUpperCase()}: ${redD}. Schieramento generato; nessun ordine iniziale applicato (unità in Hold).`;",
"      DOM.deployHint.textContent = `AUTO · BLU ${State.doctrine.roles.blue.toUpperCase()}: composizione generata, SCHIERAMENTO MANUALE. ROSSO ${State.doctrine.roles.red.toUpperCase()}: ${redD}, già schierato ma NASCOSTO fino all'inizio.`;",'auto hint')

p.write_text(s,encoding='utf-8')
print('deployment visibility patch OK')
