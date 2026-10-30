# w7r1-execute-hillclimb: 0x72810 `sweep::execute` (spelling-mutation hill-climb)

Base: origin/main 2b8582135 (1027/1035 normalized, 276 raw). Target 0x72810: ratio 0.88669,
7880 B (original 7832 B), 39/39 calls.

## Method

`scripts/gen.py` composes `sweep_fees.rs` from choice points (native-check spelling, dispatch shape,
rent helper attribute/body/signature, amount take, zero test); every alternative keeps the line
count, so the `line!()` sites (123, 145) stay put. `scripts/batch.py` builds variants on 2 private
fastbuild work dirs (shared slot locks), and `scripts/trial.py` records target_metric plus the
pre-inline block frequencies of execute (`-print-before=inline` in the scratch build only, then
LLVM 18.1.7 `opt -passes=print<block-freq>`): `f_rent` = rent helper call-site frequency, `f_event`
= `Event::data` site frequency. `scripts/sdiff.py` diffs against the original with registers and/or
stack offsets masked.

## Results

| batch | change | rent freq | calls | bytes | ratio |
|---|---|---:|---:|---:|---:|
| base | `#[inline(always)]` rent helper | - | 39 | 7880 | 0.88669 |
| b1 | plain helper, 15 native spellings that stay `memcmp==0` | 0.0160 | 35 | 7568 | <=0.803 |
| b1-05 | plain helper, `quote_mint.as_ref()==Pubkey::default().as_ref()` | 0.0214 | 39 | 7800 | 0.741 |
| b2 | plain helper, native via plain `quote_is_native(&curve)` | 0.0214 | 39 | 7800 | 0.741 |
| b3-00 | + body `Rent::get()?.minimum_balance(0)` | 0.0214 | 39 | 7824 | 0.768 |
| **b4-01** | + helper takes `a:&SweepFees` | 0.0214 | 39 | 7856 | **0.91723** |

Mechanism (confirms the w6r1-sweep-ir constraint): with `native = memcmp(...)==0` visible at inline
time, BPI's libcall zero heuristic gives the creator/native branch 0.375, so the rent call site is
0.016 of entry (< 2% cold threshold, cost 210 > 45) and the plain helper stays out of line. When the
native test is a call to a plain local `quote_is_native(&BondingCurve)` (MIR does not inline it), the
branch is 0.5 at inline time, the rent site is 0.0214 (>= 2%) while the event site stays 0.0147,
so the CGSCC inliner inlines the already-simplified rent helper (rent region equal to the original),
and the native helper inlines back to the same memcmp (with the always-inline rent helper,
`quote_is_native` is byte-identical to base). Passing `a:&SweepFees` instead of
`(&Program,&Signer,&AccountInfo)` makes the system-program pointer reload from the accounts struct at
the transfer call (original) rather than being hoisted above `Rent::get` and spilled.

Official score b4-01: 1027 normalized / 276 raw, no gains, no losses (sha256 761bbbd9...).

Remaining residual (b4-01): two `jne`/`jeq+ja` polarity flips at the admit result tests, and the
transfer_to_owned argument loads (`base_mint`/`quote_mint` derefs, `decimals`) hoisted into the
predecessor blocks instead of loaded at the join.

Ledger: 0f32d801666d47e1879f3ae5f401db76, a6fe56928cd346559167e0fca79eb6c7, b44f7ec2ee064d5c9643cbb777737079 (+ later rows, lane w7r1-execute-hillclimb).
