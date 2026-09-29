from pathlib import Path

path = Path('COFFEE_BATTLES.html')
text = path.read_text(encoding='utf-8')
original = text


def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected 1 occurrence, found {count}')
    text = text.replace(old, new, 1)


def replace_all(old, new, label, minimum=1):
    global text
    count = text.count(old)
    if count < minimum:
        raise SystemExit(f'{label}: expected >= {minimum} occurrences, found {count}')
    text = text.replace(old, new)
    print(f'{label}: replaced {count}')

replace_all('v0.89.3', 'v0.90.0', 'version labels', minimum=3)
replace_once(
    'v0.90.0 · Step 1/3 — 8 profili unità + ranged resolver unilaterale + Map/Doctrine/Army AI.',
    'v0.90.0 · Step 1/3 — Fog of War 20U + Intel Layer condiviso per lato + ghost ultima posizione nota.',
    'setup footnote'
)

replace_once(
    '    ARMY_AI_REFRESH_S: 5,\n    BATTLE_TIME_LIMIT_S: 600,',
    '    ARMY_AI_REFRESH_S: 5,\n    VISION_RANGE_U: 20,\n    BATTLE_TIME_LIMIT_S: 600,',
    'vision config'
)

replace_once(
    "    armyAI: {\n      enabled: true,\n      lastRefreshAt: -Infinity,\n      refreshCount: 0\n    },\n    battle: {",
    "    armyAI: {\n      enabled: true,\n      lastRefreshAt: -Infinity,\n      refreshCount: 0\n    },\n    intel: {\n      blue: new Map(),\n      red: new Map()\n    },\n    battle: {",
    'intel state'
)

intel_block = r'''

  // ============================================================
  // INTEL + FOG OF WAR v0.90
  // Real simulation state remains authoritative; each side receives only
  // VISIBLE / LAST_KNOWN / UNKNOWN information through this layer.
  // ============================================================
  const Intel = {
    active() {
      return !!State.battle.active && !State.deployment.active;
    },

    viewSide() {
      return State.battle.playerSide || State.selectedSide || 'blue';
    },

    reset() {
      State.intel.blue = new Map();
      State.intel.red = new Map();
      this.update();
    },

    sources(side) {
      // Future extension point: watchtowers / scouts / scenario sensors can be
      // appended here without changing AI, targeting or rendering consumers.
      return Units.alive(side);
    },

    canSeeNow(side, enemy) {
      if (!enemy?.status?.alive) return false;
      if (!this.active() || enemy.side === side) return true;

      for (const viewer of this.sources(side)) {
        const d = Geometry.distanceUnits(viewer, enemy);
        if (d > CFG.VISION_RANGE_U) continue;
        if (d <= 1.5 || Terrain.lineOfSight(viewer, enemy)) return true;
      }
      return false;
    },

    remember(side, enemy) {
      const map = State.intel[side];
      if (!map || !enemy) return null;
      const record = {
        id: enemy.id,
        side: enemy.side,
        type: enemy.type,
        name: enemy.name,
        color: enemy.color,
        state: 'visible',
        lastSeenAt: State.simTime,
        lastKnown: {
          x: enemy.pose.x,
          y: enemy.pose.y,
          angle: enemy.pose.angle,
          formation: enemy.formation?.type || 'base',
          hp: enemy.stats?.hp ?? enemy.stats?.maxHp ?? 1,
          routing: !!enemy.status?.routing,
          time: State.simTime
        }
      };
      map.set(enemy.id, record);
      return record;
    },

    updateSide(side) {
      const map = State.intel[side];
      if (!map) return;

      for (const enemy of State.units) {
        if (enemy.side === side) continue;
        const old = map.get(enemy.id) || null;

        if (enemy.status.alive && this.canSeeNow(side, enemy)) {
          this.remember(side, enemy);
          continue;
        }

        if (old?.state === 'visible') {
          if (enemy.status.alive) {
            old.state = 'last-known';
            map.set(enemy.id, old);
          } else {
            old.state = 'destroyed';
            map.set(enemy.id, old);
          }
        }
      }
    },

    update() {
      if (!this.active()) return;
      this.updateSide('blue');
      this.updateSide('red');
    },

    isVisible(side, enemy) {
      if (!enemy) return false;
      if (!this.active() || enemy.side === side) return true;
      return this.canSeeNow(side, enemy);
    },

    renderVisible(side, unit) {
      if (!unit) return false;
      if (!Deployment.visibleInDeployment(unit)) return false;
      return unit.side === side || this.isVisible(side, unit);
    },

    visibleEnemies(side) {
      return State.units.filter(enemy =>
        enemy.status.alive && enemy.side !== side && this.isVisible(side, enemy)
      );
    },

    lastKnown(side, enemyId) {
      const record = State.intel[side]?.get(enemyId);
      return record?.lastKnown ? { ...record.lastKnown } : null;
    },

    ghosts(side) {
      if (!this.active()) return [];
      const out = [];
      for (const record of State.intel[side]?.values?.() || []) {
        if (record.state !== 'last-known' || !record.lastKnown) continue;
        const live = Units.byId(record.id);
        if (live?.status?.alive && this.isVisible(side, live)) continue;
        out.push({ record, unit: live });
      }
      return out;
    },

    searchLastKnown(u, enemy, announce = true) {
      if (!u?.status?.alive || !enemy || u.side === enemy.side) return false;
      const known = this.lastKnown(u.side, enemy.id);
      if (!known) {
        Orders.clear(u);
        return false;
      }

      const point = { x: known.x, y: known.y };
      const moved = Orders.setManual(u, point, false);
      if (moved) {
        if (u.ranged) {
          u.ranged.targetId = null;
          u.ranged.clock = 0;
          u.ranged.approachTargetId = null;
        }
        if (announce) {
          Log.add(`${u.name}: CONTATTO PERSO → ultima posizione nota di ${enemy?.name || 'BERSAGLIO'} @ ${known.time.toFixed(1)}s`);
        }
      }
      return moved;
    }
  };
'''

marker = "\n  // ============================================================\n  // 3. GEOMETRY — front pivot is the single positional truth\n"
if marker not in text:
    raise SystemExit('geometry marker not found')
text = text.replace(marker, intel_block + marker, 1)

replace_once(
    "    setLock(u, enemy, silent = false) {\n      if (!u.status.alive || !enemy?.status.alive || u.side === enemy.side || u.status.routing) return false;",
    "    setLock(u, enemy, silent = false) {\n      if (!u.status.alive || !enemy?.status.alive || u.side === enemy.side || u.status.routing) return false;\n      if (!Intel.isVisible(u.side, enemy)) return false;",
    'setLock visibility'
)

replace_once(
    "    appendAttack(u, enemy) {\n      if (!u.status.alive || u.status.routing || !enemy?.status.alive || u.side === enemy.side) return false;",
    "    appendAttack(u, enemy) {\n      if (!u.status.alive || u.status.routing || !enemy?.status.alive || u.side === enemy.side) return false;\n      if (!Intel.isVisible(u.side, enemy)) return false;",
    'appendAttack visibility'
)

old_terminal = r'''      if (u.order.kind === 'manual' && u.order.finalAttackTargetId) {
        const enemy = Units.byId(u.order.finalAttackTargetId);
        u.order.finalAttackTargetId = null;

        if (enemy?.status.alive && enemy.side !== u.side) {
          u.order.kind = 'lock';
          u.order.lockTargetId = enemy.id;
          u.order.retreatThreatId = null;
          u.order.approach = null;
          u.behavior.active = false;
          u.behavior.targetId = null;

          if (u.ranged) u.ranged.approachTargetId = null;

          if (!u.ranged) {
            AI.planApproach(u, enemy, true);
          }

          Log.add(`${u.name}: FINE WAYPOINT → ATTACCO ${enemy.name}${u.ranged ? ' [RANGED]' : ''}`);
          return true;
        }
      }
'''
new_terminal = r'''      if (u.order.kind === 'manual' && u.order.finalAttackTargetId) {
        const enemy = Units.byId(u.order.finalAttackTargetId);
        u.order.finalAttackTargetId = null;

        if (enemy?.status.alive && enemy.side !== u.side && Intel.isVisible(u.side, enemy)) {
          u.order.kind = 'lock';
          u.order.lockTargetId = enemy.id;
          u.order.retreatThreatId = null;
          u.order.approach = null;
          u.behavior.active = false;
          u.behavior.targetId = null;

          if (u.ranged) u.ranged.approachTargetId = null;

          if (!u.ranged) {
            AI.planApproach(u, enemy, true);
          }

          Log.add(`${u.name}: FINE WAYPOINT → ATTACCO ${enemy.name}${u.ranged ? ' [RANGED]' : ''}`);
          return true;
        }

        if (enemy?.status.alive && enemy.side !== u.side) {
          return Intel.searchLastKnown(u, enemy);
        }
      }
'''
replace_once(old_terminal, new_terminal, 'terminal attack visibility')

replace_all(
    'for (const enemy of Units.enemiesOf(u)) {',
    'for (const enemy of Intel.visibleEnemies(u.side)) {',
    'enemy scans -> intel',
    minimum=2
)

old_pursuit = r'''      if (u.order.pursuit?.enemyId) {
        const pursued = Units.byId(u.order.pursuit.enemyId);
        if (pursued?.status.alive && this.isFleeing(pursued)) {
          this.updatePursuit(u, pursued);
          return;
        }
        this.clearPursuitState(u);
      }
'''
new_pursuit = r'''      if (u.order.pursuit?.enemyId) {
        const pursued = Units.byId(u.order.pursuit.enemyId);
        if (pursued?.status.alive && this.isFleeing(pursued)) {
          if (!Intel.isVisible(u.side, pursued)) {
            this.stopPursuit(u, pursued, 'bersaglio perso di vista');
            Intel.searchLastKnown(u, pursued, false);
            return;
          }
          this.updatePursuit(u, pursued);
          return;
        }
        this.clearPursuitState(u);
      }
'''
replace_once(old_pursuit, new_pursuit, 'pursuit fog behavior')

replace_once(
    "        if (previous?.status.alive && this.isFleeing(previous)) {",
    "        if (previous?.status.alive && Intel.isVisible(u.side, previous) && this.isFleeing(previous)) {",
    'AI fleeing target visibility'
)

replace_once(
    "        const explicitValid =\n          explicit?.status.alive &&\n          explicit.side !== u.side;",
    "        const explicitValid =\n          explicit?.status.alive &&\n          explicit.side !== u.side &&\n          Intel.isVisible(u.side, explicit);",
    'AI ranged explicit visibility'
)

old_lock = r'''      if (u.order.kind === 'lock') {
        const enemy = Units.byId(u.order.lockTargetId);
        if (!enemy?.status.alive || enemy.side === u.side) {
          Orders.clear(u);
          return;
        }
        if (this.isFleeing(enemy)) {
'''
new_lock = r'''      if (u.order.kind === 'lock') {
        const enemy = Units.byId(u.order.lockTargetId);
        if (!enemy?.status.alive || enemy.side === u.side) {
          Orders.clear(u);
          return;
        }
        if (!Intel.isVisible(u.side, enemy)) {
          Intel.searchLastKnown(u, enemy);
          return;
        }
        if (this.isFleeing(enemy)) {
'''
replace_once(old_lock, new_lock, 'AI lock lost-contact')

replace_once(
    "      if (explicit?.status.alive && explicit.side !== u.side) {",
    "      if (explicit?.status.alive && explicit.side !== u.side && Intel.isVisible(u.side, explicit)) {",
    'ranged explicit visibility'
)

replace_once(
    "          if (!u.status.alive ||\n              !target.status.alive ||\n              Geometry.distanceUnits(u, target) > (u.profile.ranged.rangeU + Terrain.rangedRangeBonusU(u)) ||",
    "          if (!u.status.alive ||\n              !target.status.alive ||\n              !Intel.isVisible(u.side, target) ||\n              Geometry.distanceUnits(u, target) > (u.profile.ranged.rangeU + Terrain.rangedRangeBonusU(u)) ||",
    'ranged volley visibility break'
)

replace_once(
    "      if (!enemy?.status.alive) return;\n      const ec = Geometry.center(enemy);",
    "      if (!enemy?.status.alive || !Intel.isVisible(u.side, enemy)) return;\n      const ec = Geometry.center(enemy);",
    'lock renderer visibility'
)

fog_renderer = r'''
    fogOverlay(w, h, side) {
      if (!Intel.active()) return;

      if (!this._fogCanvas) this._fogCanvas = document.createElement('canvas');
      const layer = this._fogCanvas;
      const iw = Math.max(1, Math.ceil(w));
      const ih = Math.max(1, Math.ceil(h));
      if (layer.width !== iw || layer.height !== ih) {
        layer.width = iw;
        layer.height = ih;
      }

      const fctx = layer.getContext('2d');
      fctx.clearRect(0, 0, iw, ih);
      fctx.globalCompositeOperation = 'source-over';
      fctx.fillStyle = 'rgba(72,76,82,.72)';
      fctx.fillRect(0, 0, iw, ih);

      fctx.globalCompositeOperation = 'destination-out';
      const radius = CFG.VISION_RANGE_U * CFG.U;
      for (const viewer of Intel.sources(side)) {
        const c = Geometry.center(viewer);
        const g = fctx.createRadialGradient(c.x, c.y, radius * 0.88, c.x, c.y, radius);
        g.addColorStop(0, 'rgba(0,0,0,1)');
        g.addColorStop(1, 'rgba(0,0,0,0)');
        fctx.fillStyle = g;
        fctx.beginPath();
        fctx.arc(c.x, c.y, radius, 0, Math.PI * 2);
        fctx.fill();
      }
      fctx.globalCompositeOperation = 'source-over';

      ctx.save();
      ctx.drawImage(layer, 0, 0, w, h);
      ctx.restore();
    },

    ghost(record, liveUnit) {
      if (!record?.lastKnown) return;
      const spec = UNIT_TYPES[record.type] || UNIT_TYPES.infantry;
      const base = liveUnit || makeUnit(
        `ghost-${record.id}`,
        record.name || 'CONTATTO',
        record.side,
        record.lastKnown.x,
        record.lastKnown.y,
        record.lastKnown.angle,
        record.color || '#ffffff',
        record.type || 'infantry'
      );
      const u = {
        ...base,
        pose: {
          x: record.lastKnown.x,
          y: record.lastKnown.y,
          angle: record.lastKnown.angle
        },
        stats: {
          ...base.stats,
          hp: Math.max(1, record.lastKnown.hp ?? spec.stats.hp)
        },
        formation: {
          ...base.formation,
          type: record.lastKnown.formation || 'base',
          transition: null
        },
        status: {
          ...base.status,
          alive: true,
          routing: !!record.lastKnown.routing
        }
      };
      const d = Geometry.dims(u);

      ctx.save();
      ctx.translate(u.pose.x, u.pose.y);
      ctx.rotate(u.pose.angle);
      ctx.globalAlpha = 0.28;
      ctx.fillStyle = u.color;
      ctx.fillRect(-d.depth, -d.front / 2, d.depth, d.front);
      ctx.strokeStyle = 'rgba(255,255,255,.78)';
      ctx.lineWidth = 2;
      ctx.setLineDash([6, 5]);
      ctx.strokeRect(-d.depth, -d.front / 2, d.depth, d.front);
      ctx.setLineDash([]);
      ctx.strokeStyle = 'rgba(241,211,107,.68)';
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.moveTo(0, -d.front / 2);
      ctx.lineTo(0, d.front / 2);
      ctx.stroke();
      UnitIcons.drawBadge(ctx, u);
      ctx.restore();
    },

'''
renderer_marker = '    unit(u) {\n'
if text.count(renderer_marker) != 1:
    raise SystemExit(f'renderer unit marker count={text.count(renderer_marker)}')
text = text.replace(renderer_marker, fog_renderer + renderer_marker, 1)

old_draw = r'''      this.battlefield(w, h);
      Terrain.draw();
      this.grid(w, h);
      this.deploymentOverlay();
      const visibleUnits = State.units.filter(u => Deployment.visibleInDeployment(u));
      visibleUnits.filter(u => u.side === State.battle.playerSide).forEach(u => this.orders(u));
      const p = Selection.primary();
      if (p && Deployment.visibleInDeployment(p)) this.lock(p);
      visibleUnits.forEach(u => this.unit(u));
      this.projectiles();
'''
new_draw = r'''      this.battlefield(w, h);
      Terrain.draw();
      this.grid(w, h);
      this.deploymentOverlay();
      const viewSide = Intel.viewSide();
      this.fogOverlay(w, h, viewSide);
      const visibleUnits = State.units.filter(u => Intel.renderVisible(viewSide, u));
      visibleUnits.filter(u => u.side === State.battle.playerSide).forEach(u => this.orders(u));
      const p = Selection.primary();
      if (p && Intel.renderVisible(viewSide, p)) this.lock(p);
      visibleUnits.forEach(u => this.unit(u));
      Intel.ghosts(viewSide).forEach(({ record, unit }) => this.ghost(record, unit));
      this.projectiles();
'''
replace_once(old_draw, new_draw, 'renderer draw fog')

replace_once(
    "      const hudUnits = State.units.filter(u => Deployment.visibleInDeployment(u));\n      hudUnits.forEach(u => this.hud(u));",
    "      const hudUnits = State.units.filter(u => Intel.renderVisible(Intel.viewSide(), u));\n      hudUnits.forEach(u => this.hud(u));",
    'HUD fog visibility'
)

replace_once(
    "      return [...State.units].reverse().find(u =>\n        u.status.alive && Deployment.visibleInDeployment(u) && Geometry.pointInUnit(u, worldPoint.x, worldPoint.y)\n      ) || null;",
    "      const viewSide = Intel.viewSide();\n      return [...State.units].reverse().find(u =>\n        u.status.alive && Intel.renderVisible(viewSide, u) && Geometry.pointInUnit(u, worldPoint.x, worldPoint.y)\n      ) || null;",
    'input fog visibility'
)

replace_once(
    "      State.armyAI.lastRefreshAt = -Infinity;\n      State.armyAI.refreshCount = 0;\n      this.hideResult();",
    "      State.armyAI.lastRefreshAt = -Infinity;\n      State.armyAI.refreshCount = 0;\n      Intel.reset();\n      this.hideResult();",
    'battle intel reset'
)

old_army_current = r'''      const currentId = u.order.lockTargetId || u.order.approach?.enemyId || u.order.pursuit?.enemyId;
      const current = Units.byId(currentId);
      if (current?.status?.alive && current.side !== u.side) return 'same';

      const found = AI.nearestEnemy(u);
      const enemy = found?.enemy || null;
      if (!enemy) {
        if (u.order.kind === 'lock' || u.order.kind === 'ai') Orders.clear(u);
        return 'none';
      }
      return Orders.setLock(u, enemy, true) ? 'new' : 'skip';
'''
new_army_current = r'''      const currentId = u.order.lockTargetId || u.order.approach?.enemyId || u.order.pursuit?.enemyId;
      const current = Units.byId(currentId);
      if (current?.status?.alive && current.side !== u.side && Intel.isVisible(u.side, current)) return 'same';

      const found = AI.nearestEnemy(u);
      const enemy = found?.enemy || null;
      if (enemy) return Orders.setLock(u, enemy, true) ? 'new' : 'skip';

      if (current?.status?.alive && current.side !== u.side && Intel.lastKnown(u.side, current.id)) {
        return Intel.searchLastKnown(u, current, false) ? 'search' : 'none';
      }

      if (u.order.kind === 'lock' || u.order.kind === 'ai') Orders.clear(u);
      return 'none';
'''
replace_once(old_army_current, new_army_current, 'ArmyAI intel targeting')

replace_once(
    "      let issued = 0, same = 0, skipped = 0;\n      for (const u of Units.alive(side)) {\n        const r = this.issueAttackNearest(u);\n        if (r === 'new') issued++;\n        else if (r === 'same') same++;\n        else skipped++;\n      }",
    "      let issued = 0, same = 0, searching = 0, skipped = 0;\n      for (const u of Units.alive(side)) {\n        const r = this.issueAttackNearest(u);\n        if (r === 'new') issued++;\n        else if (r === 'same') same++;\n        else if (r === 'search') searching++;\n        else skipped++;\n      }",
    'ArmyAI search counter'
)

replace_once(
    "        Log.add(`🤖 ARMY AI ${side.toUpperCase()} #${State.armyAI.refreshCount}: ATTACCA IL PIÙ VICINO | nuovi ${issued} · confermati ${same} · non assegnabili ${skipped}`);",
    "        Log.add(`🤖 ARMY AI ${side.toUpperCase()} #${State.armyAI.refreshCount}: INTEL TARGETING | nuovi ${issued} · confermati ${same} · ricerca last-known ${searching} · non assegnabili ${skipped}`);",
    'ArmyAI log'
)

replace_once(
    "    update(dt) {\n      ArmyAI.update();\n      State.units.forEach(Formations.update);",
    "    update(dt) {\n      Intel.update();\n      ArmyAI.update();\n      State.units.forEach(Formations.update);",
    'simulation intel pre-AI'
)

replace_once(
    "      Collision.solveGlobal();\n      this.updateFreeContacts();\n      Ranged.update(dt);",
    "      Collision.solveGlobal();\n      this.updateFreeContacts();\n      Intel.update();\n      Ranged.update(dt);",
    'simulation intel pre-ranged'
)

replace_once(
    "      Combat.update(dt);\n      Battle.checkArmyCollapse();",
    "      Combat.update(dt);\n      Intel.update();\n      Battle.checkArmyCollapse();",
    'simulation intel post-combat'
)

replace_once(
    'window.__COFFEE_BATTLES_DEBUG__ = { State, Units, Geometry, Terrain, AI, ArmyAI, Movement, Orders, Engagements, Collision, Simulation, Selection, CFG, Pathfinder, Combat, Morale, Resources, Battle, BattleSetup, Deployment, DoctrineEngine };',
    'window.__COFFEE_BATTLES_DEBUG__ = { State, Units, Intel, Geometry, Terrain, AI, ArmyAI, Movement, Orders, Engagements, Collision, Simulation, Selection, CFG, Pathfinder, Combat, Morale, Resources, Battle, BattleSetup, Deployment, DoctrineEngine };',
    'debug intel export'
)

required = [
    'VISION_RANGE_U: 20',
    'const Intel = {',
    "state: 'last-known'",
    'Intel.visibleEnemies(u.side)',
    'Intel.searchLastKnown(u, enemy)',
    'fogOverlay(w, h, side)',
    'Intel.ghosts(viewSide)',
    'Intel.renderVisible(viewSide, u)',
    '!Intel.isVisible(u.side, target)',
    'INTEL TARGETING'
]
for token in required:
    if token not in text:
        raise SystemExit(f'missing invariant: {token}')

if 'for (const enemy of Units.enemiesOf(u)) {' in text:
    raise SystemExit('omniscient enemy scan still present')

if text == original:
    raise SystemExit('no changes made')

path.write_text(text, encoding='utf-8')
print('Fog of War v0.90.0 migration applied successfully')
