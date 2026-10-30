#!/usr/bin/env python3
"""Spelling-mutation hill-climb driver for trade::buy_exact_quote (0x1489f8).

  hc.py list
  hc.py run [--stack m1,m2] [--jobs 2] [--no-ledger] name [name ...]   (name may be a glob)
  hc.py show name

Each mutation is a list of exact (old, new) text replacements on src/trade_v3.rs (each `old`
must occur exactly once, and old/new must have the same number of newlines so no line!()
immediate moves) plus optional helper text appended at the end of the file. `--stack` applies
accepted mutations first (the hill-climb state). Every trial: copy the crate, build with
fastbuild.py (shared build slots), measure with target_metric.py, record in the ledger.
"""
import argparse, fnmatch, json, os, shutil, subprocess, sys, threading, queue
from pathlib import Path

HERE = Path(__file__).resolve().parent
WT = HERE.parents[3]
H = WT / 'reconstruction/harness'
LEDGER = WT / 'reconstruction/pump-main/log_attempt.py'
OUT = Path.home() / '.cache/pumpfun-reconstruction/lanes/w7r1-buyexactquote-hillclimb'
LANE = 'w7r1-buyexactquote-hillclimb'
REL = 'src/trade_v3.rs'
SYM = r'trade::buy_exact_quote$'
BASE_TAG = os.environ.get('HC_BASE', 'fb25fce')
sys.path.insert(0, str(HERE))
from muts import MUTS  # noqa


def apply(text, names):
    tail = ''
    for n in names:
        desc, reps, extra = MUTS[n]
        for old, new in reps:
            c = text.count(old)
            if c != 1:
                raise ValueError(f'{n}: pattern occurs {c} times: {old[:80]!r}')
            if old.count('\n') != new.count('\n'):
                raise ValueError(f'{n}: newline count changes')
            text = text.replace(old, new)
        tail += extra
    if tail:
        text = text.rstrip('\n') + '\n' + tail.strip('\n') + '\n'
    return text


def metric(so):
    r = subprocess.run([sys.executable, str(H / 'target_metric.py'), str(so), '0x1489f8', '--sym', SYM, '--top', '1'],
                       capture_output=True, text=True)
    for line in r.stdout.splitlines():
        try:
            d = json.loads(line)
        except Exception:
            continue
        if d.get('symbol') == 'pump_recovered::trade::buy_exact_quote':
            return d
    return None


def trial(name, stack, work, ledger):
    names = stack + [name]
    tag = '+'.join(names)
    key = f'0x1489f8-main-{BASE_TAG}-hc-{"+".join(names)}-v1'
    res_p = OUT / 'res' / (tag + '.json')
    if res_p.exists():
        return json.loads(res_p.read_text())
    src = (WT / 'programs/pump' / REL).read_text()
    try:
        text = apply(src, names)
    except ValueError as e:
        return {'name': tag, 'error': str(e)}
    crate = OUT / 'mut' / tag
    if crate.exists():
        shutil.rmtree(crate)
    shutil.copytree(WT / 'programs/pump', crate)
    (crate / REL).write_text(text)
    out = OUT / 'out' / tag
    env = dict(os.environ, PUMP_BUILD_SLOTS='10')
    b = subprocess.run([sys.executable, str(H / 'fastbuild.py'), '--src', str(crate), '--work', str(work), '--out', str(out)],
                       capture_output=True, text=True, env=env)
    res = {'name': tag, 'key': key}
    so = out / 'unstripped.so'
    if b.returncode != 0 or not so.exists():
        res['status'] = 'compile-failed'
        res['log'] = (b.stdout + b.stderr)[-3000:]
    else:
        m = metric(so)
        res['metric'] = m
        res['status'] = 'built'
    shutil.rmtree(crate, ignore_errors=True)
    res_p.parent.mkdir(parents=True, exist_ok=True)
    res_p.write_text(json.dumps(res, indent=1))
    if ledger:
        m = res.get('metric') or {}
        st = 'compile-failed' if res['status'] == 'compile-failed' else (
            'partial' if m and (m.get('normalized_equal') or (m.get('cand_bytes') == 7856 and (m.get('slots_diff') or 99) < 10)) else 'rejected')
        hyp = 'hill-climb mutation ' + '; '.join(MUTS[n][0] for n in names)
        data = {'output': str(out), 'target': {'slots_diff': m.get('slots_diff'), 'ratio': m.get('ratio'), 'cand_bytes': m.get('cand_bytes')},
                'notes': f'stack={stack} trial={name}; base r6 0.9895/10 slots'}
        subprocess.run([sys.executable, str(LEDGER), 'record', '--lane', LANE, '--approach', 'mutation-hillclimb', '--target', '0x1489f8',
                        '--dedupe-key', key, '--hypothesis', hyp, '--status', st, '--data', json.dumps(data)], capture_output=True, text=True)
    return res


def fmt(r):
    if 'error' in r:
        return f"{r['name']:40s} ERROR {r['error'][:100]}"
    if r.get('status') == 'compile-failed':
        lines = [l for l in r.get('log', '').splitlines() if 'error' in l][:2]
        return f"{r['name']:40s} COMPILE-FAILED {' | '.join(lines)[:160]}"
    m = r.get('metric') or {}
    return f"{r['name']:40s} bytes={m.get('cand_bytes')} ratio={m.get('ratio')} slots={m.get('slots_diff')} calls={m.get('calls_candidate')} norm={m.get('normalized_equal')}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd')
    ap.add_argument('names', nargs='*')
    ap.add_argument('--stack', default='')
    ap.add_argument('--jobs', type=int, default=2)
    ap.add_argument('--no-ledger', action='store_true')
    a = ap.parse_args()
    if a.cmd == 'list':
        for n, (d, _, _) in MUTS.items():
            print(f'{n:24s} {d}')
        return
    stack = [s for s in a.stack.split(',') if s]
    names = []
    for pat in a.names:
        names += [n for n in MUTS if fnmatch.fnmatch(n, pat) and n not in names and n not in stack]
    if a.cmd == 'show':
        src = (WT / 'programs/pump' / REL).read_text()
        t = apply(src, stack + names)
        p = OUT / 'show.rs'; p.write_text(t)
        subprocess.run(['diff', str(WT / 'programs/pump' / REL), str(p)])
        return
    q = queue.Queue()
    for n in names:
        q.put(n)
    lock = threading.Lock()

    def worker(i):
        work = OUT / f'w{i}'
        while True:
            try:
                n = q.get_nowait()
            except queue.Empty:
                return
            r = trial(n, stack, work, not a.no_ledger)
            with lock:
                print(fmt(r), flush=True)
    ts = [threading.Thread(target=worker, args=(i,)) for i in range(a.jobs)]
    [t.start() for t in ts]
    [t.join() for t in ts]


if __name__ == '__main__':
    main()
