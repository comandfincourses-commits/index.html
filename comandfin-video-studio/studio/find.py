#!/usr/bin/env python3
"""Print the time at which phrases are spoken.  Usage: python3 studio/find.py projects/<name> "phrase one" "phrase two" ...
With no phrases, prints every word with its start time (for writing the storyboard)."""
import json, re, sys
tr = json.load(open(sys.argv[1].rstrip('/') + '/transcript.json'))
W = [w for s in tr['segments'] for w in s['words']]
norm = lambda x: re.sub(r'[^a-z0-9₹%]', '', x.lower())
if len(sys.argv) == 2:
    line = []
    for w in W:
        line.append(f"{w['w']}@{w['s']:.1f}")
        if re.search(r'[.?!]$', w['w']): print(' '.join(line)); line = []
    print(' '.join(line)); sys.exit()
for ph in sys.argv[2:]:
    toks = [norm(t) for t in ph.split()]
    hits = [W[i]['s'] for i in range(len(W) - len(toks) + 1) if all(norm(W[i + k]['w']).startswith(toks[k]) for k in range(len(toks)))]
    print(f'{ph!r}: {hits}')
