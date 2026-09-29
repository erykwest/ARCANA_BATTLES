from pathlib import Path
import re

p = Path('ARCANA_BATTLES.html')
s = p.read_text(encoding='utf-8')

s = s.replace('ARCANA — Campal Battle Lab v0.87.0', 'ARCANA — Campal Battle Lab v0.87.1')
s = s.replace('ARCANA — CAMPAL BATTLE LAB v0.87.0', 'ARCANA — CAMPAL BATTLE LAB v0.87.1')

s = s.replace("      if (DOM.removeDeployUnitBtn) DOM.removeDeployUnitBtn.disabled = autoPlayerDeploy;\n", "      if (DOM.removeDeployUnitBtn) DOM.removeDeployUnitBtn.disabled = false;\n")

old_cards = """        const blockedByMirror = State.battleSetup.mirrorArmy && side === 'red';
        const unaffordable = spent + cost > State.battleSetup.points;
        const lockedRoster = autoPlayerDeploy;
        card.classList.toggle('disabled', blockedByMirror || unaffordable || lockedRoster);
        card.disabled = blockedByMirror || unaffordable || lockedRoster;
        card.title = lockedRoster
          ? 'AUTO: composizione BLU già generata. Riposiziona le unità esistenti.'
          : blockedByMirror
            ? 'Mirror Army attivo: la composizione ROSSA replica automaticamente il BLU.'
            : (unaffordable ? 'Budget insufficiente.' : `Trascina ${this.spec(type).label} sul campo.`);
"""
new_cards = """        const blockedByMirror = State.battleSetup.mirrorArmy && side === 'red';
        const unaffordable = spent + cost > State.battleSetup.points;
        card.classList.toggle('disabled', blockedByMirror || unaffordable);
        card.disabled = blockedByMirror || unaffordable;
        card.title = blockedByMirror
          ? 'Mirror Army attivo: la composizione ROSSA replica automaticamente il BLU.'
          : (unaffordable ? 'Budget insufficiente.' : `Trascina ${this.spec(type).label} sul campo.`);
"""
assert old_cards in s
s = s.replace(old_cards, new_cards, 1)

s = s.replace("      if (State.deployment.active && State.battleSetup.mode === 'auto') return false;\n      const spec = this.spec(type);", "      if (State.deployment.active && State.battleSetup.mode === 'auto' && side !== 'blue') return false;\n      const spec = this.spec(type);", 1)

s = s.replace("    removeSelected() {\n      if (!State.deployment.active || State.battleSetup.mode === 'auto') return;\n      const selected = Selection.primary();\n      if (!selected) return;", "    removeSelected() {\n      if (!State.deployment.active) return;\n      const selected = Selection.primary();\n      if (!selected) return;\n      if (State.battleSetup.mode === 'auto' && selected.side !== 'blue') return;", 1)

s = s.replace("    beginCatalogDrag(type, e) {\n      if (!State.deployment.active || State.battleSetup.mode === 'auto') return;\n      const side = State.selectedSide;", "    beginCatalogDrag(type, e) {\n      if (!State.deployment.active) return;\n      const side = State.selectedSide;\n      if (State.battleSetup.mode === 'auto' && side !== 'blue') return;", 1)

old_auto = """      // BLU: composizione e dottrina esistono, ma lo schieramento resta al giocatore.
      const blueComposition = this.generateComposition(State.battleSetup.points);
      State.doctrine.compositions.blue = [...blueComposition.types];
      this.chooseDoctrine(blueComposition.types, 'blue', State.doctrine.roles.blue);
      this.stagePlayerComposition(blueComposition.types);

      Deployment.recount();
      State.selectedSide = 'blue';
      const first = State.units.find(u => u.side === 'blue') || null;
      State.selectedIds = new Set(first ? [first.id] : []);
      State.primaryId = first?.id || null;
      Deployment.updateUI();
      UI.updateSelectedInfo();

      for (const side of ['blue','red']) {
        const role = State.doctrine.roles[side].toUpperCase();
        const d = State.doctrine.selected[side];
        const spent = State.deployment.spent[side];
        Log.add(`DOCTRINE ${side.toUpperCase()} [${role}] → ${d.label} | ${spent}/${State.battleSetup.points} PT | score ${d.total.toFixed(2)} (army ${d.army.toFixed(2)} · terrain ${d.terrain.toFixed(2)} · role ${d.role.toFixed(0)})`);
      }

      const blueD = State.doctrine.selected.blue?.label || '—';
      const redD = State.doctrine.selected.red?.label || '—';
      DOM.deployHint.textContent = `AUTO · BLU ${State.doctrine.roles.blue.toUpperCase()}: composizione generata, SCHIERAMENTO MANUALE. ROSSO ${State.doctrine.roles.red.toUpperCase()}: ${redD}, già schierato ma NASCOSTO fino all'inizio.`;
"""
new_auto = """      // BLU parte VUOTO: composizione e schieramento appartengono interamente al giocatore.
      State.doctrine.compositions.blue = [];
      State.doctrine.selected.blue = null;
      State.doctrine.scores.blue = [];

      Deployment.recount();
      State.selectedSide = 'blue';
      State.selectedIds.clear();
      State.primaryId = null;
      Deployment.updateUI();
      UI.updateSelectedInfo();

      const redRole = State.doctrine.roles.red.toUpperCase();
      const spent = State.deployment.spent.red;
      Log.add(`DOCTRINE RED [${redRole}] → ${redDoctrine.label} | ${spent}/${State.battleSetup.points} PT | score ${redDoctrine.total.toFixed(2)} (army ${redDoctrine.army.toFixed(2)} · terrain ${redDoctrine.terrain.toFixed(2)} · role ${redDoctrine.role.toFixed(0)})`);
      DOM.deployHint.textContent = `AUTO · BLU ${State.doctrine.roles.blue.toUpperCase()}: ESERCITO VUOTO — scegli composizione e schieramento entro ${State.battleSetup.points} PT. ROSSO ${State.doctrine.roles.red.toUpperCase()}: già generato e schierato, NASCOSTO fino all'inizio.`;
"""
assert old_auto in s
s = s.replace(old_auto, new_auto, 1)

# Update visible footnote if present.
s = s.replace('v0.87 ·', 'v0.87.1 ·')

p.write_text(s, encoding='utf-8')
print('patched v0.87.1 blue-empty AUTO deployment')
