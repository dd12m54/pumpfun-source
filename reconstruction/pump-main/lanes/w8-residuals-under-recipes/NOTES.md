# Lane w8-residuals-under-recipes (wave 8, build inputs): integration of recipe and source results

Angle: collect the recipe changes other wave-8 lanes publish, combine them on latest main, and check
whether any residual in the still-unmatched windows (0x13f630, 0x13b9b8, 0x80df8, 0x72810, 0x1e7c0,
0x5b3b0, 0x1489f8, 0x22a10) closes under a different recipe.

Started on origin/main 2b8582135 (1027 / 276), finished on fb25fce02 (1030 / 295).
Scratch: `~/.cache/pumpfun-reconstruction/lanes/w8-residuals-under-recipes/`.

## Final state (main fb25fce02, fresh build 1030 / 295)

Main has absorbed what this lane combined. #2251 (link order) merged. The buy_handler,
buy_exact_quote_in and v3_buy_costs sources reached main through #2346, #2347 and #2348, which are
the same spellings as #2225, #2269 and #2272. On main fb25fce02 the combination therefore adds
nothing beyond its newest part:

| build (vs fresh main fb25fce02, 1030 / 295) | normalized | raw | gains | raw gains | losses |
| --- | ---: | ---: | --- | --- | --- |
| #2309 (`w7r1-execute-sibling`, sweep::execute) alone (P) | 1031 | 296 | 0x72810 | 0x65eb0 | none |
| everything this lane combined, + #2309 (N) | 1031 | 296 | 0x72810 | 0x65eb0 | none |
| main + regenerated `ordered.ld` (Q, this branch) | 1030 | 295 | | | none |

**Recommendation: merge #2309 directly.** It supersedes #2313 for sweep. It also brings create_v2
0x1e7c0 to its original size (0.9876, 42 slots). This branch now carries only:

1. `programs/pump/link/ordered.ld` regenerated with `w8-sibling-recipes/tools/regen.sh` on main
   fb25fce02. Main's script has one stale U selector, the `Vec::from_iter` instance
   `17h0e046d6f...`, which the current source names `17h05834ec0...`. The stale selector matches
   nothing, so that function falls into the root-CGU glob. The regenerated script is score-neutral
   today (1030 / 295, 0 losses). With it, `regen.sh` reproduces the committed script again.
2. This lane's analysis: none of the residuals closes under any recipe.

### How the combination evolved (each row 0 losses)

| base main | combination | result | each part alone |
| --- | --- | --- | --- |
| 2b8582135 (1027/276) | #2251 + #2225 + #2269 + #2272 | 1030 / 293 | 1027/293, 1028/276, 1028/276, 1028/276 |
| 6484b2837 (1027/293) | #2225 + #2269 + #2272 + #2313 | 1030 / 296 | 1030/295 without #2313; #2313 alone 1027/293 |
| 6484b2837 | #2225 + #2269 + #2272 + #2309 | 1031 / 296 | |
| fb25fce02 (1030/295) | + #2309 | 1031 / 296 | #2309 alone 1031/296 |

The raw gains (0x83088 0x837a8 from the v3_buy_costs size match, 0x65eb0 from the sweep size match)
appear only once the units in front of them are at their original sizes. Remaining size deltas on
main + #2309: swap_hop -40, admin_cto -56, and the 512 B `ensure_rent_exempt` wrapper. #2168 removes
the wrapper but adds no raw at today's sizes (row H below).

Merge notes for anyone composing these by hand: #2225 and #2269 conflict on adjacent `lib.rs` lines.
Each adds `#[inline(never)]` to a program fn; keep both. #2309 and #2313 conflict in
`sweep_fees.rs`; take #2309.

### Earlier rows (main 2b8582135, 1027 / 276)

| build | normalized | raw | gains | losses | raw gains | raw losses |
| --- | ---: | ---: | --- | --- | ---: | ---: |
| main 2b8582135 | 1027 | 276 | | | | |
| A: + #2251 | 1027 | 293 | | none | 17 | 0 |
| B: + #2225 | 1028 | 276 | 0x13b9b8 | none | 0 | 0 |
| G: + #2269 | 1028 | 276 | 0x13f630 | none | 0 | 0 |
| C: + #2264 (superseded by #2269) | 1027 | 276 | (0x13f630 at original size, 6 slots) | none | 0 | 0 |
| D: #2251 + #2225 + #2264 | 1028 | 293 | 0x13b9b8 | none | 17 | 0 |
| F: #2251 + #2225 + #2269 | 1029 | 293 | 0x13b9b8, 0x13f630 | none | 17 | 0 |
| H: F + #2168 (conflicts resolved toward #2225/#2269) | 1029 | 293 | same | none | 17 | 0 (no extra raw at today's sizes; not kept) |
| I: F + #2272 | **1030** | **293** | 0x80df8, 0x13b9b8, 0x13f630 | none | 17 | 0 |

The 17 raw gains are #2251's (0xa7e0 0xea68 0xf130 and 14 D-block windows). The three source matches
add no raw yet: .text is still longer than the original (sweep +48, create_v2 +8,
trade::buy_exact_quote +16, swap_hop -40, admin_cto -56, plus the 512 B `ensure_rent_exempt`
wrapper), so every address after the first wrong-size unit still shifts. #2251's model says raw
rises once those sizes match.

## Do the residuals close under a different recipe? No (evidence)

### 1. Global rustc flags (full builds, ledger approach `recipe-global-flag`)

Every flag that changes codegen at all also changes matched windows:

| flag | normalized | losses | targets |
| --- | ---: | ---: | --- |
| `-C debuginfo=2` | 945 | 82 | sweep -352 B, admin_cto 0.376 -> 0.260 |
| `-C debuginfo=1`, `line-tables-only` | build fails (SetCreator::try_accounts frame 4112 > 4096) | | |
| `-Z mir-opt-level=1` | build fails (stack) | | |
| `-Z mir-opt-level=3` | 985 | 42 | worse |
| `-Z mir-opt-level=4` | 711 | 316 | worse |
| `-Z inline-mir=no` | build fails (stack) | | |
| `-Z inline-mir-threshold=100` | 1006 | 21 | all 8 targets unchanged |
| `-Z inline-mir-hint-threshold=200` | 568 | 459 | worse |
| `-Z share-generics=yes` | 535 | 492 | worse |
| `-C target-cpu=v1` / `v2` | link fails (solana-zk-sdk) | | |
| `-C llvm-args=-ldstmemcpy-glue-max=2` / `=8` | 531 / 550 | 496 / 477 | worse |
| `-C llvm-args=-disable-sbf-peephole` | 998 | 29 | unchanged |
| `-C llvm-args=-sbf-disable-avoid-speculation` | 1026 | 1 | unchanged |
| `-bpf-expand-memcpy-in-order`, `-enable-memcpy-dag-opt=false`, `-bpf-disable-avoid-speculation`, `-bpf-disable-serialize-icmp` | 1027 | 0 | byte-identical: the BPF-named options do not reach the SBF backend |

`w8-profile-flags` covered the profile knobs (LTO fat/thin/off, opt-level 2, cgu 16, v0 mangling,
cross-crate-inline thresholds, LLVM inline threshold, vectorizers). `w8-toolchain-version` covered
real Linux v1.44, v1.45/v1.46 hybrids and host shims. I measured the 8 targets on all of their
zero-loss builds: `target_metric.py` gives the same size, ratio and slots as main for every target in
ga-linux, linux144, hyb145, shim-osx86, ga-mac, ltofat, ltothin, ltooff, cci50, cci200, llinl225,
novecloops, cpugeneric and novecslp. Within the recipe space that keeps the 1027, the eight windows
are recipe-invariant.

### 2. LLVM codegen options, as an llc oracle (ledger approach `recipe-llc-option-oracle`)

Tool: capture the root crate's bitcode (`rustc --emit link,llvm-bc`, diagnostic only) and the
rust-lld command line (`--print link-args -C save-temps`). Run v1.44 `llc -O3 -relocation-model=pic
-function-sections -mattr=+store-imm,+jmp-ext <option>`, relink with the captured arguments and run
`score.py`. That takes about 10 s per option instead of a 2.5 min dependency rebuild.

- Control: 1023 of 1027. The 8 targets come out byte for byte like the rustc build. The 4 control
  losses (0x2bf18 0x33c50 0x34558 0x567d8, scheduling swaps) come from use-list order. Bitcode does not
  preserve the in-memory use lists, so a `.ll`/`.bc` replay cannot reproduce those ties exactly.
  Without `-mattr` llc does not pick up the functions' `+store-imm,+jmp-ext`, and 512 windows are lost.
- 71 options, on both main's IR and the combined branch's IR. 36 are no-ops: every window is
  byte-identical. They include the whole MachineScheduler family: SBF uses the SelectionDAG list
  scheduler, so `-enable-misched`, `-misched-topdown/bottomup`, `-enable-post-misched`,
  `-misched-cluster`, `-misched-regpressure` do nothing. The no-ops also include `-pre-RA-sched=list-ilp`,
  greedy local reassign, exhaustive search, CSR cost 0, `-split-spill-mode=speed`, shrink-wrap and LCR limits.
- The other 35 cost 1 to 572 matched windows (`-pre-RA-sched=source/list-burr/fast/linearize/list-hybrid`,
  `-regalloc=basic`, tail-dup and tail-merge sizes, branch folding, ext-TSP, machine sink, SSC,
  store merging, global AA, post-RA scheduling ...). No option matches any target. On the combined IR,
  `-tail-dup-size=3` (19 other losses) is the only option that moves a target materially:
  `trade::buy_exact_quote` 0x1489f8 goes from 0.851 to 0.915 at unchanged size (+16). Its output has the
  same 1021 instructions in the same blocks; only greedy-RA ties flip (r6<->r9 for the 5th argument,
  which the original keeps in r9, plus an r8/r6 and an r7/r9 pair). Early tail duplication changes the
  pre-RA CFG, and with it the RA queue order. So part of 0x1489f8's residual is an RA tie that reacts to
  pre-RA CFG shape: a source hint, not a recipe. Ledger `4876b126`, `15b19b83`.

### 3. Root-crate-only middle-end and MIR options (ledger approach `recipe-root-crate-flag`, 34 builds)

Per-package flags are a legitimate recipe form (Mayhem uses `profile-rustflags`), so dependencies were
left untouched and only the root crate was rebuilt (`cargo rustc -- ARGS`). Base: the branch head on
main e3f3be8bb (1030 normalized), with 5 windows still unmatched.

- No-ops (byte-identical code): `-Z merge-functions=disabled|trampolines`, MIR
  `-DestinationPropagation`, `-DataflowConstProp`, `-EarlyOtherwiseBranch`, `+GVN`, `-CopyProp`,
  `-MatchBranchSimplification`, `+UnreachablePropagation`, `-DeadStoreElimination-initial`, and
  `-phi-node-folding-threshold=1|3`.
- Costs matched windows: `-enable-gvn-hoist` (47), `-enable-gvn-memdep=false` (153),
  `-enable-load-pre=false` (49), `-enable-pre=false` (50), `-simplifycfg-sink-common=false` (72),
  `-simplifycfg-hoist-common=false` (259), `-phi-node-folding-threshold=4` (3),
  `-two-entry-phi-node-folding-threshold=2|8` (1|1), `-jump-threading-threshold=3|9` (24|18),
  `-inlinehint-threshold=200|400` (5|5), `-inline-cold-callsite-threshold=0` (64),
  MIR `-JumpThreading` (212), `-GVN` (73), `+DestinationPropagation` (34), `-InstSimplify` (10),
  `-ScalarReplacementOfAggregates` (57).
- `-enable-gvn-sink` and MIR `-ReferencePropagation` overflow the 4 KiB stack frame.
- Only one zero-loss option touches a target: MIR `-UnreachablePropagation` rewrites `sweep::execute`
  (0x72810 -352 B, 0.887 -> 0.740, further away). `-phi-node-folding-threshold=4` raises
  create_v2 0x1e7c0 from 0.9685 to 0.9739, but it costs 3 matched windows (0xefc8 0xf6c0 0x89258).

Re-run on the branch head (main 6484b2837 + #2313), where sweep (30 slots) and trade::buy_exact_quote
(10 slots) are at original size: none of the 71 llc options lowers either slot count. The only
ratio rises are tiny admin_cto and swap_hop moves under options that cost 17 to 305 windows.

Conclusion: the remaining residuals (regalloc ties, list-scheduler order, tail duplication, memcpy
expansion) are decided by the IR the source produces. They are not decided by the toolchain, profile,
RUSTFLAGS or llc options. Raw progress comes only from layout (#2251) and from reaching original
sizes.

## Ledger rows (lane `w8-residuals-under-recipes`)

- recipe-global-flag: 20 rows (`all-main-ce53d867a-recipe-*-v1`).
- recipe-llc-option-oracle: 71 rows (`all-main-ce53d867a-llc-oracle-*-v1`) plus `4876b126` (0x1489f8 tail-dup).
- integration-combo: `all-main-2b8582135-combo-{A,B,C,D,Dr,E,F,Fr,G,H,Hr,I}-v1`, `all-main-6484b2837-combo-{K,S,J,L}-v1`, `all-main-fb25fce02-combo-{N,P}-v1`, `all-main-fb25fce02-ordered-ld-regen-v1`.

Branch head (main fb25fce02 + regenerated ordered.ld) unstripped sha256 `e3abe708e5603ceedb8f4dbeaa9f00d3d4a8bba99c8d36cc4837985e97ede8c3`.

## Tools (scratch, not committed)

`exp/trial.sh` + `exp/batch.sh` run flag trials with a copy of fastbuild that appends
`PUMP_EXP_RUSTFLAGS` (experiment only). `exp/capture.py` captures bitcode and link args.
`exp/llcvar.sh <name> <llc opts>` runs the llc oracle and relinks with the captured arguments.
`exp/combo.sh` builds a merged tree with its own harness. `exp/summ.py` prints official counts plus
the 8 target metrics.
