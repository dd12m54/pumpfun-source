# Lane w7r1-execute-inline (wave 7, round 1)

Target: `0x1e7c0` `pump_recovered::create_v2::execute` (original 15,576 B, 1,859 insns, 125 calls).
Angle: inlining boundary and callee-multiset census.
Base: origin/main 2b85821 (1027/1035 normalized, 276 raw), target 0.96854 at 15,584 B.

## Callee census (analysis)

`tools/census.py` (lane cache) decodes every `call` in the original window and in our function,
resolves original targets through the scorer's window->symbol map and ours through the symtab,
and diffs the sequences. Result on main 2b85821: 125/125 direct calls, identical callee
sequence (error-path `PumpError::name`/`Display::fmt`/`From`/`with_*`, memcmp/memcpy,
`find_program_address`, `get_associated_token_address_with_program_id`,
`nested_create::{quote_control,control_account,walk}`, `check_quote_mint_extensions`,
`initialize_metadata`, `initialize_mayhem`, `mint_supply`, `create_event`, event/CPI path,
ATA creation and `invoke` + `drop_in_place<[AccountInfo;6]>`). Every helper's
inline/outline decision already matches the original; no syscalls in the window. The
remaining differences are inside inlined bodies.

## Results

| Build | Bytes | Ratio | Official | Notes |
| --- | ---: | ---: | --- | --- |
| main 2b85821 | 15,584 | 0.96854 | 1027 / 276 | |
| t1 | 15,584 | 0.97284 | 1027 / 276, 0 losses, 0 raw losses | creator store after token_total_supply |
| **t2** | 15,576 | **0.98763** (slots_diff 42) | 1027 / 276, 0 losses, 0 raw losses | t1 + fee `if/else` expression (found by w7r1-execute-blockorder-b / -frame) |

## t1: `bonding_curve.creator=creator` after `token_total_supply`

The original's curve-store block writes, in order: initial_vqr/vqr, vtr, rtr, rqr=0, tts, then
the 32-byte creator through the separate `&mut BondingCurve` pointer (`stxdw [r4+0x18..0]`),
then mayhem, cashback, quote_mint, ... Since #2229 the creator destination is an SSA pointer
(init_curve takes `&mut BondingCurve`), so the creator memcpy is no longer re-scheduled by the
DAG and its IR position now decides its place. IR oracle (memcpy moved after the tts store):
0.97284; the source move reproduces it exactly. (w4 `v5` tried the same move when the GEP was
still folded into the Account pointer and saw no change.) init_curve has no `line!()` sites,
so moving a line inside it changes no immediates.

## t2: t1 + `let fee=if .. {require..; creator_fee_bps.0} else {0};`

Sibling lanes w7r1-execute-blockorder-b and w7r1-execute-frame found (ledger
`*-e1-fee-if-else-expr-v1`, `*-t1-let-fee-if-else-v1`) that the `mut fee` form puts the fee check
blocks between the `validate_metadata` exit and its `?` Ok target in IR order, so ISel emits
`jeq ->Ok; ja ->Err` (BPF cannot reverse a branch later) instead of the original `jne ->Err`.
The if/else expression creates the join after the then-chain. The two changes are independent
and stack: 0.98763 at the original's exact size (15,576 B). Line count unchanged.

Remaining (oracle diff, 46 lines): `mov r7,0`/`mov r2,0` order in the two `Sol` returns of
validate_quote_mint, and the creator pointer in r2 instead of r4 with the `[r10-0x718]` (name) reload
placed after the stores instead of before.

## Ledger

Lane `w7r1-execute-inline`, keys `0x1e7c0-main-2b85821-*`.
