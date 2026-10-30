#!/usr/bin/env python3
"""Greedy mutation hill-climb for one function window.

hillclimb.py --wt <worktree> --out <lane out> [--workers 2] [--rounds N] [--only id,id]

Each candidate = base file text + a set of mutations from mutations.py. A candidate's crate is
a copy of <wt>/programs/pump under <out>/hc/src<worker>, built with fastbuild.py (shared build
slots respected by fastbuild itself), measured with target_metric.py (fitness = ratio of the
target symbol) and score.py against the base build's score.json (membership losses reject).
Results are cached by source sha256 in <out>/hc/results.jsonl.
"""
import argparse, concurrent.futures as cf, hashlib, json, os, queue, shutil, subprocess, sys, threading, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
REL = "programs/pump/src/multi_hop_curve_swap.rs"
WIN = "0x5b3b0"
SYM = r"multi_hop_curve::swap_hop$"


def apply(text, muts, table):
    for mid in muts:
        old, new = table[mid]
        pairs = list(zip(old, new)) if isinstance(old, tuple) else [(old, new)]
        for o, n in pairs:
            if text.count(o) != 1:
                return None
            text = text.replace(o, n)
    return text


def inert_set(cache):
    """mutations that left the binary byte-identical to their parent in some earlier trial"""
    by_label = {r["label"]: r for r in cache.values()}
    inert = set()
    for r in cache.values():
        parts = r["label"].split("+")
        if len(parts) < 1 or r["label"] == "base" or r.get("status") != "built":
            continue
        parent = by_label.get("+".join(parts[:-1]) or "base")
        if parent and parent.get("so_sha") == r.get("so_sha"):
            inert.add(parts[-1])
    return inert


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


class Runner:
    def __init__(s, wt, out, base_score):
        s.wt, s.out, s.base_score = Path(wt), Path(out), base_score
        s.h = s.wt / "reconstruction/harness"
        s.hc = s.out / "hc"; s.hc.mkdir(parents=True, exist_ok=True)
        s.cache_path = s.hc / "results.jsonl"
        s.cache = {}
        if s.cache_path.exists():
            for l in s.cache_path.read_text().splitlines():
                d = json.loads(l); s.cache[d["sha"]] = d

    def prep(s, w):
        src = s.hc / f"src{w}"
        if not src.exists():
            shutil.copytree(s.wt / "programs/pump", src)
        return src

    def evaluate(s, w, text, label):
        sha = hashlib.sha256(text.encode()).hexdigest()
        if sha in s.cache:
            return s.cache[sha]
        src = s.prep(w)
        (src / "src/multi_hop_curve_swap.rs").write_text(text)
        o = s.hc / "o" / sha[:12]
        t0 = time.time()
        for attempt in range(4):
            b = run([sys.executable, str(s.h / "fastbuild.py"), "--src", str(src), "--work", str(s.out / f"work{w}"), "--out", str(o)])
            if (o / "unstripped.so").exists() or "error[" in (b.stdout + b.stderr):
                break
            if "Too many open files" in b.stderr or "ENFILE" in b.stderr:
                time.sleep(60)
            else:
                break
        so = o / "unstripped.so"
        r = {"sha": sha, "label": label, "secs": round(time.time() - t0, 1)}
        if not so.exists():
            err = [l for l in (b.stdout + b.stderr).splitlines() if "error" in l][:3]
            r.update(status="compile-failed", err=err)
        else:
            tm = run([sys.executable, str(s.h / "target_metric.py"), str(so), WIN, "--sym", SYM, "--top", "1"])
            t = json.loads(tm.stdout.splitlines()[0])
            sc = run([sys.executable, str(s.h / "score.py"), str(so), "--baseline", s.base_score, "--json", str(o / "score.json"), "--quiet"])
            sd = json.loads(sc.stdout.splitlines()[-1])
            r.update(status="built", ratio=t["ratio"], bytes=t["cand_bytes"], calls=t["calls_candidate"],
                     normalized=sd["normalized"], raw=sd["raw"], gains=sd["gains"], losses=sd["losses"],
                     raw_gains=sd["raw_gains"], raw_losses=sd["raw_losses"],
                     so_sha=sd["candidate_sha256"])
            for f in o.iterdir():
                if f.name not in ("unstripped.so", "score.json"):
                    shutil.rmtree(f, ignore_errors=True) if f.is_dir() else f.unlink()
        with s.lock:
            with open(s.cache_path, "a") as f:
                f.write(json.dumps(r) + "\n")
            s.cache[sha] = r
        return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wt", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--base-score", required=True)
    ap.add_argument("--workers", type=int, default=2); ap.add_argument("--rounds", type=int, default=6)
    ap.add_argument("--start", default="", help="comma list of mutations already applied")
    ap.add_argument("--only", default="")
    ap.add_argument("--module", default="mutations")
    ap.add_argument("--slack", type=float, default=0.003)
    ap.add_argument("--prune", action="store_true")
    a = ap.parse_args()
    mod = __import__(a.module)
    table = {mid: (o, n) for mid, o, n in mod.M}
    base_text = (Path(a.wt) / REL).read_text()
    R = Runner(a.wt, a.out, a.base_score)
    cur = [x for x in a.start.split(",") if x]
    R.lock = threading.Lock()
    cur_r = R.evaluate(0, apply(base_text, cur, table), "+".join(cur) or "base")
    print("START", cur, cur_r.get("ratio"), cur_r.get("bytes"), flush=True)
    pool = [x for x in (a.only.split(",") if a.only else table) if x and x not in cur]
    if a.prune:
        inert = inert_set(R.cache)
        pool = [x for x in pool if x not in inert]
        print("pruned inert:", len(inert), "pool:", len(pool), flush=True)
    for rnd in range(a.rounds):
        cands = []
        for mid in pool:
            t = apply(base_text, cur + [mid], table)
            if t is not None:
                cands.append((mid, t))
        results = []
        wq = queue.Queue()
        for w in range(a.workers): wq.put(w)
        def job(t, label):
            w = wq.get()
            try: return R.evaluate(w, t, label)
            finally: wq.put(w)
        with cf.ThreadPoolExecutor(a.workers) as ex:
            futs = {}
            for mid, t in cands:
                futs[ex.submit(job, t, "+".join(cur + [mid]))] = mid
        for f, mid in futs.items():
            r = f.result(); results.append((mid, r))
            print(f"  r{rnd} {mid:40s} {r['status']:14s} ratio={r.get('ratio')} bytes={r.get('bytes')} "
                  f"loss={len(r.get('losses',[]))}/{len(r.get('raw_losses',[]))} gain={len(r.get('gains',[]))}/{len(r.get('raw_gains',[]))}", flush=True)
        ok = [(r["ratio"], mid, r) for mid, r in results if r["status"] == "built" and not r["losses"] and not r["raw_losses"]]
        ok.sort(key=lambda x: -x[0])
        if not ok or ok[0][0] <= cur_r["ratio"]:
            print("NO IMPROVEMENT; stop", flush=True); break
        prev = cur_r["ratio"]; prev_r = cur_r
        cur.append(ok[0][1]); cur_r = ok[0][2]
        prev_sha = prev_r.get("so_sha")
        pool = [mid for r_, mid, r in ok if r_ >= prev - a.slack and mid not in cur and r.get("so_sha") != prev_sha]
        print("ACCEPT", cur, cur_r["ratio"], cur_r["bytes"], flush=True)
    print("FINAL", ",".join(cur), cur_r.get("ratio"), cur_r.get("bytes"), flush=True)


if __name__ == "__main__":
    main()
