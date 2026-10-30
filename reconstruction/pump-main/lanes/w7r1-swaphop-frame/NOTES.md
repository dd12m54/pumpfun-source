# w7r1-swaphop-frame: 0x5b3b0 multi_hop_curve::swap_hop (stack-frame / slot oracle)

Base: origin/main 7e26cbf (1027/1035 normalized, 293 raw vs the committed baseline score.json).
Target base: ratio 0.7332, 18,544 B (orig 18,584), 107/107 calls.

## Frame census (frameoracle.py on main)
Every alloca-backed object already sits at its original r10 offset (0x30..0x818, and the
16-byte call-return slots 0x828..0xa38). The only alloca group mismatch is `user` (the
whitelist key copy at line 599): ours merges it into the 232-byte `_541` group (0x260), the
original into the event group at -0x6d0, where it shares the slot with the 599 AnchorError and
the complete_fill result. So in the original the user copy is dead before the 599 error is
built (ours: lifetime.end after the error, overlapping `_215`).

What is left of the frame is the 8-byte spill area (0xa40..0xb58 ours, 0xa40..0xb30 orig: 36 vs 31
spill slots). In the current best build 455 of 611 orig-only diff lines are r10-offset-only or
jump-offset-only (spill slot numbering and layout shifts); 106 aligned pairs differ only in the
spill offset (orig 0xa60 = sret pointer is our 0xa98, orig 0xab0 = curve pointer is our 0xa40, ...).
These follow from greedy RA / StackSlotColoring on different code, not from allocas.

## Results
| trial | change | bytes | ratio | official |
|---|---|---:|---:|---|
| base | origin/main 7e26cbf | 18,544 | 0.7332 | 1027/293 |
| u2 | `let allowed = { let user = a.user.key(); !mayhem && user != wl }; require!(allowed, ..)` | 18,512 | 0.7014 | no losses |
| g1 | `require_gt!(base,0,BuyZeroAmount)` for line 590 | 18,552 | 0.7313 | no losses |
| g2 | g1 + u2 (= h1/h2 `v3_can_cross(&a.global,c,&a.user.key())`, byte-identical) | 18,520 | 0.7328 | no losses |
| m4 | `raw_output = base_amount.checked_add(match &post_fill{Some(p)=>p.base_out,None=>0})` (trade_v3 spelling), no post_out tuple element | 18,520 | 0.7372 | no losses |
| **m2** | **g1 + m4** | **18,528** | **0.73746** | **1027/293, no losses** |
| m1 | g2 + m4 | 18,528 | 0.7340 | no losses |

m2 unstripped sha256 822a7786e587cf6952231e89cceaa419a6655190b68b002775948feb4769f0e6.

## Mechanisms
1. **require_gt! creates the continue block first (block order, line 590).** `if base == 0 {..}`
   becomes `switchInt(base) -> [0: err, otherwise: cont]` (SimplifyComparisonIntegral), so rustc
   creates the 590 error llbb before the reserves-compare block. `require_gt!` (anchor: `if v1 <= v2`)
   keeps a bool switch `[0: cont, otherwise: err]`: the continue block is created first and the 590
   block lands between it and its successors, so ISel emits `jgt over; ja within` exactly like the
   original (orig 0x5d660 `jgt r1, r8, +0x1; ja +0xb1`). buy.rs, buy_v2 and trade_v3 all use
   `require_gt!(.., 0, BuyZeroAmount)`.
2. **user key dies before the 599 error (frame).** The original's `user` copy shares -0x6d0 with the
   599 error: the key must be a temporary of the condition (trade_v3's
   `v3_can_cross(&a.global, curve, &a.user.key())`, or a bool block). With it the mayhem test falls
   through into the 599 error and the memcmp block falls into complete_fill as in the original, and
   the alloca frame is then exact (frameoracle: 0 alloca group mismatches). It only pays with g1's
   block order (u2 alone -3.2 pts) and is still -0.35 pts on top of m2, so it is not in the PR head.
3. **raw_output from `match &post_fill`** (the trade_v3 buy form) instead of a post_out tuple
   element: +0.4 pts.

## IR-oracle findings (tools/irdiff.py, llc on edited IR)
- The original has a separate block on the within edge (bb59 -> join) holding the phi copies
  (orig 0x5dbf8). Ours hoists them into bb59 (BPF cannot split critical edges in MIR). An empty IR
  block is removed by CodeGenPrepare (eliminateMostlyEmptyBlocks); a block holding only a
  lifetime marker survives and gives 0.7328 -> 0.7436 on g2 (exact orig shape). Branch weights
  (3:1) do not reproduce it. The Rust construct that leaves a marker there is not found yet
  (w2: post_fill carried in the inner tuple: +32 B of unmarked 16 B pieces, no own block).
- The completion route_event! (`jne r2, r1` orig 0x5f120) is `jeq +1; ja` in ours because
  `if completed` is lowered `switchInt(reserves) -> [0: then, otherwise: else]` and the else llbb
  lands between the then block and its successors. Moving that block in IR fixes the site but the
  whole-function ratio does not improve.

## Ledger
Attempt ids: b7abcf4d (u2), a9e790f4 (u3), e2629982 (u5), 51004c38 (g1), 0e4db368 (g2), 67e6b183 (h1),
2a37b64e (h2), 0087f7c4 (w2), 3942da18 (m1), 51e59bf1 (m2), 2a19bf40 (m3), 271b2a92 (m4).
