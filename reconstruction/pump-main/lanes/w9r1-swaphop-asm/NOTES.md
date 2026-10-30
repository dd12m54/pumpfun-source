# w9r1-swaphop-asm: 0x5b3b0 multi_hop_curve::swap_hop (assembly-first)

Base: origin/main 255a0fd2e (fresh build: 1031/1035 normalized, 337 raw). swap_hop 18,544 B (orig 18,584), ratio 0.7332, calls 107/1.

## Result 1: swap_hop takes `ctx: &Context<MultiHopCurve>` (ledger 33eed5a8)

Assembly evidence: the original's r2 is the accounts struct and r3 the event-authority bump, but
every field of `a` is reloaded after calls (w7 lanes: `a` is not `noalias` in the original).
An a-derived capture is nowhere visible in the call arguments (every a-derived pointer argument is
the same in both builds), so the missing noalias has to come from the parameter itself.

Mechanism: `swap_hop(ctx: &Context<'_,'_,'info,'info,MultiHopCurve<'info>>, h, ..)` with
`let a = &*ctx.accounts; let event_bump = ctx.bumps.event_authority;` in the body. `ctx` is
only loaded from, so LLVM's ArgumentPromotion (internal function, single caller) replaces it with
the two loaded values `(accounts ptr, bump)`: exactly the original's r2/r3. The promoted accounts
pointer was loaded from memory, so it carries no `noalias`, and a's fields are reloaded after every
call. This reproduces the w7 pre-opt "drop noalias on a" oracle byte for byte.

| | main 255a0fd2e | ctx1 |
|---|---:|---:|
| swap_hop ratio | 0.7332 | **0.83042** |
| bytes (orig 18,584) | 18,544 | 18,600 |
| calls | 107/1 | 107/1 |
| normalized / raw | 1031 / 337 | 1031 / 337, no losses |
