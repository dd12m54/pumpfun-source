# w7r1-sweep-errors: 0x72810 `sweep::execute` (error-path / branch-structure lane)

Assigned lane name: `w7r1-execute-errors`. A create_v2::execute lane got the same name and
recreated/used the same worktree, branch and cache dir, so this lane works under
`w7r1-sweep-errors` (branch `swarm/w7r1-sweep-errors`, cache
`~/.cache/pumpfun-reconstruction/lanes/w7r1-sweep-errors`). Ledger rows use
`--lane w7r1-execute-errors` and keys `0x72810-main-2b85821-*`.

Base: origin/main 7e26cbf (s6 sweep; trials started on 2b85821, identical programs/pump/src). Baseline build: 1027/1035 normalized, 293 raw. Target: original 7,832 B, 39 direct calls.

| metric | base (s6) | h5p | p6 (PR head) |
|---|---:|---:|---:|
| ratio (target_metric) | 0.88669 | 0.91723 | **0.99479** |
| cand bytes (orig 7832) | 7880 | 7856 | **7832** |
| slots_diff (equal size only) | - | - | **35** |
| direct calls (orig 39) | 39 | 39 | 39 |
| fullmask diff lines (regs, stack offsets, jumps masked; llc oracle) | 64 | 22 | **8** |
| raw diff lines (llc oracle) | 222 | 159 | **10** |
| official normalized / raw | 1027 / 293 | 1027 / 293 | 1027 / 293 |
| gains / losses | - | none / none | none / none |
| unstripped sha256 | 0560a482.. | dfc8eb87.. | 9c53f9167d338c4f16b0fc367f21aab4ac3dbb2f6b91bd895b2c95729e3e1f4e |

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

## p6: transfer through a `pay_owned` wrapper (trade_v3 shape)

The original loads the base/quote mint Box pointers in each predecessor of the transfer call
and dereferences them (`+0x58` AccountInfo, `+0x30` decimals) in the merge *below* the Option
diamond (+0x16d8). Call arguments are evaluated in order, so with `transfer_to_owned(..)` called
directly the derefs come before the recipient clone and the `if native {None} else {Some}`
diamonds. With `#[inline(always)] fn pay_owned(native, base_mint: &InterfaceAccount<Mint>, curve,
destination: AccountInfo, amount, quote_mint: &InterfaceAccount<Mint>, token_program, src, dst,
bump)` (the `trade_v3::pay_owned` body), the caller only evaluates the Box derefs (`&a.base_mint`)
and the wrapper body does `.as_ref()`/`.decimals` after all arguments, so they end up in the
merge as in the original.

The parameter order matters. With `token_program` before `quote_mint` (the trade_v3 order, p1),
the `&a.quote_token_program` gep is evaluated before the quote box load and gets hoisted into
the token path (`bb27.thread`), which re-lays-out the token path (fullmask 308). With
`quote_mint` first (p6), the function is 7,832 B, the same size as the original, with ratio 0.99479.

## Remaining residuals (p6, 10 raw diff lines)
1. Admit branch polarity (first `jeq;ja` vs `jne`, second the other way): IR block order (w4-sweep).
2. Event: `bucket` store (creator reload) scheduled before `amount` (orig after `recipient`).

## Ledger
Attempts recorded with keys `0x72810-main-2b85821-*` (lane w7r1-execute-errors).
