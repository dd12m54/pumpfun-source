# Lane w6r2-buyexactquote-sem (wave 6, round 2)

Target `0x1489f8` `trade::buy_exact_quote` (v3), original 7856 B. Base origin/main a7135a6a6 (1027 normalized / 276 raw):
7872 B, ratio 0.85100 (llc masked 0.9675), 66/66 calls.

**Best (y2): ratio 0.95643, 7864 B, masked 0.9827, 66/66 calls; official 1027 / 276, no gains or losses.**
Ledger attempt `68659d27` (key `0x1489f8-main-a7135a6-y2-v1`).

## Mechanism

1. Block-level diff: after the non-whitelist `tokens_for_quote(curve,net)?` the original loads the payload word `[8]`
   before the tag branch (like the whitelist call) and both error edges tail-merge into one block. Ours loads it in each
   successor. llc oracle (hoist that load): 0.8510 -> 0.8813.
2. Why: LLVM SROA types the TradeFees slice that overlaps the `Err` Box pointer as `ptr`. In the base the `ptrtoint`
   lands at the definition of the MIR-SROA fragment `_539` (inner `net_fees`), InstCombine sinks it to the head of the
   `Ok` block once the empty forwarding block is gone, and that leading `ptrtoint` blocks SimplifyCFG's common-load hoist.
3. Raw-IR oracle (`--emit llvm-ir -C no-prepopulate-passes`, then `opt -O3` reproduces the base byte for byte): LLVM
   SROA pops allocas LIFO, i.e. lowest MIR local first. Splitting `fees` (_68) and the outer `net_fees` (_70) **after**
   `_85` / `_539` / `_525` gives 0.9543 (and fixes the r6/r9 rotation that wave 6 round 1 attributed to the lifetime-only
   error block). Moving only one of them: 0.69.
4. Source lever: make both locals address-taken until LLVM inlining. A plain helper that contains a call is not
   cross-crate-inlinable, so the MIR inliner leaves it alone and LLVM inlines it after the body's first SROA run:
   * `net_quote(curve,&fees,budget)` wraps `net_quote_for_budget(&curve.creator,fees.protocol_fee_bps,fees.creator_fee_bps,budget)`
   * `net_costs(a,&quote_fee,net,&net_fees)` wraps the two identical non-cross `v3_buy_costs(..,net_fees.protocol_fee,net_fees.creator_fee,None)` calls.
   Either alone: 0.6941. Both: 0.95643. Leaf helpers (`fee_bps(&fees)`) are MIR-inlined and change nothing.
   No runtime change: the wrappers forward the same values.

## Residuals (y2)

Prologue lea late (-0x190), `fees` stack-colouring group (-0x160 group in orig), a few spill/reload orders.

## Trials (keys `0x1489f8-main-a7135a6-*-v1`)

| trial | mechanism | bytes | ratio | result |
| --- | --- | ---: | ---: | --- |
| base | a7135a6 | 7872 | 0.8510 | |
| a01/a02 | `q=..?` whole / `let (net,net_fees)=q` | | = base | |
| a03/a04 | `TradeFees{..net_fees}` in tuple | 7768 | 0.7649 | |
| c01 | `ref net_fees` + `*net_fees` | 7856 | 0.7941 | = oracle "net_fees32 split first" |
| c02/c05/c06 | rename / clone / shadow | | = base | |
| e01/e02/e04 | `let mut fees` reassigned in arm | 7768 | 0.6931 | |
| f01-f04 | fn-scope deferred locals for the arm | | = base | CopyProp unifies them |
| h01/h02 | tokens expression inline in the tuple | | = base | |
| h01 (w6r1) | nested inline(always) split | 7864 | 0.7979 | |
| n01/n02 | outer tuple with the whole `(u64,TradeFees)` | 7896 | 0.6957 | |
| s1-s3 | `(fees,)=(..?,)`, late destructure of `split` | | = base | |
| t1-t3 | field-wise rebuilt TradeFees | 7776-7792 | 0.64 | |
| v1/v2 | cross arm reads net_fees bps | 7784 | 0.7261 | |
| w01-w03 | no wrapper / named `quoted?` | | 0.69-0.74 | |
| x1-x3 | leaf `&TradeFees` helpers | | = base | MIR-inlined |
| y1 / y3 | one plain wrapper | 7792 | 0.6941 | |
| **y2** | both plain wrappers | 7864 | **0.95643** | kept |

Oracles: hoist8 0.8813; hoist8 + lifetime.end(_86) removal 0.9343; alloca order k1 (trio first) 0.9161; fees+net_fees last 0.9543.
