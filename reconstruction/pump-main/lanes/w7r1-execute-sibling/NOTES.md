# w7r1-execute-sibling: 0x72810 `sweep::execute` (sibling-transplant lane)

Base: PR #2298 head d11716091 (w7r1-execute-regsched: `pay_owned` wrapper taking the accounts
struct, sweep 0.8867 -> 0.9495), itself on origin/main 2b85821 (1027 normalized / 276 raw).

| metric | main 2b85821 | #2298 head | this lane (r5) |
|---|---|---|---|
| ratio (target_metric) | 0.88669 | 0.94951 | **0.99479** |
| bytes (orig 7832) | 7880 | 7856 | **7832** |
| slots_diff | - | - | 35 |
| calls (orig 37+2) | 37+2 | 37+2 | 37+2 |
| full-mask diff lines (regs+stack masked) | 64 | 50 | 8 |
| official normalized / raw | 1027 / 276 | 1027 / 276 | 1027 / 276 |
| gains / losses | - | none | none (raw 0xa868 kept) |
| unstripped sha256 | ec660de7.. | | 279944c5c94b56d7df394e3ce603a32ce7dc51d8329d7ca9cc1a61213d296519 |

## Mechanism (two sibling transplants)

1. **Why the plain rent helper was never inlined.** LLVM 18 `InlineCostCallAnalyzer::updateThreshold`
   calls `DisallowAllBonuses()` on a cold call site, which also drops the LastCallToStaticBonus.
   So a sole-call local helper is inlined only if its call site is at least 2% of entry
   (w6r1-sweep-ir measured 0.01602). Replaying `opt -passes='cgscc(inline)'` on the
   `-print-before=inline -print-module-scope` dump reproduces the remark exactly
   (`scripts/wprobe.py` adds branch weights to one branch and reports the decisions). Making only
   the creator-path native test 50/50 inlines the rent helper (cost -14790) while Event::data,
   the event clone, from_iter and exchange_malloc stay out of line, as in the original.
2. **Native test as a sibling helper** `quote_is_native(curve:&BondingCurve)->bool` (verbatim from
   trade_v3.rs). Before the inliner runs, the creator-path native branch is a branch on a call
   result. The zero heuristic (memcmp==0 gets 0.375) does not apply, so the branch is 0.5. The
   inliner updates the caller's BFI incrementally, so the earlier inline of this helper does not
   bring the 0.375 back. The rent site goes to 0.02136 (warm), and the plain helper with the
   legacy_native_payments body (`Rent::get()?.minimum_balance(0)`) is CGSCC-inlined after its
   own simplification. That is the original rent region, payload slice and frame (frameoracle:
   every alloca at its original offset).
3. **Rent helper takes the accounts struct** `ensure_rent_exempt(a:&SweepFees,destination:&AccountInfo)`.
   With `system_program:&Program`, ArgumentPromotion turns the argument into the loaded info
   pointer. The load then happens at the call site, before Rent::get, and that swaps
   r6/r9 for the whole function (ratio 0.814). `&a.payer` escapes into transfer, so `a`
   cannot be promoted, and the system_program/payer loads stay at the transfer site
   (`ldxdw r2,[r9+0x30]; mov r3,r9`) as in the original. Taking only `a`, with the recipient
   read inside, is worse (0.8795).

## Residuals at r5 (full-mask diff 8 lines)
- Admit branch polarity (+0xeb0, +0xf98): original `jeq r1,2,+1; ja err` then `jne r1,2,err`.
  The ledger has this as IR block order (w4-sweep s6a oracle).
- Event bucket byte (+0x1910): the original reloads the spilled `creator` (`ldxdw r1,[r10-0x318]; stxb [r10-0x1b0],r1`).
  Ours keeps a 0/1 value in r0 and stores it earlier.

## Ledger ids
8f8425ae (plain rent cost analysis), 9aa75942 (t2), 9b602cd5 (t3), b47ae727 (pay_owned verbatim),
9a56e1e6 (r2), 426cb6e7 (r3/r4), 6206fdb5 (r6), 86cfdc23 (r5).

Scripts (lane cache ~/.cache/pumpfun-reconstruction/lanes/w7r1-execute-sibling/scripts): trial.sh,
bt.sh (pre-inline BFI listing), bpath.py (block freq + terminators), wprobe.py (branch-weight inline probe),
fmso.py (full-mask / stack-mask / no-mask diff vs original).
