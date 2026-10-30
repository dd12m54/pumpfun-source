# w7r1-sweep-errors: 0x72810 `sweep::execute` (error-path / branch-structure lane)

Assigned lane name: `w7r1-execute-errors`. A create_v2::execute lane got the same name and
recreated/used the same worktree, branch and cache dir, so this lane works under
`w7r1-sweep-errors` (branch `swarm/w7r1-sweep-errors`, cache
`~/.cache/pumpfun-reconstruction/lanes/w7r1-sweep-errors`). Ledger rows use
`--lane w7r1-execute-errors` and keys `0x72810-main-2b85821-*`.

Base: origin/main 7e26cbf (s6 sweep; trials started on 2b85821, identical programs/pump/src). Baseline build: 1027/1035 normalized, 293 raw. Target: original 7,832 B, 39 direct calls.

| metric | base (s6) | h5p (this PR) |
|---|---:|---:|
| ratio (target_metric) | 0.88669 | **0.91723** |
| cand bytes (orig 7832) | 7880 | **7856** |
| direct calls (orig 39) | 39 | 39 |
| fullmask diff lines (regs, stack offsets, jumps masked; llc oracle) | 64 | **22** |
| official normalized / raw | 1027 / 293 | 1027 / 293 |
| gains / losses | - | none / none |
| unstripped sha256 | 0560a482.. | dfc8eb87b1eb7ae1a0a48aed4230b3897a1eee81741ccd3833e20170a01b4d73 |

## Mechanism

w6r1-sweep-ir showed the original rent top-up is a normal (not always-inline) helper that the
CGSCC inliner inlined *after* the helper had been simplified on its own, and that this needs the
call site to be warm (pre-inline block frequency at least 2% of entry), while the event call
sites must stay below 2%. In s6 the rent site was 0.01602.

The rent path in the pre-inline IR crosses the creator-only native test
`quote_mint == Pubkey::default()`, a `memcmp(..) == 0`, which the BranchProbabilityInfo zero
heuristic gives 0.375 for "equal". Computing `native` through a plain
`fn is_native(&Pubkey) -> bool` keeps the final code byte-identical (n6 = s6 + is_native is
identical in the window: it is inlined later by the CGSCC inliner), but in the pre-inline IR the
creator-path branch is on a call result, so it gets 0.5. The rent call site rises to 0.02136
(warm), the event block stays at 0.0147 (cold), the shared join clone stays warm (0.0267).

With the site warm, the helper body decides the rent block:
- `let minimum = Rent::get()?.minimum_balance(0); if destination.lamports() < minimum { transfer(..) } else { Ok(()) }`
  (the body of `legacy_native_payments::ensure_rent_exempt`) reproduces the original rent region:
  Rent payload copy before the tag branch, `From(&payload)`, transfer block placed after the
  protocol-native block, Ok path threaded straight to the join.
- As a private (internal) fn, ArgPromotion promotes `&Program<System>` to its loaded pointer, so
  `system_program` is loaded before `Rent::get` and spilled, which perturbs register allocation
  for the whole function (ratio 0.768). As `pub fn` (hidden linkage, no ArgPromotion) the load
  stays in the transfer block as in the original (+0x14f0). The helper is fully inlined and its
  symbol does not appear in the binary.

## Remaining residuals (h5p, fullmask 22)
1. Admit branch polarity (first `jeq;ja` vs `jne`, second the other way): IR block order (w4-sweep).
2. Join loads: we load `quote_token_program`/`quote_mint` fields ([+0x10] then [+0x58]) before
   the clone sequence; the original loads them after.
3. Event: `bucket` store scheduled before `amount` (orig after `recipient`).

## Ledger
Attempts recorded with keys `0x72810-main-2b85821-*` (lane w7r1-execute-errors).
