from pathlib import Path
import re, sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'COFFEE_BATTLES.html')
s = path.read_text(encoding='utf-8')
orig = s

def rep(old, new, count=1, required=True, label=None):
    global s
    n = s.count(old)
    if required and n < count:
        raise SystemExit(f"PATCH FAIL [{label or old[:80]}]: expected >= {count}, found {n}")
    s = s.replace(old, new, count)
    print(f"replace {label or old[:40]!r}: {min(n,count)}")

def sub(pattern, repl, count=1, required=True, flags=0, label=None):
    global s
    s2, n = re.subn(pattern, repl, s, count=count, flags=flags)
    if required and n < count:
        raise SystemExit(f"PATCH FAIL regex [{label or pattern[:80]}]: expected {count}, found {n}")
    s = s2
    print(f"regex {label or pattern[:40]!r}: {n}")

s = s.replace('v0.88.4', 'v0.89.2').replace('v0.88.3', 'v0.89.2').replace('v0.88.2', 'v0.89.2')
rep('    <div class="setup-footnote">v0.88 · Step 1/3 — Map Engine biomi + Doctrine Engine + Army AI + limite battaglia 600s.</div>',
    '    <div class="setup-footnote">v0.89.2 · Step 1/3 — 8 profili unità + ranged resolver unilaterale + Map/Doctrine/Army AI.</div>',
    required=False, label='setup footnote')

rep('  .unit-card[data-unit-type="cavalry"] .reg{left:14px;top:17px;width:24px;height:14px}\n  .unit-card[data-unit-type="archer"] .reg:after{content:"→";position:absolute;right:-14px;top:-8px;font-size:12px;color:#f0d36f}',
'''  .unit-card[data-unit-type="cavalry"] .reg,
  .unit-card[data-unit-type="horse_archer"] .reg{left:14px;top:17px;width:24px;height:14px}
  .unit-card[data-unit-type="archer"] .reg:after,
  .unit-card[data-unit-type="light_infantry"] .reg:after,
  .unit-card[data-unit-type="crossbow"] .reg:after,
  .unit-card[data-unit-type="horse_archer"] .reg:after{content:"→";position:absolute;right:-14px;top:-8px;font-size:12px;color:#f0d36f}''', label='unit card CSS')

old_cards = '''    <button class="unit-card" type="button" data-unit-type="infantry" data-cost="100">
      <span class="unit-card-preview"><span class="reg"></span></span>
      <span class="unit-card-copy"><strong>Fanteria</strong><span>C2 · AR1 · V100</span><span class="cost">100 PT</span></span>
    </button>
    <button class="unit-card" type="button" data-unit-type="archer" data-cost="110">
      <span class="unit-card-preview"><span class="reg"></span></span>
      <span class="unit-card-copy"><strong>Arcieri</strong><span>C1 · Mira2 · AR0 · V100</span><span class="cost">110 PT</span></span>
    </button>
    <button class="unit-card" type="button" data-unit-type="cavalry" data-cost="180">
      <span class="unit-card-preview"><span class="reg"></span></span>
      <span class="unit-card-copy"><strong>Cavalleria</strong><span>C3 · AR2 · V30</span><span class="cost">180 PT</span></span>
    </button>'''
new_cards = '''    <button class="unit-card" type="button" data-unit-type="infantry" data-cost="100">
      <span class="unit-card-preview"><span class="reg"></span></span>
      <span class="unit-card-copy"><strong>Fanteria</strong><span>C2 · AR1 · V100</span><span class="cost">100 PT</span></span>
    </button>
    <button class="unit-card" type="button" data-unit-type="light_infantry" data-cost="80">
      <span class="unit-card-preview"><span class="reg"></span></span>
      <span class="unit-card-copy"><strong>Fanteria leggera</strong><span>C2 · Mira2 · 5U · 5s</span><span class="cost">80 PT</span></span>
    </button>
    <button class="unit-card" type="button" data-unit-type="heavy_infantry" data-cost="140">
      <span class="unit-card-preview"><span class="reg"></span></span>
      <span class="unit-card-copy"><strong>Fanteria pesante</strong><span>C2 · AR2 · M0.8</span><span class="cost">140 PT</span></span>
    </button>
    <button class="unit-card" type="button" data-unit-type="spearman" data-cost="120">
      <span class="unit-card-preview"><span class="reg"></span></span>
      <span class="unit-card-copy"><strong>Lanceri</strong><span>C2 · AR2 · COVER FRONTE</span><span class="cost">120 PT</span></span>
    </button>
    <button class="unit-card" type="button" data-unit-type="archer" data-cost="110">
      <span class="unit-card-preview"><span class="reg"></span></span>
      <span class="unit-card-copy"><strong>Arcieri</strong><span>C1 · Mira2 · AR0 · 15U · 3s</span><span class="cost">110 PT</span></span>
    </button>
    <button class="unit-card" type="button" data-unit-type="crossbow" data-cost="125">
      <span class="unit-card-preview"><span class="reg"></span></span>
      <span class="unit-card-copy"><strong>Balestrieri</strong><span>C1 · Mira3 · AP1 · 13U · 7s</span><span class="cost">125 PT</span></span>
    </button>
    <button class="unit-card" type="button" data-unit-type="cavalry" data-cost="180">
      <span class="unit-card-preview"><span class="reg"></span></span>
      <span class="unit-card-copy"><strong>Cavalleria</strong><span>C3 · AR3 · V30</span><span class="cost">180 PT</span></span>
    </button>
    <button class="unit-card" type="button" data-unit-type="horse_archer" data-cost="160">
      <span class="unit-card-preview"><span class="reg"></span></span>
      <span class="unit-card-copy"><strong>Cavalleria leggera</strong><span>C1 · Mira2 · M2 · 10U</span><span class="cost">160 PT</span></span>
    </button>'''
rep(old_cards, new_cards, label='deployment cards')
rep('title="Fuoco a volontà: automatico entro 15U, indipendente dalla stance"',
    'title="Fuoco a volontà: automatico entro la gittata del profilo, indipendente dalla stance"', required=False, label='fire button title')
rep('<span class="pill">🎯</span> Arcieri: autofire; target esplicito = tiro anche con 🎯 OFF / Hold<br>',
    '<span class="pill">🎯</span> Tiratori: autofire; target esplicito = tiro anche con 🎯 OFF / Hold<br>', required=False, label='controls ranged label')

s = s.replace('CAVALRY_ARMOR: 2,', 'CAVALRY_ARMOR: 3,')
unit_types = r'''  // ============================================================
  // UNIT TYPE CATALOG — single source of truth for stats + roles
  // ============================================================
  const UNIT_TYPES = Object.freeze({
    infantry: Object.freeze({
      label:'Fanteria', short:'INF', cost:100,
      stats:Object.freeze({ hp:100, combat:2, armor:1, aim:null }),
      profile:Object.freeze({ marchMult:1, chargeMult:3, fleeMult:3, moveEnergyFactor:1, chargeEnergyFactor:1, mounted:false, forestBlocked:false, chargeShockMult:1, frontCover:0, ranged:null }),
      roles:Object.freeze({ line:1.0, reserve:0.6 })
    }),
    light_infantry: Object.freeze({
      label:'Fanteria leggera', short:'LEG', cost:80,
      stats:Object.freeze({ hp:100, combat:2, armor:0, aim:2 }),
      profile:Object.freeze({ marchMult:1.25, chargeMult:3.5, fleeMult:3.5, moveEnergyFactor:0.80, chargeEnergyFactor:0.85, mounted:false, forestBlocked:false, chargeShockMult:1, frontCover:0, ranged:Object.freeze({ rangeU:5, volleyInterval:5, armorPiercing:0 }) }),
      roles:Object.freeze({ line:0.35, ranged:0.55, mobile:0.65, screen:1.0, reserve:0.25 })
    }),
    heavy_infantry: Object.freeze({
      label:'Fanteria pesante', short:'PES', cost:140,
      stats:Object.freeze({ hp:100, combat:2, armor:2, aim:null }),
      profile:Object.freeze({ marchMult:0.80, chargeMult:2.5, fleeMult:2.5, moveEnergyFactor:1.15, chargeEnergyFactor:1.15, mounted:false, forestBlocked:false, chargeShockMult:1, frontCover:0, ranged:null }),
      roles:Object.freeze({ line:1.0, shock:0.45, reserve:0.85 })
    }),
    spearman: Object.freeze({
      label:'Lanceri', short:'LAN', cost:120,
      stats:Object.freeze({ hp:100, combat:2, armor:2, aim:null }),
      profile:Object.freeze({ marchMult:0.90, chargeMult:2.5, fleeMult:3, moveEnergyFactor:1, chargeEnergyFactor:1, mounted:false, forestBlocked:false, chargeShockMult:1, frontCover:1, ranged:null }),
      roles:Object.freeze({ line:1.0, screen:0.25, reserve:0.75 })
    }),
    archer: Object.freeze({
      label:'Arcieri', short:'ARC', cost:110,
      stats:Object.freeze({ hp:100, combat:1, armor:0, aim:2 }),
      profile:Object.freeze({ marchMult:1, chargeMult:3, fleeMult:3, moveEnergyFactor:1, chargeEnergyFactor:1, mounted:false, forestBlocked:false, chargeShockMult:1, frontCover:0, ranged:Object.freeze({ rangeU:15, volleyInterval:3, armorPiercing:0 }) }),
      roles:Object.freeze({ ranged:1.0, screen:0.5 })
    }),
    crossbow: Object.freeze({
      label:'Balestrieri', short:'BAL', cost:125,
      stats:Object.freeze({ hp:100, combat:1, armor:1, aim:3 }),
      profile:Object.freeze({ marchMult:0.90, chargeMult:2.5, fleeMult:3, moveEnergyFactor:1.05, chargeEnergyFactor:1.05, mounted:false, forestBlocked:false, chargeShockMult:1, frontCover:0, ranged:Object.freeze({ rangeU:13, volleyInterval:7, armorPiercing:1 }) }),
      roles:Object.freeze({ line:0.20, ranged:1.0, reserve:0.45 })
    }),
    cavalry: Object.freeze({
      label:'Cavalleria', short:'CAV', cost:180,
      stats:Object.freeze({ hp:30, combat:3, armor:3, aim:null }),
      profile:Object.freeze({ marchMult:1, chargeMult:6, fleeMult:6, moveEnergyFactor:0.5, chargeEnergyFactor:0.25, mounted:true, forestBlocked:true, chargeShockMult:2, frontCover:0, ranged:null }),
      roles:Object.freeze({ mobile:1.0, shock:0.9, reserve:0.4 })
    }),
    horse_archer: Object.freeze({
      label:'Cavalleria leggera', short:'CAV-L', cost:160,
      stats:Object.freeze({ hp:30, combat:1, armor:0, aim:2 }),
      profile:Object.freeze({ marchMult:2, chargeMult:5, fleeMult:6, moveEnergyFactor:0.45, chargeEnergyFactor:0.30, mounted:true, forestBlocked:true, chargeShockMult:1, frontCover:0, ranged:Object.freeze({ rangeU:10, volleyInterval:3.5, armorPiercing:0 }) }),
      roles:Object.freeze({ ranged:0.75, mobile:1.0, screen:0.9, reserve:0.15 })
    })
  });

'''
if 'const UNIT_TYPES = Object.freeze({' not in s:
    rep('  const worldPx = () => ({ w: CFG.WORLD_W_U * CFG.U, h: CFG.WORLD_H_U * CFG.U });',
        unit_types + '  const worldPx = () => ({ w: CFG.WORLD_W_U * CFG.U, h: CFG.WORLD_H_U * CFG.U });', label='insert UNIT_TYPES')

new_factory = r'''  function makeUnit(id, name, side, x, y, angle, color, type = 'infantry') {
    const spec = UNIT_TYPES[type] || UNIT_TYPES.infantry;
    const rangedSpec = spec.profile.ranged;
    return {
      id, name, side, color, type,
      profile: {
        marchMult: spec.profile.marchMult, chargeMult: spec.profile.chargeMult, fleeMult: spec.profile.fleeMult,
        moveEnergyFactor: spec.profile.moveEnergyFactor, chargeEnergyFactor: spec.profile.chargeEnergyFactor,
        mounted: !!spec.profile.mounted, forestBlocked: !!spec.profile.forestBlocked,
        chargeShockMult: Math.max(0, Number(spec.profile.chargeShockMult) || 1),
        frontCover: Math.max(0, Number(spec.profile.frontCover) || 0),
        ranged: rangedSpec ? { rangeU:rangedSpec.rangeU, volleyInterval:rangedSpec.volleyInterval, armorPiercing:Math.max(0, Number(rangedSpec.armorPiercing) || 0) } : null
      },
      pose: { x, y, angle },
      stats: { maxHp:spec.stats.hp, hp:spec.stats.hp, energy:CFG.MAX_ENERGY, brain:CFG.MAX_BRAIN, combat:spec.stats.combat, armor:spec.stats.armor, aim:spec.stats.aim, shock:0 },
      battleRecord: { damageV:0, damageB:0, damageVTaken:0, damageBTaken:0, kills:0, routsOut:0 },
      formation: { type:'base', transition:null },
      behavior: { stance:'hold', active:false, targetId:null },
      order: { kind:'idle', target:null, queue:[], lockTargetId:null, finalAttackTargetId:null, approach:null, retreatThreatId:null, retreatAngle:null, pursuit:null, pursuitBlockedEnemyId:null },
      motion: { moveMult:spec.profile.marchMult, chargeMode:false, chargeOverride:null, moving:false, turn:null, detour:null, terrainClearanceBoostUntil:0, wallCrossing:null, wallPassId:null },
      engagement: { outbound:null, inbound:{ front:null, rear:null, 'flank-left':null, 'flank-right':null } },
      ranged: rangedSpec ? { fireAtWill:true, clock:0, active:false, targetId:null, approachTargetId:null } : null,
      status: { alive:true, exited:false, exitReason:null, routing:false, permanentRout:false, routAngle:null, chargeUntil:0, suppressedUntil:0, brainLossClock:0, brainRecoveryClock:0, rearExposureClock:0, moraleState:'steady', routShockEmitted:false, lastHostileSourceId:null, routedById:null, friendlyFleeImpactVictims:new Set() }
    };
  }
'''
sub(r"  function makeUnit\(id, name, side, x, y, angle, color, type = 'infantry'\) \{.*?\n  \}\n\n  const Units = \{", new_factory + "\n  const Units = {", flags=re.S, label='makeUnit factory')
rep("      if (u.type !== 'cavalry') return { ...base };", "      if (!u.profile.mounted) return { ...base };", label='mounted geometry')
s = s.replace('// Cavalleria: BASE = 2×1U.', '// Unità montate: BASE = 2×1U.')
s = s.replace('// Gli arcieri interpretano SEMPRE il lock come ordine RANGED.', '// Le unità ranged interpretano SEMPRE il lock come ordine RANGED.')
s = s.replace('// ARCIERI — RANGED COMPLETAMENTE SEPARATO DALLA STANCE.', '// RANGED — COMPLETAMENTE SEPARATO DALLA STANCE.')
s = s.replace('if (State.simTime >= u.status.chargeUntil) u.motion.moveMult = 1;', 'if (State.simTime >= u.status.chargeUntil) u.motion.moveMult = u.profile.marchMult;')
s = re.sub(r"t\.type === 'forest' && u\.type === 'cavalry'", "t.type === 'forest' && u.profile.forestBlocked", s)
s = re.sub(r"t\.type==='forest'\s*&&\s*u\.type==='cavalry'", "t.type==='forest' && u.profile.forestBlocked", s)
rep("      const cavalryMult = attacker.type === 'cavalry' ? CFG.CAVALRY_CHARGE_SHOCK_MULT : 1;\n      const totalMult = positionMult * cavalryMult;", "      const chargeShockMult = Math.max(0, Number(attacker.profile.chargeShockMult) || 1);\n      const totalMult = positionMult * chargeShockMult;", label='charge shock multiplier')
rep("        `×${positionMult}${attacker.type === 'cavalry' ? ' ×2 CAV' : ''} | ` +", "        `×${positionMult}${chargeShockMult !== 1 ? ` ×${chargeShockMult} MOUNT` : ''} | ` +", label='charge log')

rep("      const legacyMovement=Terrain.movementMultiplier.bind(Terrain);\n      const legacyRangedDefense=Terrain.rangedDefenseBonus.bind(Terrain);\n      const legacyLos=Terrain.lineOfSight.bind(Terrain);", "      const legacyMovement=Terrain.movementMultiplier.bind(Terrain);\n      const legacyRangedAttack=Terrain.rangedAttackPenalty.bind(Terrain);\n      const legacyRangedDefense=Terrain.rangedDefenseBonus.bind(Terrain);\n      const legacyLos=Terrain.lineOfSight.bind(Terrain);", required=False, label='map adapter capture ranged attack')
old_building_cover = '''      Terrain.rangedDefenseBonus=(attacker,defender)=>{
        let bonus=legacyRangedDefense(attacker,defender);
        const a=Geometry.center(attacker),d=Geometry.center(defender);
        for(const t of State.terrain){
          if(t.type==='building'&&Terrain.segmentIntersects(t,a,d)&&Terrain.containsPoint(t,d,1.6*CFG.U))bonus=Math.max(bonus,1);
        }
        return bonus;
      };'''
new_building_cover = '''      Terrain.rangedAttackPenalty=(attacker,defender)=>{
        let penalty=legacyRangedAttack(attacker,defender);
        const a=Geometry.center(attacker),d=Geometry.center(defender);
        for(const t of State.terrain){
          if(t.type==='building'&&Terrain.segmentIntersects(t,a,d)&&Terrain.containsPoint(t,d,1.6*CFG.U))penalty=Math.max(penalty,1);
        }
        return penalty;
      };
      Terrain.rangedDefenseBonus=(attacker,defender)=>0;'''
rep(old_building_cover, new_building_cover, required=False, label='building cover -> aim penalty')

rep('      // F attacchi ogni 3 secondi.', '      // F attacchi a ogni volley; la cadenza dipende dal profilo unità.', required=False, label='volley comment')
new_volley = r'''    coverPenalty(attacker, defender) {
      const terrain = Math.max(0, Number(Terrain.rangedAttackPenalty(attacker, defender)) || 0);
      const incomingSlot = Geometry.incomingSlot(defender, attacker);
      const frontal = incomingSlot === 'front' ? Math.max(0, Number(defender.profile.frontCover) || 0) : 0;
      return Math.max(terrain, frontal);
    },

    resolveShot(attacker, defender) {
      const cover = this.coverPenalty(attacker, defender);
      const aim = Math.max(0, (attacker.stats.aim || 0) - cover);
      const armorPiercing = Math.max(0, Number(attacker.profile.ranged?.armorPiercing) || 0);
      const effectiveArmor = Math.max(0, defender.stats.armor - armorPiercing);
      const die = Combat.battleDie();
      const hit = die === 6 || (die !== 1 && die + aim >= 6 + effectiveArmor);
      return { hit, die, aim, cover, armorPiercing, effectiveArmor };
    },

    volley(attacker, defender) {
      if (!attacker.status.alive || !defender.status.alive) return;
      const attacks = this.attacksPerVolley(attacker);
      let hits = 0;
      let resolved = null;
      for (let i = 0; i < attacks; i++) {
        this.spawnProjectile(attacker, defender, i, attacks);
        const shot = this.resolveShot(attacker, defender);
        resolved = shot;
        if (shot.hit) hits++;
      }
      const hpBefore = defender.stats.hp;
      const brainBefore = defender.stats.brain;
      defender.stats.hp = Math.max(0, defender.stats.hp - hits);
      defender.stats.brain = Math.max(0, defender.stats.brain - hits);
      const shock = Combat.moraleShock(defender, hits, hpBefore, null);
      defender.stats.shock += shock;
      const converted = Combat.convertShock(defender);
      Battle.recordDamage(attacker, defender, hpBefore - defender.stats.hp, brainBefore - defender.stats.brain);
      const ap = resolved?.armorPiercing || 0;
      const cover = resolved?.cover || 0;
      Log.add(`🏹 ${attacker.name} → ${defender.name}: ${attacks}A tiro | Mira ${resolved?.aim ?? 0} vs AR${resolved?.effectiveArmor ?? defender.stats.armor} | -${hits}V` + `${ap ? ` | AP${ap}` : ''}` + `${cover ? ` | COVER -${cover} Mira` : ''}` + `${shock ? ` | +${shock}S` : ''}` + `${converted ? ` → -${converted}B` : ''}`);
      if (defender.stats.hp <= 0) Combat.destroy(defender, attacker);
      else if (defender.stats.brain <= 0) Orders.startRout(defender, attacker);
    },'''
sub(r"    volley\(attacker, defender\) \{.*?\n    \},\n\n    update\(dt\) \{", new_volley + "\n\n    update(dt) {", flags=re.S, label='unilateral ranged resolver')
s = s.replace("Log.add(`ARCIERI (${archers.length}): FUOCO A VOLONTÀ ${enable ? 'ON' : 'OFF'}`);", "Log.add(`RANGED (${archers.length}): FUOCO A VOLONTÀ ${enable ? 'ON' : 'OFF'}`);")

sub(r"      if \(u\.type === 'cavalry' \|\| u\.type === 'archer'\) \{\n        ctx\.save\(\);\n        ctx\.fillStyle = '#ffffff';\n        ctx\.font = 'bold 10px Segoe UI, Arial';\n        ctx\.textAlign = 'center';\n        ctx\.textBaseline = 'bottom';\n        ctx\.fillText\(u\.type === 'cavalry' \? 'CAV' : 'ARC', cp\.x, cp\.y - 14\);\n        ctx\.restore\(\);\n      \}", '''      const unitShort = (UNIT_TYPES[u.type] || UNIT_TYPES.infantry).short;
      if (unitShort) {
        ctx.save(); ctx.fillStyle = '#ffffff'; ctx.font = 'bold 9px Segoe UI, Arial'; ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
        ctx.fillText(unitShort, cp.x, cp.y - 14); ctx.restore();
      }''', required=False, flags=re.S, label='renderer unit short')

sub(r"  const Deployment = \{\n    catalog: Object\.freeze\(\{.*?\n    \}\),\n\n    zone\(side\) \{", "  const Deployment = {\n    catalog: UNIT_TYPES,\n\n    zone(side) {", flags=re.S, label='deployment catalog')
rep("      const suffix = type === 'archer' ? ' ARC' : type === 'cavalry' ? ' CAV' : '';", "      const suffix = spec.short ? ` ${spec.short}` : '';", label='deployment suffix')

new_composer = r'''    generateComposition(budget) {
      const entries = Object.entries(Deployment.catalog).map(([type,spec]) => ({type,spec}));
      const maxUnits = 32;
      const minLineShare = 0.25;
      const minCosts = entries.map(x => x.spec.cost).sort((a,b)=>a-b);
      let targetDistinct = 1, running = 0;
      for (let i=0; i<Math.min(3,minCosts.length); i++) { running += minCosts[i]; if (budget >= running) targetDistinct = i + 1; }
      const candidates = [];
      const seen = new Set();
      const addCandidate = counts => {
        const count = Object.values(counts).reduce((a,b)=>a+b,0);
        if (!count || count > maxUnits) return;
        const spent = entries.reduce((n,{type,spec}) => n + (counts[type]||0)*spec.cost, 0);
        if (spent <= 0 || spent > budget || spent < budget*0.80) return;
        const roleSpend = Object.fromEntries(this.roles.map(r=>[r,0]));
        for (const {type,spec} of entries) { const n = counts[type] || 0; if (!n) continue; for (const role of this.roles) roleSpend[role] += n * spec.cost * this.roleValue(spec,role); }
        const lineShare = roleSpend.line / spent;
        if (lineShare + 1e-9 < minLineShare) return;
        const key = entries.map(({type})=>counts[type]||0).join(',');
        if (seen.has(key)) return; seen.add(key);
        const typeShares = entries.map(({type,spec})=>({type,share:(counts[type]||0)*spec.cost/spent})).filter(x=>x.share>0);
        const distinct = typeShares.length;
        const entropyRaw = distinct>1 ? -typeShares.reduce((sum,x)=>sum+x.share*Math.log(x.share),0) : 0;
        const entropy = distinct>1 ? entropyRaw/Math.log(distinct) : 0;
        const maxTypeShare = Math.max(...typeShares.map(x=>x.share));
        const primaryCoverage = ['line','ranged','mobile'].filter(role=>(roleSpend[role]/spent)>=0.10).length / Math.max(1,targetDistinct);
        const coverage = Math.min(1,primaryCoverage);
        const diversity = Math.min(1,distinct/Math.max(1,targetDistinct));
        const types = entries.flatMap(({type})=>Array(counts[type]||0).fill(type));
        candidates.push({counts:{...counts},types,spent,roleSpend,lineShare,coverage,diversity,entropy,maxTypeShare});
      };
      const cheapestLine = entries.filter(x => this.roleValue(x.spec,'line') >= 0.5).sort((a,b)=>a.spec.cost-b.spec.cost)[0] || entries[0];
      for (const specialist of entries) {
        const counts = Object.fromEntries(entries.map(x=>[x.type,0]));
        while (counts[specialist.type] < 2 && (counts[specialist.type]+1)*specialist.spec.cost <= budget*0.45) counts[specialist.type]++;
        let spent = counts[specialist.type]*specialist.spec.cost;
        while (spent + cheapestLine.spec.cost <= budget && Object.values(counts).reduce((a,b)=>a+b,0) < maxUnits) { counts[cheapestLine.type]++; spent += cheapestLine.spec.cost; }
        addCandidate(counts);
      }
      for (let trial=0; trial<3200; trial++) {
        const counts = Object.fromEntries(entries.map(x=>[x.type,0]));
        let spent = 0, count = 0, lineSpend = 0;
        while (count < maxUnits) {
          const affordable = entries.filter(x => spent + x.spec.cost <= budget); if (!affordable.length) break;
          const currentLineShare = spent > 0 ? lineSpend/spent : 0;
          const pick = this.weightedPick(affordable, x => { const newType = counts[x.type] ? 1 : 1.45; const lineNeed = currentLineShare < minLineShare && this.roleValue(x.spec,'line') >= 0.5 ? 2.6 : 1; const saturation = 1 / (1 + counts[x.type]*0.22); return newType * lineNeed * saturation * this.rand(0.72,1.28); });
          if (!pick) break; counts[pick.type]++; spent += pick.spec.cost; lineSpend += pick.spec.cost*this.roleValue(pick.spec,'line'); count++; if (spent >= budget*0.92 && Math.random() < 0.18) break;
        }
        addCandidate(counts);
      }
      if (!candidates.length) return {types:['infantry'],spent:Deployment.catalog.infantry.cost,quality:0};
      const maxCandidateSpend = Math.max(...candidates.map(x=>x.spent));
      const tacticalBias = Object.fromEntries(this.roles.map(r=>[r,this.rand(0.82,1.18)]));
      for (const c of candidates) {
        const spendRatio = c.spent/Math.max(1,maxCandidateSpend);
        const roleAffinity = this.roles.reduce((sum,role)=>sum+(c.roleSpend[role]/c.spent)*tacticalBias[role],0)/3;
        const dominancePenalty = Math.max(0,c.maxTypeShare-0.67);
        const lowSpendPenalty = Math.max(0,0.90-spendRatio);
        c.quality = spendRatio*4.0 + c.coverage*2.5 + c.diversity*1.4 + c.entropy*1.0 + Math.min(1,c.lineShare/minLineShare)*0.6 + roleAffinity*0.6 - dominancePenalty*4.0 - lowSpendPenalty*10.0;
      }
      candidates.sort((a,b)=>b.quality-a.quality);
      const pool = candidates.slice(0,Math.min(24,candidates.length));
      const best = pool[0].quality;
      return this.weightedPick(pool,x=>Math.exp((x.quality-best)*1.7)) || pool[0];
    },'''
sub(r"    generateComposition\(budget\) \{.*?\n    \},\n\n    openLaneRatio\(side\) \{", new_composer + "\n\n    openLaneRatio(side) {", flags=re.S, label='generic 8-type composer')
s = s.replace("${u.type === 'cavalry' ? 'CAVALLERIA' : (u.type === 'archer' ? 'ARCIERI' : 'FANTERIA')}", "${(UNIT_TYPES[u.type] || UNIT_TYPES.infantry).label.toUpperCase()}")
s = s.replace('<b>C</b> = Combat, unico valore melee usato sia in attacco sia in difesa: Arcieri <b>C1</b> · Fanteria <b>C2</b> · Cavalleria <b>C3</b>.<br>', '<b>C</b> = Combat, usato <b>solo nel melee</b>: tiratori leggeri C1 · fanterie C2 · cavalleria pesante C3.<br>')
s = s.replace('<b>AR</b> = Armor: Arcieri <b>0</b> · Fanteria <b>1</b> · Cavalleria <b>2</b>.<br>', '<b>AR</b> = Armor: AR0 leggeri · AR1 Fanteria/Balestrieri · AR2 Pesante/Lanceri · AR3 Cavalleria.<br>')
sub(r"        <b>Arcieri:</b>.*?Tiro: <b>0 Energia</b>\.<br>", '        <b>Ranged:</b> resolver unilaterale <b>DA + Mira ≥ 6 + AR effettiva</b>; 6 naturale = successo, 1 naturale = fallimento. Il difensore non tira e C non entra nel ranged. Cover = <b>−1 Mira</b>; AP1 riduce AR di 1. Tutti i tiratori partono con 🎯 FUOCO A VOLONTÀ ON. Arcieri 15U/3s · Leggera 5U/5s · Balestrieri 13U/7s · Cavalleria leggera 10U/3,5s. Tiro: <b>0 Energia</b>.<br>', required=False, flags=re.S, label='rules ranged paragraph')

checks = {
    '8 unit catalog': all(x in s for x in ['light_infantry:', 'heavy_infantry:', 'spearman:', 'crossbow:', 'horse_archer:']),
    'crossbow AP1': 'armorPiercing:1' in s,
    'cavalry AR3': "stats:Object.freeze({ hp:30, combat:3, armor:3" in s,
    'all ranged default fire': 'fireAtWill:true' in s or 'fireAtWill: true' in s,
    'unilateral resolver': 'die + aim >= 6 + effectiveArmor' in s,
    'natural 6': 'die === 6' in s,
    'natural 1': 'die !== 1' in s,
    'composer generic': 'for (let trial=0; trial<3200; trial++)' in s,
    'wall crossing preserved': 'wallCrossing:null' in s or 'wallCrossing: null' in s,
    'wall runtime preserved': 'interceptWallTraversal' in s,
    'map engine preserved': 'MapEngine.installTerrainAdapters();' in s,
    'building aim cover': "Terrain.rangedAttackPenalty=(attacker,defender)=>" in s,
}
for k,v in checks.items():
    print(f"CHECK {k}: {'OK' if v else 'FAIL'}")
    if not v: raise SystemExit(f'PATCH FAIL sanity: {k}')
if s == orig: raise SystemExit('PATCH FAIL: no changes')
path.write_text(s, encoding='utf-8')
print(f'PATCH OK: {path} {len(orig)} -> {len(s)} bytes')
