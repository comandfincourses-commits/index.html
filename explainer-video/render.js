// Renders gamma_explainer.html to MP4 (1280x720, 25 fps) using Playwright + ffmpeg.
// Usage:  node render.js [out.mp4]            -> full video
//         node render.js --stills 3,15,30,...  -> PNG previews only
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');

(async () => {
  const args = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  await page.goto('file://' + path.join(__dirname, 'gamma_explainer.html') + '?render=1');
  await page.evaluate(() => document.fonts.ready);
  const canvas = await page.$('#c');

  if (args[0] === '--stills') {
    for (const t of args[1].split(',').map(Number)) {
      await page.evaluate(t => window.drawFrame(t), t);
      await canvas.screenshot({ path: path.join(args[2] || '.', `still_${String(t).padStart(5, '0')}.png`) });
    }
    await browser.close(); return;
  }

  const out = args[0] || path.join(__dirname, 'COMandFIN_Option_Gamma_Explainer.mp4');
  const fps = 25, dur = await page.evaluate(() => window.DURATION), n = Math.round(dur * fps);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = 0; i < n; i++) {
    await page.evaluate(t => window.drawFrame(t), i / fps);
    const buf = await canvas.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 250 === 0) console.log(`frame ${i}/${n}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
  console.log('done ->', out);
})();
