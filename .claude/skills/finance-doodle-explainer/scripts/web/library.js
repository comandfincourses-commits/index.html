/* Finance Doodle Explainer — illustration library.
 * Flat cartoon style: thick #111 outlines, rounded joins, flat fills.
 * Every generator returns { svg, w, h } where w/h are the natural size (px at 1080p).
 * Runs in the browser (window.LIB) and is also require()-able from Node for validation.
 */
(function (root) {
  const K = '#111';
  const SW = 6;
  const C = {
    yellow: '#FDCF3F', red: '#E53935', green: '#43A047', lightGreen: '#7BC67B', darkGreen: '#2E7D32',
    blue: '#2F6FD6', navy: '#1C2B4A', orange: '#F28C28', pink: '#F7A8C4', gold: '#F5B800',
    tan: '#D9A55B', brown: '#7A4E1D', grey: '#9AA3AE', darkGrey: '#4A5568', white: '#FFFFFF', cream: '#FFF6DC',
    skin: '#FFFFFF', purple: '#7E57C2', teal: '#26A69A'
  };
  const esc = s => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const svg = (vb, w, h, inner) => ({
    w, h,
    svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${vb}" width="100%" height="100%" ` +
      `stroke-linejoin="round" stroke-linecap="round">${inner}</svg>`
  });
  const st = (fill, sw = SW, stroke = K) => `fill="${fill}" stroke="${stroke}" stroke-width="${sw}"`;
  const txt = (x, y, s, size, fill = K, extra = '') =>
    `<text x="${x}" y="${y}" font-family="Mali, Chewy, sans-serif" font-weight="700" font-size="${size}" ` +
    `fill="${fill}" text-anchor="middle" dominant-baseline="central" ${extra}>${esc(s)}</text>`;
  // Outlined limb: black wide stroke under a coloured narrower stroke.
  const limb = (d, color, w = 24) =>
    `<path d="${d}" fill="none" stroke="${K}" stroke-width="${w + 11}"/>` +
    `<path d="${d}" fill="none" stroke="${color}" stroke-width="${w}"/>`;
  const hand = (x, y, r = 17) => `<circle cx="${x}" cy="${y}" r="${r}" ${st('#fff', 5)}/>`;

  /* ---------------- Character ---------------- */
  const FACES = {
    neutral: { pupil: [0, 2], mouth: 'M136,172 Q150,178 164,172' },
    happy: { pupil: [0, 2], mouth: 'M122,160 Q150,198 178,160', fillMouth: true },
    smile: { pupil: [0, 2], mouth: 'M128,166 Q150,186 172,166' },
    worried: { pupil: [0, 4], brows: 'M98,86 L134,76 M166,76 L202,86', mouth: 'M128,178 Q139,168 150,178 Q161,188 172,178', sweat: true },
    shocked: { pupil: [0, 0], big: true, mouthO: true, brows: 'M98,70 Q118,58 138,68 M162,68 Q182,58 202,70' },
    sad: { pupil: [0, 6], brows: 'M100,90 L134,80 M166,80 L200,90', mouth: 'M130,182 Q150,164 170,182' },
    smirk: { pupil: [4, 2], lids: true, mouth: 'M130,172 Q158,182 176,160' },
    thinking: { pupil: [-6, -6], mouth: 'M140,174 L166,170', brows: 'M100,82 L134,86 M166,78 L200,72' },
    angry: { pupil: [0, 3], brows: 'M100,76 L136,92 M164,92 L200,76', mouth: 'M132,180 Q150,170 168,180' },
    tired: { pupil: [0, 6], lids: true, heavy: true, mouth: 'M134,178 Q150,172 166,178' },
    excited: { pupil: [0, 0], big: true, mouth: 'M118,156 Q150,206 182,156', fillMouth: true, brows: 'M100,70 Q118,60 136,70 M164,70 Q182,60 200,70' },
    confused: { pupil: [5, -3], brows: 'M100,78 L134,84 M166,72 Q182,64 200,74', mouth: 'M134,178 Q144,170 152,178 Q160,186 168,176' }
  };

  function face(expr) {
    const f = FACES[expr] || FACES.neutral;
    const ry = f.big ? 28 : 23, rx = f.big ? 24 : 20, pr = f.big ? 6 : 8;
    let s = `<g class="eyes" style="transform-origin:150px 116px">`;
    for (const ex of [118, 182]) {
      s += `<ellipse cx="${ex}" cy="116" rx="${rx}" ry="${ry}" ${st('#fff', 5)}/>`;
      s += `<circle cx="${ex + f.pupil[0]}" cy="${118 + f.pupil[1]}" r="${pr}" fill="${K}"/>`;
      if (f.lids) {
        const ly = f.heavy ? 118 : 108;
        s += `<path d="M${ex - rx},${ly} Q${ex},${ly - (f.heavy ? 2 : 10)} ${ex + rx},${ly} L${ex + rx},${116 - ry} L${ex - rx},${116 - ry} Z" fill="#fff"/>`;
        s += `<path d="M${ex - rx + 2},${ly} Q${ex},${ly - (f.heavy ? 2 : 10)} ${ex + rx - 2},${ly}" fill="none" stroke="${K}" stroke-width="5"/>`;
        s += `<ellipse cx="${ex}" cy="116" rx="${rx}" ry="${ry}" fill="none" stroke="${K}" stroke-width="5"/>`;
      }
    }
    s += `</g>`;
    if (f.brows) s += `<path d="${f.brows}" fill="none" stroke="${K}" stroke-width="6"/>`;
    if (f.mouthO) s += `<ellipse cx="150" cy="176" rx="13" ry="17" fill="${K}"/>`;
    else if (f.fillMouth) s += `<path d="${f.mouth} Z" fill="#7a1f1f" stroke="${K}" stroke-width="5"/>`;
    else s += `<path d="${f.mouth}" fill="none" stroke="${K}" stroke-width="6"/>`;
    if (f.sweat) s += `<path d="M214,92 q10,18 0,26 q-10,-8 0,-26 Z" fill="#7EC8F2" stroke="${K}" stroke-width="4"/>`;
    return s;
  }

  function hair(style, color) {
    switch (style) {
      case 'bald': return '';
      case 'old': return `<path d="M88,96 q-8,-22 6,-30 M212,96 q8,-22 -6,-30" fill="none" stroke="${K}" stroke-width="5"/><path d="M146,30 q6,-12 14,-4" fill="none" stroke="${K}" stroke-width="5"/>`;
      case 'spiky': return `<path d="M72,92 L84,40 L104,62 L120,22 L140,52 L158,16 L172,52 L192,24 L202,62 L222,44 L226,96 Q150,58 72,92 Z" ${st(color || '#2b2b2b', 5)}/>`;
      case 'bob': return `<path d="M50,170 Q36,30 150,22 Q264,30 250,170 Z" ${st(color || '#E91E8C', 5)}/>`;
      case 'long': return `<path d="M50,250 Q30,30 150,22 Q270,30 250,250 Z" ${st(color || '#5D3A1A', 5)}/>`;
      case 'fringe': return `<path d="M62,104 Q64,32 150,26 Q236,32 238,104 Q214,70 180,78 Q150,62 120,80 Q86,70 62,104 Z" ${st(color || '#E91E8C', 5)}/>`;
      case 'side': return `<path d="M66,104 Q58,30 150,24 Q236,26 238,96 Q214,58 160,62 Q120,64 100,48 Q84,70 66,104 Z" ${st(color || '#B08D57', 5)}/><path d="M100,48 Q130,40 160,62" fill="none" stroke="${K}" stroke-width="4"/>`;
      case 'cap': return `<path d="M62,100 Q62,22 150,22 Q238,22 238,100 Z" ${st(color || C.red, 5)}/><path d="M200,96 L282,100 Q284,112 236,112 L200,108 Z" ${st(color || C.red, 5)}/><circle cx="150" cy="24" r="7" ${st(color || C.red, 4)}/>`;
      case 'curl':
      default: return `<path d="M150,32 q2,-30 26,-24 q12,4 4,14" fill="none" stroke="${K}" stroke-width="6"/>`;
    }
  }

  const ARMS = {
    // [left arm path, left hand, right arm path, right hand]
    stand: ['M94,226 Q70,300 84,362', [84, 366], 'M206,226 Q230,300 216,362', [216, 366]],
    point: ['M94,226 Q70,300 84,362', [84, 366], 'M206,226 Q268,214 312,186', [318, 182]],
    pointUp: ['M94,226 Q70,300 84,362', [84, 366], 'M206,226 Q248,170 252,96', [252, 88]],
    armsUp: ['M94,226 Q58,160 50,96', [48, 88], 'M206,226 Q242,160 250,96', [252, 88]],
    think: ['M94,226 Q70,300 84,362', [84, 366], 'M206,228 Q262,300 186,212', [184, 206]],
    shrug: ['M94,226 Q36,270 40,206', [40, 198], 'M206,226 Q264,270 260,206', [260, 198]],
    hold: ['M94,226 Q86,306 126,302', [132, 300], 'M206,226 Q214,306 174,302', [168, 300]],
    present: ['M94,226 Q70,300 84,362', [84, 366], 'M206,226 Q262,300 316,282', [322, 278]],
    hips: ['M94,226 Q44,286 92,334', [94, 336], 'M206,226 Q256,286 208,334', [206, 336]],
    headScratch: ['M94,226 Q70,300 84,362', [84, 366], 'M206,226 Q268,180 222,70', [220, 64]],
    facepalm: ['M94,226 Q70,300 84,362', [84, 366], 'M206,226 Q250,280 168,124', [164, 118]]
  };

  function character(o = {}) {
    const pose = ARMS[o.pose] ? o.pose : 'stand';
    const outfit = o.outfit || 'tshirt';
    const color = o.color || C.blue;
    const [la, lh, ra, rh] = ARMS[pose];
    const sleeve = outfit === 'suit' ? '#2b2b2b' : color;
    let body = '';
    // legs
    body += `<path d="M104,370 L100,490 L138,490 L146,392 L154,392 L162,490 L200,490 L196,370 Z" ${st(o.pants || '#3a3a3a', 5)}/>`;
    body += `<path d="M92,492 Q92,470 120,474 L140,476 L140,500 L92,500 Z" ${st('#222', 5)}/><path d="M160,476 L180,474 Q208,470 208,492 L208,500 L160,500 Z" ${st('#222', 5)}/>`;
    // torso
    if (outfit === 'suit') {
      body += `<path d="M86,214 Q150,192 214,214 L224,384 L76,384 Z" ${st('#2b2b2b', SW)}/>`;
      body += `<path d="M128,206 L150,262 L172,206 Z" fill="#fff" stroke="${K}" stroke-width="4"/>`;
      body += `<path d="M150,216 L141,232 L150,300 L159,232 Z" fill="${o.tie || C.red}" stroke="${K}" stroke-width="4"/>`;
      body += `<path d="M128,206 L120,262 L150,262 M172,206 L180,262 L150,262" fill="none" stroke="#555" stroke-width="4"/>`;
    } else if (outfit === 'hoodie') {
      body += `<path d="M84,216 Q150,190 216,216 L226,386 L74,386 Z" ${st(color, SW)}/>`;
      body += `<path d="M112,206 Q150,250 188,206" fill="none" stroke="${K}" stroke-width="5"/>`;
      body += `<path d="M110,320 L190,320 L182,362 L118,362 Z" fill="none" stroke="${K}" stroke-width="4"/>`;
    } else if (outfit === 'uniform') {
      body += `<path d="M86,214 Q150,192 214,214 L224,384 L76,384 Z" ${st(color, SW)}/>`;
      body += `<path d="M126,206 L150,236 L174,206" fill="none" stroke="${K}" stroke-width="5"/>`;
      body += txt(150, 300, o.logo || '', 40, '#FFD54F');
    } else {
      body += `<path d="M86,214 Q150,192 214,214 L224,384 L76,384 Z" ${st(color, SW)}/>`;
      body += `<path d="M128,207 Q150,222 172,207" fill="none" stroke="${K}" stroke-width="5"/>`;
      if (o.logo) body += txt(150, 290, o.logo, 40, '#FFD54F');
    }
    const arms = limb(la, sleeve) + hand(lh[0], lh[1]) + limb(ra, sleeve) + hand(rh[0], rh[1]);
    let head = `<circle cx="150" cy="118" r="92" ${st('#fff', SW)}/>`;
    const longHair = o.hair === 'long' || o.hair === 'bob';
    const hairSvg = hair(o.hair || 'curl', o.hairColor);
    const fringe = longHair ? hair('fringe', o.hairColor || (o.hair === 'long' ? '#5D3A1A' : '#E91E8C')) : '';
    head = (longHair ? hairSvg : '') + head + fringe + face(o.expr || 'neutral') + (longHair ? '' : hairSvg);
    if (o.glasses) head += `<g fill="none" stroke="${K}" stroke-width="5"><circle cx="118" cy="116" r="30"/><circle cx="182" cy="116" r="30"/><path d="M148,112 L152,112 M88,110 L66,100 M212,110 L234,100"/></g>`;
    // Stack: back arms behind torso for natural look when holding
    const inner = `<g class="char">${body}${head}${arms}</g>`;
    return svg('-40 -14 380 524', 380, 524, inner);
  }

  /* ---------------- Props ---------------- */
  const P = {};

  P.coin = (o = {}) => svg('0 0 120 120', 120, 120,
    `<circle cx="60" cy="60" r="52" ${st(C.gold)}/><circle cx="60" cy="60" r="38" fill="none" stroke="#C98A00" stroke-width="5"/>` +
    txt(60, 62, o.symbol || '₹', 52, '#8A5A00'));

  P.coins = (o = {}) => {
    let s = '';
    const n = o.count || 6;
    for (let i = 0; i < n; i++) s += `<ellipse cx="80" cy="${170 - i * 18}" rx="64" ry="20" ${st(C.gold, 5)}/>`;
    s += `<ellipse cx="80" cy="${170 - (n - 1) * 18}" rx="40" ry="11" fill="none" stroke="#C98A00" stroke-width="4"/>`;
    return svg('0 0 160 200', 160, 200, s);
  };

  P.note = (o = {}) => svg('0 0 250 130', 250, 130,
    `<rect x="6" y="6" width="238" height="118" rx="10" ${st(o.color || C.lightGreen)}/>` +
    `<rect x="20" y="20" width="210" height="90" rx="6" fill="none" stroke="#3E8E41" stroke-width="4"/>` +
    `<circle cx="125" cy="65" r="30" ${st('#A5D6A7', 5)}/>` + txt(125, 67, o.symbol || '₹', 38, '#1B5E20') +
    txt(42, 40, o.value || '500', 18, '#1B5E20') + txt(208, 92, o.value || '500', 18, '#1B5E20'));

  P.cash_stack = (o = {}) => {
    let s = '';
    const n = o.count || 5;
    for (let i = n - 1; i >= 0; i--) {
      const y = 40 + i * 16;
      s += `<path d="M20,${y + 40} L120,${y} L260,${y + 26} L160,${y + 70} Z" ${st(C.lightGreen, 5)}/>`;
    }
    s += `<path d="M78,63 L218,89" stroke="#3E8E41" stroke-width="4" fill="none"/>`;
    s += `<path d="M104,46 L132,52 L172,124 L144,118 Z" fill="#F3E5AB" stroke="${K}" stroke-width="4"/>`;
    s += `<ellipse cx="190" cy="76" rx="18" ry="10" fill="#A5D6A7" stroke="#2E7D32" stroke-width="3"/>`;
    return svg('0 0 280 ' + (130 + n * 16), 280, 130 + n * 16, s);
  };

  P.money_bag = (o = {}) => svg('0 0 200 220', 200, 220,
    `<path d="M70,62 Q20,120 30,170 Q40,212 100,212 Q160,212 170,170 Q180,120 130,62 Z" ${st(o.color || C.tan)}/>` +
    `<path d="M66,30 L80,62 L120,62 L134,30 Q100,46 66,30 Z" ${st(o.color || C.tan)}/>` +
    `<path d="M70,64 L130,64" stroke="${K}" stroke-width="10"/>` + txt(100, 150, o.symbol || '₹', 70, '#5B3A0E'));

  P.piggy_bank = (o = {}) => svg('0 0 300 220', 300, 220,
    `<path d="M70,174 L66,206 L96,206 L100,180 M190,180 L194,206 L224,206 L220,174" ${st(C.pink)}/>` +
    `<ellipse cx="150" cy="120" rx="118" ry="80" ${st(C.pink)}/>` +
    `<path d="M88,62 L82,24 L120,48 Z" ${st(C.pink)}/>` +
    `<ellipse cx="262" cy="124" rx="24" ry="30" ${st('#F48FB1')}/>` +
    `<circle cx="256" cy="116" r="4" fill="${K}"/><circle cx="268" cy="132" r="4" fill="${K}"/>` +
    `<circle cx="212" cy="92" r="7" fill="${K}"/>` +
    `<path d="M126,50 L176,50" stroke="${K}" stroke-width="9"/>` +
    `<path d="M32,116 q-28,-8 -16,-28 q10,-10 18,6" fill="none" stroke="${K}" stroke-width="5"/>` +
    (o.label ? `<rect x="96" y="96" width="104" height="56" rx="6" ${st('#fff', 4)}/>` + txt(148, 124, o.label, 18) : ''));

  P.bank = (o = {}) => svg('0 0 340 300', 340, 300,
    `<path d="M20,96 L170,20 L320,96 Z" ${st('#E8D9B5')}/>` +
    `<rect x="34" y="96" width="272" height="34" ${st('#E8D9B5')}/>` + txt(170, 114, o.label || 'BANK', 30) +
    [64, 124, 186, 246].map(x => `<rect x="${x}" y="130" width="30" height="120" ${st('#F4EBD3', 5)}/>`).join('') +
    `<rect x="24" y="250" width="292" height="22" ${st('#D8C7A0', 5)}/><rect x="10" y="272" width="320" height="20" ${st('#CBB994', 5)}/>`);

  P.credit_card = (o = {}) => svg('0 0 300 190', 300, 190,
    `<rect x="6" y="6" width="288" height="178" rx="18" ${st(o.color || C.blue)}/>` +
    `<rect x="30" y="56" width="50" height="38" rx="6" ${st('#F5C542', 4)}/>` +
    `<path d="M30,75 L80,75 M55,56 L55,94" stroke="${K}" stroke-width="3"/>` +
    txt(150, 128, o.number || '•••• •••• •••• 4821', 22, '#fff') +
    txt(206, 36, o.label || 'CREDIT CARD', 20, '#fff') +
    `<circle cx="236" cy="160" r="14" fill="#E53935" opacity=".9"/><circle cx="256" cy="160" r="14" fill="#F5B800" opacity=".9"/>`);

  P.phone = (o = {}) => {
    const rows = o.rows || [];
    let s = `<rect x="6" y="6" width="228" height="428" rx="30" ${st('#222')}/>` +
      `<rect x="20" y="40" width="200" height="350" rx="8" fill="#fff" stroke="${K}" stroke-width="3"/>` +
      `<rect x="90" y="404" width="60" height="10" rx="5" fill="#555"/>`;
    if (o.header) s += `<rect x="20" y="40" width="200" height="46" fill="${o.headerColor || C.blue}"/>` + txt(120, 64, o.header, 24, '#fff');
    let y = o.header ? 120 : 80;
    const fit = (str, max) => Math.min(max, Math.floor(330 / Math.max(1, String(str).length)));
    if (o.title) { s += txt(120, y, o.title, fit(o.title, 28)); y += 46; }
    if (o.big) { s += txt(120, y + 10, o.big, Math.min(46, Math.floor(300 / String(o.big).length)), o.bigColor || K); y += 70; }
    for (const r of rows) {
      const fs = Math.min(19, Math.floor(300 / (String(r[0]).length + String(r[1]).length + 2)));
      s += `<text x="34" y="${y}" font-family="Mali" font-weight="700" font-size="${fs}" fill="${K}" dominant-baseline="central">${esc(r[0])}</text>`;
      s += `<text x="206" y="${y}" font-family="Mali" font-weight="700" font-size="${fs}" fill="${r[2] || K}" text-anchor="end" dominant-baseline="central">${esc(r[1])}</text>`;
      y += 38;
    }
    return svg('0 0 240 440', 240, 440, s);
  };

  P.calculator = (o = {}) => {
    let s = `<rect x="6" y="6" width="188" height="268" rx="18" ${st(C.darkGrey)}/>` +
      `<rect x="24" y="24" width="152" height="56" rx="6" ${st('#C6F6D5', 4)}/>` +
      `<text x="166" y="54" font-family="Mali" font-weight="700" font-size="30" text-anchor="end" dominant-baseline="central" fill="${K}">${esc(o.display || '1,250')}</text>`;
    for (let r = 0; r < 4; r++) for (let c = 0; c < 4; c++)
      s += `<rect x="${24 + c * 39}" y="${98 + r * 42}" width="30" height="32" rx="6" ${st(c === 3 ? C.orange : '#E2E8F0', 3)}/>`;
    return svg('0 0 200 280', 200, 280, s);
  };

  P.chart_up = (o = {}) => svg('0 0 300 240', 300, 240,
    `<path d="M30,20 L30,214 L286,214" fill="none" stroke="${K}" stroke-width="7"/>` +
    [[56, 150], [110, 120], [164, 86], [218, 46]].map(([x, y]) => `<rect x="${x}" y="${y}" width="40" height="${214 - y}" ${st(o.color || C.green, 5)}/>`).join('') +
    `<path d="M50,140 L120,96 L170,110 L262,30" fill="none" stroke="${K}" stroke-width="16"/><path d="M50,140 L120,96 L170,110 L262,30" fill="none" stroke="${C.red}" stroke-width="8"/>` +
    `<path d="M236,24 L272,18 L266,54 Z" ${st(C.red, 4)}/>`);

  P.chart_down = (o = {}) => svg('0 0 300 240', 300, 240,
    `<path d="M30,20 L30,214 L286,214" fill="none" stroke="${K}" stroke-width="7"/>` +
    [[56, 46], [110, 86], [164, 120], [218, 160]].map(([x, y]) => `<rect x="${x}" y="${y}" width="40" height="${214 - y}" ${st(o.color || C.red, 5)}/>`).join('') +
    `<path d="M50,40 L120,90 L170,80 L262,170" fill="none" stroke="${K}" stroke-width="16"/><path d="M50,40 L120,90 L170,80 L262,170" fill="none" stroke="${C.darkGrey}" stroke-width="8"/>` +
    `<path d="M240,178 L274,184 L270,148 Z" ${st(C.darkGrey, 4)}/>`);

  P.house = (o = {}) => svg('0 0 260 240', 260, 240,
    `<rect x="186" y="34" width="30" height="60" ${st('#B85C38', 5)}/>` +
    `<rect x="40" y="110" width="180" height="120" ${st(o.color || '#F4E1C1')}/>` +
    `<path d="M14,118 L130,18 L246,118 Z" ${st(o.roof || '#D9534F')}/>` +
    `<rect x="110" y="160" width="44" height="70" ${st('#8D5524', 5)}/><circle cx="144" cy="196" r="4" fill="${K}"/>` +
    `<rect x="58" y="138" width="38" height="36" ${st('#9AD7F5', 5)}/><rect x="168" y="138" width="38" height="36" ${st('#9AD7F5', 5)}/>`);

  P.car = (o = {}) => svg('0 0 300 160', 300, 160,
    `<path d="M20,110 L24,76 L70,70 L104,30 L200,30 L236,70 L280,80 L282,110 Z" ${st(o.color || C.blue)}/>` +
    `<path d="M112,40 L148,40 L148,70 L84,70 Z M160,40 L194,40 L222,70 L160,70 Z" ${st('#9AD7F5', 4)}/>` +
    `<circle cx="80" cy="114" r="26" ${st('#333')}/><circle cx="80" cy="114" r="10" fill="#aaa"/>` +
    `<circle cx="222" cy="114" r="26" ${st('#333')}/><circle cx="222" cy="114" r="10" fill="#aaa"/>`);

  P.briefcase = (o = {}) => svg('0 0 260 200', 260, 200,
    `<path d="M92,50 L92,26 Q92,16 102,16 L158,16 Q168,16 168,26 L168,50" fill="none" stroke="${K}" stroke-width="10"/>` +
    `<rect x="10" y="48" width="240" height="144" rx="16" ${st(o.color || '#8B5A2B')}/>` +
    `<path d="M10,104 L250,104" stroke="${K}" stroke-width="5"/><rect x="112" y="92" width="36" height="26" rx="4" ${st(C.gold, 4)}/>`);

  P.calendar = (o = {}) => {
    let s = `<rect x="10" y="26" width="220" height="200" rx="12" ${st('#fff')}/>` +
      `<path d="M10,38 Q10,26 22,26 L218,26 Q230,26 230,38 L230,76 L10,76 Z" ${st(C.red)}/>` +
      txt(120, 52, o.label || 'DUE DATE', Math.min(24, Math.floor(330 / String(o.label || 'DUE DATE').length)), '#fff') +
      `<path d="M60,12 L60,40 M180,12 L180,40" stroke="${K}" stroke-width="10"/>`;
    if (o.day) s += txt(120, 152, o.day, 80);
    else for (let r = 0; r < 3; r++) for (let c = 0; c < 4; c++) s += `<rect x="${30 + c * 48}" y="${92 + r * 42}" width="34" height="30" rx="4" fill="${r === 1 && c === 2 ? C.red : '#EEE'}" stroke="${K}" stroke-width="3"/>`;
    return svg('0 0 240 236', 240, 236, s);
  };

  P.clock = (o = {}) => {
    const h = ((o.hour ?? 10) % 12) * 30 + (o.minute ?? 10) * 0.5, m = (o.minute ?? 10) * 6;
    const hx = 120 + 50 * Math.sin(h * Math.PI / 180), hy = 120 - 50 * Math.cos(h * Math.PI / 180);
    const mx = 120 + 74 * Math.sin(m * Math.PI / 180), my = 120 - 74 * Math.cos(m * Math.PI / 180);
    let ticks = '';
    for (let i = 0; i < 12; i++) { const a = i * 30 * Math.PI / 180; ticks += `<path d="M${120 + 84 * Math.sin(a)},${120 - 84 * Math.cos(a)} L${120 + 96 * Math.sin(a)},${120 - 96 * Math.cos(a)}" stroke="${K}" stroke-width="5"/>`; }
    return svg('0 0 240 240', 240, 240, `<circle cx="120" cy="120" r="110" ${st(o.color || C.gold)}/><circle cx="120" cy="120" r="96" ${st('#fff', 5)}/>${ticks}` +
      `<path d="M120,120 L${hx},${hy}" stroke="${K}" stroke-width="10"/><path d="M120,120 L${mx},${my}" stroke="${K}" stroke-width="7"/><circle cx="120" cy="120" r="9" fill="${K}"/>`);
  };

  P.hourglass = () => svg('0 0 180 260', 180, 260,
    `<rect x="14" y="10" width="152" height="24" rx="6" ${st('#8D5524')}/><rect x="14" y="226" width="152" height="24" rx="6" ${st('#8D5524')}/>` +
    `<path d="M36,34 L144,34 Q144,100 96,130 Q144,160 144,226 L36,226 Q36,160 84,130 Q36,100 36,34 Z" ${st('#E3F2FD')}/>` +
    `<path d="M60,70 L120,70 Q112,100 90,118 Q68,100 60,70 Z" fill="${C.gold}"/><path d="M50,224 Q90,170 130,224 Z" fill="${C.gold}"/><path d="M90,124 L90,200" stroke="${C.gold}" stroke-width="5"/>`);

  P.plant = (o = {}) => {
    const g = o.size || 1;
    let leaves = `<path d="M100,150 L100,${150 - 60 * g}" stroke="${K}" stroke-width="7"/>`;
    leaves += `<path d="M100,${120 - 20 * g} Q56,${100 - 30 * g} 50,${126 - 20 * g} Q78,${142 - 20 * g} 100,${120 - 20 * g} Z" ${st(C.green, 5)}/>`;
    leaves += `<path d="M100,${104 - 30 * g} Q146,${80 - 40 * g} 152,${110 - 30 * g} Q124,${126 - 30 * g} 100,${104 - 30 * g} Z" ${st(C.green, 5)}/>`;
    return svg('0 0 200 260', 200, 260, leaves +
      `<rect x="44" y="146" width="112" height="26" rx="4" ${st('#C8643B')}/><path d="M54,172 L66,250 L134,250 L146,172 Z" ${st('#D9774B')}/>`);
  };

  P.money_tree = () => {
    let s = `<path d="M130,330 L122,200 Q100,170 70,160 M126,220 Q150,170 190,160" fill="none" stroke="${K}" stroke-width="30"/>` +
      `<path d="M130,330 L122,200 Q100,170 70,160 M126,220 Q150,170 190,160" fill="none" stroke="#8D5524" stroke-width="18"/>`;
    for (const [x, y, r] of [[80, 110, 70], [170, 100, 74], [128, 60, 70], [60, 170, 46], [196, 168, 48]])
      s += `<circle cx="${x}" cy="${y}" r="${r}" ${st(C.green)}/>`;
    for (const [x, y] of [[90, 90], [160, 70], [130, 130], [196, 140], [60, 150], [120, 40]])
      s += `<circle cx="${x}" cy="${y}" r="17" ${st(C.gold, 4)}/>` + txt(x, y + 1, '₹', 18, '#8A5A00');
    s += `<path d="M60,330 L200,330" stroke="${K}" stroke-width="8"/>`;
    return svg('0 0 260 340', 260, 340, s);
  };

  P.fire = () => svg('0 0 200 240', 200, 240,
    `<path d="M100,10 Q130,70 160,80 Q190,140 170,190 Q150,236 100,236 Q50,236 30,190 Q10,140 50,90 Q60,130 80,120 Q70,60 100,10 Z" ${st(C.orange)}/>` +
    `<path d="M100,90 Q120,140 140,150 Q150,200 100,214 Q56,206 62,170 Q70,150 84,160 Q84,120 100,90 Z" fill="${C.gold}" stroke="${K}" stroke-width="4"/>`);

  P.lightbulb = () => svg('0 0 220 280', 220, 280,
    [[110, 4, 110, 30], [30, 40, 50, 58], [190, 40, 170, 58], [4, 120, 30, 120], [216, 120, 190, 120]].map(([a, b, c, d]) => `<path d="M${a},${b} L${c},${d}" stroke="${K}" stroke-width="7"/>`).join('') +
    `<path d="M110,44 Q178,44 178,118 Q178,150 150,178 L146,204 L74,204 L70,178 Q42,150 42,118 Q42,44 110,44 Z" ${st('#FFE066')}/>` +
    `<path d="M92,170 L100,120 L110,140 L120,120 L128,170" fill="none" stroke="${K}" stroke-width="4"/>` +
    `<rect x="72" y="204" width="76" height="22" rx="4" ${st('#B0B8C1', 5)}/><rect x="78" y="226" width="64" height="20" rx="4" ${st('#B0B8C1', 5)}/><path d="M92,246 L128,246 L118,262 L102,262 Z" ${st('#555', 4)}/>`);

  P.scale = (o = {}) => {
    const tilt = o.tilt || 0; // -1 left heavy, 1 right heavy
    const ly = 90 + tilt * -24, ry = 90 + tilt * 24;
    return svg('0 0 320 280', 320, 280,
      `<path d="M160,40 L160,250 M110,256 L210,256" stroke="${K}" stroke-width="12"/>` +
      `<path d="M50,${ly} L270,${ry}" stroke="${K}" stroke-width="10"/><circle cx="160" cy="40" r="14" ${st(C.gold, 5)}/>` +
      `<path d="M50,${ly} L20,${ly + 80} M50,${ly} L80,${ly + 80} M270,${ry} L240,${ry + 80} M270,${ry} L300,${ry + 80}" stroke="${K}" stroke-width="4"/>` +
      `<path d="M10,${ly + 80} L90,${ly + 80} Q50,${ly + 116} 10,${ly + 80} Z" ${st(C.gold, 5)}/><path d="M230,${ry + 80} L310,${ry + 80} Q270,${ry + 116} 230,${ry + 80} Z" ${st(C.gold, 5)}/>` +
      (o.left ? txt(50, ly + 140, o.left, 24) : '') + (o.right ? txt(270, ry + 140, o.right, 24) : ''));
  };

  P.shield = (o = {}) => svg('0 0 220 260', 220, 260,
    `<path d="M110,10 L200,44 Q204,170 110,250 Q16,170 20,44 Z" ${st(o.color || C.blue)}/>` +
    `<path d="M66,128 L100,162 L160,96" fill="none" stroke="#fff" stroke-width="18"/>`);

  P.vault = () => {
    let s = `<rect x="10" y="10" width="300" height="300" rx="16" ${st('#B0B8C1')}/><circle cx="160" cy="160" r="118" ${st('#CFD6DD')}/>` +
      `<circle cx="160" cy="160" r="40" ${st('#8A94A0')}/>`;
    for (let i = 0; i < 6; i++) { const a = i * Math.PI / 3; s += `<path d="M${160 + 40 * Math.cos(a)},${160 + 40 * Math.sin(a)} L${160 + 86 * Math.cos(a)},${160 + 86 * Math.sin(a)}" stroke="${K}" stroke-width="10"/>`; }
    for (const [x, y] of [[40, 40], [280, 40], [40, 280], [280, 280]]) s += `<circle cx="${x}" cy="${y}" r="8" fill="#555"/>`;
    return svg('0 0 320 320', 320, 320, s);
  };

  P.document = (o = {}) => {
    let s = `<path d="M10,10 L170,10 L220,60 L220,290 L10,290 Z" ${st('#fff')}/><path d="M170,10 L170,60 L220,60" ${st('#E0E0E0', 5)}/>`;
    s += txt(100, 48, o.title || 'REPORT', Math.min(26, Math.floor(250 / String(o.title || 'REPORT').length)));
    const rows = o.rows || null;
    if (rows) rows.slice(0, 6).forEach((r, i) => {
      s += `<text x="26" y="${100 + i * 32}" font-family="Mali" font-weight="700" font-size="17" dominant-baseline="central">${esc(r[0])}</text>` +
        `<text x="204" y="${100 + i * 32}" font-family="Mali" font-weight="700" font-size="17" text-anchor="end" fill="${r[2] || K}" dominant-baseline="central">${esc(r[1])}</text>`;
    });
    else for (let i = 0; i < 6; i++) s += `<path d="M30,${96 + i * 30} L${i % 2 ? 160 : 196},${96 + i * 30}" stroke="#9E9E9E" stroke-width="6"/>`;
    if (o.stamp) { const sw2 = Math.max(110, String(o.stamp).length * 15 + 24); s += `<g transform="rotate(-14 150 250)"><rect x="${151 - sw2 / 2}" y="226" width="${sw2}" height="44" rx="6" fill="#fff" fill-opacity=".6" stroke="${o.stampColor || C.red}" stroke-width="5"/>` + txt(151, 249, o.stamp, 22, o.stampColor || C.red) + '</g>'; }
    return svg('0 0 230 300', 230, 300, s);
  };

  P.receipt = (o = {}) => {
    const rows = o.rows || [['Item', '₹0']];
    const h = 120 + rows.length * 34;
    let d = `M10,10 L230,10 L230,${h}`;
    for (let x = 230, i = 0; x > 10; x -= 20, i++) d += ` L${x - 10},${h - 12} L${x - 20},${h}`;
    let s = `<path d="${d} Z" ${st('#fff')}/>`;
    s += txt(120, 44, o.title || 'SALARY SLIP', 24) + `<path d="M26,70 L214,70" stroke="${K}" stroke-width="3" stroke-dasharray="8 6"/>`;
    rows.forEach((r, i) => {
      s += `<text x="26" y="${96 + i * 34}" font-family="Mali" font-weight="700" font-size="18" dominant-baseline="central">${esc(r[0])}</text>` +
        `<text x="214" y="${96 + i * 34}" font-family="Mali" font-weight="700" font-size="18" text-anchor="end" fill="${r[2] || K}" dominant-baseline="central">${esc(r[1])}</text>`;
    });
    return svg(`0 0 240 ${h + 6}`, 240, h + 6, s);
  };

  P.arrow_up = (o = {}) => svg('0 0 160 220', 160, 220, `<path d="M80,10 L150,96 L106,96 L106,210 L54,210 L54,96 L10,96 Z" ${st(o.color || C.green)}/>`);
  P.arrow_down = (o = {}) => svg('0 0 160 220', 160, 220, `<path d="M80,210 L150,124 L106,124 L106,10 L54,10 L54,124 L10,124 Z" ${st(o.color || C.red)}/>`);
  P.arrow_right = (o = {}) => svg('0 0 220 160', 220, 160, `<path d="M210,80 L124,150 L124,106 L10,106 L10,54 L124,54 L124,10 Z" ${st(o.color || C.blue)}/>`);
  P.check = () => svg('0 0 160 160', 160, 160, `<circle cx="80" cy="80" r="70" ${st(C.green)}/><path d="M44,82 L70,108 L118,56" fill="none" stroke="#fff" stroke-width="16"/>`);
  P.cross = () => svg('0 0 160 160', 160, 160, `<circle cx="80" cy="80" r="70" ${st(C.red)}/><path d="M52,52 L108,108 M108,52 L52,108" stroke="#fff" stroke-width="16"/>`);
  P.question = () => svg('0 0 120 180', 120, 180, txt(60, 80, '?', 170, K, `stroke="${K}" stroke-width="2" font-family="Luckiest Guy"`));
  P.exclamation = () => svg('0 0 80 180', 80, 180, txt(40, 80, '!', 170, C.red, `stroke="${K}" stroke-width="4" font-family="Luckiest Guy"`));
  P.rupee = (o = {}) => svg('0 0 200 200', 200, 200, `<circle cx="100" cy="100" r="90" ${st(o.color || C.gold)}/>` + txt(100, 106, '₹', 120, '#5B3A0E'));
  P.percent = (o = {}) => svg('0 0 200 200', 200, 200, `<circle cx="100" cy="100" r="90" ${st(o.color || C.blue)}/>` + txt(100, 106, '%', 110, '#fff', `stroke="${K}" stroke-width="3"`));

  P.office = (o = {}) => {
    let s = `<rect x="30" y="20" width="200" height="330" ${st(o.color || '#90A4AE')}/>`;
    for (let r = 0; r < 7; r++) for (let c = 0; c < 4; c++) s += `<rect x="${50 + c * 45}" y="${40 + r * 40}" width="28" height="26" ${st('#BBDEFB', 4)}/>`;
    s += `<rect x="108" y="306" width="44" height="44" ${st('#5D4037', 4)}/>`;
    if (o.label) { const lw = Math.max(140, String(o.label).length * 15 + 24); s += `<rect x="${130 - lw / 2}" y="-6" width="${lw}" height="40" rx="6" ${st('#fff', 4)}/>` + txt(130, 14, o.label, 22); }
    return svg('-60 -10 380 370', 380, 370, s);
  };

  P.factory = () => svg('0 0 320 240', 320, 240,
    `<rect x="220" y="20" width="36" height="120" ${st('#A1887F')}/>` +
    `<path d="M10,230 L10,110 L80,150 L80,110 L150,150 L150,110 L220,150 L220,100 L310,100 L310,230 Z" ${st('#B0BEC5')}/>` +
    [40, 110, 180, 250].map(x => `<rect x="${x}" y="176" width="34" height="30" ${st('#FFE082', 4)}/>`).join('') +
    `<circle cx="250" cy="8" r="14" fill="#CFD8DC" stroke="${K}" stroke-width="4"/><circle cx="276" cy="-6" r="10" fill="#CFD8DC" stroke="${K}" stroke-width="4"/>`);

  P.cart = () => svg('0 0 260 220', 260, 220,
    `<path d="M10,30 L50,30 L80,150 L220,150" fill="none" stroke="${K}" stroke-width="10"/>` +
    `<path d="M56,54 L240,54 L218,128 L76,128 Z" ${st('#E0E0E0')}/><path d="M100,54 L108,128 M150,54 L150,128 M200,54 L190,128" stroke="${K}" stroke-width="4"/>` +
    `<circle cx="96" cy="184" r="18" ${st('#555')}/><circle cx="200" cy="184" r="18" ${st('#555')}/>`);

  P.grad_cap = () => svg('0 0 300 200', 300, 200,
    `<path d="M70,90 L70,150 Q150,190 230,150 L230,90 Z" ${st('#333')}/><path d="M10,70 L150,10 L290,70 L150,130 Z" ${st('#333')}/>` +
    `<path d="M150,70 L250,96 L250,160" fill="none" stroke="${C.gold}" stroke-width="7"/><circle cx="250" cy="166" r="12" fill="${C.gold}" stroke="${K}" stroke-width="4"/>`);

  P.target = () => svg('0 0 240 240', 240, 240,
    `<circle cx="110" cy="130" r="100" ${st(C.red)}/><circle cx="110" cy="130" r="70" ${st('#fff')}/><circle cx="110" cy="130" r="40" ${st(C.red)}/><circle cx="110" cy="130" r="12" ${st('#fff', 4)}/>` +
    `<path d="M110,130 L220,20" stroke="${K}" stroke-width="9"/><path d="M200,14 L232,8 L226,40 Z" ${st(C.gold, 4)}/>`);

  P.rocket = () => svg('0 0 200 300', 200, 300,
    `<path d="M70,230 Q100,300 130,230 Z" ${st(C.orange, 5)}/>` +
    `<path d="M100,10 Q160,70 150,220 L50,220 Q40,70 100,10 Z" ${st('#ECEFF1')}/>` +
    `<path d="M50,160 L14,230 L52,220 Z M150,160 L186,230 L148,220 Z" ${st(C.red, 5)}/>` +
    `<circle cx="100" cy="104" r="26" ${st('#81D4FA', 5)}/>`);

  P.umbrella = (o = {}) => svg('0 0 280 280', 280, 280,
    `<path d="M140,130 L140,240 Q140,268 114,262" fill="none" stroke="${K}" stroke-width="9"/>` +
    `<path d="M10,130 Q20,20 140,16 Q260,20 270,130 Q245,110 205,130 Q175,110 140,130 Q105,110 75,130 Q35,110 10,130 Z" ${st(o.color || C.blue)}/>`);

  P.gold_bars = () => svg('0 0 300 200', 300, 200,
    [[20, 120], [150, 120], [85, 50]].map(([x, y]) => `<path d="M${x + 20},${y} L${x + 110},${y} L${x + 130},${y + 70} L${x},${y + 70} Z" ${st(C.gold)}/><path d="M${x + 30},${y + 14} L${x + 100},${y + 14}" stroke="#FFF59D" stroke-width="6"/>`).join(''));

  P.magnifier = () => svg('0 0 240 240', 240, 240,
    `<path d="M150,150 L224,224" stroke="${K}" stroke-width="30"/><path d="M150,150 L220,220" stroke="#8D5524" stroke-width="18"/>` +
    `<circle cx="96" cy="96" r="80" ${st('#B3E5FC')}/><path d="M56,70 Q70,44 100,40" fill="none" stroke="#fff" stroke-width="10"/>`);

  P.gear = (o = {}) => {
    let d = '';
    for (let i = 0; i < 8; i++) {
      const a = i * Math.PI / 4;
      const p = (r, da) => `${100 + r * Math.cos(a + da)},${100 + r * Math.sin(a + da)}`;
      d += `${i ? 'L' : 'M'}${p(70, -0.22)} L${p(92, -0.14)} L${p(92, 0.14)} L${p(70, 0.22)} `;
    }
    return svg('0 0 200 200', 200, 200, `<path d="${d}Z" ${st(o.color || C.grey)}/><circle cx="100" cy="100" r="28" ${st('#fff', 5)}/>`);
  };

  P.hand = (o = {}) => svg('0 0 300 160', 300, 160,
    `<path d="M0,40 L110,40 L110,120 L0,120 Z" ${st(o.sleeve || '#222')}/>` +
    `<path d="M108,46 Q150,30 190,40 L262,44 Q282,48 276,64 Q270,74 230,72 L240,80 Q262,84 258,100 Q252,112 230,108 Q246,116 238,130 Q228,138 210,132 Q200,146 176,140 L130,128 Q110,124 108,116 Z" ${st('#fff', 5)}/>`);

  P.lock = (o = {}) => svg('0 0 200 240', 200, 240,
    `<path d="M50,110 L50,70 Q50,16 100,16 Q150,16 150,70 L150,110" fill="none" stroke="${K}" stroke-width="22"/><path d="M50,110 L50,70 Q50,16 100,16 Q150,16 150,70 L150,110" fill="none" stroke="${C.grey}" stroke-width="10"/>` +
    `<rect x="20" y="104" width="160" height="126" rx="16" ${st(o.color || C.gold)}/><circle cx="100" cy="156" r="16" fill="${K}"/><path d="M100,160 L100,196" stroke="${K}" stroke-width="12"/>`);

  P.chain_ball = () => svg('0 0 300 200', 300, 200,
    `<circle cx="220" cy="120" r="70" ${st('#424242')}/>` + txt(220, 124, 'DEBT', 30, '#fff') +
    [30, 70, 110].map(x => `<ellipse cx="${x}" cy="110" rx="22" ry="13" fill="none" stroke="${K}" stroke-width="9"/>`).join(''));

  P.stock_screen = (o = {}) => {
    const up = o.trend !== 'down';
    const pts = up ? '30,190 80,160 120,170 170,120 210,130 260,70 300,80 340,40' : '30,50 80,80 120,70 170,120 210,110 260,160 300,150 340,190';
    return svg('0 0 380 260', 380, 260,
      `<rect x="6" y="6" width="368" height="230" rx="14" ${st('#1E2A3A')}/>` +
      `<polyline points="${pts}" fill="none" stroke="${up ? '#4CAF50' : '#F44336'}" stroke-width="9"/>` +
      `<rect x="160" y="236" width="60" height="20" ${st('#555', 4)}/>` +
      (o.label ? txt(80, 32, o.label, 22, '#fff') : ''));
  };

  P.thought_money = () => svg('0 0 260 200', 260, 200,
    `<path d="M60,150 Q10,150 20,110 Q0,70 50,60 Q60,16 110,30 Q150,0 190,34 Q250,30 240,90 Q262,130 220,150 Q200,180 150,160 Q110,180 60,150 Z" ${st('#fff')}/>` +
    `<circle cx="70" cy="178" r="10" ${st('#fff', 4)}/><circle cx="50" cy="196" r="5" ${st('#fff', 3)}/>` +
    `<rect x="80" y="70" width="110" height="56" rx="6" ${st(C.lightGreen, 5)}/>` + txt(135, 99, '₹', 34, '#1B5E20'));

  P.protein_bar = (o = {}) => svg('0 0 320 130', 320, 130,
    `<path d="M14,22 L30,10 L30,120 L14,108 Z M306,22 L290,10 L290,120 L306,108 Z" ${st('#B0BEC5', 5)}/>` +
    `<rect x="30" y="10" width="260" height="110" rx="10" ${st(o.color || '#6D4C41')}/>` +
    `<rect x="62" y="34" width="196" height="62" rx="8" ${st('#FFE082', 4)}/>` + txt(160, 66, o.label || 'PROTEIN', 30));

  P.chips_bag = (o = {}) => svg('0 0 220 290', 220, 290,
    `<path d="M24,30 L40,14 L56,30 L72,14 L88,30 L104,14 L120,30 L136,14 L152,30 L168,14 L184,30 L196,18 ` +
    `Q214,150 196,270 L180,278 L164,270 L148,278 L132,270 L116,278 L100,270 L84,278 L68,270 L52,278 L36,270 L24,278 Q6,150 24,30 Z" ${st(o.color || '#43A047')}/>` +
    `<ellipse cx="110" cy="150" rx="70" ry="54" ${st('#FFF59D', 5)}/>` + txt(110, 140, o.label || 'CHIPS', 34) + txt(110, 172, o.sub || 'HEALTHY', 18, '#2E7D32') +
    `<ellipse cx="80" cy="232" rx="20" ry="14" fill="${C.gold}" stroke="${K}" stroke-width="4"/><ellipse cx="140" cy="236" rx="18" ry="12" fill="${C.gold}" stroke="${K}" stroke-width="4"/>`);

  P.heart = (o = {}) => svg('0 0 200 180', 200, 180,
    `<path d="M100,170 Q20,110 14,62 Q10,14 56,12 Q86,12 100,44 Q114,12 144,12 Q190,14 186,62 Q180,110 100,170 Z" ${st(o.color || C.red)}/>` +
    `<path d="M44,50 Q50,32 68,30" fill="none" stroke="#fff" stroke-width="8"/>`);

  P.seesaw = (o = {}) => {
    // tilt: -1 = left side down, +1 = right side down
    const a = (o.tilt ?? 0.6) * 14;
    const cx = 300, cy = 190, L = 270;
    let s = `<path d="M${cx},${cy + 8} L${cx - 60},300 L${cx + 60},300 Z" ${st(C.grey)}/>`;
    s += `<g transform="rotate(${a} ${cx} ${cy})"><rect x="${cx - L}" y="${cy - 12}" width="${2 * L}" height="24" rx="8" ${st('#B07A3F')}/>` +
      `<rect x="${cx - L + 10}" y="${cy - 92}" width="120" height="80" rx="10" ${st(o.leftColor || C.blue)}/>` + txt(cx - L + 70, cy - 52, o.left || 'YIELD', 26, '#fff') +
      `<rect x="${cx + L - 130}" y="${cy - 92}" width="120" height="80" rx="10" ${st(o.rightColor || C.green)}/>` + txt(cx + L - 70, cy - 52, o.right || 'PRICE', 26, '#fff') + '</g>';
    s += `<circle cx="${cx}" cy="${cy}" r="12" ${st(C.gold, 5)}/>`;
    return svg('0 -20 600 330', 600, 330, s);
  };

  P.flag = (o = {}) => {
    let s = `<path d="M20,10 L20,290" stroke="${K}" stroke-width="10"/>`;
    if (o.country === 'us') {
      for (let i = 0; i < 7; i++) s += `<rect x="26" y="${20 + i * 22}" width="230" height="22" fill="${i % 2 ? '#fff' : '#D62828'}"/>`;
      s += `<rect x="26" y="20" width="100" height="88" fill="#1D3A8A"/>`;
      for (let r = 0; r < 4; r++) for (let c = 0; c < 4; c++) s += `<circle cx="${40 + c * 24}" cy="${32 + r * 21}" r="4" fill="#fff"/>`;
    } else {
      s += `<rect x="26" y="20" width="230" height="51" fill="#FF9933"/><rect x="26" y="71" width="230" height="52" fill="#fff"/><rect x="26" y="123" width="230" height="51" fill="#138808"/>`;
      s += `<circle cx="141" cy="97" r="20" fill="none" stroke="#1D3A8A" stroke-width="4"/><circle cx="141" cy="97" r="4" fill="#1D3A8A"/>`;
      for (let i = 0; i < 12; i++) { const an = i * Math.PI / 6; s += `<path d="M141,97 L${141 + 20 * Math.cos(an)},${97 + 20 * Math.sin(an)}" stroke="#1D3A8A" stroke-width="2"/>`; }
    }
    s += `<rect x="26" y="20" width="230" height="154" fill="none" stroke="${K}" stroke-width="6"/>`;
    return svg('0 0 270 300', 270, 300, s);
  };

  P.bond = (o = {}) => svg('0 0 340 230', 340, 230,
    `<rect x="8" y="8" width="324" height="214" rx="10" ${st('#FFF8E1')}/><rect x="24" y="24" width="292" height="182" rx="6" fill="none" stroke="#B8860B" stroke-width="5" stroke-dasharray="14 6"/>` +
    txt(170, 62, o.title || 'GOVT BOND', 30) + txt(170, 110, o.value || '₹1,000', 46, '#1B5E20') + txt(170, 160, o.sub || '7% · 10 YEARS', 24, '#555') +
    `<circle cx="280" cy="180" r="22" ${st(C.red, 4)}/>`);

  P.chat = (o = {}) => {
    // group-chat phone: o.title, o.msgs = [[sender, text], ...]
    const msgs = o.msgs || [['Friend', 'Hi!']];
    let s = `<rect x="6" y="6" width="288" height="528" rx="34" ${st('#222')}/>` +
      `<rect x="20" y="40" width="260" height="450" rx="8" fill="#ECE5DD" stroke="${K}" stroke-width="3"/>` +
      `<rect x="20" y="40" width="260" height="56" fill="#128C7E"/>` + txt(150, 68, o.title || 'IPO GROUP', 22, '#fff') +
      `<rect x="120" y="506" width="60" height="10" rx="5" fill="#555"/>`;
    let y = 112;
    msgs.slice(0, 4).forEach(([who, text], i) => {
      const words = String(text).split(' '), lines = [];
      let cur = '';
      for (const wd of words) { if ((cur + ' ' + wd).trim().length > 20) { lines.push(cur.trim()); cur = wd; } else cur += ' ' + wd; }
      if (cur.trim()) lines.push(cur.trim());
      const h = 30 + lines.length * 22;
      s += `<rect x="32" y="${y}" width="236" height="${h}" rx="10" fill="${i % 2 ? '#DCF8C6' : '#fff'}" stroke="${K}" stroke-width="2"/>`;
      s += `<text x="44" y="${y + 18}" font-family="Mali" font-weight="700" font-size="14" fill="#128C7E">${esc(who)}</text>`;
      lines.forEach((ln, k) => { s += `<text x="44" y="${y + 40 + k * 22}" font-family="Mali" font-weight="700" font-size="17" fill="${K}">${esc(ln)}</text>`; });
      y += h + 10;
    });
    return svg('0 0 300 540', 300, 540, s);
  };

  P.anchor = (o = {}) => svg('0 0 240 280', 240, 280,
    `<circle cx="120" cy="40" r="24" fill="none" stroke="${K}" stroke-width="20"/><circle cx="120" cy="40" r="24" fill="none" stroke="${o.color || C.grey}" stroke-width="9"/>` +
    `<path d="M120,64 L120,250 M70,110 L170,110 M30,170 Q40,250 120,250 Q200,250 210,170" fill="none" stroke="${K}" stroke-width="30"/>` +
    `<path d="M120,64 L120,250 M70,110 L170,110 M30,170 Q40,250 120,250 Q200,250 210,170" fill="none" stroke="${o.color || C.grey}" stroke-width="16"/>` +
    `<path d="M14,186 L30,150 L50,184 Z M226,186 L210,150 L190,184 Z" ${st(o.color || C.grey, 5)}/>`);

  P.ms_logo = (o = {}) => svg('0 0 240 240', 240, 240,
    `<rect x="10" y="10" width="105" height="105" fill="#F25022"/><rect x="125" y="10" width="105" height="105" fill="#7FBA00"/>` +
    `<rect x="10" y="125" width="105" height="105" fill="#00A4EF"/><rect x="125" y="125" width="105" height="105" fill="#FFB900"/>` +
    (o.text ? txt(120, 270, o.text, 34) : ''));

  P.robot = (o = {}) => svg('0 0 260 320', 260, 320,
    `<path d="M130,10 L130,44" stroke="${K}" stroke-width="8"/><circle cx="130" cy="12" r="12" ${st(C.red, 5)}/>` +
    `<rect x="40" y="44" width="180" height="130" rx="30" ${st(o.color || '#B0BEC5')}/>` +
    `<circle cx="94" cy="104" r="24" ${st('#81D4FA', 5)}/><circle cx="166" cy="104" r="24" ${st('#81D4FA', 5)}/>` +
    `<circle cx="94" cy="104" r="8" fill="${K}"/><circle cx="166" cy="104" r="8" fill="${K}"/>` +
    `<rect x="96" y="140" width="68" height="16" rx="6" ${st('#fff', 4)}/>` + txt(130, 149, 'AI', 14) +
    `<rect x="60" y="180" width="140" height="120" rx="20" ${st(o.color || '#B0BEC5')}/>` +
    `<rect x="98" y="206" width="64" height="44" rx="8" ${st('#FFE082', 4)}/>` +
    `<path d="M60,200 L14,250 M200,200 L246,250" stroke="${K}" stroke-width="16"/><path d="M60,200 L14,250 M200,200 L246,250" stroke="${o.color || '#B0BEC5'}" stroke-width="8"/>`);

  P.laptop = (o = {}) => {
    let s = `<rect x="40" y="10" width="300" height="200" rx="14" ${st('#263238')}/><rect x="56" y="26" width="268" height="168" fill="#1E1E1E"/>`;
    const lines = o.lines || ['def model():', '  rev = 1.2*x', '  return rev', 'print(model())'];
    const cols = ['#82AAFF', '#C3E88D', '#F78C6C', '#FFCB6B'];
    lines.slice(0, 6).forEach((l, i) => { s += `<text x="70" y="${56 + i * 28}" font-family="monospace" font-weight="700" font-size="20" fill="${cols[i % 4]}">${esc(l)}</text>`; });
    s += `<path d="M10,214 L370,214 L346,244 L34,244 Z" ${st('#90A4AE')}/>`;
    if (o.label) s += txt(190, 278, o.label, 30);
    return svg('0 0 380 290', 380, 290, s);
  };

  P.slides = (o = {}) => svg('0 0 320 260', 320, 260,
    `<path d="M160,200 L160,250 M110,250 L210,250" stroke="${K}" stroke-width="8"/>` +
    `<rect x="10" y="10" width="300" height="190" rx="8" ${st('#fff')}/><rect x="10" y="10" width="300" height="40" fill="${o.color || C.blue}" stroke="${K}" stroke-width="6"/>` +
    txt(160, 31, o.title || 'Q3 REVIEW', 22, '#fff') +
    [[60, 150, 40], [110, 120, 70], [160, 100, 90], [210, 80, 110]].map(([x, y, h]) => `<rect x="${x}" y="${y}" width="34" height="${h}" fill="${C.green}" stroke="${K}" stroke-width="4"/>`).join('') +
    `<path d="M260,70 L290,70 M260,95 L290,95 M260,120 L284,120" stroke="#9E9E9E" stroke-width="6"/>`);

  P.spreadsheet = (o = {}) => {
    let s = `<rect x="6" y="6" width="348" height="248" rx="10" ${st('#fff')}/><rect x="6" y="6" width="348" height="36" fill="#1D6F42" stroke="${K}" stroke-width="6"/>` + txt(180, 25, o.title || 'MODEL.xlsx', 20, '#fff');
    for (let r = 0; r < 5; r++) for (let c = 0; c < 4; c++) s += `<rect x="${20 + c * 82}" y="${56 + r * 38}" width="82" height="38" fill="${r === 0 ? '#E8F5E9' : '#fff'}" stroke="#9E9E9E" stroke-width="2"/>`;
    const vals = o.rows || [['', 'FY24', 'FY25', 'FY26'], ['Rev', '120', '148', '182'], ['EBITDA', '24', '31', '40'], ['PAT', '12', '16', '21'], ['Margin', '10%', '11%', '12%']];
    vals.forEach((row, r) => row.forEach((v, c) => { s += txt(61 + c * 82, 76 + r * 38, v, 16); }));
    return svg('0 0 360 260', 360, 260, s);
  };

  /* ---------------- Backgrounds ---------------- */
  function background(bg, W = 1920, H = 1080) {
    const wrap = inner => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}">${inner}</svg>`;
    switch (bg) {
      case undefined: case null: case 'yellow': return wrap(`<rect width="${W}" height="${H}" fill="${C.yellow}"/>`);
      case 'cream': return wrap(`<rect width="${W}" height="${H}" fill="#F8E7B0"/>`);
      case 'white': return wrap(`<rect width="${W}" height="${H}" fill="#FFFDF5"/>`);
      case 'navy': return wrap(`<rect width="${W}" height="${H}" fill="#0F1B3D"/>` +
        `<path d="M0,${H * 0.62} Q${W * 0.25},${H * 0.55} ${W * 0.5},${H * 0.63} T${W},${H * 0.6} L${W},${H} L0,${H} Z" fill="#132350"/>` +
        `<path d="M0,${H * 0.8} Q${W * 0.3},${H * 0.72} ${W * 0.6},${H * 0.8} T${W},${H * 0.78} L${W},${H} L0,${H} Z" fill="#17295C"/>`);
      case 'room': return wrap(`<rect width="${W}" height="${H}" fill="#F6DFA0"/><rect y="${H * 0.78}" width="${W}" height="${H * 0.22}" fill="#8A5A24"/><path d="M0,${H * 0.78} L${W},${H * 0.78}" stroke="${K}" stroke-width="7"/>`);
      case 'desk': return wrap(`<rect width="${W}" height="${H}" fill="${C.yellow}"/><rect y="${H * 0.72}" width="${W}" height="${H * 0.28}" fill="#5A3A1A"/><path d="M0,${H * 0.72} L${W},${H * 0.72}" stroke="${K}" stroke-width="8"/>`);
      case 'office': return wrap(`<rect width="${W}" height="${H}" fill="#DCE6EE"/>` +
        `<rect x="${W * 0.62}" y="${H * 0.12}" width="${W * 0.28}" height="${H * 0.42}" fill="#9AD7F5" stroke="${K}" stroke-width="7"/><path d="M${W * 0.76},${H * 0.12} L${W * 0.76},${H * 0.54} M${W * 0.62},${H * 0.33} L${W * 0.9},${H * 0.33}" stroke="${K}" stroke-width="6"/>` +
        `<rect y="${H * 0.8}" width="${W}" height="${H * 0.2}" fill="#9E9E9E"/><path d="M0,${H * 0.8} L${W},${H * 0.8}" stroke="${K}" stroke-width="7"/>`);
      case 'street': {
        let b = `<rect width="${W}" height="${H}" fill="#8FD3F4"/>`;
        const blds = [[60, 420, '#F4B183'], [300, 300, '#A9D18E'], [520, 380, '#F8CBAD'], [1240, 340, '#9DC3E6'], [1480, 260, '#FFD966'], [1700, 400, '#C9C9C9']];
        for (const [x, h, c] of blds) {
          b += `<rect x="${x}" y="${H * 0.7 - h}" width="200" height="${h}" fill="${c}" stroke="${K}" stroke-width="6"/>`;
          for (let r = 0; r < Math.floor(h / 80); r++) for (let cc = 0; cc < 3; cc++) b += `<rect x="${x + 24 + cc * 56}" y="${H * 0.7 - h + 24 + r * 80}" width="36" height="44" fill="#E3F2FD" stroke="${K}" stroke-width="4"/>`;
        }
        b += `<rect y="${H * 0.7}" width="${W}" height="${H * 0.08}" fill="#CFCFCF" stroke="${K}" stroke-width="6"/><rect y="${H * 0.78}" width="${W}" height="${H * 0.22}" fill="#555"/>`;
        for (let x = 40; x < W; x += 260) b += `<rect x="${x}" y="${H * 0.88}" width="150" height="16" fill="#fff"/>`;
        return wrap(b);
      }
      case 'night': {
        let b = `<rect width="${W}" height="${H}" fill="#0F1B3D"/>`;
        for (let i = 0; i < 40; i++) b += `<circle cx="${(i * 397) % W}" cy="${(i * 211) % (H * 0.5)}" r="${2 + (i % 3)}" fill="#FFF8E1"/>`;
        for (let x = 0; x < W; x += 140) { const h = 160 + ((x * 7) % 260); b += `<rect x="${x}" y="${H - h}" width="130" height="${h}" fill="#1B2A52" stroke="#0A1430" stroke-width="5"/>`; }
        return wrap(b);
      }
      default:
        if (/^#|^rgb/.test(bg)) return wrap(`<rect width="${W}" height="${H}" fill="${bg}"/>`);
        return wrap(`<rect width="${W}" height="${H}" fill="${C.yellow}"/>`);
    }
  }

  const LIB = { COLORS: C, FACES: Object.keys(FACES), POSES: Object.keys(ARMS), PROPS: P, character, background, esc };
  if (typeof module !== 'undefined' && module.exports) module.exports = LIB;
  root.LIB = LIB;
})(typeof window !== 'undefined' ? window : globalThis);
