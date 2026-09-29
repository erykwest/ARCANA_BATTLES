from pathlib import Path
p=Path('COFFEE_BATTLES.html')
s=p.read_text(encoding='utf-8')
if 'Campal Battle Lab v0.88.4' not in s:
    raise SystemExit('Unexpected source version')

def once(old,new,label):
    global s
    if old not in s: raise SystemExit(f'Missing anchor: {label}')
    s=s.replace(old,new,1)

once(
"      Geometry.clampToWorld(u);\n      Morale.markPermanentRoutIfInBorder(u);\n",
"      Geometry.clampToWorld(u);\n      if (Terrain.interceptWallTraversal(u, old)) return;\n      Morale.markPermanentRoutIfInBorder(u);\n",
'rout wall intercept')

once(
"        Geometry.clampToWorld(u);\n\n        // Il magnet scatta esclusivamente sul lato prenotato.\n",
"        Geometry.clampToWorld(u);\n        if (Terrain.interceptWallTraversal(u, old)) return;\n\n        // Il magnet scatta esclusivamente sul lato prenotato.\n",
'approach wall intercept')

once(
"      Geometry.clampToWorld(u);\n\n      for (const other of Units.enemiesOf(u)) {\n",
"      Geometry.clampToWorld(u);\n      if (Terrain.interceptWallTraversal(u, old)) return;\n\n      for (const other of Units.enemiesOf(u)) {\n",
'normal wall intercept')

p.write_text(s,encoding='utf-8')
