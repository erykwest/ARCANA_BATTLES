from pathlib import Path

p = Path('ARCANA_BATTLES.html')
s = p.read_text(encoding='utf-8')

def rep(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        raise SystemExit(f'{label}: expected 1 occurrence, found {n}')
    s = s.replace(old, new, 1)

def between(start, end, new, label):
    global s
    a = s.find(start)
    if a < 0:
        raise SystemExit(f'{label}: start not found')
    b = s.find(end, a)
    if b < 0:
        raise SystemExit(f'{label}: end not found')
    s = s[:a] + new + s[b:]

s = s.replace('v0.87.1', 'v0.87.2')

rep(
"""    CELL_U: 1,\n    REPLAN_INTERVAL: 0.35,\n""",
"""    // 1.5U riduce la griglia da ~5400 a ~2400 celle: sufficiente per reparti 2-6U.\n    CELL_U: 1.5,\n    REPLAN_INTERVAL: 0.80,\n    DIRECT_CHECK_INTERVAL: 0.18,\n    MAX_EXPANSIONS: 3200,\n""",
'constants')

rep(
"""    excludedObstacle(u, other) {\n      if (!other || other.id === u.id) return true;\n      // Intentional target must remain reachable.\n      if (u.order.lockTargetId === other.id) return true;\n      if (u.order.approach?.enemyId === other.id) return true;\n      if (u.ranged?.approachTargetId === other.id) return true;\n      return false;\n    },\n\n    ignoredIds(u) {\n      const ids = [u.id];\n      // Il bersaglio d'attacco deve restare raggiungibile: A* evita gli ALTRI\n      // reparti, non il corpo del nemico che stiamo cercando di contattare.\n      if (u.order.approach?.enemyId) ids.push(u.order.approach.enemyId);\n      if (u.order.lockTargetId) ids.push(u.order.lockTargetId);\n      if (u.order.pursuit?.enemyId) ids.push(u.order.pursuit.enemyId);\n      if (u.ranged?.approachTargetId) ids.push(u.ranged.approachTargetId);\n      return [...new Set(ids)];\n    },\n\n    segmentBlockedByAny(u, a, b) {\n      const ignored = new Set(this.ignoredIds(u));\n      const clearance = this.moverClearance(u);\n      for (const other of State.units) {\n        if (!other.status.alive || ignored.has(other.id)) continue;\n        if (Geometry.segmentHitsBodyWithClearance(other, a.x, a.y, b.x, b.y, clearance)) {\n          return true;\n        }\n      }\n      if (Terrain.segmentBlocked(u, a, b, this.terrainClearance(u))) return true;\n      return false;\n    },\n\n    pointBlocked(u, point) {\n      const ignored = new Set(this.ignoredIds(u));\n      const clearance = this.moverClearance(u);\n      for (const other of State.units) {\n        if (!other.status.alive || ignored.has(other.id)) continue;\n        if (Geometry.distancePointToBody(point, other) <= clearance) return true;\n      }\n      if (Terrain.blocksPoint(u, point, this.terrainClearance(u))) return true;\n      return false;\n    },\n""",
"""    excludedObstacle(u, other) {\n      if (!other || other.id === u.id || !other.status.alive) return true;\n      // Il bersaglio intenzionale deve restare raggiungibile. Niente Set temporanei:\n      // questa funzione vive nell'hot path del planner.\n      if (u.order.lockTargetId === other.id) return true;\n      if (u.order.approach?.enemyId === other.id) return true;\n      if (u.order.pursuit?.enemyId === other.id) return true;\n      if (u.ranged?.approachTargetId === other.id) return true;\n      return false;\n    },\n\n    buildContext(u) {\n      const cols = Math.ceil(CFG.WORLD_W_U / this.CELL_U);\n      const rows = Math.ceil(CFG.WORLD_H_U / this.CELL_U);\n      return {\n        cols, rows,\n        bounds: Geometry.battlefieldBounds(),\n        moverClearance: this.moverClearance(u),\n        terrainClearance: this.terrainClearance(u),\n        obstacles: State.units.filter(other => !this.excludedObstacle(u, other)),\n        // 0=unknown, 1=free, 2=blocked. Ogni cella viene testata al massimo una volta per A*.\n        cellState: new Uint8Array(cols * rows)\n      };\n    },\n\n    segmentBlockedByAny(u, a, b) {\n      const clearance = this.moverClearance(u);\n      for (const other of State.units) {\n        if (this.excludedObstacle(u, other)) continue;\n        if (Geometry.segmentHitsBodyWithClearance(other, a.x, a.y, b.x, b.y, clearance)) return true;\n      }\n      return Terrain.segmentBlocked(u, a, b, this.terrainClearance(u));\n    },\n\n    pointBlocked(u, point, ctx = null) {\n      const obstacles = ctx?.obstacles || State.units;\n      const clearance = ctx?.moverClearance ?? this.moverClearance(u);\n      for (const other of obstacles) {\n        if (!ctx && this.excludedObstacle(u, other)) continue;\n        if (Geometry.distancePointToBody(point, other) <= clearance) return true;\n      }\n      return Terrain.blocksPoint(u, point, ctx?.terrainClearance ?? this.terrainClearance(u));\n    },\n""",
'hot path obstacle scans')

new_astar = r'''    validCell(u, x, y, goalCell, ctx) {
      const { cols, rows } = ctx;
      if (x < 0 || y < 0 || x >= cols || y >= rows) return false;
      if (goalCell && x === goalCell.x && y === goalCell.y) return true;

      const idx = y * cols + x;
      const cached = ctx.cellState[idx];
      if (cached) return cached === 1;

      const p = this.cellToWorld({ x, y });
      if (!u.status.routing) {
        const b = ctx.bounds;
        if (p.x < b.minX || p.x > b.maxX || p.y < b.minY || p.y > b.maxY) {
          ctx.cellState[idx] = 2;
          return false;
        }
      }

      const free = !this.pointBlocked(u, p, ctx);
      ctx.cellState[idx] = free ? 1 : 2;
      return free;
    },

    nearestFreeCell(u, cell, goalCell, ctx, maxRadius = 5) {
      if (this.validCell(u, cell.x, cell.y, goalCell, ctx)) return cell;
      for (let r = 1; r <= maxRadius; r++) {
        let best = null, bestD = Infinity;
        for (let dx = -r; dx <= r; dx++) {
          for (let dy = -r; dy <= r; dy++) {
            if (Math.max(Math.abs(dx), Math.abs(dy)) !== r) continue;
            const x = cell.x + dx, y = cell.y + dy;
            if (!this.validCell(u, x, y, goalCell, ctx)) continue;
            const d = dx * dx + dy * dy;
            if (d < bestD) { bestD = d; best = { x, y }; }
          }
        }
        if (best) return best;
      }
      return null;
    },

    heapPush(heap, node) {
      let i = heap.length;
      heap.push(node);
      while (i > 0) {
        const p = (i - 1) >> 1;
        if (heap[p].f <= node.f) break;
        heap[i] = heap[p];
        i = p;
      }
      heap[i] = node;
    },

    heapPop(heap) {
      if (!heap.length) return null;
      const root = heap[0];
      const last = heap.pop();
      if (!heap.length) return root;
      let i = 0;
      while (true) {
        const l = i * 2 + 1, r = l + 1;
        if (l >= heap.length) break;
        let c = r < heap.length && heap[r].f < heap[l].f ? r : l;
        if (heap[c].f >= last.f) break;
        heap[i] = heap[c];
        i = c;
      }
      heap[i] = last;
      return root;
    },

    astar(u, startPoint, goalPoint) {
      if (!u.status.routing) goalPoint = Geometry.clampPointToBattlefield(goalPoint);
      const ctx = this.buildContext(u);
      const rawStart = this.worldToCell(startPoint);
      const rawGoal = this.worldToCell(goalPoint);
      const goalCell = this.nearestFreeCell(u, rawGoal, rawGoal, ctx, 5) || rawGoal;
      const startCell = this.nearestFreeCell(u, rawStart, goalCell, ctx, 3) || rawStart;
      const { cols, rows } = ctx;
      const total = cols * rows;
      const startIdx = startCell.y * cols + startCell.x;
      const goalIdx = goalCell.y * cols + goalCell.x;
      if (startIdx === goalIdx) return [goalPoint];

      const gScore = new Float64Array(total);
      gScore.fill(Infinity);
      gScore[startIdx] = 0;
      const came = new Int32Array(total);
      came.fill(-1);
      const closed = new Uint8Array(total);
      const heap = [];

      const heuristic = (x, y) => {
        const dx = Math.abs(goalCell.x - x), dy = Math.abs(goalCell.y - y);
        return (dx + dy) + (Math.SQRT2 - 2) * Math.min(dx, dy);
      };

      this.heapPush(heap, { x:startCell.x, y:startCell.y, idx:startIdx, f:heuristic(startCell.x, startCell.y) });
      const dirs = [
        [1,0,1],[-1,0,1],[0,1,1],[0,-1,1],
        [1,1,Math.SQRT2],[1,-1,Math.SQRT2],[-1,1,Math.SQRT2],[-1,-1,Math.SQRT2]
      ];
      let expansions = 0;
      const cap = Math.min(this.MAX_EXPANSIONS, total * 2);

      while (heap.length && expansions++ < cap) {
        const cur = this.heapPop(heap);
        if (!cur || closed[cur.idx]) continue;
        if (cur.idx === goalIdx) {
          const cells = [];
          let idx = cur.idx;
          while (idx >= 0) {
            cells.push({ x:idx % cols, y:Math.floor(idx / cols) });
            if (idx === startIdx) break;
            idx = came[idx];
          }
          cells.reverse();
          const pts = cells.slice(1).map(c => this.cellToWorld(c));
          pts.push({ ...goalPoint });
          return this.smooth(u, startPoint, pts);
        }
        closed[cur.idx] = 1;

        const baseG = gScore[cur.idx];
        for (const [dx, dy, cost] of dirs) {
          const nx = cur.x + dx, ny = cur.y + dy;
          if (!this.validCell(u, nx, ny, goalCell, ctx)) continue;
          const ni = ny * cols + nx;
          if (closed[ni]) continue;

          if (dx !== 0 && dy !== 0) {
            if (!this.validCell(u, cur.x + dx, cur.y, goalCell, ctx) ||
                !this.validCell(u, cur.x, cur.y + dy, goalCell, ctx)) continue;
          }

          const tentative = baseG + cost;
          if (tentative >= gScore[ni]) continue;
          came[ni] = cur.idx;
          gScore[ni] = tentative;
          this.heapPush(heap, { x:nx, y:ny, idx:ni, f:tentative + heuristic(nx, ny) });
        }
      }
      return null;
    },

'''
between('    validCell(u, x, y, goalCell) {', '    smooth(u, startPoint, points) {', new_astar, 'A* core')

new_replan = r'''    needsReplan(u, finalTarget) {
      const d = u.motion.detour;
      if (!d) return true;
      if (State.simTime < (d.replanAt || 0)) return false;
      d.replanAt = State.simTime + this.REPLAN_INTERVAL;

      const wp = d.waypoints?.[d.index];
      if (!wp || this.segmentBlockedByAny(u, { x:u.pose.x, y:u.pose.y }, wp)) return true;

      // Solo al tick di replan controlliamo se possiamo tornare alla linea diretta.
      if (!this.segmentBlockedByAny(u, { x:u.pose.x, y:u.pose.y }, finalTarget)) {
        u.motion.detour = null;
        return false;
      }
      return false;
    },

    ensure(u, finalTarget) {
      if (!u?.status.alive || !finalTarget || Engagements.hasAny(u)) return null;

      // Con una polyline valida non rifacciamo neppure il test LOS ogni frame.
      if (u.motion.detour) {
        if (State.simTime < (u.motion.detour.replanAt || 0)) return this.currentWaypoint(u);
        const mustReplan = this.needsReplan(u, finalTarget);
        if (!mustReplan) return this.currentWaypoint(u);
      } else {
        // Anche il controllo del corridoio diretto è throttled; collisioni reali restano
        // comunque gestite dal collision solver frame-per-frame.
        if (State.simTime < (u.motion.pathCheckAt || 0)) return null;
        u.motion.pathCheckAt = State.simTime + this.DIRECT_CHECK_INTERVAL;
        const start = { x:u.pose.x, y:u.pose.y };
        if (!this.segmentBlockedByAny(u, start, finalTarget)) return null;
      }

      const start = { x:u.pose.x, y:u.pose.y };
      const path = this.astar(u, start, finalTarget);
      if (!path?.length) {
        u.motion.detour = null;
        return null;
      }

      const waypoints = path.slice(0, -1);
      if (!waypoints.length) {
        u.motion.detour = null;
        return null;
      }

      u.motion.detour = {
        kind:'astar',
        waypoints,
        index:0,
        replanAt:State.simTime + this.REPLAN_INTERVAL
      };
      Log.add(`${u.name}: A* PATH → ${waypoints.length} waypoint${waypoints.length === 1 ? '' : 's'}`);
      return waypoints[0];
    },

'''
between('    needsReplan(u, finalTarget) {', '    currentWaypoint(u) {', new_replan, 'replan/ensure')

rep(
"""    advance(u) {\n      const d = u.motion.detour;\n      if (!d) return false;\n\n      // Un waypoint A* non è più parte di una polyline \"congelata\".\n      // Appena raggiunto viene scartato tutto il vecchio percorso:\n      // il prossimo tick ricalcola A* dalla posa reale corrente verso\n      // il target finale, tenendo conto di unità, terreno e orientamento aggiornati.\n      const hadMore = d.index + 1 < d.waypoints.length;\n      u.motion.detour = null;\n      return hadMore;\n    }\n""",
"""    advance(u) {\n      const d = u.motion.detour;\n      if (!d) return false;\n      if (d.index + 1 < d.waypoints.length) {\n        d.index += 1;\n        // Mantiene la polyline: niente nuovo A* solo perché è stato raggiunto un waypoint.\n        d.replanAt = Math.max(d.replanAt || 0, State.simTime + 0.12);\n        return true;\n      }\n      u.motion.detour = null;\n      return false;\n    }\n""",
'advance polyline')

s = s.replace("          Log.add(`${u.name}: A* ATTACK WAYPOINT → REPLAN`);\n", '')
s = s.replace("        // Il waypoint raggiunto invalida l'intera vecchia polyline.\n        // Il prossimo frame Pathfinder.ensure() ricostruisce il percorso\n        // dalla posizione reale attuale verso il target finale.\n", '')
s = s.replace("        Log.add(`${u.name}: A* WAYPOINT → REPLAN`);\n", '')

p.write_text(s, encoding='utf-8')
print('pathfinder v0.87.2 patch applied')
