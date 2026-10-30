# w7r1-buyhandler-inline (wave 7, round 1)

Target: `0x13b9b8` `buy_v2::buy_handler` (original 15,480 B). Angle: inlining boundaries and
callee-multiset census. Base: origin/main 6edd839 (1027 normalized / 276 raw), buy_handler
15,512 B, ratio 0.97998, llc-masked distance 42 (jump offsets masked, `scripts/sodist.py`).

## Callee census (analysis)

Ordered direct-call list of the original window vs the candidate (90 vs 90 calls, targets
resolved to windows/symbols): the multiset is identical. One order difference only: the two
`ok_or_else(||error!(Overflow))` closure calls of the `require_gte!` add chain (orig: add2's
closure (line 500) is laid out before the TooMuchSolRequired error block, ours after it). That is
block placement, not inlining. Raw-only target differences: the original calls window 0x3b598
(`ensure_rent_exempt_matched`) where we call `ensure_rent_exempt`, and two distinct but identical
`transfer_from_user` copies (0x97930 for the curve payment, 0x97bf0 for both recipient payments).
Every helper's outlined/inlined status already matches the original.

MIR-inliner check (`-Zdump-mir=Inline`): in this rustc, `#[inline(always)]` still obeys the MIR
cost threshold (100), so `complete_and_prepare` and `snapshot_quote_mint` are LLVM-inlined, not
MIR-inlined; a tiny `#[inline(always)]` predicate is MIR-inlined.

## Result: program-fn form + inline Complete emission (dist 42 -> 27, size 15512 -> 15488)

The original buy_handler body sits in the `#[program]` run (layout-order-census), i.e. it is
the body of the `buy_v2` program fn. Two evidence points fit that exactly:
- the CompleteEvent CPI temporaries carry LLVM-inliner lifetime markers (w4/w6r1 oracles), and
- the Complete CPI `?` reaches the shared return with no Result tag retest.
Both follow if the whole handler is an LLVM-inlined callee whose Result the program fn
returns directly. Neither program-fn form alone (P0: 15520, dist 40) nor the inlined Complete
block alone (D1: 15480, dist 46) helps; together (PD1) the entire Complete/prepare tail matches
(dist 31). Adding the w7r1-regsched/frame TradeEvent field order (virtual before real sol
reserves) removes the two spill swaps (dist 27).

Source change (ordinary Rust, line-neutral):
- lib.rs: `#[inline(never)]` on the `buy_v2` program fn (same line).
- buy_v2.rs: `buy_handler` `#[inline(never)]` -> `#[inline(always)]`; CompleteEvent emission +
  `prepare_bonding_curve(..)?` written in the handler, `drop(ev)` after `emit_cpi!(ev)`;
  TradeEvent literal lists virtual_token/virtual_sol before real_sol reserves.

Residual (dist 27): fee zero-phi mov order (4) and the add2 block placement (+1 `ja`, ~22).

| trial | form | bytes | ratio | dist |
| --- | --- | ---: | ---: | ---: |
| base | module, complete_and_prepare helper | 15512 | 0.97998 | 42 |
| P0 | program fn | 15520 | 0.97129 | 40 |
| D1 | module + inline complete | 15480 | 0.97732 | 46 |
| PD1 | program fn + inline complete | 15488 | 0.97390 | 31 |
| PD1vs | PD1 + virtual-before-real sol | 15488 | 0.97601 | 27 |

Official: 1027 normalized / 276 raw, no gains, no losses. unstripped sha256
30263e3e745b230eb565a4bf3e2d6405320df17f96d0b358d8509aed9d33e234.

Rejected this lane: complete_and_prepare plain fn / #[inline] (outlined, 80 calls);
fee helper buy_fees #[inline(always)] (dist 123) / plain (dist 426).
