# w7r1-sweep-anchor: 0x72810 `sweep::execute` (Anchor account-access angle)

Assigned lane name: `w7r1-execute-anchor`. Another agent uses the same lane name (its own
target) and recreated the worktree `worktrees/w7r1-execute-anchor` mid-run, so this lane works
under `w7r1-sweep-anchor` (branch `swarm/w7r1-sweep-anchor`, cache
`~/.cache/pumpfun-reconstruction/lanes/w7r1-sweep-anchor`). Ledger rows use
`--lane w7r1-execute-anchor` and keys `0x72810-main-2b85821-*` / `0x72810-main-7e26cbf-*`.

Base: origin/main 7e26cbf (1027 normalized / 293 raw). Target 7,832 B, 39 calls.

| metric | base (s6 on main) | t13 | t16 | t30 (PR head) |
|---|---|---|---|---|
| ratio (target_metric) | 0.88669 | 0.94951 | 0.95159 | **0.99687** (slots_diff 30) |
| struct ratio (regs/stack masked) | 0.9615 | 0.9693 | 0.9714 | |
| cand bytes (orig 7832) | 7880 | 7856 | 7856 | **7832** |
| direct calls (orig 39) | 39 | 39 | 39 | 39 |
| official normalized / raw | 1027 / 293 | 1027 / 293 | 1027 / 293 | 1027 / 293 |
| gains / losses | - | none / none | none / none | none / none |
| unstripped sha256 | 0560a482.. | cdef3b75.. | 14de8a21.. | 17774048.. |

## Mechanism: the payout call goes through an inlined wrapper that takes the Anchor accounts by reference

At the join before the out-of-line `transfer_to_owned`, the original loads the `base_mint` Box
pointer in each predecessor (spilled to -0x320) and the `quote_mint` Box pointer in each predecessor
(r5). After the `if native {None} else {Some(..)}` Option diamond it then loads `[base+0x58]` (the
`&AccountInfo` inside `InterfaceAccount`), `[quote+0x30]` (decimals) and `[quote+0x58]`. Main
derefs them in the predecessors because `a.base_mint.as_ref().as_ref()` and
`a.quote_mint.decimals` are evaluated as call arguments before the Options.

The original shape needs `&InterfaceAccount<Mint>` handed to a small (MIR-inlined) helper whose body
does `base_mint.as_ref()`, `quote_mint.decimals` and `quote_mint.as_ref()` *after* all arguments,
including the Options, have been evaluated:

```rust
pay_fee(native,&a.base_mint,a.bonding_curve.as_ref(),a.recipient.to_account_info(),amount,
        &a.quote_mint, if native{None}else{Some(..)}, if native{None}else{Some(..)},
        &a.quote_token_program, ctx.bumps.bonding_curve)?;
```

The position of `&a.quote_token_program` is the second key. With it in its `transfer_to_owned`
position (t01/t04, 0.7488/0.7356), the pre-inline SimplifyCFG hoists the common `gep a,32` from
the protocol-native path and the token path into the protocol memcmp block. JumpThreading then
clones it into `bb26.thread`, which becomes the token block's better layout predecessor, so
MachineBlockPlacement chains memcmp_p into the protocol-native clone. IR oracle (llc on the t04
module with the two GEP phis folded) gives 0.9371. In source, passing the token program after the
Options moves its GEP past the Option diamond, where the original computes it (`mov r1,r9; add
r1,0x20` at +0x1728). That gives t12 (base only by ref) 0.93708 and t13 (both by ref) 0.94951.

The wrapper's attribute does not matter: `#[inline(always)]`, `#[inline]` and none are
byte-identical, because it is MIR-inlined.

## Trials (ledger)
t01-t03 both by ref, tp in place (0.7488, attribute-independent); t04 base only (0.7356); t05 quote
only (0.8716, struct +); t06 `&*a.base_mint` / t07 `.as_ref()` spellings = t01; t08 wrapper taking
`&SweepFees` (0.6973); t09 `&Box<..>` param / t11 base_mint last (0.7981); t12 base ref + tp last
(0.93708); t13 both ref + tp last (**0.94951**); t14 quote ref + tp last = t05; t15 direct + tp last = base.

## t16: event bucket store order (`match creator as u32`)

In the original, the bucket byte is stored after the timestamp (`ldxdw r1,[r10-0x318]; stxb
[r10-0x1b0],r1`). On main it is stored first. The vault/validate dispatch `match creator as u8`
emits `zext i1 %creator to i8` in a block that dominates everything after it, so GVN CSEs the
event's `bucket: if creator{1}else{0}` (and the msg's `creator as u8`) into it. The event block then
stores a cross-block vreg, and the scheduler puts that store first. IR oracle: an in-block zext moves
the store after the timestamp (0.9495 -> 0.9516). In source, a different-width scrutinee
(`as u32`; `as u64` is byte-identical) gives the same MIR switch with no CSE partner, so the event
block gets its own zext: **0.95159**, with no losses.

## t30: the rent helper is a plain function that the CGSCC inliner inlines (0.9516 -> 0.99687, 7832 B)

This follows w6r1's conclusion that the original rent helper was a normal function, CGSCC-inlined
after its own simplification. Getting there took three steps:

1. **Warm call site.** The plain helper (t17) stayed out of line: its pre-inline call-site frequency
   was 0.01602 of entry, below 2%, so it got the cold threshold of 45 (cost 210). The native check
   `quote_mint == Pubkey::default()` is a memcmp `== 0` branch, and BPI's zero heuristic gives it
   0.375. Moving that check into a plain `fn is_native_quote(&BondingCurve) -> bool` changes it.
   The fn is not MIR-inlined, MIR JumpThreading still duplicates it per bucket, and LLVM inlines both
   copies. Pre-inline, the branch is then on a call result (0.5), which puts the rent site at
   0.0214-0.0244 (>= 2%), so the helper is inlined (39 calls). On its own, with the inline(always)
   rent helper (t23), this change is byte-identical to t16. (t19/t21 also moved the vault check into
   a nested helper. That raised the rent site too, but broke the layout.)
2. **Rent as a temporary.** With `let rent = Rent::get()?; rent.minimum_balance(0)` (t22, 0.8067),
   `rent`'s lifetime.end sits in the Ok/transfer merge block, which blocks JumpThreading of the Ok edge.
   `let minimum = Rent::get()?.minimum_balance(0);` (t27; the same body as
   `legacy_native_payments::ensure_rent_exempt`) threads Ok straight to the clone and places the
   transfer block as in the original. Struct ratio 0.9833, but registers still differed (0.8161).
3. **No argument promotion.** The CGSCC ArgumentPromotion turned `system_program: &Program` into a
   by-value pointer. The caller then loaded `[a+0x30]` before Rent::get and spilled it, and register
   assignment shifted everywhere. With `fn ensure_rent_exempt(a: &SweepFees, destination: &AccountInfo)`
   reading `a.system_program` / `&a.payer` inside, `a` escapes into `transfer`, so nothing is
   promoted: **0.99687, 7832 B (the original size), slots_diff 30**, 1027/293 with no losses.
   t31 (`ensure_rent_exempt(a)`, which reads the recipient inside as well) gives 0.88159.
