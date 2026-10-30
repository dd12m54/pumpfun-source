# Lane w7r1-execute-frame (wave 7, round 1)

Target: `0x1e7c0` `pump_recovered::create_v2::execute` (original 15,576 B, 1,859 insns, 125 calls).
Angle: stack-frame / slot oracle, then MIR block/local order.
Base: origin/main 2b85821 (1027/1035 normalized, 276 raw), target 0.96854 at 15,584 B.

## Frame audit

On main 2b85821 every `r10` offset in the candidate already equals the original: all stack-slot
tokens sit in equal diff runs. The frame is solved; the residuals are scheduling and block layout:

1. `jeq r9,2,+1; ja LBB92` after the inlined `validate_metadata` (+8 B) where the original has a single
   `jne r9,2,LBB92`.
2. the `init_curve` creator memcpy is scheduled first (through r2) where the original stores it after
   `token_total_supply` (through r4).
3. `mov r7,0` / `mov r2,0` swapped at the end of two `[-0x4c0..]` zeroing blocks.

## Results

| Build | Bytes | Ratio | slots_diff | Official | unstripped sha256 |
| --- | ---: | ---: | ---: | --- | --- |
| main 2b85821 | 15,584 | 0.96854 | | 1027 / 276 | ec660de7 |
| **c1 = `let fee=if .. {..} else {0}`** | **15,576** | **0.98332** | 43 | 1027 / 276, 0 losses, 0 raw losses | 651e83a1 |

## Mechanism c1: the fee then-blocks must be created before the fee join

BPF's `analyzeBranch` cannot analyze conditional branches, so a conditional branch keeps the
polarity SelectionDAG gave it from the IR block order. In main the IR order was
`bb58 (fee join, init_curve) .. validate_metadata.exit, bb47 bb48 bb52 bb54 (fee require! blocks), bb116`,
so ISel emitted `jeq tag,2 -> bb116` + `ja err`, and block placement could not invert it. IR oracle:
moving `bb47..bb54` before `bb58` (or to the end) gives 0.98332 at 1,859 insns.

rustc creates LLVM blocks on first reference. With `let mut fee=0; if cond {..; fee=x}` the switch's
`0` target is the join, so the join is created before the then-block. With
`let fee=if cond {..; creator_fee_bps.0} else {0};` the `0` target is the `else` arm, the then-block is
codegened first (RPO), and the join is created after the fee checks, exactly the oracle order.
Behaviour is unchanged; no `line!()` site moves (the `else {0};` replaces the closing brace line).

## Ledger

Lane `w7r1-execute-frame`, dedupe keys `0x1e7c0-main-2b85821-*`.
