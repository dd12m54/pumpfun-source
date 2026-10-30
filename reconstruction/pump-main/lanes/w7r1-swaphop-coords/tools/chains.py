# chains.py dis base lo hi : split into fallthrough chains (break after ja/exit), label with calls + sites
import re,sys
f,base,lo,hi=sys.argv[1],int(sys.argv[2],0),int(sys.argv[3],0),int(sys.argv[4],0)
ins=[]
for l in open(f):
    m=re.match(r'(0x[0-9a-f]+)\s+(.*)',l.strip())
    if m: ins.append((int(m.group(1),16)-base,m.group(2)))
ch=[];cur=[]
for a,s in ins:
    cur.append((a,s))
    if s.startswith('ja ') or s=='exit':
        ch.append(cur); cur=[]
if cur: ch.append(cur)
for c in ch:
    if c[-1][0]<lo or c[0][0]>hi: continue
    desc=[]
    for a,s in c:
        if s.startswith('call'): desc.append('call')
        m=re.match(r'stw \[r10 - 0x[0-9a-f]+\], (0x[0-9a-f]+)',s)
        if m and 400<int(m.group(1),16)<800: desc.append('L%d'%int(m.group(1),16))
        if s.startswith('j') and not s.startswith('ja'):
            j=re.search(r'([+-]0x[0-9a-f]+)$',s); desc.append('?%#x'%(a+8+int(j.group(1),16)*8))
    t=c[-1][1]; j=re.search(r'([+-]0x[0-9a-f]+)$',t)
    end=('->%#x'%(c[-1][0]+8+int(j.group(1),16)*8)) if t.startswith('ja') else t
    print(f'{c[0][0]:#06x}-{c[-1][0]:#06x} n={len(c):3d} {end:10s} {" ".join(desc)}')
