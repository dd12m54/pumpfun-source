# Lane w6r1-layout-order (wave 6, round 1): function order and placement for raw

Base: origin/main 099b0dd (1027 normalized / 276 raw; 8 unmatched windows). Tools in `tools/` are
small scripts on top of layout-order-census's `census.py`/`refine.py`/`fastmodel.py` and
w3-raw-layout's `m13.py` (copied under `$OUT/tools`, `UNMATCHED_NAMES` cut to the 8 open windows).
The model reproduces the official raw set (276) exactly.

## Why the 751 normalized-only windows are not raw (model census on 099b0dd)

| class | windows | blocker |
| --- | ---: | --- |
| data lddw (.rodata / .data.rel.ro pointer) | 601 | section bases move with `.text` size: cand 0x1b5a10 vs orig 0x1b58d0 (+320 B) |
| call-only | 150 | call distance crosses a size delta, a misplaced handler, or U/D hash order |

`.text` +320 = unmatched size deltas (-192: create_v2 +8, admin_cto +16, swap_hop -256, sweep +48,
v3_buy_costs +16, buy_handler +32, buy_exact_quote_in +32, v3 buy_exact_quote -88) + one ours-only unit,
the 512-B `v2_native_payments::ensure_rent_exempt` black_box wrapper (+512).

What order alone can do at today's sizes (`scen3.py`, `scen5.py`, `movebrute.py`, `extrapos.py`):
- L (local) order is already the original's except the five v2/v3 handler bodies (at their module
  position, about 53 KB away from the original's #[program] position) and the two `pay_out_native`
  instances (symbol-hash order). Moving them: +0 raw now.
- Moving any one of the 8 unmatched functions or the extra unit to any L position: max 276, +0.
- Full original order at today's sizes: 293 (+3 from U hash order, +14 from D hash order). Both are
  symbol-hash order of generic instances, fixed by crate metadata, not reachable from source.

So official raw cannot rise through order changes until the unmatched windows reach their sizes.

## Kept: drop the ensure_rent_exempt wrapper (`857b6b91`)

The matched twin `ensure_rent_exempt_matched` (window 0x3b598) already keeps `_size` live through
DeadArgElim with its `if _size != 0 { unreachable_unchecked() }` hint, so the callers (buy_handler,
buy_exact_quote_in_handler, sell_v2) can call it directly. The wrapper (`size == usize::MAX` arm +
`black_box(size).wrapping_mul(0)`) is deleted and the twin renamed to `ensure_rent_exempt`.

| metric | main 099b0dd | this lane |
| --- | ---: | ---: |
| official normalized / raw | 1027 / 276 | 1027 / 276, 0 gains, 0 losses |
| 8 unmatched windows (bytes, ratio) | | all identical |
| ours-only units | 1 (512 B) | 0 |
| `.text` size vs original | +320 | -192 (= sum of unmatched deltas) |
| model raw once the 8 match in size, our order | 276 | **429** |
| same, handlers at #[program] position | 326 | **653** |
| model raw, full original order, sizes fixed | 1022 | 1023 |

Before this change, fixing all 8 unmatched windows would still have left `.text` 512 B long and every
data window non-raw. Unstripped sha256 8e56a1bcc1f85140...
