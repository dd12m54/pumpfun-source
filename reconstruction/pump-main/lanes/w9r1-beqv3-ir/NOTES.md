# w9r1-beqv3-ir: 0x1489f8 buy_exact_quote_in_v3 (IR-oracle angle)

Outcome: no new source change. The target was already closed when this lane started.
Open PR #2397 (w9r1-beqv3-frame, head c42e23ee4) uses the same fit_owned mechanism as #2377.

Independent rebuild on main 255a0fd2e:

| build | unstripped sha256 | normalized / raw | gains / losses |
| --- | --- | --- | --- |
| main 255a0fd2e | 9467216956a4a1da7ae16aca9d258f8bf39a8475818e6cc086f1ad28e72979c0 | 1031 / 337 | |
| PR #2397 | 6de8bcdcb64b4eae986d0e75535ce163cc5307351f77f68eeb4bd31dddd203ef | 1032 / 337 | +0x1489f8 / none, raw losses none |

Both shas match what the PR claims. The IR-oracle angle (alloca order and lifetime markers for the tail
slots) is moot: the by-value plain helper `fit_owned` already gives `post` helper-scoped lifetime
markers, so StackColoring stops merging `fees` into the 64-byte group.

Ledger: this lane did not record a row. The key 0x1489f8-main-255a0fd-pr2397-independent-verify-v1
was already logged by w9r1-beqv3-hillclimb (attempt 6201634e30b64f8b9ed21a2f5f3857e1) with the same result.
