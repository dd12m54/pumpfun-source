# absm.py cand.so [cand2.so ...]: ratios for swap_hop vs orig: exact(masked like score), noR10 (r10 offsets masked), noJ (also jump offsets), opregs
import sys,os,struct,difflib
H='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w7r1-swaphop-frame/reconstruction/harness'
sys.path.insert(0,H); a=sys.argv[1:]; sys.argv=sys.argv[:1]
import score
from pathlib import Path
W={x['start']:x for x in score.original_windows()}
def toks(raw,mode):
    i=0;r=[]
    while i<len(raw):
        op,regs,off,imm=struct.unpack_from('<BBhi',raw,i); k=16 if op==0x18 else 8
        dst=regs&15; src=regs>>4; cls=op&7
        if op==0x85 or op==0x18: imm=0
        if mode>=1 and cls in (1,2,3) and ((cls==1 and src==10) or (cls in(2,3) and dst==10)): off=0
        if mode>=1 and op==0x07 and imm<0: imm=-1  # add64 rX, -off (frame addr)
        if mode>=2 and cls==5: off=0
        if mode>=3: off=0; imm=0
        r.append((op,dst,src,off,imm)); i+=k
    return r
orig=W[0x5b3b0]['raw']
for p in a:
    pp=Path(p); blob=pp.read_bytes(); cs=score.sections(blob)
    st,n,_=next(f for f in score.candidate_functions(pp) if '8swap_hop17h' in f[2])
    c=score.body(blob,cs,st,n)
    out=[]
    for m in range(4):
        sm=difflib.SequenceMatcher(None,toks(orig,m),toks(c,m),autojunk=False); out.append(f"{sm.ratio():.4f}")
    print(os.path.basename(os.path.dirname(p)),len(c),' '.join(out))
