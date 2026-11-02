// Frame renderer for the COMandFIN engine.
//   node studio/render.js <projectDir> video <segment> <out.mp4> [workers]   segment = teaser|body|end
//   node studio/render.js <projectDir> stills <segment> <t1,t2,..> <outDir>
//   node studio/render.js <projectDir> events <out.json>                    SFX cue list
//   node studio/render.js <projectDir> durations                              prints JSON of segment durations
//   node studio/render.js <projectDir> thumb <out.png> [cover]                 thumbnail (cover = 1080x1920)
const { chromium } = require('playwright');
const { spawn, execFileSync } = require('child_process');
const fs = require('fs'), path = require('path');
const FPS = 30;
const ROOT = path.resolve(__dirname, '..');

function loadProject(dir) {
  const p = JSON.parse(fs.readFileSync(path.join(dir, 'project.json'), 'utf8'));
  p.transcript = JSON.parse(fs.readFileSync(path.join(dir, 'transcript.json'), 'utf8'));
  if (process.env.BODY_END) p.bodyEnd = +process.env.BODY_END;
  p.avatarUrl = 'file://' + path.join(ROOT, 'assets', 'presenter_avatar.png');
  p.cutoutUrl = 'file://' + path.join(ROOT, 'assets', 'presenter_cutout.png');
  return p;
}
async function openEngine(browser, project, page = 'engine.html') {
  const pg = await browser.newPage({ viewport: { width: 1920, height: 1920 } });
  await pg.goto('file://' + path.join(__dirname, page));
  await pg.evaluate(() => document.fonts.ready);
  await pg.evaluate(p => window.ENGINE.setup(p), project);
  return pg;
}
async function renderRange(browser, project, seg, f0, f1, out) {
  const pg = await openEngine(browser, project);
  const canvas = await pg.$('#c');
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'veryfast', '-r', String(FPS), out], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let f = f0; f < f1; f++) {
    await pg.evaluate(([s, t]) => window.ENGINE.draw(s, t), [seg, f / FPS]);
    const buf = await canvas.screenshot({ type: 'jpeg', quality: 93 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r)); await pg.close();
}

(async () => {
  const [dir, mode, ...a] = process.argv.slice(2);
  const project = loadProject(path.resolve(dir));
  const browser = await chromium.launch();
  try {
    if (mode === 'durations' || mode === 'events') {
      const pg = await openEngine(browser, project);
      const r = mode === 'events' ? await pg.evaluate(() => window.ENGINE.events())
        : await pg.evaluate(() => ({ teaser: window.ENGINE.duration('teaser'), body: window.ENGINE.duration('body'), end: window.ENGINE.duration('end') }));
      if (mode === 'events') fs.writeFileSync(a[0], JSON.stringify(r)); else console.log(JSON.stringify(r));
    } else if (mode === 'stills') {
      const [seg, ts, outDir] = a; fs.mkdirSync(outDir, { recursive: true });
      const pg = await openEngine(browser, project); const canvas = await pg.$('#c');
      for (const t of ts.split(',').map(Number)) {
        await pg.evaluate(([s, t]) => window.ENGINE.draw(s, t), [seg, t]);
        await canvas.screenshot({ path: path.join(outDir, `${seg}_${t.toFixed(1).padStart(6, '0')}.png`) });
      }
    } else if (mode === 'video') {
      const [seg, out, workers = '4'] = a;
      const pg = await openEngine(browser, project);
      const dur = await pg.evaluate(s => window.ENGINE.duration(s), seg); await pg.close();
      const n = Math.round(dur * FPS), W = Math.max(1, Math.min(+workers, Math.ceil(n / 60)));
      const parts = [], per = Math.ceil(n / W), t0 = Date.now();
      await Promise.all([...Array(W).keys()].map(async i => {
        const f0 = i * per, f1 = Math.min(n, f0 + per); if (f0 >= f1) return;
        const part = `${out}.part${i}.mp4`; parts[i] = part; await renderRange(browser, project, seg, f0, f1, part);
      }));
      const list = out + '.txt'; fs.writeFileSync(list, parts.filter(Boolean).map(p => `file '${path.resolve(p)}'`).join('\n'));
      execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', out]);
      parts.filter(Boolean).forEach(p => fs.unlinkSync(p)); fs.unlinkSync(list);
      console.log(`${seg}: ${n} frames in ${((Date.now() - t0) / 1000).toFixed(0)}s -> ${out}`);
    } else if (mode === 'thumb') {
      const [out, kind] = a;
      const pg = await browser.newPage({ viewport: { width: 1920, height: 1920 } });
      await pg.goto('file://' + path.join(__dirname, 'thumbnail.html'));
      await pg.evaluate(() => document.fonts.ready);
      await pg.evaluate(([p, k]) => window.THUMB(p, k), [project, kind || (project.format === 'short' ? 'cover' : 'yt')]);
      await (await pg.$('#c')).screenshot({ path: out });
      console.log('thumbnail ->', out);
    }
  } finally { await browser.close(); }
})();
