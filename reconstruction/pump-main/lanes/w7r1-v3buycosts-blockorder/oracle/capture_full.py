#!/usr/bin/env python3
"""Lane-local capture: build a scratch crate copy with --emit llvm-ir. Diagnostic only."""
import sys, json, shutil
from pathlib import Path
T=Path('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w7r1-v3buycosts-blockorder/reconstruction/harness')
sys.path.insert(0,str(T)); import fastbuild
src,work,out=map(Path,sys.argv[1:4]); extra=sys.argv[4:]
real=fastbuild.run_compiler
def hook(cmd,*a,**k):
    if isinstance(cmd,list) and len(cmd)>1 and str(cmd[0]).endswith('/cargo') and cmd[1]=='build':
        cmd=cmd[:]; cmd[1]='rustc'; cmd+=['--lib','--','--emit=link,llvm-ir']+extra
    return real(cmd,*a,**k)
fastbuild.run_compiler=hook
r=fastbuild.build(src,work,out,recipe='identity')
if r.get('ok'):
    for p in work.glob('target-identity/sbpf-solana-solana/release/deps/pump_recovered*.ll'):
        shutil.copy2(p,out/'pump_recovered.ll')
print(json.dumps(r,indent=1))
