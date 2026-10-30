# Lane w9r1-admincto-relocs (wave 9, round 1)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`). Angle: pair every `lddw` of the
candidate with the original's and remove the 2 extra constant-address loads (86 vs 84 data relocations).
Base: origin/main 255a0fd2e (1031/1035 normalized, 337 raw). Builds: `~/.cache/pumpfun-reconstruction/lanes/w9r1-admincto-relocs/`.

## lddw census (attempt f9db0fcc)

All `lddw` of both functions, the original's data addresses rebased by -0x60 (its `.rodata` starts 0x60 later because
`.text` is 96 B longer), each target classified by section and content:

- Every `.rodata` target (panic/error `Location` file strings, `&PumpError` constants, seeds, program ids, messages)
  and every other `.data.rel.ro` target pairs 1:1.
- The only multiset difference: `.data.rel.ro+0x128`, the `String as core::fmt::Write` vtable, 9 in the original,
  11 in ours. It is loaded by every inlined `<T as ToString>::to_string` (anchor's `error!` builds `error_msg` with it).
- Per `PumpError` site: the original calls the outlined `to_string` at `InvalidCreator` (312) and
  `CreatorShouldNotBeZero` (307), and main inlines both. That is w6r3-layout-rodata's finding
  (PR #2370), reproduced here. Both sites sit at 2.2% block frequency of `validate`'s entry, just above the 2%
  cold-call-site cut that drops the inline threshold from 325 to 45 (`to_string` costs 130).

## Change

1. PR #2370's change: the line-296 `HolderRewardDisabled` check moves inside the `if holder` arm. 307/312 go cold,
   `to_string` stays outlined there, and the lddw multiset equals the original's (86 = 86, String vtable 9 = 9).
   On its own this costs ratio: 0.37637 -> 0.32392, 26,928 B. The original is 472 B larger without the two
   inlined bodies.
2. New in this lane: `validate` takes `mut new` and both consumers use `new.take()` (298 `new.take().is_some()`,
   306 `let Some(t)=new.take() else`). The caller passes a copy of `new` (it is used again for `sharing_update`).
   While nothing wrote that copy, memcpyopt forwarded every read to execute's `readonly` `new` argument.
   The original keeps a local copy of `new` (it loads all 33 bytes at entry, before the mayhem branch, and reloads them
   from stack slots later). Writing the copy through `take()` keeps a local copy in ours too. Behaviour is unchanged,
   because `new` is `validate`'s own by-value parameter.

| metric | main 255a0fd | t01 (#2370 only) | t04 (this PR) | original |
| --- | ---: | ---: | ---: | ---: |
| admin_cto bytes | 27,344 | 26,928 | 27,144 | 27,400 |
| win.py ratio | 0.37637 | 0.32392 | **0.39061** | 1 |
| calls (internal+external) | 154+3 | 154+3 | 154+3 | 154+3 |
| lddw total / String vtable | 88 / 11 | 86 / 9 | **86 / 9** | 86 / 9 |
| lddw target multiset | 2 extra | equal | **equal** | |
| official normalized / raw | 1031 / 337 | 1031 / 337 | 1031 / 337 | |
| gains / losses (norm, raw) | | 0 / 0 | 0 / 0 | |

Opcode bag of t04 against the original: stack reloads -46, stack stores -13. The remaining ~256 B are mostly spill
and reload traffic.

## Attempts (ledger, approach `lddw-reloc-pairing`)

| trial | mechanism | result |
| --- | --- | --- |
| census | lddw pairing | only diff: String vtable 9 vs 11 (307/312 inlined to_string) |
| t01 | #2370 rebuilt on 255a0fd | 26,928 B, 0.32392, lddw equal |
| t02 | sharing_update computed before validate | rejected: validate stops being inlined (119 calls) |
| t03 | t01 + `mut new`, 306 `new.take()` | 27,104 B, 0.38940 |
| t04 | t03 + 298 `new.take().is_some()` | **27,144 B, 0.39061 (kept)** |
| t05 | t01 + take only at 298 | 27,120 B, 0.38115 |
