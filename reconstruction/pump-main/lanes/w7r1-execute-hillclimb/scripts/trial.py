#!/usr/bin/env python3
"""trial.py NAME FILE.rs [--slot N] [--bfi] [--score]
Lane-local hill-climb trial: copy FILE.rs over src-<slot>/src/sweep_fees.rs, build with
fastbuild (shared slot locks), report target_metric for 0x72810 and optionally the
pre-inline block frequencies of execute (diagnostic llvm-args only in this scratch build).
Appends a JSON line to OUT/results.jsonl and prints it."""
import sys, os, json, re, subprocess, shutil, argparse, time
from pathlib import Path
OUT = Path.home() / '.cache/pumpfun-reconstruction/lanes/w7r1-execute-hillclimb'
WT = Path('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w7r1-execute-hillclimb')
H = WT / 'reconstruction/harness'
OPT = '/Users/shawwalters/.rustup/toolchains/solana/lib/rustlib/aarch64-apple-darwin/bin/opt'
SYM = '_ZN14pump_recovered5sweep7execute17h63039d4d7bb21efdE'
sys.path.insert(0, str(H))
os.environ['PUMP_BUILD_SLOTS'] = '10'
import fastbuild

ap = argparse.ArgumentParser()
ap.add_argument('name'); ap.add_argument('file')
ap.add_argument('--slot', default='0'); ap.add_argument('--bfi', action='store_true')
ap.add_argument('--score', action='store_true'); ap.add_argument('--keep', action='store_true')
a = ap.parse_args()
src = OUT / f'src-{a.slot}'; work = OUT / f'work-{a.slot}'; out = OUT / 'trials' / a.name
out.mkdir(parents=True, exist_ok=True)
shutil.copy2(a.file, src / 'src/sweep_fees.rs'); shutil.copy2(a.file, out / 'sweep_fees.rs')
if a.bfi:
    real = fastbuild.run_compiler
    def hook(cmd, *x, **k):
        if isinstance(cmd, list) and len(cmd) > 1 and str(cmd[0]).endswith('/cargo') and cmd[1] == 'build':
            cmd = cmd[:]; cmd[1] = 'rustc'
            cmd += ['--lib', '--', '-C', 'llvm-args=-print-before=inline', '-C', f'llvm-args=-filter-print-funcs={SYM}']
        return real(cmd, *x, **k)
    fastbuild.run_compiler = hook
for attempt in range(5):
    try:
        r = fastbuild.build(src, work, out, quiet=True, recipe='identity'); break
    except OSError as e:
        print('retry', e, file=sys.stderr); time.sleep(60)
res = {'name': a.name, 'ok': r.get('ok')}
if not r.get('ok'):
    log = (out / 'build.log').read_text(errors='replace') if (out / 'build.log').exists() else ''
    errs = [l for l in log.splitlines() if l.startswith('error')][:3]
    res['error'] = errs or r.get('stack_warnings') or log[-500:]
else:
    m = subprocess.run(['python3', str(H / 'target_metric.py'), str(out / 'unstripped.so'), '0x72810', '--sym', r'sweep::execute$', '--top', '1'], capture_output=True, text=True).stdout
    try:
        tm = json.loads(m.splitlines()[0]); res.update(ratio=tm['ratio'], bytes=tm['cand_bytes'], calls=tm['calls_candidate'], norm=tm['normalized_equal'], raw=tm['raw_equal'])
    except Exception:
        res['metric_error'] = m[-300:]
    res['sha'] = r.get('unstripped_sha256')
    if a.bfi:
        t = (out / 'build.log').read_text(errors='replace')
        i = t.find('; *** IR Dump Before InlinerPass')
        if i >= 0:
            f = t[i:]; f = f[f.index('define'):]; f = f[:f.index('\n}\n') + 3]
            f = re.sub(r' #\d+', ' ', f); f = re.sub(r'@(\d+)\b', r'@g\1', f)
            f = re.sub(r'!(noundef|nonnull) !\{\}', '', f)
            f = re.sub(r'\n\s*call void @llvm.experimental.noalias.scope.decl\(metadata ![0-9]+\)', '', f)
            f = re.sub(r', !\w[\w.]* ![0-9]+', '', f)
            names = set(re.findall(r'@("[^"]+"|[\w.$]+)', f)); me = re.search(r'@(\S+?)\(', f).group(1); names.discard(me)
            decls = []
            for n in names:
                if re.search(r'(call|invoke) [^@]*@' + re.escape(n) + r'\(', f):
                    if not n.startswith('llvm.'): decls.append(f'declare void @{n}()')
                else: decls.append(f'@{n} = external global i8')
            p = out / 'fn.ll'; p.write_text('\n'.join(decls) + '\n' + f)
            q = subprocess.run([OPT, '-S', '-passes=instnamer', str(p), '-o', str(out / 'fn.n.ll')], capture_output=True, text=True)
            if q.returncode == 0:
                q = subprocess.run([OPT, '-disable-output', '-passes=print<block-freq>', str(out / 'fn.n.ll')], capture_output=True, text=True)
                freq = {mm.group(1): float(mm.group(2)) for mm in re.finditer(r' - (\S+): float = (\S+),', q.stderr)}
                cur = None; sites = []
                for l in (out / 'fn.n.ll').read_text().splitlines():
                    mm = re.match(r'^(\S+):', l)
                    if mm: cur = mm.group(1)
                    c = re.search(r'call .*?@([\w.$"]+)\(', l)
                    if c and cur and not c.group(1).startswith('llvm.'):
                        sites.append((freq.get(cur, -1), cur, c.group(1)))
                (out / 'sites.txt').write_text('\n'.join(f'{x:9.5f} {b:10s} {n}' for x, b, n in sites))
                def fmax(pat):
                    v = [x for x, b, n in sites if re.search(pat, n)]
                    return max(v) if v else None
                res['f_rent'] = fmax(r'ensure_rent_exempt')
                res['f_event'] = fmax(r'Event.*4data')
            else:
                res['bfi_error'] = q.stderr[-300:]
        if not a.keep:
            (out / 'build.log').write_text('\n'.join(l for l in t.splitlines() if not l.startswith((' ', '%', '!', 'define', 'declare', '}')) )[-20000:])
    if a.score:
        s = subprocess.run(['python3', str(H / 'score.py'), str(out / 'unstripped.so'), '--baseline', str(OUT / 'out/base/score.json'), '--json', str(out / 'score.json'), '--quiet'], capture_output=True, text=True).stdout
        try:
            sj = json.loads(s.strip().splitlines()[-1])
            res.update(N=sj['normalized'], R=sj['raw'], gains=sj['gains'], losses=sj['losses'], rgains=sj['raw_gains'], rlosses=sj['raw_losses'])
        except Exception:
            res['score_error'] = s[-300:]
for p in ('candidate.so',):
    (out / p).unlink(missing_ok=True)
line = json.dumps(res)
with open(OUT / 'results.jsonl', 'a') as fh: fh.write(line + '\n')
print(line)
