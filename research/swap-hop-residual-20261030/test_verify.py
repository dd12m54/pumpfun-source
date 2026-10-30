#!/usr/bin/env python3
"""Consistency checks for the swap_hop residual packet.

Verifies, without needing a built candidate:
- RESULT.json is internally consistent (counts match the positions list,
  cluster bounds cover every position, window identity is as recorded);
- analyze.py's clustering groups the recorded positions into one cluster;
- SHA256SUMS matches the packet files it lists.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_analyze():
    spec = importlib.util.spec_from_file_location("packet_analyze", HERE / "analyze.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    result = json.loads((HERE / "RESULT.json").read_text())
    window = result["window"]
    positions = [int(p, 16) for p in window["positions"]]
    assert len(positions) == window["normalized_diff_bytes"], "position count"
    assert positions == sorted(positions), "positions sorted"
    assert all(0 <= p < window["bytes"] for p in positions), "positions in window"
    assert len(window["clusters"]) == 1, "one recorded cluster"
    cluster = window["clusters"][0]
    assert int(cluster["first_offset"], 16) == positions[0], "cluster start"
    assert int(cluster["last_offset"], 16) == positions[-1], "cluster end"
    assert cluster["diff_bytes"] == len(positions), "cluster size"
    assert window["raw_diff_bytes"] >= window["normalized_diff_bytes"], "raw >= norm"

    analyze = load_analyze()
    grouped = analyze.clusters(positions)
    assert len(grouped) == 1 and grouped[0] == positions, "clustering reproduces"

    for line in (HERE / "SHA256SUMS").read_text().splitlines():
        if not line.strip():
            continue
        digest, name = line.split()
        actual = hashlib.sha256((HERE / name).read_bytes()).hexdigest()
        assert actual == digest, f"sha256 mismatch: {name}"
    print("swap-hop-residual packet checks OK")


if __name__ == "__main__":
    main()
