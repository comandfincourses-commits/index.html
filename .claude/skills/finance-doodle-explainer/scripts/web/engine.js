/* Finance Doodle Explainer — deterministic frame engine.
 * ENGINE.init(resolvedStory) once, then ENGINE.renderAt(t) per frame.
 * renderAt returns a signature string; identical signatures mean an identical frame,
 * which lets the Node renderer reuse the previous screenshot (big speed-up on static shots).
 */
(function () {
  const LIB = window.LIB;
  const C = LIB.COLORS;
  let S = null, W = 1920, H = 1080;
  let stage, current = null, built = null, capEl = null;

  /* ---------- easing ---------- */
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const ease = {
    linear: p => p,
    out: p => 1 - Math.pow(1 - p, 3),
    inOut: p => p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2,
    back: p => { const c1 = 1.9, c3 = c1 + 1; return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2); },
    bounce: p => {
      const n = 7.5625, d = 2.75;
      if (p < 1 / d) return n * p * p;
      if (p < 2 / d) return n * (p -= 1.5 / d) * p + .75;
      if (p < 2.5 / d) return n * (p -= 2.25 / d) * p + .9375;
      return n * (p -= 2.625 / d) * p + .984375;
    }
  };
  const r2 = v => Math.round(v * 100) / 100;

  /* ---------- formatting ---------- */
  function fmtNum(v, o = {}) {
    const d = o.decimals || 0;
    let s;
    if (o.format === 'inr' || o.format === undefined) {
      const neg = v < 0; v = Math.abs(v);
      const fixed = v.toFixed(d);
      let [int, frac] = fixed.split('.');
      if (int.length > 3) {
        const last3 = int.slice(-3);
        let rest = int.slice(0, -3);
        rest = rest.replace(/\B(?=(\d{2})+(?!\d))/g, ',');
        int = rest + ',' + last3;
      }
      s = (neg ? '-' : '') + int + (frac ? '.' + frac : '');
    } else if (o.format === 'intl') {
      s = Number(v).toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });
    } else s = Number(v).toFixed(d);
    return (o.prefix || '') + s + (o.suffix || '');
  }

  /* ---------- element factories ---------- */
  function box(el, w, h, html) {
    const d = document.createElement('div');
    d.className = 'el';
    d.style.width = w + 'px'; d.style.height = h + 'px';
    d.innerHTML = html || '';
    el._w = w; el._h = h;
    return d;
  }

  const norm = s => String(s).toLowerCase().replace(/[^a-z0-9₹%$.]/g, '');

  function textNode(el, font) {
    const size = el.size || (font === 'title' ? 150 : 64);
    const maxW = el.maxWidth || (font === 'title' ? 1700 : 1500);
    const d = document.createElement('div');
    d.className = 'el text ' + (font === 'title' ? 'title' : 'body');
    d.style.fontSize = size + 'px';
    d.style.maxWidth = maxW + 'px';
    d.style.width = maxW + 'px';
    d.style.textAlign = el.align || 'center';
    d.style.color = el.color || '#111';
    if (el.stroke) d.style.webkitTextStroke = el.stroke;
    if (el.bg) { d.style.background = el.bg; d.style.padding = '10px 26px'; d.style.borderRadius = '18px'; d.style.border = '6px solid #111'; d.style.width = 'auto'; }
    const hl = (el.highlight || []).map(norm);
    const words = el._words || [];
    el._spans = [];
    words.forEach((wd, i) => {
      const sp = document.createElement('span');
      sp.textContent = wd.w;
      if (hl.includes(norm(wd.w))) sp.style.color = el.highlightColor || C.red;
      sp.className = 'w';
      d.appendChild(sp);
      if (i < words.length - 1) d.appendChild(document.createTextNode(' '));
      el._spans.push(sp);
    });
    el._w = maxW; el._h = size * 1.3;
    return d;
  }

  function cardboard(text, o) {
    const w = o.w || 420, h = o.h || 260, dpt = 40;
    const fill = o.fill || '#D9A55B', top = o.topFill || '#E7BE7E', side = o.sideFill || '#B9843E';
    const size = o.size || 52;
    return { w: w + dpt, h: h + dpt, svg: `<svg viewBox="0 0 ${w + dpt + 8} ${h + dpt + 8}" width="100%" height="100%" stroke-linejoin="round">` +
      `<path d="M4,${dpt + 4} L${dpt + 4},4 L${w + dpt + 4},4 L${w + 4},${dpt + 4} Z" fill="${top}" stroke="#111" stroke-width="6"/>` +
      `<path d="M${w + 4},${dpt + 4} L${w + dpt + 4},4 L${w + dpt + 4},${h + 4} L${w + 4},${h + dpt + 4} Z" fill="${side}" stroke="#111" stroke-width="6"/>` +
      `<rect x="4" y="${dpt + 4}" width="${w}" height="${h}" fill="${fill}" stroke="#111" stroke-width="6"/>` +
      `<foreignObject x="10" y="${dpt + 10}" width="${w - 12}" height="${h - 12}"><div xmlns="http://www.w3.org/1999/xhtml" class="cardtxt" style="font-size:${size}px">${LIB.esc(text)}</div></foreignObject></svg>` };
  }

  function make(el) {
    const t = el.type;
    if (t === 'character') {
      const g = LIB.character(el);
      const hgt = el.h || 520 * (el.scale || 1);
      const w = g.w * hgt / g.h;
      const d = box(el, w, hgt, g.svg);
      el._eyes = d.querySelector('.eyes');
      return d;
    }
    if (t === 'prop') {
      const fn = LIB.PROPS[el.name];
      if (!fn) throw new Error('Unknown prop: ' + el.name);
      const g = fn(el);
      const w = el.w || g.w * (el.scale || 1);
      const hh = el.h || g.h * w / g.w;
      return box(el, w, hh, g.svg);
    }
    if (t === 'image') {
      const w = el.w || 600, h = el.h || 600;
      return box(el, w, h, `<img src="${el.src}" style="width:100%;height:100%;object-fit:${el.fit || 'contain'}">`);
    }
    if (t === 'svg') {
      const w = el.w || 400, h = el.h || 400;
      return box(el, w, h, el.svg.replace('<svg', '<svg width="100%" height="100%"'));
    }
    if (t === 'text') return textNode(el, 'body');
    if (t === 'title') return textNode(el, 'title');
    if (t === 'label') {
      const size = el.size || 40;
      const d = document.createElement('div');
      d.className = 'el label';
      d.style.fontSize = size + 'px';
      d.style.color = el.color || '#111';
      if (el.bg) { d.style.background = el.bg; d.style.border = '5px solid #111'; d.style.borderRadius = '14px'; d.style.padding = '4px 18px'; }
      d.textContent = el.text;
      el._w = null; el._h = null;
      return d;
    }
    if (t === 'card') {
      if ((el.style || 'box') === 'box') {
        const g = cardboard(el.text, el);
        return box(el, g.w, g.h, g.svg);
      }
      const w = el.w || 440, h = el.h || 220;
      const fill = el.fill || (el.style === 'sticky' ? '#FFF176' : '#fff');
      return box(el, w, h, `<div class="card" style="background:${fill};font-size:${el.size || 48}px;color:${el.color || '#111'}">${LIB.esc(el.text)}</div>`);
    }
    if (t === 'bubble') {
      const w = el.w || 460, h = el.h || 260, thought = el.style === 'thought';
      const tail = el.tail || 'bottom-left';
      const tx = tail.includes('left') ? w * 0.22 : w * 0.78;
      const shape = thought
        ? `<path d="M${w * .2},${h * .78} Q${w * .02},${h * .8} ${w * .06},${h * .5} Q${-w * .02},${h * .2} ${w * .2},${h * .16} Q${w * .3},0 ${w * .5},${h * .08} Q${w * .72},-${h * .02} ${w * .82},${h * .18} Q${w},${h * .2} ${w * .96},${h * .5} Q${w},${h * .82} ${w * .78},${h * .8} Q${w * .6},${h * .92} ${w * .45},${h * .82} Q${w * .3},${h * .9} ${w * .2},${h * .78} Z" fill="#fff" stroke="#111" stroke-width="6"/>` +
          `<circle cx="${tx}" cy="${h * .9}" r="14" fill="#fff" stroke="#111" stroke-width="5"/><circle cx="${tx + (tail.includes('left') ? -24 : 24)}" cy="${h * .99}" r="8" fill="#fff" stroke="#111" stroke-width="4"/>`
        : `<path d="M30,10 L${w - 30},10 Q${w - 6},10 ${w - 6},34 L${w - 6},${h * .74} Q${w - 6},${h * .8} ${w - 30},${h * .8} L${tx + 30},${h * .8} L${tx + (tail.includes('left') ? -30 : 50)},${h - 4} L${tx - 10},${h * .8} L30,${h * .8} Q6,${h * .8} 6,${h * .74} L6,34 Q6,10 30,10 Z" fill="#fff" stroke="#111" stroke-width="6"/>`;
      return box(el, w, h, `<svg viewBox="-8 -8 ${w + 16} ${h + 16}" width="100%" height="100%" stroke-linejoin="round">${shape}` +
        `<foreignObject x="20" y="18" width="${w - 40}" height="${h * .8 - 26}"><div xmlns="http://www.w3.org/1999/xhtml" class="cardtxt" style="font-size:${el.size || 40}px">${LIB.esc(el.text || '')}</div></foreignObject></svg>`);
    }
    if (t === 'arrow' || t === 'line') {
      const [x1, y1] = el.from, [x2, y2] = el.to;
      const bend = el.bend || 0;
      const mx = (x1 + x2) / 2 - (y2 - y1) * bend, my = (y1 + y2) / 2 + (x2 - x1) * bend;
      const col = el.color || '#111', sw = el.width || (t === 'arrow' ? 12 : 8);
      const d = `M${x1},${y1} Q${mx},${my} ${x2},${y2}`;
      const ang = Math.atan2(y2 - my, x2 - mx), hs = sw * 3.2;
      const head = t === 'arrow' ? `<path class="head" d="M${x2},${y2} L${x2 - hs * Math.cos(ang - .45)},${y2 - hs * Math.sin(ang - .45)} L${x2 - hs * Math.cos(ang + .45)},${y2 - hs * Math.sin(ang + .45)} Z" fill="${col}" stroke="${col}" stroke-width="4" stroke-linejoin="round"/>` : '';
      const dash = t === 'line' && el.dashed !== false ? `stroke-dasharray="${sw * 2.2} ${sw * 1.8}"` : '';
      const dv = box(el, W, H, `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}"><path class="stroke" d="${d}" fill="none" stroke="${col}" stroke-width="${sw}" stroke-linecap="round" ${dash}/>${head}</svg>`);
      el._full = true;
      el._path = dv.querySelector('.stroke'); el._head = dv.querySelector('.head');
      el._len = el._path.getTotalLength ? null : 0;
      return dv;
    }
    if (t === 'bars') {
      const w = el.w || 900, h = el.h || 520, vals = el.values, n = vals.length;
      const max = el.max || Math.max(...vals) * 1.1;
      const gap = w / n, bw = gap * 0.58, base = h - 70;
      const cols = el.colors || [C.green];
      let s = `<svg viewBox="0 0 ${w} ${h}" width="100%" height="100%" stroke-linejoin="round" overflow="visible"><path d="M6,0 L6,${base} L${w},${base}" fill="none" stroke="#111" stroke-width="7"/>`;
      vals.forEach((v, i) => {
        const x = gap * i + (gap - bw) / 2 + 6;
        s += `<rect class="bar" data-i="${i}" x="${x}" y="${base}" width="${bw}" height="0" fill="${cols[i % cols.length]}" stroke="#111" stroke-width="6"/>`;
        s += `<text class="bv" data-i="${i}" x="${x + bw / 2}" y="${base - 18}" text-anchor="middle" font-family="Mali" font-weight="700" font-size="${el.valueSize || 34}" fill="#111"></text>`;
        if (el.labels) s += `<text x="${x + bw / 2}" y="${base + 44}" text-anchor="middle" font-family="Mali" font-weight="700" font-size="${el.labelSize || 32}" fill="#111">${LIB.esc(el.labels[i])}</text>`;
      });
      s += '</svg>';
      const d = box(el, w, h, s);
      el._bars = [...d.querySelectorAll('.bar')]; el._bv = [...d.querySelectorAll('.bv')];
      el._geom = { base, max, h: base - 30 };
      return d;
    }
    if (t === 'linechart') {
      const w = el.w || 1000, h = el.h || 520, vals = el.values, n = vals.length;
      const max = el.max || Math.max(...vals) * 1.1, min = el.min ?? 0, base = h - 60;
      const px = i => 20 + i * (w - 40) / (n - 1), py = v => base - (v - min) / (max - min) * (base - 30);
      const pts = vals.map((v, i) => `${px(i)},${py(v)}`).join(' L');
      let s = `<svg viewBox="0 0 ${w} ${h}" width="100%" height="100%" overflow="visible"><path d="M6,0 L6,${base} L${w},${base}" fill="none" stroke="#111" stroke-width="7" stroke-linejoin="round"/>`;
      s += `<path class="stroke" d="M${pts}" fill="none" stroke="#111" stroke-width="${(el.width || 10) + 8}" stroke-linejoin="round" stroke-linecap="round"/>`;
      s += `<path class="stroke2" d="M${pts}" fill="none" stroke="${el.color || C.green}" stroke-width="${el.width || 10}" stroke-linejoin="round" stroke-linecap="round"/>`;
      if (el.labels) el.labels.forEach((l, i) => { if (l) s += `<text x="${px(i)}" y="${base + 40}" text-anchor="middle" font-family="Mali" font-weight="700" font-size="28">${LIB.esc(l)}</text>`; });
      if (el.endLabel) s += `<text class="endl" x="${px(n - 1)}" y="${py(vals[n - 1]) - 34}" text-anchor="end" font-family="Mali" font-weight="700" font-size="40" fill="${el.color || C.darkGreen}">${LIB.esc(el.endLabel)}</text>`;
      s += '</svg>';
      const d = box(el, w, h, s);
      el._path = d.querySelector('.stroke'); el._path2 = d.querySelector('.stroke2'); el._endl = d.querySelector('.endl');
      return d;
    }
    if (t === 'pie') {
      const sz = el.w || 460, vals = el.values, tot = vals.reduce((a, b) => a + b, 0);
      const cols = el.colors || [C.blue, C.green, C.orange, C.red, C.purple, C.teal];
      let s = `<svg viewBox="-10 -10 ${sz + 20} ${sz + 20}" width="100%" height="100%" overflow="visible">`;
      const R = sz / 2;
      let acc = 0;
      el._slices = [];
      vals.forEach((v, i) => {
        s += `<path class="sl" data-a0="${acc / tot}" data-a1="${(acc + v) / tot}" fill="${cols[i % cols.length]}" stroke="#111" stroke-width="6" stroke-linejoin="round"/>`;
        acc += v;
      });
      if (el.labels) {
        acc = 0;
        vals.forEach((v, i) => {
          const a = ((acc + v / 2) / tot) * 2 * Math.PI - Math.PI / 2; acc += v;
          s += `<text class="pl" x="${R + Math.cos(a) * R * 0.62}" y="${R + Math.sin(a) * R * 0.62}" text-anchor="middle" dominant-baseline="central" font-family="Mali" font-weight="700" font-size="${el.labelSize || 30}" fill="#fff" stroke="#111" stroke-width="1.5">${LIB.esc(el.labels[i])}</text>`;
        });
      }
      s += '</svg>';
      const d = box(el, sz, sz, s);
      el._slices = [...d.querySelectorAll('.sl')]; el._pl = [...d.querySelectorAll('.pl')]; el._R = R;
      return d;
    }
    if (t === 'gauge') {
      const w = el.w || 700, R = w * 0.36, cx = w / 2, cy = w * 0.5;
      const segs = el.segments || [[300, 600, C.red], [601, 660, C.orange], [661, 780, '#F6E03A'], [781, 900, C.green]];
      const min = el.min ?? segs[0][0], max = el.max ?? segs[segs.length - 1][1];
      const ang = v => Math.PI + (v - min) / (max - min) * Math.PI;
      let s = `<svg viewBox="0 0 ${w} ${w * 0.62}" width="100%" height="100%" overflow="visible">`;
      for (const [a, b, col, lab] of segs) {
        const a0 = ang(a), a1 = ang(b);
        const p = (r, an) => `${cx + r * Math.cos(an)},${cy + r * Math.sin(an)}`;
        s += `<path d="M${p(R, a0)} A${R},${R} 0 0 1 ${p(R, a1)} L${p(R * .62, a1)} A${R * .62},${R * .62} 0 0 0 ${p(R * .62, a0)} Z" fill="${col}" stroke="#111" stroke-width="5"/>`;
        const am = (a0 + a1) / 2;
        s += `<text x="${cx + (R + 54) * Math.cos(am)}" y="${cy + (R + 40) * Math.sin(am)}" text-anchor="middle" font-family="Mali" font-weight="700" font-size="${el.labelSize || 30}">${LIB.esc(lab || `${a}-${b}`)}</text>`;
      }
      s += `<g class="needle"><path d="M${cx},${cy - 10} L${cx - R * .86},${cy} L${cx},${cy + 10} Z" fill="#333" stroke="#111" stroke-width="3"/></g><circle cx="${cx}" cy="${cy}" r="22" fill="#555" stroke="#111" stroke-width="5"/>`;
      if (el.caption) s += `<text x="${cx}" y="${cy + 66}" text-anchor="middle" font-family="Mali" font-weight="700" font-size="36">${LIB.esc(el.caption)}</text>`;
      s += '</svg>';
      const d = box(el, w, w * 0.62, s);
      el._needle = d.querySelector('.needle'); el._g = { cx, cy, min, max };
      return d;
    }
    if (t === 'counter') {
      const d = document.createElement('div');
      d.className = 'el counter';
      d.style.fontSize = (el.size || 140) + 'px';
      d.style.color = el.color || '#111';
      if (el.stroke !== false) d.style.webkitTextStroke = el.stroke || '0px';
      d.textContent = fmtNum(el.from || 0, el);
      el._w = null;
      return d;
    }
    if (t === 'table') {
      const d = document.createElement('div');
      d.className = 'el tbl';
      d.style.fontSize = (el.size || 38) + 'px';
      let h = '<table>';
      if (el.header) h += '<tr class="hd">' + el.header.map(c => `<th>${LIB.esc(c)}</th>`).join('') + '</tr>';
      el.rows.forEach((r, i) => { h += `<tr class="rw" data-i="${i}">` + r.map((c, j) => `<td style="${el.colColors && el.colColors[j] ? 'color:' + el.colColors[j] : ''}">${LIB.esc(c)}</td>`).join('') + '</tr>'; });
      d.innerHTML = h + '</table>';
      el._rows = [...d.querySelectorAll('.rw')];
      return d;
    }
    throw new Error('Unknown element type: ' + t);
  }

  /* ---------- per-frame animation ---------- */
  function animState(el, lt) {
    // returns {o, tx, ty, s, rot, sx, sy, clip}
    const at = el.at || 0, dur = el.dur || (el.in === 'drop' ? 0.6 : 0.35);
    const st = { o: 1, tx: 0, ty: 0, s: 1, rot: 0, clip: null };
    if (lt < at) { st.o = 0; return st; }
    const p = clamp((lt - at) / dur);
    switch (el.in || 'pop') {
      case 'none': break;
      case 'fade': st.o = ease.out(p); break;
      case 'pop': st.s = p >= 1 ? 1 : Math.max(0.0001, ease.back(p)); st.o = clamp(p * 4); break;
      case 'grow': st.s = Math.max(0.0001, ease.out(p)); break;
      case 'slide-left': st.tx = -(el.x + (el._w || 400)) * (1 - ease.out(p)); break;
      case 'slide-right': st.tx = (W - el.x + (el._w || 400)) * (1 - ease.out(p)); break;
      case 'slide-up': st.ty = (H - el.y + (el._h || 400)) * (1 - ease.out(p)); break;
      case 'slide-down': st.ty = -(el.y + (el._h || 400)) * (1 - ease.out(p)); break;
      case 'drop': st.ty = -(el.y + (el._h || 400)) * (1 - ease.bounce(p)); break;
      case 'wipe': st.clip = `inset(0 ${r2((1 - ease.out(p)) * 100)}% 0 0)`; break;
      case 'rise': st.ty = 60 * (1 - ease.out(p)); st.o = ease.out(p); break;
      default: break;
    }
    if (el.emph) {
      for (const e of [].concat(el.emph)) {
        const et = lt - (e.at ?? at + dur);
        const ed = e.dur || 0.5;
        if (et >= 0 && et <= ed) {
          const q = et / ed;
          if (e.type === 'shake') st.rot += Math.sin(q * Math.PI * 8) * 6 * (1 - q);
          if (e.type === 'pulse') st.s *= 1 + 0.18 * Math.sin(q * Math.PI);
          if (e.type === 'bounce') st.ty -= 40 * Math.sin(q * Math.PI);
          if (e.type === 'spin') st.rot += 360 * ease.inOut(q);
        }
      }
    }
    if (el.float) st.ty += Math.sin((lt) * 2 * Math.PI / 2.2) * el.float;
    if (el.out != null && lt >= el.out) {
      const q = clamp((lt - el.out) / 0.25);
      if (el.outAnim === 'pop') st.s *= Math.max(0.0001, 1 - ease.inOut(q));
      else if (el.outAnim === 'slide-left') st.tx -= (el.x + (el._w || 400)) * ease.inOut(q);
      else if (el.outAnim === 'slide-right') st.tx += (W - el.x + (el._w || 400)) * ease.inOut(q);
      else st.o *= 1 - q;
    }
    return st;
  }

  function place(el, d) {
    // centre anchoring; arrows/lines cover the full canvas
    if (el._full) { d.style.left = '0px'; d.style.top = '0px'; return; }
    const w = el._w != null ? el._w : d.offsetWidth, h = el._h != null && el.type !== 'text' && el.type !== 'title' ? el._h : d.offsetHeight;
    el._w = w; el._h = h;
    d.style.left = (el.x - w / 2) + 'px';
    d.style.top = (el.y - h / 2) + 'px';
  }

  function build(sc) {
    const root = document.createElement('div');
    root.className = 'scene';
    const cam = document.createElement('div');
    cam.className = 'cam';
    root.appendChild(cam);
    stage.appendChild(root); // must be in the document before measuring elements
    const bgs = Array.isArray(sc.bg) ? sc.bg : [sc.bg];
    bgs.forEach((b, i) => {
      const bd = document.createElement('div');
      bd.className = 'bg';
      if (bgs.length > 1) {
        bd.style.clipPath = `inset(0 ${i === 0 ? 50 : 0}% 0 ${i === 0 ? 0 : 50}%)`;
      }
      bd.innerHTML = LIB.background(b, W, H);
      cam.appendChild(bd);
    });
    if (bgs.length > 1) {
      const dv = document.createElement('div'); dv.className = 'divider'; cam.appendChild(dv);
    }
    const els = sc.elements.map(src => Object.assign({}, src));
    for (const el of els) {
      el.x = el.x ?? W / 2; el.y = el.y ?? H / 2;
      const d = make(el);
      if (el.z) d.style.zIndex = el.z;
      cam.appendChild(d);
      place(el, d);
      el._d = d;
      if (el._path && el._path.getTotalLength) el._len = el._path.getTotalLength();
    }
    return { root, cam, els };
  }

  function camState(sc, lt) {
    const c = sc.camera;
    if (!c || c === 'none') return null;
    const dur = sc.end - sc.start;
    const p = clamp(lt / dur);
    let s = 1, tx = 0, ty = 0;
    const fx = (c.focus || [W / 2, H / 2])[0], fy = (c.focus || [W / 2, H / 2])[1];
    const mode = typeof c === 'string' ? c : c.type || 'push';
    const amt = (typeof c === 'object' && c.amount) || null;
    if (mode === 'push') s = 1 + (amt || 0.06) * p;
    else if (mode === 'pull') s = 1 + (amt || 0.06) * (1 - p);
    else if (mode === 'punch') s = 1 + (amt || 0.15) * ease.out(clamp(lt / 0.35));
    else if (mode === 'pan-left') { s = 1.08; tx = (amt || 60) * (0.5 - p); }
    else if (mode === 'pan-right') { s = 1.08; tx = -(amt || 60) * (0.5 - p); }
    else if (mode === 'shake') { tx = Math.sin(lt * 60) * 10 * clamp(1 - lt / 0.5); }
    return { s, tx, ty, fx, fy };
  }

  function renderAt(t) {
    let sc = null;
    for (const s of S.scenes) if (t >= s.start && t < s.end) { sc = s; break; }
    if (!sc) sc = S.scenes[S.scenes.length - 1];
    if (current !== sc) {
      if (built) built.root.remove();
      built = build(sc);
      current = sc;
    }
    const lt = t - sc.start;
    let sig = sc.id + '|';
    const cs = camState(sc, lt);
    if (cs) {
      built.cam.style.transformOrigin = `${cs.fx}px ${cs.fy}px`;
      built.cam.style.transform = `translate(${r2(cs.tx)}px,${r2(cs.ty)}px) scale(${r2(cs.s * 1000) / 1000})`;
      sig += `c${r2(cs.s * 1000)},${r2(cs.tx)};`;
    }
    for (const el of built.els) {
      const a = animState(el, lt);
      const d = el._d;
      d.style.opacity = a.o;
      d.style.transform = `translate(${r2(a.tx)}px,${r2(a.ty)}px) rotate(${r2(a.rot + (el.rotate || 0))}deg) scale(${r2(a.s * 1000) / 1000}) ${el.flip ? 'scaleX(-1)' : ''}`;
      d.style.clipPath = a.clip || '';
      sig += `${a.o.toFixed(3)},${r2(a.tx)},${r2(a.ty)},${r2(a.rot)},${r2(a.s * 1000)},${a.clip};`;
      const since = lt - (el.at || 0);
      // word reveal
      if (el._spans) {
        let n = 0;
        el._words.forEach((wd, i) => { const on = lt >= wd.t; el._spans[i].style.visibility = on ? 'visible' : 'hidden'; if (on) n++; });
        sig += 'w' + n;
      }
      if (el._eyes && a.o > 0) {
        const seed = (el.x * 7 + el.y * 3) % 2.3;
        const ph = (lt + seed) % 3.6;
        const blink = el.blink !== false && ph > 3.45;
        el._eyes.style.transform = blink ? 'scaleY(0.12)' : '';
        sig += blink ? 'b' : '';
      }
      if (el.type === 'arrow' || el.type === 'line') {
        const p = clamp(since / (el.drawDur || 0.5));
        const L = el._len || 2000;
        if (el.type === 'arrow' || el.dashed === false) {
          el._path.style.strokeDasharray = `${L}`;
          el._path.style.strokeDashoffset = `${r2(L * (1 - ease.out(p)))}`;
        } else {
          el._path.style.clipPath = '';
          d.style.clipPath = `inset(0 ${r2((1 - ease.out(p)) * 100)}% 0 0)`;
        }
        if (el._head) el._head.style.opacity = p >= 0.95 ? 1 : 0;
        sig += 'a' + p.toFixed(4);
      }
      if (el.type === 'bars') {
        const stagger = el.stagger ?? 0.25, gd = el.growDur || 0.6;
        el._bars.forEach((b, i) => {
          const p = ease.out(clamp((since - i * stagger) / gd));
          const v = el.values[i], hh = (v / el._geom.max) * el._geom.h * p;
          b.setAttribute('y', el._geom.base - hh); b.setAttribute('height', Math.max(0, hh));
          el._bv[i].setAttribute('y', el._geom.base - hh - 18);
          const label = p > 0 && el.showValues !== false ? fmtNum(v * p, el) : '';
          el._bv[i].textContent = label;
          sig += p.toFixed(4) + label;
        });
      }
      if (el.type === 'linechart') {
        const p = ease.inOut(clamp(since / (el.drawDur || 1.6)));
        const L = el._len || 3000;
        for (const pth of [el._path, el._path2]) { pth.style.strokeDasharray = `${L}`; pth.style.strokeDashoffset = `${r2(L * (1 - p))}`; }
        if (el._endl) el._endl.style.opacity = p >= 1 ? 1 : 0;
        sig += 'l' + p.toFixed(4);
      }
      if (el.type === 'pie') {
        const p = ease.inOut(clamp(since / (el.drawDur || 1.0)));
        const R = el._R;
        el._slices.forEach(sl => {
          const a0 = +sl.dataset.a0 * p, a1 = +sl.dataset.a1 * p;
          const A0 = a0 * 2 * Math.PI - Math.PI / 2, A1 = a1 * 2 * Math.PI - Math.PI / 2;
          const large = (a1 - a0) > 0.5 ? 1 : 0;
          sl.setAttribute('d', a1 - a0 <= 0 ? '' : `M${R},${R} L${R + R * Math.cos(A0)},${R + R * Math.sin(A0)} A${R},${R} 0 ${large} 1 ${R + R * Math.cos(A1)},${R + R * Math.sin(A1)} Z`);
        });
        el._pl.forEach(l => l.style.opacity = p >= 1 ? 1 : 0);
        sig += 'p' + p.toFixed(4);
      }
      if (el.type === 'gauge') {
        const p = ease.inOut(clamp((since - 0.2) / (el.drawDur || 1.4)));
        const g = el._g, v = g.min + (el.value - g.min) * p;
        const deg = (v - g.min) / (g.max - g.min) * 180;
        el._needle.setAttribute('transform', `rotate(${r2(deg)} ${g.cx} ${g.cy})`);
        sig += 'g' + deg.toFixed(3);
      }
      if (el.type === 'counter') {
        const p = ease.out(clamp(since / (el.countDur || 1.4)));
        const v = (el.from || 0) + (el.to - (el.from || 0)) * p;
        const txt = fmtNum(v, el);
        d.textContent = txt;
        if (since >= 0) { d.style.left = (el.x - d.offsetWidth / 2) + 'px'; }
        sig += txt;
      }
      if (el.type === 'table') {
        const stagger = el.stagger ?? 0.5;
        el._rows.forEach((rw, i) => {
          const rt = el.rowTimes ? el.rowTimes[i] : (el.at || 0) + 0.3 + i * stagger;
          const on = lt >= rt;
          rw.style.opacity = on ? 1 : 0;
          sig += on ? 1 : 0;
        });
      }
    }
    if (S.captions) {
      const g = S.captions.groups.find(x => t >= x.t && t < x.end);
      let html = '';
      if (g) {
        let cur = -1;
        g.words.forEach((wd, i) => { if (t >= wd.t) cur = i; });
        html = g.words.map((wd, i) => `<span class="${i === cur ? 'on' : ''}">${LIB.esc(wd.w)}</span>`).join(' ');
        sig += 'C' + S.captions.groups.indexOf(g) + ':' + cur;
      }
      if (capEl.innerHTML !== html) capEl.innerHTML = html;
      capEl.style.display = g ? 'block' : 'none';
    }
    // watermark is static, no signature impact
    return sig;
  }

  function init(story) {
    S = story; W = story.width || 1920; H = story.height || 1080;
    stage = document.getElementById('stage');
    stage.style.width = W + 'px'; stage.style.height = H + 'px';
    if (story.watermark) {
      const wm = document.createElement('div');
      wm.className = 'wm ' + (story.watermark.position || 'bottom-right');
      wm.style.opacity = story.watermark.opacity ?? 0.85;
      wm.innerHTML = story.watermark.image ? `<img src="${story.watermark.image}" style="height:${story.watermark.height || 56}px">` : LIB.esc(story.watermark.text || '');
      document.body.appendChild(wm);
    }
    if (story.captions) {
      capEl = document.createElement('div');
      capEl.className = 'caps';
      capEl.style.top = (story.captions.y * H) + 'px';
      capEl.style.fontSize = story.captions.size + 'px';
      document.body.appendChild(capEl);
    }
    current = null; built = null;
    return true;
  }

  window.ENGINE = { init, renderAt, fmtNum };
})();
