# Lane w6r2-execute-ir (wave 6, round 2)

Target: `0x1e7c0` `pump_recovered::create_v2::execute` (original 15,576 B, 1,859 insns, 125 calls).
Approach: IR oracle (SDK llc on rustc's IR reproduces fastbuild), minimal IR edit, then Rust spelling.
Base: origin/main a7135a6a6 (1027/1035 normalized, 276 raw), target 0.85100 at 15,576 B.

## Results

| Build | Bytes | Ratio | Official | unstripped sha256 |
| --- | ---: | ---: | --- | --- |
| main a7135a6a6 (p1) | 15,576 | 0.85100 | 1027 / 276 | |
| **f1 = found binding + mutable override** | 15,656 | **0.88948** | 1027 / 276, 0 losses | 44782f4f2aade26b |

## Mechanism f1: the Some payload is loaded before the Option test

In the original, right after `control_account` returns `Ok`, the payload at `[r10-0x498]` is loaded and
spilled (`mov r1,1; mov r7,2; ldxdw r2,[-0x498]; stxdw [-0x758],r2`) *before* `jeq r9,0` (None), and
the `walk` block is laid out directly after the test (fall-through), storing its reserves into the same
spill slot. Ours (p1, explicit `Ok(Some(r))`/`Ok(None)` arms) loaded the payload only in the `Some` arm
and placed `walk` at the end of the function.

IR oracle: hoisting the payload load into the Option-test block and deleting the `Some` arm block
(`ied/spec.py`) reproduces the test block exactly (0.85361), but `walk` stays at the end. The source
form that yields both is a merge of the *whole* `Option<u64>` value:

```rust
let found=nested_create::control_account(control,mint_key)?;
let mut source=QuoteSource::Controlled;
let mut reserves=found;
if found.is_none() {
 let (r,depth)=nested_create::walk(remaining_accounts,&a.global)?;
 reserves=Some(r);source=QuoteSource::Nested(depth);
}
(source,reserves)
```

The payload feeds a phi at the join, so it is loaded unconditionally next to the tag, and the
`walk` path becomes a plain then-block that falls through. `?` and an explicit `Ok(v)/Err` match are
byte-identical here. Behaviour is unchanged (Some -> Controlled with its reserves, None -> walk).
Line count of the region is unchanged (no `line!()` sites inside it).

## Ledger

Lane `w6r2-execute-ir`, dedupe keys `0x1e7c0-main-a7135a6a6-*`.
