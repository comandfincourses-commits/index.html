#!/usr/bin/env python3
"""COMandFIN video builder: one command from voice-over + storyboard to a publish-ready video.

    python3 studio/make.py projects/<name>            # full build
    python3 studio/make.py projects/<name> --preview  # body only, 15 fps, fast check

Inputs in projects/<name>/ : voiceover.(wav|mp3|m4a), project.json  (transcript.json is created if missing)
Outputs in projects/<name>/output/ : <slug>.mp4, thumbnail.png (+ cover.png for shorts), chapters.txt

Long  (16:9): TEASER -> BRAND INTRO (full) -> LESSON (with CTAs) -> END SCREEN (12 s)
Short (9:16): TEASER (flash-forward) -> LESSON (with CTAs) -> END CARD -> brand-intro logo tail
"""
import glob, json, os, re, subprocess, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STUDIO = os.path.join(ROOT, 'studio')
INTRO = os.path.join(ROOT, 'assets', 'intro.mp4')
SR, FPS = 48000, 30


def sh(*cmd, **kw):
    print('  $', ' '.join(str(c) for c in cmd)[:160], flush=True)
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


def node(*a, capture=False):
    r = subprocess.run(['node', os.path.join(STUDIO, 'render.js'), *map(str, a)], check=True, capture_output=capture, text=True)
    return r.stdout if capture else None


def read_audio(path, start=None, dur=None):
    cmd = ['ffmpeg', '-v', 'error']
    if start is not None: cmd += ['-ss', str(start)]
    if dur is not None: cmd += ['-t', str(dur)]
    cmd += ['-i', path, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).reshape(-1, 2).copy()


def write_wav(path, a):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', path],
                   input=np.clip(a, -1, 1).astype(np.float32).tobytes(), check=True)


# ---------- synthesized sound effects (subtle, brand-neutral) ----------
def sfx_bank():
    rng = np.random.default_rng(7); t = lambda d: np.arange(int(SR * d)) / SR
    def lp(x, k): return np.convolve(x, np.ones(k) / k, 'same')
    tt = t(0.07); pop = np.sin(2 * np.pi * (900 - 3000 * tt) * tt) * np.exp(-tt * 60) * 0.16
    tt = t(0.02); click = lp(rng.standard_normal(len(tt)), 3) * np.exp(-tt * 300) * 0.35
    tt = t(0.45); env = np.sin(np.pi * tt / 0.45) ** 2; whoosh = lp(rng.standard_normal(len(tt)), 18) * env * 0.22
    tt = t(0.7); ding = (np.sin(2 * np.pi * 1320 * tt) + 0.5 * np.sin(2 * np.pi * 1980 * tt)) * np.exp(-tt * 7) * 0.09
    return {k: np.stack([v, v], 1) for k, v in dict(pop=pop, click=click, whoosh=whoosh, ding=ding).items()}


def place(buf, clip, at):
    i = int(at * SR)
    if i >= len(buf) or i < 0: return
    n = min(len(clip), len(buf) - i); buf[i:i + n] += clip[:n]


def music_bed(proj_dir, project, n, voice):
    cands = [os.path.join(proj_dir, project['music'])] if project.get('music') else glob.glob(os.path.join(ROOT, 'assets', 'music', '*.*'))
    if not cands: return np.zeros((n, 2), np.float32)
    m = read_audio(cands[0])
    m = np.tile(m, (int(np.ceil(n / len(m))) , 1))[:n]
    # duck under the voice: 0.16 in pauses, 0.05 under speech
    lvl = np.abs(voice).max(1); k = SR // 10
    env = np.convolve(lvl, np.ones(k) / k, 'same'); speaking = env > 0.02
    g = np.where(speaking, 0.05, 0.16); g = np.convolve(g, np.ones(SR // 4) / (SR // 4), 'same')
    return m * g[:, None] * project.get('music_volume', 1.0)


def mux(video, audio_wav, out):
    sh('ffmpeg', '-v', 'error', '-y', '-i', video, '-i', audio_wav, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', SR, '-shortest', out)


def intro_part(fmt, mode, work):
    """Brand intro normalised to the output format. mode: full | tail | none"""
    if mode == 'none': return None
    out = os.path.join(work, f'intro_{mode}.mp4')
    ss = ['-ss', '6.6'] if mode == 'tail' else []
    if fmt == 'long':
        vf = f'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps={FPS},format=yuv420p'
    else:  # vertical: sharp 16:9 intro on a blurred, darkened fill
        vf = (f'split[a][b];[a]scale=-2:1920,crop=1080:1920,boxblur=30:3,eq=brightness=-0.12[bg];[b]scale=1080:-2[fg];'
              f'[bg][fg]overlay=0:(H-h)/2,fps={FPS},format=yuv420p')
    sh('ffmpeg', '-v', 'error', '-y', *ss, '-i', INTRO, '-filter_complex', vf, '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast',
       '-c:a', 'aac', '-b:a', '192k', '-ar', SR, '-ac', '2', out)
    return out


def chapters(project, offset):
    def ts(x): x = int(round(x)); return f'{x // 60}:{x % 60:02d}'
    lines = ['0:00 Introduction']
    for s in project['scenes']:
        if s.get('chapter'): lines.append(f"{ts(s['start'] + offset)} {s['chapter']}")
    return '\n'.join(lines)


def main():
    pdir = os.path.abspath(sys.argv[1]); preview = '--preview' in sys.argv
    until = float(sys.argv[sys.argv.index('--until') + 1]) if '--until' in sys.argv else None
    if until: os.environ['BODY_END'] = str(until)   # sample build: lesson cut at this second, no end screen
    project = json.load(open(os.path.join(pdir, 'project.json')))
    fmt = project.get('format', 'long')
    voice_path = os.path.join(pdir, project.get('audio') or next(f for f in os.listdir(pdir) if f.startswith('voiceover')))
    out_dir = os.path.join(pdir, 'output'); work = os.path.join(pdir, '.work'); os.makedirs(out_dir, exist_ok=True); os.makedirs(work, exist_ok=True)
    slug = re.sub(r'[^A-Za-z0-9]+', '_', project.get('title', os.path.basename(pdir)))[:60].strip('_')
    slug = f"COMandFIN_{'Short' if fmt == 'short' else 'Long'}_{slug}" + (f'_SAMPLE_{int(until)}s' if until else '')

    if not os.path.exists(os.path.join(pdir, 'transcript.json')):
        print('1/6 transcribing voice-over …'); sh('python3', os.path.join(STUDIO, 'transcribe.py'), voice_path, '--lang', project.get('language', 'en'))
    durs = json.loads(node(pdir, 'durations', capture=True).strip().splitlines()[-1])
    print('segment durations', durs)

    print('2/6 rendering animation …')
    body_v = os.path.join(work, 'body.mp4'); node(pdir, 'video', 'body', body_v, 4)
    if preview:
        mux(body_v, voice_path, os.path.join(out_dir, 'preview.mp4')); print('preview ready'); return
    end_v = os.path.join(work, 'end.mp4')
    endseg = project.get('end_segment', 'end')
    if not until: node(pdir, 'video', endseg, end_v, 2)
    clips = (project.get('teaser') or {}).get('clips') or []
    teaser_v = os.path.join(work, 'teaser.mp4') if clips else None
    if clips: node(pdir, 'video', 'teaser', teaser_v, 2)

    print('3/6 mixing audio …')
    voice = read_audio(voice_path); n = int(durs['body'] * SR)
    voice = np.pad(voice, ((0, max(0, n - len(voice))), (0, 0)))[:n]
    bank = sfx_bank(); ev = os.path.join(work, 'events.json'); node(pdir, 'events', ev)
    fx = np.zeros_like(voice)
    if project.get('sfx', True):
        for e in json.load(open(ev)): place(fx, bank[e['k']], e['t'])
    body_a = voice + fx * project.get('sfx_volume', 1.0) + music_bed(pdir, project, n, voice)
    write_wav(os.path.join(work, 'body.wav'), body_a)
    intro_audio = read_audio(INTRO)
    end_n = int(durs[project.get('end_segment', 'end')] * SR); end_a = np.zeros((end_n, 2), np.float32)
    seg = intro_audio[:end_n] * (0.55 if fmt == 'long' else 0.35); fade = np.linspace(1, 0, min(len(seg), SR * 3))
    seg[-len(fade):] *= fade[:, None]; end_a[:len(seg)] = seg; place(end_a, bank['whoosh'], 0.05)
    write_wav(os.path.join(work, 'end.wav'), end_a)
    if clips:
        parts = []
        for c in clips:
            a = read_audio(voice_path, c[0], c[1] - c[0]); a = np.pad(a, ((0, max(0, int((c[1] - c[0]) * SR) - len(a))), (0, 0)))[:int((c[1] - c[0]) * SR)]
            r = min(len(a), SR // 20); a[:r] *= np.linspace(0, 1, r)[:, None]; a[-r:] *= np.linspace(1, 0, r)[:, None]
            place(a, bank['whoosh'] * 0.8, 0); parts.append(a)
        write_wav(os.path.join(work, 'teaser.wav'), np.concatenate(parts))

    print('4/6 muxing segments …')
    mux(body_v, os.path.join(work, 'body.wav'), os.path.join(work, 'body_av.mp4'))
    if not until: mux(end_v, os.path.join(work, 'end.wav'), os.path.join(work, 'end_av.mp4'))
    if clips: mux(teaser_v, os.path.join(work, 'teaser.wav'), os.path.join(work, 'teaser_av.mp4'))
    mode = project.get('intro_mode', 'full' if fmt == 'long' else 'tail')
    intro = intro_part(fmt, mode, work)

    seq = []
    if clips: seq.append(os.path.join(work, 'teaser_av.mp4'))
    if intro and mode == 'full': seq.append(intro)
    seq += [os.path.join(work, 'body_av.mp4')] + ([] if until else [os.path.join(work, 'end_av.mp4')])
    if intro and mode == 'tail': seq.append(intro)

    print('5/6 final assembly + loudness normalisation (-14 LUFS) …')
    final = os.path.join(out_dir, slug + '.mp4')
    inputs = sum([['-i', p] for p in seq], [])
    fc = ''.join(f'[{i}:v][{i}:a]' for i in range(len(seq))) + f'concat=n={len(seq)}:v=1:a=1[v][a0];[a0]loudnorm=I=-14:TP=-1.5:LRA=11,aresample={SR}[a]'
    sh('ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', fc, '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-crf', '19', '-preset', 'medium',
       '-pix_fmt', 'yuv420p', '-r', FPS, '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', final)

    print('6/6 thumbnails + chapters …')
    if fmt == 'long':
        node(pdir, 'thumb', os.path.join(out_dir, 'thumbnail.png'), 'yt')
        offset = (sum(c[1] - c[0] for c in clips) if clips else 0) + (10.0 if mode == 'full' else 0)
        open(os.path.join(out_dir, 'chapters.txt'), 'w').write(chapters(project, offset) + '\n')
    else:
        node(pdir, 'thumb', os.path.join(out_dir, 'cover.png'), 'cover')
        node(pdir, 'thumb', os.path.join(out_dir, 'thumbnail.png'), 'yt')
    d = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', final], capture_output=True, text=True).stdout)
    print(f'\nDONE  {final}  ({d:.1f}s)')


if __name__ == '__main__':
    main()
