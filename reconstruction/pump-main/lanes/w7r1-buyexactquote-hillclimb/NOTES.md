# Lane w7r1-buyexactquote-hillclimb (wave 7, round 1)

Target `0x1489f8` `pump_recovered::trade::buy_exact_quote` (v3, 7856 B). Base origin/main fb25fce02
(fresh build: 1030 normalized / 295 raw; target 7856 B, ratio 0.9895, 10 stack-offset slots: the
`fees10` / `_301` StackColoring residual described in `lanes/w6r2-buyexactquote-sem/NOTES.md`).

**Result: normalized match. 1031 normalized / 295 raw, gains `0x1489f8`, no normalized or raw losses
(vs the fresh fb25fce02 build and vs baseline-main-d2cb88d). unstripped sha256
`f8c310ff04f0e671f4f76ba69ba1a36535977f2aa05a8ac41fdb30b2f95d3751`.**

## Method

`hc.py` + `muts.py`: a spelling-mutation generator. Each mutation is a set of exact text
replacements inside `buy_exact_quote_body` (old/new keep the same newline count, so no `line!()`
immediate moves) plus optional plain helpers appended at the end of `trade_v3.rs`. The driver copies
the crate under the lane cache, builds with `fastbuild.py` (2 concurrent builds, shared slots),
scores with `target_metric.py` and records every trial in the ledger (`0x1489f8-main-fb25fce-hc-*-v1`).
Round 1 had 29 mutations around the residual (fit call, estimate, slippage `base_out`, execute/emit tail,
cross-arm result); the batch was stopped after the 4th build because `fitv` already matched.

| trial | mutation | bytes | ratio | slots |
| --- | --- | ---: | ---: | ---: |
| base | r6 (main) | 7856 | 0.9895 | 10 |
| fitf | fit via helper taking `&curve_fees`, `&mut post` | 7856 | 0.9895 | 10 |
| fitfv | fit via helper taking `curve_fees` by value, `&mut post` | 7856 | 0.9895 | 10 |
| **fitv** | `Some(post)=>fit_owned(.., post, ..)`: plain helper takes `post` by value | 7856 | **1.0** | **0** |
| fitvv | helper taking both `curve_fees` and `post` by value | 7856 | 1.0 | 0 |

## Mechanism

The residual was StackColoring: `fees10` (the `TradeFees` that `v3_emit_buy` borrows) was merged into the
64-byte group (`formatter.i`, `formatter.i184`, `post23`) because its interval did not overlap `post23`,
the `Some(mut post)` binding around `fit_post_complete`. With `Some(post)=>fit_owned(..,post,..)` and a
plain (non-`#[inline]`, non-leaf, so not MIR-inlined) helper `fn fit_owned(.., mut post: PostComplete, ..)`
that calls `fit_post_complete(.., &mut post, ..)`, the match binding is a by-value move: it becomes SSA in
MIR (CopyProp drops its StorageLive/Dead), and the address-taken `post` alloca now belongs to the helper,
whose lifetime markers the LLVM inliner places at the call site. That is the same "plain helper taking a
value by value" mechanism wave 4 used for sell_v3 and wave 6 used for `emit_exact_quote`. The resulting
lifetimes give the original grouping: `fees10` lands in the 0x160 group and the `v3_execute_buy` result
back at 0x90. Both paths compute the same values (the helper just forwards); no runtime change.
Taking only `curve_fees` by value or by reference (fitf/fitfv) changes nothing, so the lever is `post`.
