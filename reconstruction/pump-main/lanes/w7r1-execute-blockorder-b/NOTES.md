# Lane w7r1-execute-blockorder (instance b), wave 7 round 1

Target: `0x1e7c0` `pump_recovered::create_v2::execute` (original 15,576 B, 1,859 insns, 125 calls).
Angle: basic-block order and branch sense.

A second agent was already running this lane in the shared `w7r1-execute-blockorder` worktree,
so this instance works in its own worktree/branch/OUT with a `-b` suffix
(`swarm/w7r1-execute-blockorder-b`, `~/.cache/pumpfun-reconstruction/lanes/w7r1-execute-blockorder-b`).
Ledger rows use lane `w7r1-execute-blockorder-b`, keys `0x1e7c0-main-2b85821-*`.

Base: origin/main 2b85821 (1027/1035 normalized, 276 raw), target 0.96854 at 15,584 B (+8 B).

## Results

| Build | Bytes | Ratio | slots_diff | Official | unstripped sha256 |
| --- | ---: | ---: | ---: | --- | --- |
| main 2b85821 | 15,584 | 0.96854 | | 1027 / 276 | ec660de7 |
| **e1** | **15,576 (= orig)** | **0.98332** | 43 | 1027 / 276, 0 losses, 0 raw losses | 651e83a1 |

## Mechanism (e1): fee as an `if .. else` expression

The only +8 B residual was the `validate_metadata(..)?` test in execute: the original has
`jne r9,2,<err>` falling through into the Ok path, ours had `jeq r9,2,+1; ja <err>`.
SBF's `analyzeBranch` cannot handle conditional branches, so branch sense is fixed at ISel:
SelectionDAG inverts `br (icmp eq tag,2), ok, err` to `jne err` only when `ok` is the IR-next
block. In our IR the inlined `validate_metadata.exit` block was followed by the creator-fee check
blocks (bb47..bb54): with `let mut fee=0; if cond {..; fee=x;}` the `&&` switch references the
join block first (MIR `[0: join, otherwise: ..]`), so rustc creates the join LLVM block (which
later absorbs depth, init_curve and the validate_metadata call) before the fee-check blocks.
IR oracle: flipping only that branch to `icmp ne`/err-first gives 0.98332 at 1,859 insns.

Spelling: `let fee=if matches!(..) && creator_fee_bps.0>0 { require!..; require!..; creator_fee_bps.0 } else {0};`
The join is now first referenced from the then/else ends, so it is created after the fee-check
blocks; the validate call block sits after them and its Ok successor is IR-next at ISel. Result is
byte-identical to the IR-oracle edit (0.98332, exact original size 15,576 B). Line count and every
`line!()` immediate are unchanged (lines 772/779/780 edited in place). Behaviour is identical.

(The same spelling was rejected on the much older base 630a074 (`g8`, 0.82359 < mut form), before
the later RA-affecting changes; on current main it is the winner.)

## Remaining residuals (43 slots)

1. `mov64 r7,0` / `mov64 r2,0` order swapped at two sites (0x1ec50, 0x20ad0): scheduling.
2. init_curve store block: original stores creator through r4 (`mov r4,r7; add r4,8` after the
   quote_mint memcmp) after `[r7+0x68]`; ours computes it in r2, stores creator first, and loads
   `[r10-0x718]` (r2) late.

## Ledger

`98bd0661` (IR oracle ne), `4ee6327f` (e1), `c25ff263` (e2: explicit match on validate_metadata,
byte-identical).
