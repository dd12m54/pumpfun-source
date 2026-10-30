# Lane w7r1-v3buycosts-blockorder: `trade::v3_buy_costs` (original 0x80df8, 2,120 B)

**Result: normalized match.** Official score on origin/main 2b8582135: 1027/276 -> **1028/276**, gain `0x80df8`,
no normalized or raw losses. Target: 2,136 B / ratio 0.920 / 19 differing slots -> **2,120 B / 1.000 / 0**, 17/17 calls.
Unstripped sha256 `60381081bd55975735ce1efeda198dfa50290c98d3949c5acdbb0799cd350c88`.

## Mechanism

The original propagates the errors of **both** `add3` calls through one Err arm. With two separate `?`
operators, rustc emits two Err arms that each store the error payload into the return place, and LLVM
keeps them as two IR blocks (only the tag store gets sunk into the return block). Machine code is the same
after post-RA tail merging, but the extra pre-RA block changes the greedy region-split cost of the
sret pointer, so the candidate kept it in r6 across the late tails while the original spills it
everywhere and reloads it into r3 at each tail. This is the "sret r6/r3 split" residual that earlier
waves read as an MBFI tie.

Source (lines 372-373, same line count, no line-number shift):

```rust
let sums:Result<(u64,u64)>='s:{let first=match add3(quote,protocol_fee,creator_fee){Ok(v)=>v,Err(e)=>break 's Err(e)};
let second=if let Some(p)=post{match add3(p.quote_in,p.fees.protocol_fee,p.fees.creator_fee){Ok(v)=>v,Err(e)=>break 's Err(e)}}else{0};Ok((first,second))}; let (first,second)=sums?;
```

A labeled block with `break 's Err(e)` routes both errors to one `?`. The same merge done with an
immediately-invoked closure (`(||->Result<(u64,u64)>{..})()?`) also fixes the sret allocation (2,112 B,
0.982) but flips the add3#1 Ok check from the original's `jeq r1,2,+1; ja` to `jne r1,2` (the closure
changes the block order). The labeled block keeps the original block order.

Runtime behaviour is unchanged: same calls, same order, same error values.

## How it was found

1. IR capture (`oracle/capture_full.py`), one-function module (`oracle/mkone.py`), llc oracle (`oracle/irx.py`,
   about 0.1 s per run), `-print-machine-bfi` for block frequencies.
2. Reproduced w6r2's both-outer-mayhem: late sret RA matches the original although both panic-block
   frequencies are unchanged, so the front/mid CFG shape (not only the two leaks) enters the cost.
3. `oracle/irmerge.py`: sinking the Err-arm sret stores of chosen error tails into one shared block.
   Merging add3#1 + add3#2 (bb20+bb22) gives 0 differing lines at 2,120 B; merging all five tails gives
   2,104 B. That pointed to the source shape.
4. Source trials g01-g11 (ledger keys `0x80df8-main-a418dd3-<mechanism>-v1`).

| Trial | Spelling | Bytes | ratio | -/+ |
| --- | --- | ---: | ---: | --- |
| base | two `?` | 2,136 | 0.920 | 19/21 |
| g01 | `add3#1.and_then(..add3#2?..)?` | 2,136 | 0.952 | 11/13 |
| g03 | `and_then(match post ..)` | 2,176 | 0.737 | 63/70 |
| g04/g05/g07/g10 | closure `->Result<(u64,u64)>` | 2,112 | 0.982 | 5/4 |
| **g11** | **labeled block + `break 's Err(e)`** | **2,120** | **1.000** | **0/0** |

Front spellings with byte-identical ELF: destructured split tuple, post.map().unwrap_or, tuple pair,
if-let with local bool, `post.map_or(Ok(0), add3)?`. Worse: total_buyback operand swap (2,104 B 0.835),
`post.map(add3).transpose()?` (0.876).

## Lesson for other windows

When a residual is "only register allocation" and the source already has several `?` on the same
Result type in sequence, check whether the original shares one Err arm (labeled block + `break`, or one
`?` over a combined Result). Code after tail merging looks the same, but the pre-RA CFG does not.
