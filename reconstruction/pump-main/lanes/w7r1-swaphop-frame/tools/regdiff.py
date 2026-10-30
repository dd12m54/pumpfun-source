# regdiff.py a.diff b.diff [bucket]: per original-address bucket, count orig-only lines ('-') in each diff
import sys,re,collections
def load(p,B):
    c=collections.Counter(); last=0x5b3b0
    for l in open(p):
        m=re.match(r'^([-+ ]) (?:(0x[0-9a-f]+) )?',l)
        if not m: continue
        if l.startswith('- ') or l.startswith('  0x'):
            a=int(l.split()[1],16) if l.startswith('-') else int(l.split()[0],16)
            last=a
        if l.startswith('- '): c[(last-0x5b3b0)//B]+=1
        elif l.startswith('+ '): c[(last-0x5b3b0)//B]+=1
    return c
B=int(sys.argv[3],0) if len(sys.argv)>3 else 0x400
a=load(sys.argv[1],B); b=load(sys.argv[2],B)
for k in sorted(set(a)|set(b)):
    d=b[k]-a[k]
    print(f"{hex(0x5b3b0+k*B)} {a[k]:4d} {b[k]:4d} {d:+5d} {'#'*min(40,abs(d)//2)}")
print('total',sum(a.values()),sum(b.values()))
