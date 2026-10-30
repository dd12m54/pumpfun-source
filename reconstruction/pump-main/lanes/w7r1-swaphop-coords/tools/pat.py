# pat.py dis base : list conditional branches with pattern (A=fallthrough glued, B=jcc+1;ja = MBP-chosen) and call index
import re,sys
def load(f,base):
    r=[]
    for l in open(f):
        m=re.match(r'(0x[0-9a-f]+)\s+(.*)',l.strip())
        if m: r.append((int(m.group(1),16)-base,m.group(2)))
    return r
def pats(ins):
    out=[];ci=0
    for k,(a,s) in enumerate(ins):
        if s.startswith('call'): ci+=1
        if s.startswith('j') and not s.startswith('ja'):
            nxt=ins[k+1][1] if k+1<len(ins) else ''
            m=re.search(r'([+-]0x[0-9a-f]+)',s.split(',')[-1]); off=int(m.group(1),16) if m else None
            if off==1 and nxt.startswith('ja'): out.append((a,ci,'B',s.split(',')[0]))
            else: out.append((a,ci,'A',s.split(',')[0]))
    return out
o=pats(load(sys.argv[1],int(sys.argv[2],0))); c=pats(load(sys.argv[3],int(sys.argv[4],0)))
import difflib
ko=[(x[1],x[2],x[3].split()[0]) for x in o]; kc=[(x[1],x[2],x[3].split()[0]) for x in c]
sm=difflib.SequenceMatcher(None,ko,kc,autojunk=False)
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op=='equal': continue
    print(op, [f'{o[i][0]:#x}:c{o[i][1]}:{o[i][2]}:{o[i][3]}' for i in range(i1,i2)], '|', [f'{c[j][0]:#x}:c{c[j][1]}:{c[j][2]}:{c[j][3]}' for j in range(j1,j2)])
print('orig B',sum(x[2]=='B' for x in o),'A',sum(x[2]=='A' for x in o),' cand B',sum(x[2]=='B' for x in c),'A',sum(x[2]=='A' for x in c))
