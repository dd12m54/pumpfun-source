# w7r1-swaphop-coords: `0x5b3b0` `multi_hop_curve::swap_hop` (coordinate archaeology)

Base: origin/main `7e26cbf` (1027 normalized / 293 raw vs the d2cb88d baseline), swap_hop
ratio 0.7332, 18,544 B (orig 18,584 B), 107/107 calls, segdist (w4 `seg.py`) 522/680.

## 1. Source coordinates: all already exact

`tools/filesites.py` lists every `Source{file,line}` site that references
`programs/pump/src/multi_hop_curve_swap.rs` in every original window and every candidate
function. Original 20 sites, candidate 20, same line multiset, same functions:

| line | function | | line | function |
|---:|---|---|---:|---|
| 208, 214, 218, 262 | `execute` | | 571 | swap_hop closure#0 |
| 259 | `execute` closure | | 589 | closure#1 |
| 295 | `complete_fill` | | 624 | closure#2 |
| 359 | `token_program_for` | | 673 | closure#3 |
| 369 | `require_ata` | | 692 | closure#4 |
| 484, 546, 686, 599, 590 | `swap_hop` (inline sites, in this layout order) | | 736 / 744 | closure#5 / #6 |

The closure def order (text order 571 < 589 < 624 < 673 < 692 < 736 < 744) matches. The window's
only panic `Location` is alloc `string.rs:2559:14` (the inlined `to_string`), present in both.
Error codes (0x1784, 0x1785), the filename length (41) and the `with_values` monomorph
(both 590 and 686 call the same `with_values::<u64,_>` at 0x340) match. The coordinates of the
remaining residual are therefore layout, not lines: the only site whose *position* differs is
the closure-736 call block (ours before `complete_fill`, orig after the `complete_fill` Some tail).

## 2. Control-flow coordinates (new tools)

`tools/pat.py orig.txt 0x5b3b0 cand.txt <cand_start>` classifies every conditional branch:

- **A** `jcc T` + fallthrough: at ISel the fallthrough block was the IR-next block (BPF
  `analyzeBranch` fails, so MBP keeps it glued);
- **B** `jcc +1; ja F`: at ISel neither successor was IR-next (or the next block was an error
  block later tail-merged into a bare `ja`); MBP then chose the successor.

The A/B sequence, aligned on call indices, is equal to the original everywhere except a handful of
spots (base: c28, c31, c47-c66, c70, c93). `tools/chains.py` splits a region into fallthrough
chains (cut after `ja`/`exit`) labelled with calls, error lines and branch targets, which shows
MBP's chain order directly. `tools/calllines.py` prints the two 107-call sequences with each
callee's coordinate lines (closure lines identify which `ok_or_else` a call is).

## 3. Results

| trial | change | bytes | ratio | segdist | official |
|---|---|---:|---:|---:|---|
| base | origin/main 7e26cbf | 18,544 | 0.7332 | 522/680 | 1027/293 |
| c1 | `if !buy { amount } else { post_fee_amount(..)? }` | = base (byte-identical) | | | |
| c2 | `match buy { false => amount, true => .. }` | = base | | | |
| **b1** | `else if paid_buyback != 0 { transfer_buyback_out(..)? }` -> `else { transfer_buyback_out(..)? }` | **18,544** | **0.73539** | **515/673** | 1027/293, 0 losses |

### b1 mechanism
Control-flow spot c70: the original goes from the buyback native test (0x2f40 `jeq native → 0x3788`)
straight into the `mhc_transfer_buyback_out` argument setup; there is no `paid_buyback != 0` test
(ours had `jeq r7, 0` at 0x2f18). `mhc_transfer_buyback_out` already starts with
`if amount==0 {return Ok(());}`, so the guard in swap_hop is redundant and dropping it is
behaviour-identical (same mechanism as w6r1-swaphop-ir's `if last` for `transfer_base_out`).
Size is unchanged (18,544 B), so raw 0xa868 stays matched.

Ledger ids: census 20f42d0f, c1 886786e5, c2 946528be, b1 55786c05.
