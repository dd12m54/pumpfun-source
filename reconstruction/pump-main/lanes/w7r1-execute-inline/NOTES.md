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
| **t1** | 15,584 | **0.97284** | 1027 / 276, 0 losses, 0 raw losses | creator store after token_total_supply |

## t1: `bonding_curve.creator=creator` after `token_total_supply`

The original's curve-store block writes, in order: initial_vqr/vqr, vtr, rtr, rqr=0, tts, then
the 32-byte creator through the separate `&mut BondingCurve` pointer (`stxdw [r4+0x18..0]`),
then mayhem, cashback, quote_mint, ... Since #2229 the creator destination is an SSA pointer
(init_curve takes `&mut BondingCurve`), so the creator memcpy is no longer re-scheduled by the
DAG and its IR position now decides its place. IR oracle (memcpy moved after the tts store):
0.97284; the source move reproduces it exactly. (w4 `v5` tried the same move when the GEP was
still folded into the Account pointer and saw no change.) init_curve has no `line!()` sites,
so moving a line inside it changes no immediates.

## Ledger

Lane `w7r1-execute-inline`, keys `0x1e7c0-main-2b85821-*`.
