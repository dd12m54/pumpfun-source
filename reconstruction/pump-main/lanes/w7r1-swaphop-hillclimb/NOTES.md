# w7r1-swaphop-hillclimb: 0x5b3b0 multi_hop_curve::swap_hop (automated spelling-mutation hill-climb)

Base: origin/main 7e26cbf: 1027/1035 normalized, 293 raw; swap_hop ratio 0.7332, 18,544 B (orig 18,584), 107/107 calls.

## Method
`hillclimb.py` (this dir) applies line-preserving, behaviour-preserving text mutations
(`mutations.py`, `mutations2.py`, `mutations3.py`) to `programs/pump/src/multi_hop_curve_swap.rs`,
builds each candidate with `fastbuild.py` (2 workers, shared build slots), scores it with
`target_metric.py` (fitness = swap_hop ratio) and `score.py` against the main build (any
normalized/raw loss rejects), and climbs greedily: each round tries every remaining mutation on the
current best, accepts the best strict improvement, and keeps only mutations that changed the binary and
stayed within a slack of the parent for the next round. Results are cached by source sha256;
`--prune` skips mutations that were byte-identical to their parent in an earlier trial.
`record.py` writes every trial to the shared ledger (dedupe keys `0x5b3b0-main-7e26cbf-hc-<mutation>[-on-<depth>]-v1`).

Mutation families (all keep every `line!()` immediate: old/new have equal newline counts):
operand order of commutative/pure ops, short-circuit order of side-effect-free conditions,
if/else polarity, `if let` vs `match` (and arm order), let-binding splits/merges, borrow vs copy
(`&post_fill`, `ref`, by value), method vs free fn / UFCS `AsRef`, `checked_*` vs ops,
`?` vs explicit `match` (generated for all 38 `?` sites) and `?` vs `.map_err(|e| e)?`,
`.key()` temporaries bound in lets (generated), whitelist/complete_fill restructurings,
pure statement reorders (seeds / `c` / curve_key / fee_config_len), and sibling-lane findings as
composable seeds.

## Results
| state | ratio | bytes | official |
|---|---:|---:|---|
| main 7e26cbf | 0.7332 | 18,544 | 1027/293 |
| + raw_output adds `match &post_fill {..}` (w7r1-swaphop-frame) | 0.73719 | 18,520 | no losses |
| + no `paid_buyback != 0` guard (w7r1-swaphop-coords) | 0.7385 | 18,520 | no losses |
| + `require_gt!(base,0,BuyZeroAmount)` (w7r1-swaphop-frame) | **0.73878** | 18,528 | 1027/293, no losses |

The three sibling mechanisms compose (each lane's PR has one or two of them); the climb found the
order and that nothing else among ~200 single mutations improves on top (see below).

### Single-mutation landscape on main (round 0, 67 mutations) and on the climb states
- About 75% of spellings are byte-identical (MIR normalizes them): if/else polarity, `match` vs `if let`,
  `?` vs `match`/`map_err` at almost every site, comparison operand order (except below), binding splits
  of `.key()` arguments, `AsRef` UFCS vs method, `try_from` vs `try_into`, struct field init order.
- Small gains: `post_out.checked_add(base_amount)` (+0.0013 on main; subsumed by the match-post_fill form).
- Harmful: binding `a.fee_config.to_account_info()` (0.656), `UserVolumeAccumulator::default()` bound
  (0.638), event keys bound (0.645), whitelist split into two requires/ifs (0.63, +3 calls),
  `post_fill` matched by value (0.59-0.62), `?` -> `match` on token_program_for/tokens_for_quote/
  buy_fee_market_cap (0.69-0.72), checked_sub -> `<` compare (adds 160 B and loses a closure window).
