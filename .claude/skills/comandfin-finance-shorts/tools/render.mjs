// Render timeline.json + voice.wav into a 1080x1920 Short.
// Usage: node render.mjs <out_dir> [--preview t1,t2,...]
// Frames come from template.html (stepped per frame in Chromium) and are piped into ffmpeg.
import { createRequire } from 'node:module';
import { spawn } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';

const dir = path.resolve(process.argv[2]);
const previewArg = process.argv.indexOf('--preview');
const tl = JSON.parse(readFileSync(path.join(dir, 'timeline.json'), 'utf8'));
// resolve playwright from the project or a global install (NODE_PATH / npm root -g)
const req = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = req('playwright')); }
catch { const { execSync } = await import('node:child_process');
  ({ chromium } = req(path.join(execSync('npm root -g').toString().trim(), 'playwright'))); }
const here = path.dirname(fileURLToPath(import.meta.url));
const exe = process.env.CHROMIUM_PATH || undefined;

const browser = await chromium.launch(exe ? { executablePath: exe } : {});
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
await page.goto(pathToFileURL(path.join(here, 'template.html')).href);
await page.evaluate(t => window.setTimeline(t), tl);
await page.evaluate(() => document.fonts.ready);

if (previewArg > 0) {
  for (const t of process.argv[previewArg + 1].split(',').map(Number)) {
    await page.evaluate(x => window.renderFrame(x), t);
    await page.screenshot({ path: path.join(dir, `preview_${t.toFixed(1)}.png`) });
  }
  await browser.close(); process.exit(0);
}

const fps = tl.fps, n = Math.ceil(tl.duration * fps);
// whoosh on every scene change, mixed quietly under the voice
const cuts = tl.scenes.slice(1).map(s => s.start);
const sfx = cuts.map((t, i) => `[${i + 2}:a]adelay=${Math.round(Math.max(0, t - 0.12) * 1000)}:all=1[w${i}]`);
const args = ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
  '-i', path.join(dir, 'voice.wav')];
for (const _ of cuts) args.push('-f', 'lavfi', '-t', '0.4', '-i',
  'anoisesrc=color=pink:amplitude=0.5,highpass=f=600,lowpass=f=4500,afade=t=in:d=0.15,afade=t=out:st=0.15:d=0.25,volume=-30dB,aformat=channel_layouts=stereo:sample_rates=48000');
const mix = cuts.length
  ? `${sfx.join(';')};[1:a]${cuts.map((_, i) => `[w${i}]`).join('')}amix=inputs=${cuts.length + 1}:normalize=0:duration=first[a]`
  : '[1:a]anull[a]';
args.push('-filter_complex', mix, '-map', '0:v', '-map', '[a]', '-c:v', 'libx264', '-preset', 'medium', '-crf', '19',
  '-pix_fmt', 'yuv420p', '-r', String(fps), '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart',
  path.join(dir, `${tl.id}.mp4`));
const ff = spawn('ffmpeg', args, { stdio: ['pipe', 'inherit', 'inherit'] });
const t0 = Date.now();
for (let i = 0; i < n; i++) {
  await page.evaluate(x => window.renderFrame(x), i / fps);
  const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  if (i % 300 === 0) console.log(`${tl.id}: frame ${i}/${n} (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
}
ff.stdin.end();
await new Promise(r => ff.on('close', r));
await browser.close();
console.log(`${tl.id}: done -> ${tl.id}.mp4`);
