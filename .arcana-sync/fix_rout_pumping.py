from pathlib import Path

p = Path('ARCANA_BATTLES.html')
s = p.read_text(encoding='utf-8')

# Version bump.
s = s.replace('v0.87.2', 'v0.87.3')

old_solve = '''    solveGlobal(iterations = 6) {
      for (let iter = 0; iter < iterations; iter++) {
        let changed = false;
        for (let i = 0; i < State.units.length; i++) {
          const a = State.units[i];
          if (!a.status.alive) continue;
          for (let j = i + 1; j < State.units.length; j++) {
            const b = State.units[j];
            if (!b.status.alive || Engagements.pair(a, b)) continue;
            const mtv = Geometry.overlapMTV(a, b);
            if (!mtv) continue;
            changed = true;
            const aa = this.isAnchored(a);
            const ba = this.isAnchored(b);
            if (aa && !ba) {
              b.pose.x -= mtv.x;
              b.pose.y -= mtv.y;
              Geometry.clampToWorld(b);
            } else if (ba && !aa) {
              a.pose.x += mtv.x;
              a.pose.y += mtv.y;
              Geometry.clampToWorld(a);
            } else {
              a.pose.x += mtv.x * 0.5;
              a.pose.y += mtv.y * 0.5;
              b.pose.x -= mtv.x * 0.5;
              b.pose.y -= mtv.y * 0.5;
              Geometry.clampToWorld(a);
              Geometry.clampToWorld(b);
            }
          }
        }
        if (!changed) break;
      }
    },
'''

new_solve = '''    routedPushBudget(u, wantedPx) {
      if (!u?.status?.routing) return Math.max(0, wantedPx);

      // solveGlobal() runs twice in the same simulation frame. Keep one shared
      // per-frame budget so repeated MTV iterations cannot accelerate a ROUT.
      if (u.motion.routSeparationAt !== State.simTime) {
        u.motion.routSeparationAt = State.simTime;
        u.motion.routSeparationUsed = 0;
      }

      const stepPx = Math.max(0, Number(u.motion.routStepPx) || 0);
      // Collision correction is allowed to be only a fraction of the intended
      // rout movement. Tiny floor prevents permanent interpenetration at low dt.
      const maxPx = Math.max(0.015 * CFG.U, stepPx * 0.35);
      const used = Math.max(0, Number(u.motion.routSeparationUsed) || 0);
      return Math.min(Math.max(0, wantedPx), Math.max(0, maxPx - used));
    },

    pushWithRoutBudget(u, dx, dy) {
      const len = Math.hypot(dx, dy);
      if (len <= 1e-6) return false;

      let scale = 1;
      if (u.status.routing) {
        const allowed = this.routedPushBudget(u, len);
        if (allowed <= 1e-6) return false;
        scale = allowed / len;
        u.motion.routSeparationUsed = (u.motion.routSeparationUsed || 0) + allowed;
      }

      u.pose.x += dx * scale;
      u.pose.y += dy * scale;
      Geometry.clampToWorld(u);
      return true;
    },

    solveGlobal(iterations = 6) {
      for (let iter = 0; iter < iterations; iter++) {
        let changed = false;
        for (let i = 0; i < State.units.length; i++) {
          const a = State.units[i];
          if (!a.status.alive) continue;
          for (let j = i + 1; j < State.units.length; j++) {
            const b = State.units[j];
            if (!b.status.alive || Engagements.pair(a, b)) continue;

            // ROUT formations are a disordered flow, not rigid bodies that should
            // repeatedly push each other apart. Let routed friends/enemies overlap
            // rather than create solver pumping through 6 iterations × 2 passes.
            if (a.status.routing && b.status.routing) continue;

            const mtv = Geometry.overlapMTV(a, b);
            if (!mtv) continue;

            // ROUT vs active unit: move only the routed formation, and cap the
            // correction for the entire simulation frame. Never shove the stable line.
            if (a.status.routing !== b.status.routing) {
              const moved = a.status.routing
                ? this.pushWithRoutBudget(a, mtv.x, mtv.y)
                : this.pushWithRoutBudget(b, -mtv.x, -mtv.y);
              changed = moved || changed;
              continue;
            }

            changed = true;
            const aa = this.isAnchored(a);
            const ba = this.isAnchored(b);
            if (aa && !ba) {
              b.pose.x -= mtv.x;
              b.pose.y -= mtv.y;
              Geometry.clampToWorld(b);
            } else if (ba && !aa) {
              a.pose.x += mtv.x;
              a.pose.y += mtv.y;
              Geometry.clampToWorld(a);
            } else {
              a.pose.x += mtv.x * 0.5;
              a.pose.y += mtv.y * 0.5;
              b.pose.x -= mtv.x * 0.5;
              b.pose.y -= mtv.y * 0.5;
              Geometry.clampToWorld(a);
              Geometry.clampToWorld(b);
            }
          }
        }
        if (!changed) break;
      }
    },
'''

if old_solve not in s:
    raise SystemExit('solveGlobal block not found')
s = s.replace(old_solve, new_solve, 1)

old_resolve = '''        if (this.tryPursuitStrikeOnContact(u, other)) {
          // Pursuit contact non è un muro: lascia il movimento e separa poi globalmente.
          return 'pursuit';
        }
        if (this.tryEngageOnContact(u, other)) return 'magnet';
        u.pose.x = oldPose.x;
        u.pose.y = oldPose.y;
        u.motion.moving = false;
        return 'blocked';
'''

new_resolve = '''        if (this.tryPursuitStrikeOnContact(u, other)) {
          // Pursuit contact non è un muro: lascia il movimento e separa poi globalmente.
          return 'pursuit';
        }

        // A ROUT must not treat another formation as blocking terrain. Keeping the
        // forward step prevents oscillation oldPose <-> MTV; solveGlobal performs
        // only a small capped separation against active formations afterwards.
        if (u.status.routing) return 'unit-overlap';

        if (this.tryEngageOnContact(u, other)) return 'magnet';
        u.pose.x = oldPose.x;
        u.pose.y = oldPose.y;
        u.motion.moving = false;
        return 'blocked';
'''

if old_resolve not in s:
    raise SystemExit('resolveMover unit collision block not found')
s = s.replace(old_resolve, new_resolve, 1)

old_rout_speed = '''      const old = { ...u.pose };
      const speed = CFG.SPEED_U_S * CFG.U * u.profile.fleeMult * Terrain.movementMultiplier(u);
      u.pose.x += Math.cos(u.status.routAngle) * speed * dt;
'''
new_rout_speed = '''      const old = { ...u.pose };
      const speed = CFG.SPEED_U_S * CFG.U * u.profile.fleeMult * Terrain.movementMultiplier(u);
      // Used by the collision solver to cap lateral separation in proportion
      // to the legal ROUT movement of this exact simulation frame.
      u.motion.routStepPx = speed * dt;
      u.pose.x += Math.cos(u.status.routAngle) * speed * dt;
'''
if old_rout_speed not in s:
    raise SystemExit('updateRout speed block not found')
s = s.replace(old_rout_speed, new_rout_speed, 1)

# Clarify that only true terrain blocking can trigger route deflection.
old_deflect = '''      const terrainResult = Collision.resolveMover(u, old);
      if (terrainResult === 'terrain-recovered' || terrainResult === 'blocked') {
        const oldAngle = u.status.routAngle;
'''
new_deflect = '''      const terrainResult = Collision.resolveMover(u, old);
      // 'unit-overlap' deliberately keeps the same rout direction. Only terrain
      // recovery/blocking is allowed to choose a new escape heading.
      if (terrainResult === 'terrain-recovered' || terrainResult === 'blocked') {
        const oldAngle = u.status.routAngle;
'''
if old_deflect not in s:
    raise SystemExit('updateRout deflection block not found')
s = s.replace(old_deflect, new_deflect, 1)

p.write_text(s, encoding='utf-8')
print('patched rout pumping -> v0.87.3')
