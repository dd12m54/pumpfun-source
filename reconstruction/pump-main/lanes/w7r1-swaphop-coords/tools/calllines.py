# calllines.py <harness> <cand.so> [symre]: call sequence with callee coordinate lines, orig vs cand
import sys,struct,re,difflib
H=sys.argv[1]; sys.path.insert(0,H); cand=sys.argv[2]; symre=sys.argv[3] if len(sys.argv)>3 else r'8swap_hop17h'; sys.argv=sys.argv[:1]
import coords, score
from pathlib import Path
W={x['start']:x for x in coords.original_windows()}
def calls(raw,base):
    i=0;r=[]
    while i<len(raw):
        op=raw[i]; k=16 if op==0x18 else 8
        if op==0x85 and (raw[i+1]>>4)==1:
            imm=struct.unpack_from('<i',raw,i+4)[0]; r.append((i,base+i+8+imm*8))
        i+=k
    return r
o=W[0x5b3b0]; oc=calls(o['raw'],0x5b3b0)
def olines(t):
    if t in W:
        try: return [s['line'] for s in coords.orig_sites(t)]
        except Exception: return '?'
    return None
CP=Path(cand); funcs=score.candidate_functions(CP); blob=CP.read_bytes(); cs=score.sections(blob)
fs={s:(n,nm) for s,n,nm in funcs}
st,n,nm=next(f for f in funcs if re.search(symre,f[2]))
cc=calls(score.body(blob,cs,st,n),st)
def clines(t):
    try:
        f=fs[t]; raw=score.body(blob,cs,t,f[0]); return [s['line'] for s in coords.sites(blob,cs,t,raw)]
    except Exception as e: return '?'
def short(nm):
    nm=re.sub(r'17h[0-9a-f]{16}E$','',nm); return nm[-60:]
ol=[(off,hex(t),W[t]['bytes'] if t in W else '?',olines(t)) for off,t in oc]
cl=[(off,short(fs[t][1]) if t in fs else hex(t),fs[t][0] if t in fs else '?',clines(t)) for off,t in cc]
for i in range(max(len(ol),len(cl))):
    a=ol[i] if i<len(ol) else ''; b=cl[i] if i<len(cl) else ''
    print(f'{i:3d} {a[0]:#7x} {a[1]:>9} {a[2]!s:>6} {str(a[3]):14} | {b[0]:#7x} {b[2]!s:>6} {str(b[3]):14} {b[1]}' if a and b else (a,b))
