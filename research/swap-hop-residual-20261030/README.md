# swap_hop residual: one scheduling cluster (window 0x5b3b0)

`multi_hop_curve::swap_hop` is one of the two windows still unmatched when
Pump is built from current main (base `f3403117`) on native Linux with the
pinned platform-tools v1.44: the build scores **1033/1035 normalized, 192
raw, zero normalized losses** against the committed baseline. This packet
pins down exactly what the remaining difference in `swap_hop` is, so the
window does not need to be re-measured from scratch.

## The residual

- Window `0x5b3b0`, 18,584 bytes; the candidate function has the **same
  length** and the same start address.
- **125 raw** diff bytes, **47 normalized** diff bytes.
- All 47 normalized differences fall in **one cluster**, window offsets
  `0x29f9..0x2a84` (VA `0x5dda9..0x5de34`). Every other byte of the window
  is normalized-equal. Exact positions are in `RESULT.json` and are
  reproduced by `analyze.py`.

## What the cluster is

Decoding the cluster shows a pure instruction-scheduling difference around
the `complete_fill` call in `programs/pump/src/multi_hop_curve_swap.rs`
(the `match complete_fill(&a.global, &a.fee_config, ...)` site):

- The two instructions `ldxdw r2, [r10-0xb28]; add64 r2, 0x8` compute the
  `&a.fee_config` argument (the fee-config data pointer held in the stack
  slot, plus the 8-byte Anchor discriminator offset).
- In the **original**, the pair is emitted immediately after the whitelist
  `memcmp` call, **before** the ~9-field stack struct build that precedes
  the `complete_fill` call.
- In the **recovered build**, the pair is emitted **after** the struct
  build, immediately before the call.
- The struct build, both calls, and all argument values are otherwise
  identical; the block's total instruction count is unchanged.

## Experiments already run (both at the base commit)

1. **Early let-binding** — binding `let fee_config = &a.fee_config;` at
   the top of the enclosing block and passing the binding produces a
   **byte-identical candidate** (same sha256 as the unmodified build).
   The scheduler's placement does not follow the binding position, so
   this lever is ruled out.
2. **Let-then-match** — splitting `match complete_fill(..)?` into
   `let filled = complete_fill(..)?; match filled` is a **regression**:
   score drops to 1028/1035 with 5 normalized losses
   (`0x60058, 0x60260, 0x60468, 0x60670, 0x60878`) and `swap_hop` changes
   size. Reverted; the match-on-call shape appears to be load-bearing.

## Reproduce

```
python3 reconstruction/harness/fastbuild.py --src programs/pump --work <dir>
python3 research/swap-hop-residual-20261030/analyze.py <dir>/last/unstripped.so
```

`analyze.py` prints the diff counts, the cluster, and every differing
offset, and exits 1 while any normalized difference remains (0 once the
window matches). `test_verify.py` checks this packet's internal
consistency without a build.

## Limits

- Measured on native Linux; the maintainers' macOS baseline lists this
  window among its unmatched set as well, but macOS-side byte counts were
  not measured here.
- No source change is proposed: the two obvious source shapes are ruled
  out above, and the remaining lever is an IR/scheduling-level difference
  that this packet does not identify.
- The second Linux-unmatched window, `admin_cto::execute` (`0x22a10`),
  differs in 12,811 normalized bytes and is out of scope here.
