#!/usr/bin/env node
/* Finance Doodle Explainer — renderer.
 *
 *   node render.cjs --story work/storyboard.json [--transcript work/transcript.json]
 *                   [--out work/video_noaudio.mp4] [--workers 4] [--draft]
 *                   [--preview work/preview] [--times 12.5,30] [--range 0-60]
 *
 * --preview DIR   one still per scene (end-state) + contact sheets, no video
 * --times a,b     render stills at the given seconds into the preview dir
 * --range a-b     render only that time window (seconds) — for quick checks
 * --draft         half resolution, faster, for review only
 * --thumb FILE    render meta.thumbnail (a scene object) as a 1920x1080 PNG
 * Writes <story dir>/resolved_storyboard.json (used by mix_audio.py for SFX timing).
 */
const fs = require('fs');
const path = require('path');
const { spawn, execFileSync } = require('child_process');

function loadPlaywright() {
  const tries = ['playwright', path.join(__dirname, 'node_modules', 'playwright'), '/opt/node22/lib/node_modules/playwright'];
  try { const g = execFileSync('npm', ['root', '-g'], { encoding: 'utf8' }).trim(); tries.push(path.join(g, 'playwright')); } catch (e) { /* npm missing */ }
  for (const t of tries) { try { return require(t); } catch (e) { /* next */ } }
  console.error('Playwright not found. Run: npm install playwright  (inside the skill scripts folder) and  npx playwright install chromium');
  process.exit(1);
}

const args = {};
for (let i = 2; i < process.argv.length; i++) {
  const a = process.argv[i];
  if (a.startsWith('--')) {
    const k = a.slice(2), v = process.argv[i + 1];
    if (v === undefined || v.startsWith('--')) args[k] = true; else { args[k] = v; i++; }
  }
}
if (!args.story) { console.error('Missing --story'); process.exit(1); }

const WEB = path.join(__dirname, 'web');
const FONTS = path.join(__dirname, '..', 'assets', 'fonts');
const storyPath = path.resolve(args.story);
const storyDir = path.dirname(storyPath);

/* ---------------- load + resolve ---------------- */
function readJSON(p) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8')); }
  catch (e) { console.error(`Cannot parse ${p}: ${e.message}`); process.exit(1); }
}

function probeDuration(file) {
  const out = execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nk=1:nw=1', file], { encoding: 'utf8' });
  return parseFloat(out);
}

const norm = s => String(s).toLowerCase().replace(/[^a-z0-9₹%$.]/g, '').replace(/\.$/, '');

function resolveStory(story, transcript) {
  const meta = story.meta || {};
  let scenes = story.scenes || [];
  for (const inc of story.include || []) scenes = scenes.concat(readJSON(path.resolve(storyDir, inc)).scenes || []);
  const words = transcript ? transcript.words : [];
  const audio = meta.audio ? path.resolve(storyDir, meta.audio) : null;
  const duration = meta.duration || (audio && fs.existsSync(audio) ? probeDuration(audio) : null) ||
    (words.length ? words[words.length - 1].end + 1.0 : null);
  if (!duration) { console.error('Cannot determine duration: set meta.audio or meta.duration'); process.exit(1); }

  scenes = scenes.map((s, i) => {
    const sc = Object.assign({}, s);
    sc.id = sc.id || `s${i + 1}`;
    if (sc.start == null && sc.word != null) {
      if (!words[sc.word]) throw new Error(`Scene ${sc.id}: word index ${sc.word} out of range`);
      sc.start = Math.max(0, words[sc.word].start - (meta.lead ?? 0.08));
    }
    if (sc.start == null) throw new Error(`Scene ${sc.id}: needs "start" (seconds) or "word" (transcript index)`);
    return sc;
  }).sort((a, b) => a.start - b.start);
  if (scenes.length === 0) throw new Error('Storyboard has no scenes');
  scenes[0].start = 0;
  scenes.forEach((sc, i) => { sc.end = i + 1 < scenes.length ? scenes[i + 1].start : duration; });

  const fileUrl = p => 'file://' + path.resolve(storyDir, p);
  for (const sc of scenes) {
    const dur = sc.end - sc.start;
    sc.bg = sc.bg || meta.bg || 'yellow';
    sc.elements = (sc.elements || []).map(e0 => {
      const el = Object.assign({}, e0);
      if (el.at_word != null) {
        if (!words[el.at_word]) throw new Error(`Scene ${sc.id}: at_word ${el.at_word} out of range`);
        el.at = Math.max(0, words[el.at_word].start - sc.start);
      }
      el.at = el.at || 0;
      if (el.out_word != null && words[el.out_word]) el.out = Math.max(0, words[el.out_word].start - sc.start);
      if (el.type === 'image' && el.src && !/^(file|https?|data):/.test(el.src)) el.src = fileUrl(el.src);
      if (el.type === 'text' || el.type === 'title') el._words = timeWords(el, sc, dur, words);
      if (el.type === 'table' && el.row_words) el.rowTimes = el.row_words.map(w => words[w] ? Math.max(0, words[w].start - sc.start) : 0);
      return el;
    });
  }
  const wm = meta.watermark ? Object.assign({}, meta.watermark) : null;
  if (wm && wm.image) wm.image = fileUrl(wm.image);
  return {
    width: meta.width || 1920, height: meta.height || 1080, fps: meta.fps || 30,
    duration, audio, watermark: wm, meta, scenes
  };
}

function timeWords(el, sc, dur, words) {
  const tokens = String(el.text || '').split(/\s+/).filter(Boolean);
  const n = tokens.length;
  const at = el.at || 0;
  if (Array.isArray(el.words)) return tokens.map((w, i) => ({ w, t: el.words[i] != null ? el.words[i] : at }));
  if (el.reveal === 'all' || el.type === 'title' && el.reveal !== 'words') return tokens.map(w => ({ w, t: at }));
  const times = new Array(n).fill(null);
  if (words.length && el.sync !== false) {
    const cands = words.filter(w => w.start >= sc.start - 0.6 && w.start <= sc.end + 0.3);
    let j = 0;
    tokens.forEach((tok, i) => {
      const nt = norm(tok);
      if (!nt) return;
      for (let k = j; k < Math.min(cands.length, j + 7); k++) {
        if (norm(cands[k].w) === nt) { times[i] = cands[k].start - sc.start; j = k + 1; break; }
      }
    });
  }
  // fill gaps: interpolate between known anchors, else even spacing
  const step = Math.min(0.3, Math.max(0.08, (dur * 0.75 - at) / Math.max(1, n)));
  let lastKnown = -1;
  for (let i = 0; i <= n; i++) {
    if (i === n || times[i] != null) {
      const t0 = lastKnown >= 0 ? times[lastKnown] : at - step;
      const gap = i - lastKnown;
      const t1 = i < n ? times[i] : t0 + gap * step;
      for (let k = lastKnown + 1; k < i; k++) times[k] = t0 + (t1 - t0) * (k - lastKnown) / gap;
      lastKnown = i;
    }
  }
  let prev = 0;
  return tokens.map((w, i) => { const t = Math.max(prev, Math.max(at, times[i] ?? at)); prev = t; return { w, t: Math.min(t, Math.max(0, dur - 0.05)) }; });
}

/* ---------------- browser ---------------- */
async function openPage(chromium, story, scale) {
  const browser = await chromium.launch({ args: ['--font-render-hinting=none', '--disable-gpu', '--allow-file-access-from-files'] });
  const page = await browser.newPage({ viewport: { width: story.width, height: story.height }, deviceScaleFactor: scale });
  page.on('pageerror', e => console.error('[page error]', e.message));
  const tmpl = fs.readFileSync(path.join(WEB, 'template.html'), 'utf8')
    .replace(/__FONTS__/g, 'file://' + FONTS).replace(/__WEB__/g, 'file://' + WEB);
  const htmlPath = path.join(storyDir, '.render_page.html');
  fs.writeFileSync(htmlPath, tmpl);
  await page.goto('file://' + htmlPath);
  await page.evaluate(async () => { await document.fonts.ready; });
  await page.evaluate(s => window.ENGINE.init(s), story);
  // force-load fonts used only inside SVG text
  await page.evaluate(async () => { await Promise.all(['700 40px Mali', '40px "Luckiest Guy"', '40px Chewy'].map(f => document.fonts.load(f))); });
  return { browser, page };
}

async function renderStill(page, t, file, quality) {
  await page.evaluate(tt => window.ENGINE.renderAt(tt), t);
  await page.screenshot({ path: file, type: 'jpeg', quality: quality || 88 });
}

function encoder(out, fps, draft) {
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', draft ? 'veryfast' : 'medium', '-crf', draft ? '26' : '18', '-pix_fmt', 'yuv420p',
    '-r', String(fps), '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => ff.on('close', c => c === 0 ? res() : rej(new Error('ffmpeg exit ' + c))));
  const write = buf => new Promise(res => { if (!ff.stdin.write(buf)) ff.stdin.once('drain', res); else res(); });
  return { write, end: async () => { ff.stdin.end(); await done; } };
}

async function renderChunk(chromium, story, f0, f1, out, opts, progress) {
  const { browser, page } = await openPage(chromium, story, opts.draft ? 0.5 : 1);
  const enc = encoder(out, story.fps, opts.draft);
  let lastSig = null, lastBuf = null, shots = 0;
  for (let f = f0; f < f1; f++) {
    const t = f / story.fps;
    const sig = await page.evaluate(tt => window.ENGINE.renderAt(tt), t);
    if (sig !== lastSig || !lastBuf) {
      lastBuf = await page.screenshot({ type: 'jpeg', quality: opts.draft ? 80 : 92 });
      lastSig = sig; shots++;
    }
    await enc.write(lastBuf);
    progress(1);
  }
  await enc.end();
  await browser.close();
  return shots;
}

(async () => {
  const story0 = readJSON(storyPath);
  const transcriptPath = args.transcript ? path.resolve(args.transcript) : path.join(storyDir, 'transcript.json');
  const transcript = fs.existsSync(transcriptPath) ? readJSON(transcriptPath) : null;
  let story;
  try { story = resolveStory(story0, transcript); } catch (e) { console.error('Storyboard error: ' + e.message); process.exit(1); }
  const resolvedPath = path.join(storyDir, 'resolved_storyboard.json');
  fs.writeFileSync(resolvedPath, JSON.stringify(story, null, 1));
  const { chromium } = loadPlaywright();
  console.log(`Scenes: ${story.scenes.length}  Duration: ${story.duration.toFixed(2)}s  Avg shot: ${(story.duration / story.scenes.length).toFixed(2)}s`);

  if (args.thumb) {
    const th = story0.meta && story0.meta.thumbnail;
    if (!th) { console.error('meta.thumbnail is not defined in the storyboard'); process.exit(1); }
    const one = resolveStory({ meta: Object.assign({}, story0.meta, { duration: 5 }), scenes: [Object.assign({ id: 'thumbnail', start: 0 }, th)] }, null);
    one.watermark = story.watermark;
    const { browser, page } = await openPage(chromium, one, 1);
    await page.evaluate(() => window.ENGINE.renderAt(4.9));
    await page.screenshot({ path: path.resolve(args.thumb), type: 'png' });
    await browser.close();
    console.log('Thumbnail written: ' + path.resolve(args.thumb));
    return;
  }

  if (args.preview || args.times) {
    const dir = path.resolve(args.preview && args.preview !== true ? args.preview : path.join(storyDir, 'preview'));
    fs.mkdirSync(dir, { recursive: true });
    for (const f of fs.readdirSync(dir)) if (/\.(jpg|png)$/.test(f)) fs.unlinkSync(path.join(dir, f));
    const { browser, page } = await openPage(chromium, story, 0.5);
    let list;
    if (args.times) list = String(args.times).split(',').map(Number).map((t, i) => ({ t, name: `t_${String(i).padStart(3, '0')}_${t}s` }));
    else list = story.scenes.map((s, i) => ({ t: Math.max(s.start, s.end - 1 / story.fps - 0.02), name: `scene_${String(i + 1).padStart(3, '0')}`, label: `${i + 1}. ${s.id}  ${s.start.toFixed(1)}s` }));
    await page.evaluate(() => { const d = document.createElement('div'); d.id = 'dbg'; d.style.cssText = 'position:fixed;left:8px;top:6px;background:#000;color:#ff0;font:bold 30px monospace;padding:2px 10px;z-index:999'; document.body.appendChild(d); });
    for (const it of list) {
      await page.evaluate(l => { document.getElementById('dbg').textContent = l || ''; }, it.label || `${it.t}s`);
      await renderStill(page, it.t, path.join(dir, it.name + '.jpg'));
    }
    await browser.close();
    if (!args.times) {
      execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-pattern_type', 'glob', '-i', path.join(dir, 'scene_*.jpg'),
        '-vf', 'scale=480:-1,tile=4x4:padding=6:color=black', path.join(dir, 'sheet_%02d.png')]);
    }
    console.log(`Preview stills written to ${dir}`);
    return;
  }

  let f0 = 0, f1 = Math.round(story.duration * story.fps);
  if (args.range) { const [a, b] = String(args.range).split('-').map(Number); f0 = Math.round(a * story.fps); f1 = Math.min(f1, Math.round(b * story.fps)); }
  const out = path.resolve(args.out || path.join(storyDir, 'video_noaudio.mp4'));
  const nW = Math.max(1, Math.min(parseInt(args.workers || '4', 10), Math.ceil((f1 - f0) / 60)));
  const per = Math.ceil((f1 - f0) / nW);
  const segDir = path.join(storyDir, '.segments');
  fs.mkdirSync(segDir, { recursive: true });
  let doneFrames = 0; const total = f1 - f0; const t0 = Date.now(); let lastLog = 0;
  const progress = n => {
    doneFrames += n;
    const now = Date.now();
    if (now - lastLog > 5000 || doneFrames === total) {
      lastLog = now;
      const el = (now - t0) / 1000, rate = doneFrames / el;
      console.log(`  ${(100 * doneFrames / total).toFixed(1)}%  ${doneFrames}/${total} frames  ${rate.toFixed(1)} fps  ETA ${((total - doneFrames) / rate / 60).toFixed(1)} min`);
    }
  };
  const jobs = [];
  for (let i = 0; i < nW; i++) {
    const a = f0 + i * per, b = Math.min(f1, a + per);
    if (a >= b) continue;
    jobs.push(renderChunk(chromium, story, a, b, path.join(segDir, `seg_${i}.mp4`), { draft: !!args.draft }, progress).then(shots => ({ i, shots, frames: b - a })));
  }
  const res = await Promise.all(jobs);
  const shots = res.reduce((a, r) => a + r.shots, 0);
  const list = res.sort((a, b) => a.i - b.i).map(r => `file '${path.join(segDir, `seg_${r.i}.mp4`)}'`).join('\n');
  fs.writeFileSync(path.join(segDir, 'list.txt'), list);
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', path.join(segDir, 'list.txt'), '-c', 'copy', out]);
  fs.rmSync(segDir, { recursive: true, force: true });
  console.log(`Video written: ${out}  (${total} frames, ${shots} unique, ${((Date.now() - t0) / 1000).toFixed(0)}s)`);
})().catch(e => { console.error(e); process.exit(1); });
