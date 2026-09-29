from pathlib import Path
p=Path('COFFEE_BATTLES.html')
s=p.read_text(encoding='utf-8')

if 'v0.90.0' not in s:
    raise SystemExit('expected v0.90.0 base')
s=s.replace('v0.90.0','v0.90.1')

anchor="""    aiSide() { return this.opposite(State.battle.playerSide); },\n\n    releaseSide(side) {"""
insert="""    aiSide() { return this.opposite(State.battle.playerSide); },\n\n    blindAdvance(u) {\n      // With no contact and no last-known intel, an ATTACKER still has a\n      // strategic mission. Advance straight toward the enemy half without\n      // reading any hidden enemy position. DEFENDERS remain in place.\n      if (State.doctrine.roles[u.side] !== 'attack') return false;\n      const b = battlefieldPx();\n      const targetY = u.side === 'red'\n        ? b.y + b.h * 0.72\n        : b.y + b.h * 0.28;\n      const point = { x: u.pose.x, y: targetY };\n      const dU = Math.hypot(point.x - u.pose.x, point.y - u.pose.y) / CFG.U;\n      if (dU <= 1) return false;\n      return Orders.setManual(u, point, false);\n    },\n\n    releaseSide(side) {"""
if s.count(anchor)!=1:
    raise SystemExit(f'aiSide anchor count {s.count(anchor)}')
s=s.replace(anchor,insert,1)

old="""      if (u.order.kind === 'lock' || u.order.kind === 'ai') Orders.clear(u);\n      return 'none';\n    },\n\n    refresh(force = false) {"""
new="""      if (u.order.kind === 'lock' || u.order.kind === 'ai') Orders.clear(u);\n      if (this.blindAdvance(u)) return 'search';\n      return 'none';\n    },\n\n    refresh(force = false) {"""
if s.count(old)!=1:
    raise SystemExit(f'issue tail count {s.count(old)}')
s=s.replace(old,new,1)

for token in ['blindAdvance(u)', "State.doctrine.roles[u.side] !== 'attack'", 'if (this.blindAdvance(u)) return \'search\';']:
    if token not in s:
        raise SystemExit(f'missing {token}')

p.write_text(s,encoding='utf-8')
print('v0.90.1 blind attacker advance applied')
