#!/usr/bin/env python3
"""Record hill-climb results (results.jsonl) in the shared ledger, one row per single-mutation
trial relative to its parent state; skips rows already recorded."""
import json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WT = HERE.parents[3]
L = WT / "reconstruction/pump-main/log_attempt.py"
OUT = Path.home() / ".cache/pumpfun-reconstruction/lanes/w7r1-swaphop-hillclimb"
sys.path.insert(0, str(HERE))
import mutations3 as mutations2

DESC = {mid: (o, n) for mid, o, n in mutations2.M}
done_path = OUT / "hc/recorded.txt"
done = set(done_path.read_text().split()) if done_path.exists() else set()
rows = [json.loads(l) for l in open(OUT / "hc/results.jsonl")]
by_label = {r["label"]: r for r in rows}
for r in rows:
    lab = r["label"]
    if lab == "base" or r["sha"] in done:
        continue
    parts = lab.split("+")
    mid, parent = parts[-1], "+".join(parts[:-1]) or "base"
    pr = by_label.get(parent, {})
    key = f"0x5b3b0-main-7e26cbf-hc-{mid}-on-{len(parts)-1}-v1" if len(parts) > 1 else f"0x5b3b0-main-7e26cbf-hc-{mid}-v1"
    o, n = DESC.get(mid, ("?", "?"))
    hyp = f"hill-climb spelling mutation {mid} on [{parent}]: `{o[:140]}` -> `{n[:160]}`"
    if r["status"] != "built":
        status = "compile-failed"; note = "; ".join(r.get("err", []))[:300]
    else:
        same = pr.get("so_sha") == r.get("so_sha")
        better = r["ratio"] > pr.get("ratio", 0) and not r["losses"] and not r["raw_losses"]
        status = "rejected" if (same or not better) else "partial"
        note = ("byte-identical to parent" if same else
                f"ratio {pr.get('ratio')}->{r['ratio']}, {pr.get('bytes')}->{r['bytes']} B, calls {r['calls']}, "
                f"losses {r['losses']}/{r['raw_losses']}")
    data = {"output": str(OUT / "hc/o" / r["sha"][:12]), "normalized": r.get("normalized"), "raw": r.get("raw"),
            "gains": r.get("gains", []), "losses": r.get("losses", []),
            "target": {"ratio": r.get("ratio"), "cand_bytes": r.get("bytes")}, "notes": note}
    c = subprocess.run([sys.executable, str(L), "check", "--dedupe-key", key], capture_output=True, text=True)
    if '"duplicate": true' in c.stdout:
        done.add(r["sha"]); continue
    p = subprocess.run([sys.executable, str(L), "record", "--lane", "w7r1-swaphop-hillclimb", "--approach", "mutation-hillclimb",
                        "--target", "0x5b3b0", "--dedupe-key", key, "--hypothesis", hyp, "--status", status,
                        "--data", json.dumps(data)], capture_output=True, text=True)
    if p.returncode == 0:
        done.add(r["sha"])
    else:
        print("FAIL", key, p.stderr[-300:])
done_path.write_text("\n".join(sorted(done)))
print("recorded", len(done))
