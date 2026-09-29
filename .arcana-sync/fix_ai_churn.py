from pathlib import Path
p=Path('ARCANA_BATTLES.html')
s=p.read_text(encoding='utf-8')

def rep(old,new,label):
    global s
    n=s.count(old)
    if n!=1: raise SystemExit(f'{label}: expected 1, found {n}')
    s=s.replace(old,new,1)

rep("    APPROACH_REACHED_U: 0.18,\n    NAV_WAYPOINT_FRONT_RATIO: 0.50,",
"    APPROACH_REACHED_U: 0.18,\n    APPROACH_REFRESH_S: 0.10, // aggiornamento target tattico max 10 Hz, non ogni frame\n    NAV_WAYPOINT_FRONT_RATIO: 0.50,",'cfg approach refresh')

old="""    slotContactPoint(defender, slot, contactT = 0.5) {
      const seg = Geometry.slotSegment(defender, slot);
      const t = Math.max(0, Math.min(1, Number.isFinite(contactT) ? contactT : 0.5));
      return {
        x: seg.a.x + (seg.b.x - seg.a.x) * t,
        y: seg.a.y + (seg.b.y - seg.a.y) * t
      };
    },"""
new="""    slotContactPoint(defender, slot, contactT = 0.5, out = null) {
      const seg = Geometry.slotSegment(defender, slot);
      const t = Math.max(0, Math.min(1, Number.isFinite(contactT) ? contactT : 0.5));
      const p = out || { x:0, y:0 };
      p.x = seg.a.x + (seg.b.x - seg.a.x) * t;
      p.y = seg.a.y + (seg.b.y - seg.a.y) * t;
      return p;
    },"""
rep(old,new,'slot contact reuse')

old="""    refreshApproachTarget(u, enemy) {
      const ap = u.order.approach;
      if (!ap || ap.enemyId !== enemy.id) return false;

      // Lo slot e' LOCKED. Lo cambiamo soltanto se e' diventato realmente
      // indisponibile (occupato/prenotato da un altro reparto).
      if (!Engagements.slotAvailable(u, enemy, ap.slot, false)) {
        const next = Engagements.chooseSlot(u, enemy);
        if (!next) {
          u.order.approach = null;
          u.order.target = null;
          u.order.queue = [];
          return false;
        }
        ap.slot = next;
        ap.contactT = this.slotContactT(u, enemy, next);
        ap.phase = this.initialApproachPhase(u, enemy, next, ap.contactT);
      }

      ap.contactPoint = this.slotContactPoint(enemy, ap.slot, ap.contactT);
      ap.gatePoint = null;
      ap.navPoint = ap.contactPoint;
      u.order.target = { ...ap.contactPoint };
      u.order.queue = [];
      return true;
    },"""
new="""    refreshApproachTarget(u, enemy) {
      const ap = u.order.approach;
      if (!ap || ap.enemyId !== enemy.id) return false;

      // Lo slot e' LOCKED. Lo cambiamo soltanto se e' diventato realmente
      // indisponibile (occupato/prenotato da un altro reparto).
      if (!Engagements.slotAvailable(u, enemy, ap.slot, false)) {
        const next = Engagements.chooseSlot(u, enemy);
        if (!next) {
          u.order.approach = null;
          u.order.target = null;
          u.order.queue.length = 0;
          return false;
        }
        ap.slot = next;
        ap.contactT = this.slotContactT(u, enemy, next);
        ap.phase = this.initialApproachPhase(u, enemy, next, ap.contactT);
      }

      // HOT PATH: riusa gli stessi oggetti invece di allocarne 2-3 per unità/frame.
      ap.contactPoint = this.slotContactPoint(enemy, ap.slot, ap.contactT, ap.contactPoint);
      ap.gatePoint = null;
      ap.navPoint = ap.contactPoint;
      if (!u.order.target) u.order.target = { x:ap.contactPoint.x, y:ap.contactPoint.y };
      else {
        u.order.target.x = ap.contactPoint.x;
        u.order.target.y = ap.contactPoint.y;
      }
      if (u.order.queue.length) u.order.queue.length = 0;
      ap.nextRefreshAt = State.simTime + CFG.APPROACH_REFRESH_S;
      return true;
    },"""
rep(old,new,'refresh approach reuse')

rep("      const existing = u.order.approach?.enemyId === enemy.id ? u.order.approach : null;\n      let slot = existing?.slot || null;",
"      const existing = u.order.approach?.enemyId === enemy.id ? u.order.approach : null;\n      if (!force && existing && u.order.target && State.simTime < (existing.nextRefreshAt || 0)) return true;\n      let slot = existing?.slot || null;",'approach throttle')
rep("          navPoint: null\n        };",
"          navPoint: null,\n          nextRefreshAt: 0\n        };",'approach refresh state')

old="""    issueAttackNearest(u) {
      if (!u?.status?.alive || u.status.routing || u.order.kind === 'retreat' || Engagements.hasAny(u)) return 'skip';
      const found = AI.nearestEnemy(u);
      const enemy = found?.enemy || null;
      if (!enemy) {
        if (u.order.kind === 'lock' || u.order.kind === 'ai') Orders.clear(u);
        return 'none';
      }
      if (u.order.lockTargetId === enemy.id && (u.order.kind === 'lock' || u.order.kind === 'ai')) return 'same';
      return Orders.setLock(u, enemy, true) ? 'new' : 'skip';
    },"""
new="""    issueAttackNearest(u) {
      if (!u?.status?.alive || u.status.routing || u.order.kind === 'retreat' || Engagements.hasAny(u)) return 'skip';

      // Sticky target: il refresh strategico non resetta un ordine ancora valido.
      // Si cerca un nuovo "più vicino" solo quando il target precedente non esiste più.
      const currentId = u.order.lockTargetId || u.order.approach?.enemyId || u.order.pursuit?.enemyId;
      const current = Units.byId(currentId);
      if (current?.status?.alive && current.side !== u.side) return 'same';

      const found = AI.nearestEnemy(u);
      const enemy = found?.enemy || null;
      if (!enemy) {
        if (u.order.kind === 'lock' || u.order.kind === 'ai') Orders.clear(u);
        return 'none';
      }
      return Orders.setLock(u, enemy, true) ? 'new' : 'skip';
    },"""
rep(old,new,'sticky target')

rep("      Log.add(`🤖 ARMY AI ${side.toUpperCase()} #${State.armyAI.refreshCount}: ATTACCA IL PIÙ VICINO | nuovi ${issued} · confermati ${same} · non assegnabili ${skipped}`);\n      return true;",
"      // Evita churn DOM/log quando il refresh conferma soltanto ordini invariati.\n      if (issued > 0 || force) {\n        Log.add(`🤖 ARMY AI ${side.toUpperCase()} #${State.armyAI.refreshCount}: ATTACCA IL PIÙ VICINO | nuovi ${issued} · confermati ${same} · non assegnabili ${skipped}`);\n      }\n      return true;",'quiet unchanged refresh')

p.write_text(s,encoding='utf-8')
print('AI churn patch OK')
