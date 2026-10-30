#!/usr/bin/env python3
"""batch.py PREFIX 'k=v,k=v' ['k=v' ...] [--score] : generate variants and build them on 2 slots."""
import sys, os, subprocess, threading, queue, json
OUT = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w7r1-execute-hillclimb')
sys.path.insert(0, OUT + '/scripts'); import gen
args = sys.argv[1:]; score = '--score' in args; args = [x for x in args if x != '--score']
prefix, specs = args[0], ' '.join(args[1:]).split()
q = queue.Queue()
for i, s in enumerate(specs):
    ch = {k: int(v) for k, v in (x.split('=') for x in s.split(',') if x)}
    name = f'{prefix}-{i:02d}-' + '_'.join(f'{k}{v}' for k, v in sorted(ch.items()))
    path = f'{OUT}/v/{name}.rs'; open(path, 'w').write(gen.make(ch)); q.put((name, path))
def worker(slot):
    while True:
        try: name, path = q.get_nowait()
        except queue.Empty: return
        cmd = ['python3', OUT + '/scripts/trial.py', name, path, '--slot', str(slot), '--bfi'] + (['--score'] if score else [])
        r = subprocess.run(cmd, capture_output=True, text=True)
        print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-400:], flush=True)
ts = [threading.Thread(target=worker, args=(s,)) for s in (0, 1)]
[t.start() for t in ts]; [t.join() for t in ts]
