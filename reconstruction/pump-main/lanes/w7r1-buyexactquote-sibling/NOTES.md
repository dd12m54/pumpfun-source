# Lane w7r1-buyexactquote-sibling (wave 7, round 1)

Target `0x1489f8` `pump_recovered::trade::buy_exact_quote` (7856 B). Base origin/main fb25fce02
(1030 normalized / 295 raw; target 7856 B, ratio 0.9895, 10 stack-offset slots).

## Finding

The 10-slot residual is StackColoring of `fees10` (outer `fees`) and `_301` (v3_execute_buy result).
llc oracle (frameoracle `--edit`): deleting only `post23`'s lifetime.end on the fit_post_complete Ok
edge gives masked-exact 1.00000; deleting the Err-edge end changes nothing. So in the original the
`PostComplete` passed as `&mut` to fit_post_complete stays live past the merge, through
v3_execute_buy, on the Ok path: it has body scope, not match-arm scope.

## Source step (s1)

`let mut fitted;` declared at body scope (on the line of the outer `let (amount,quote,fees,post,costs)=`,
so no line moves), and the arm `Some(post)=>{fitted=post;fit_post_complete(..,&mut fitted,..)?}`.
Stack colouring is now as in the original (fees10 at 0x160, _301 at 0x90). Remaining: the copy of
the estimate payload into `fitted` emits the 48-byte memcpy before the two 8-byte header stores
(original: header stores first). Ratio 0.9895 -> 0.9958, 7856 B, 1030/295, no losses.
Same values everywhere; no runtime change.

## Trials (ledger keys `0x1489f8-main-fb25fce-*-v1`)

| trial | mechanism | bytes | ratio | result |
| --- | --- | ---: | ---: | --- |
| oracle | drop post23 lifetime.end on fit Ok edge | 7856 | 1.0000 (masked) | analysis |
| s1 | body-scope `let mut fitted;` before outer let; `fitted=post` in arm | 7856 | **0.9958** | kept |
| s2 | same, declared at function start | 7856 | 0.7521 | |
| s3 | `{fitted=post;&mut fitted}` as the fit argument | 7856 | 0.9958 (14 slots) | |
| s6 | body-scope Option `fitted=estimate; match &mut fitted` | 7816 | 0.4929 | |
| s7 | `Some(ref post)=>{fitted=*post;..}` | 7864 | 0.9753 | |
| s13 | `match &estimate{Some(post)=>{fitted=*post;..}}` | 7864 | 0.9753 | |
