from pathlib import Path

path = Path('COFFEE_BATTLES.html')
text = path.read_text(encoding='utf-8')


def replace_once(old, new, label):
    global text
    n = text.count(old)
    if n != 1:
        raise SystemExit(f'{label}: expected 1 match, found {n}')
    text = text.replace(old, new, 1)


preview_old = '<span class="unit-card-preview"><span class="reg"></span></span>'
preview_new = '<span class="unit-card-preview"><span class="reg"><span class="reg-icon" aria-hidden="true"></span></span></span>'
preview_count = text.count(preview_old)
if preview_count != 8:
    raise SystemExit(f'unit card previews: expected 8, found {preview_count}')
text = text.replace(preview_old, preview_new)

css_anchor = '  .unit-card-preview .reg:before{content:"";position:absolute;left:-1px;right:-1px;top:-2px;border-top:3px solid #eef4fb}\n'
css_icon = css_anchor + '  .unit-card-preview .reg-icon{position:absolute;left:50%;top:50%;width:18px;height:18px;transform:translate(-50%,-50%);display:grid;place-items:center;border:1px solid rgba(255,255,255,.92);border-radius:50%;background:rgba(12,18,28,.78);padding:2px;color:#fff;pointer-events:none}\n  .unit-card-preview .reg-icon svg{display:block;width:100%;height:100%;overflow:visible}\n'
replace_once(css_anchor, css_icon, 'unit icon css')

ranged_arrow = '''  .unit-card[data-unit-type="archer"] .reg:after,
  .unit-card[data-unit-type="light_infantry"] .reg:after,
  .unit-card[data-unit-type="crossbow"] .reg:after,
  .unit-card[data-unit-type="horse_archer"] .reg:after{content:"→";position:absolute;right:-14px;top:-8px;font-size:12px;color:#f0d36f}
'''
replace_once(ranged_arrow, '', 'legacy ranged preview arrows')

unit_icons = r'''
  const UnitIcons = {
    key(type) {
      const map = {
        infantry: 'sword',
        light_infantry: 'javelin_round',
        heavy_infantry: 'warhammer',
        spearman: 'spear_kite',
        archer: 'bow',
        crossbow: 'crossbow',
        cavalry: 'horse',
        horse_archer: 'horse_bow'
      };
      return map[type] || 'sword';
    },

    svg(type) {
      const key = this.key(type);
      const common = 'fill="none" stroke="currentColor" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"';
      const glyphs = {
        sword: `<g ${common}><path d="M50 14 L50 72"/><path d="M34 34 L66 34"/><path d="M44 78 L56 78"/><path d="M50 72 L44 84 L56 84 Z" fill="currentColor" stroke="none"/></g>`,
        javelin_round: `<g ${common}><path d="M27 76 L70 22"/><path d="M70 22 L77 26 L69 31 Z" fill="currentColor" stroke="none"/><circle cx="38" cy="48" r="17"/><circle cx="38" cy="48" r="4" fill="currentColor" stroke="none"/></g>`,
        warhammer: `<g ${common}><path d="M50 30 L50 82"/><rect x="31" y="18" width="38" height="19" rx="3"/><path d="M31 23 L22 17"/></g>`,
        spear_kite: `<g ${common}><path d="M34 18 L34 83"/><path d="M34 10 L43 24 L34 20 L25 24 Z" fill="currentColor" stroke="none"/><path d="M53 28 Q76 29 74 51 Q70 72 57 86 Q44 72 40 51 Q39 32 53 28 Z"/><circle cx="57" cy="49" r="4" fill="currentColor" stroke="none"/></g>`,
        bow: `<g ${common}><path d="M30 76 Q57 50 30 24"/><path d="M30 24 L30 76"/><path d="M36 66 L72 30"/><path d="M72 30 L61 31 L67 24 Z" fill="currentColor" stroke="none"/></g>`,
        crossbow: `<g ${common}><path d="M50 20 L50 82"/><path d="M24 35 Q50 55 76 35"/><path d="M34 55 L66 55"/><path d="M50 20 L58 32 L50 28 L42 32 Z" fill="currentColor" stroke="none"/></g>`,
        horse: `<g ${common}><path d="M68 27 L54 18 L40 24 L34 38 L24 49 L39 49 L43 70 L57 70 L55 55 L67 44 L72 34 Z"/></g>`,
        horse_bow: `<g ${common}><path d="M26 68 Q39 42 58 29 L72 31"/><path d="M26 68 L20 56 L29 56"/><path d="M61 72 Q78 58 64 40"/><path d="M61 40 L61 72"/><path d="M59 66 L82 44"/><path d="M82 44 L71 45 L77 38 Z" fill="currentColor" stroke="none"/></g>`
      };
      return `<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">${glyphs[key] || glyphs.sword}</svg>`;
    },

    paint(ctx, type, x, y, size, color = '#fff') {
      const key = this.key(type);
      const s = size / 100;
      ctx.save();
      ctx.translate(x, y);
      ctx.scale(s, s);
      ctx.translate(-50, -50);
      ctx.strokeStyle = color;
      ctx.fillStyle = color;
      ctx.lineWidth = 7;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      const line = (x1, y1, x2, y2) => { ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke(); };

      if (key === 'sword') {
        line(50,14,50,72); line(34,34,66,34); line(44,78,56,78);
        ctx.beginPath(); ctx.moveTo(50,72); ctx.lineTo(44,84); ctx.lineTo(56,84); ctx.closePath(); ctx.fill();
      } else if (key === 'javelin_round') {
        line(27,76,70,22);
        ctx.beginPath(); ctx.moveTo(70,22); ctx.lineTo(77,26); ctx.lineTo(69,31); ctx.closePath(); ctx.fill();
        ctx.beginPath(); ctx.arc(38,48,17,0,Math.PI*2); ctx.stroke();
        ctx.beginPath(); ctx.arc(38,48,4,0,Math.PI*2); ctx.fill();
      } else if (key === 'warhammer') {
        line(50,30,50,82); ctx.strokeRect(31,18,38,19); line(31,23,22,17);
      } else if (key === 'spear_kite') {
        line(34,18,34,83);
        ctx.beginPath(); ctx.moveTo(34,10); ctx.lineTo(43,24); ctx.lineTo(34,20); ctx.lineTo(25,24); ctx.closePath(); ctx.fill();
        ctx.beginPath(); ctx.moveTo(53,28); ctx.quadraticCurveTo(76,29,74,51); ctx.quadraticCurveTo(70,72,57,86); ctx.quadraticCurveTo(44,72,40,51); ctx.quadraticCurveTo(39,32,53,28); ctx.closePath(); ctx.stroke();
        ctx.beginPath(); ctx.arc(57,49,4,0,Math.PI*2); ctx.fill();
      } else if (key === 'bow') {
        ctx.beginPath(); ctx.moveTo(30,76); ctx.quadraticCurveTo(57,50,30,24); ctx.stroke();
        line(30,24,30,76); line(36,66,72,30);
        ctx.beginPath(); ctx.moveTo(72,30); ctx.lineTo(61,31); ctx.lineTo(67,24); ctx.closePath(); ctx.fill();
      } else if (key === 'crossbow') {
        line(50,20,50,82);
        ctx.beginPath(); ctx.moveTo(24,35); ctx.quadraticCurveTo(50,55,76,35); ctx.stroke();
        line(34,55,66,55);
        ctx.beginPath(); ctx.moveTo(50,20); ctx.lineTo(58,32); ctx.lineTo(50,28); ctx.lineTo(42,32); ctx.closePath(); ctx.fill();
      } else if (key === 'horse') {
        ctx.beginPath(); ctx.moveTo(68,27); ctx.lineTo(54,18); ctx.lineTo(40,24); ctx.lineTo(34,38); ctx.lineTo(24,49); ctx.lineTo(39,49); ctx.lineTo(43,70); ctx.lineTo(57,70); ctx.lineTo(55,55); ctx.lineTo(67,44); ctx.lineTo(72,34); ctx.closePath(); ctx.stroke();
      } else if (key === 'horse_bow') {
        ctx.beginPath(); ctx.moveTo(26,68); ctx.quadraticCurveTo(39,42,58,29); ctx.lineTo(72,31); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(26,68); ctx.lineTo(20,56); ctx.lineTo(29,56); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(61,72); ctx.quadraticCurveTo(78,58,64,40); ctx.stroke();
        line(61,40,61,72); line(59,66,82,44);
        ctx.beginPath(); ctx.moveTo(82,44); ctx.lineTo(71,45); ctx.lineTo(77,38); ctx.closePath(); ctx.fill();
      }
      ctx.restore();
    },

    drawBadge(ctx, unit) {
      if (!unit?.status?.alive) return;
      const d = Geometry.dims(unit);
      const radius = Math.max(7, Math.min(d.depth, d.front) * 0.28);
      const cx = -d.depth * 0.5;
      const cy = 0;
      ctx.save();
      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(12,18,28,.78)';
      ctx.fill();
      ctx.lineWidth = Math.max(1.4, radius * 0.14);
      ctx.strokeStyle = 'rgba(255,255,255,.94)';
      ctx.stroke();
      this.paint(ctx, unit.type, cx, cy, radius * 1.45, '#ffffff');
      ctx.restore();
    },

    syncDeploymentCards(root = DOM.deploymentCards) {
      if (!root) return;
      root.querySelectorAll('.unit-card').forEach(card => {
        const slot = card.querySelector('.reg-icon');
        if (slot) slot.innerHTML = this.svg(card.dataset.unitType);
      });
    }
  };

'''
marker = '  const Renderer = {'
if text.count(marker) != 1:
    raise SystemExit(f'Renderer marker: expected 1, found {text.count(marker)}')
text = text.replace(marker, unit_icons + marker, 1)

front_old = "        ctx.strokeStyle = '#f1d36b';\n        ctx.lineWidth = 6;\n        ctx.beginPath(); ctx.moveTo(0, -d.front / 2); ctx.lineTo(0, d.front / 2); ctx.stroke();"
front_new = front_old + "\n        UnitIcons.drawBadge(ctx, u);"
replace_once(front_old, front_new, 'battlefield unit badge')

hud_old = '''      ctx.save();
      ctx.translate(cp.x, cp.y);
      ctx.rotate(u.pose.angle);
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 24px Segoe UI, Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('>', 0, 0);
      ctx.restore();

      const unitShort = (UNIT_TYPES[u.type] || UNIT_TYPES.infantry).short;
      if (unitShort) {
        ctx.save(); ctx.fillStyle = '#ffffff'; ctx.font = 'bold 9px Segoe UI, Arial'; ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
        ctx.fillText(unitShort, cp.x, cp.y - 14); ctx.restore();
      }

'''
replace_once(hud_old, '', 'legacy unit HUD symbols')

boot_old = '  Input.bind();\n  Deployment.bind();'
boot_new = '  Input.bind();\n  UnitIcons.syncDeploymentCards();\n  Deployment.bind();'
replace_once(boot_old, boot_new, 'boot icon sync')

path.write_text(text, encoding='utf-8')
print('Unit icons applied to latest main.')
