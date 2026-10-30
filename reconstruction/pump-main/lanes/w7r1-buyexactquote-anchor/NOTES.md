# w7r1-buyexactquote-anchor

Target `0x1489f8` `pump_recovered::trade::buy_exact_quote` (7856 B). Angle: Anchor/account-access shape.

## Result: target already matched by another lane; no anchor-angle work needed

- origin/main 5bd9e1b53 built alone: 1031 / 296 (vs baseline-main-d2cb88d, no losses); target 0.9895, 10 stack-offset slots.
- Open PR #2377 (`swarm/w7r1-buyexactquote-hillclimb`, head 7cfa6bf07: `Some(post)=>fit_owned(.., post by value, ..)`)
  merged onto 5bd9e1b53: **1032 / 296**, gain `0x1489f8` (ratio 1.0, slots_diff 0, 66/66 calls), no losses, no raw losses.
  unstripped sha256 `ac19f50f8ae5f90bb976ac071b7422231e1b17da5f1260d4d91f054388ae9d2c`.
- The residual on main was StackColoring only (block order, instruction count and account-access shape already
  matched), so the Anchor account-load / CPI / emit angle had nothing left to change.
- `0x1489f8` is not raw: the candidate sits at 0x85f80 vs 0x1489f8 in the original, so its call displacements
  depend on global function layout, not on this function's source.

Ledger: `0x1489f8-main-5bd9e1b-verify-pr2377-on-main-v1` (attempt 1bf47281fce045ba85c9a682735ead2e).
Remaining unmatched after #2377: 0x1e7c0 create_v2::execute, 0x22a10 admin_cto::execute, 0x5b3b0 swap_hop.
