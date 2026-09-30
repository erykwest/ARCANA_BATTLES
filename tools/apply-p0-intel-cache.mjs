import fs from 'node:fs';

const path = 'COFFEE_BATTLES.html';
let src = fs.readFileSync(path, 'utf8');

if (src.includes('_visibilityPairCache:new Map()')) {
  console.log('Intel LOS pair cache already present.');
  process.exit(0);
}

const before = `    reset() {
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
    },`;

const after = `    _visibilityPairCache:new Map(),
    _visibilityStats:{ pairChecks:0, cacheHits:0, cacheMisses:0, losChecks:0 },

    resetVisibilityCache(resetStats = false) {
      this._visibilityPairCache.clear();
      if (resetStats) {
        this._visibilityStats = { pairChecks:0, cacheHits:0, cacheMisses:0, losChecks:0 };
      }
    },

    visibilityStats() {
      const s = this._visibilityStats;
      return {
        pairChecks:s.pairChecks,
        cacheHits:s.cacheHits,
        cacheMisses:s.cacheMisses,
        losChecks:s.losChecks,
        cacheSize:this._visibilityPairCache.size,
        hitRate:s.pairChecks ? s.cacheHits / s.pairChecks : 0
      };
    },

    reset() {
      State.intel.blue = new Map();
      State.intel.red = new Map();
      this.resetVisibilityCache(true);
      this.update();
    },

    sources(side) {
      // Future extension point: watchtowers / scouts / scenario sensors can be
      // appended here without changing AI, targeting or rendering consumers.
      return Units.alive(side);
    },

    viewerCanSee(viewer, enemy) {
      const vc = Geometry.center(viewer);
      const ec = Geometry.center(enemy);
      const key = viewer.id + '>' + enemy.id;
      const cached = this._visibilityPairCache.get(key);
      const stats = this._visibilityStats;
      stats.pairChecks++;

      // Visibility depends on the two current geometric centers and static
      // battlefield terrain. Geometry.center already captures HP/formations,
      // including transitions that evolve with State.simTime.
      if (cached &&
          cached.vx === vc.x && cached.vy === vc.y &&
          cached.ex === ec.x && cached.ey === ec.y) {
        stats.cacheHits++;
        return cached.visible;
      }

      stats.cacheMisses++;
      const d = Math.hypot(vc.x - ec.x, vc.y - ec.y) / CFG.U;
      let visible = false;
      if (d <= CFG.VISION_RANGE_U) {
        if (d <= 1.5) {
          visible = true;
        } else {
          stats.losChecks++;
          visible = Terrain.lineOfSight(viewer, enemy);
        }
      }

      this._visibilityPairCache.set(key, {
        vx:vc.x, vy:vc.y, ex:ec.x, ey:ec.y, visible
      });
      return visible;
    },

    canSeeNow(side, enemy) {
      if (!enemy?.status?.alive) return false;
      if (!this.active() || enemy.side === side) return true;

      for (const viewer of this.sources(side)) {
        if (this.viewerCanSee(viewer, enemy)) return true;
      }
      return false;
    },`;

if (!src.includes(before)) {
  throw new Error('Intel reset/sources/canSeeNow target not found');
}

src = src.replace(before, after);
fs.writeFileSync(path, src);
console.log('Intel LOS pair cache applied.');
