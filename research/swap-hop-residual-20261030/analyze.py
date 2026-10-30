#!/usr/bin/env python3
"""Measure the residual difference of one original window against a candidate.

Usage: python3 analyze.py <candidate-unstripped.so> [window-start-hex]

Reads the original window set from reconstruction/base (via the in-repo
harness modules) and prints the raw/normalized diff-byte counts plus the
cluster layout of the normalized differences for the chosen window
(default 0x5b3b0, multi_hop_curve::swap_hop). Exits non-zero if the window
is fully matched, so callers can use it as a residual detector.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reconstruction" / "harness"))

import score  # noqa: E402
from elf_symbols import function_symbols  # noqa: E402


def clusters(positions, gap=16):
    out = []
    for i in positions:
        if out and i - out[-1][-1] <= gap:
            out[-1].append(i)
        else:
            out.append([i])
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    cand_path = Path(sys.argv[1])
    target = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x5B3B0
    cand = cand_path.read_bytes()
    cs = score.sections(cand)
    names = {s: n for s, _, n in function_symbols(cand)}
    window = {w["start"]: w for w in score.original_windows()}[target]
    raw_c = score.body(cand, cs, target, window["bytes"])
    norm_c = score.normalize(raw_c, target, cs)
    pos = [i for i in range(window["bytes"]) if norm_c[i] != window["norm"][i]]
    raw_diff = sum(a != b for a, b in zip(raw_c, window["raw"]))
    print(f"window {target:#x} ({names.get(target, '?')}) bytes={window['bytes']}")
    print(f"raw diff bytes: {raw_diff}")
    print(f"normalized diff bytes: {len(pos)}")
    for c in clusters(pos):
        print(f"cluster: window offsets {c[0]:#x}..{c[-1]:#x} "
              f"(va {target + c[0]:#x}..{target + c[-1]:#x}), {len(c)} diff bytes")
    print("positions:", ",".join(hex(i) for i in pos))
    return 1 if pos else 0


if __name__ == "__main__":
    raise SystemExit(main())
