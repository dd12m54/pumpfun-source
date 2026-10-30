# chains.py file.diff o|c : chains (split at ja/exit) of orig or cand side of a win.py --full diff
import sys,re
side=sys.argv[2]
rows=[]
for l in open(sys.argv[1]):
    l=l.rstrip('\n')
    m=re.match(r'^([-+ ]) +(0x[0-9a-f]+)\s+(0x[0-9a-f]+)?\s*(.*)$',l)
    if not m: continue
    t=m.group(1)
    if t==' ':
        a=m.group(2) if side=='o' else m.group(3); ins=m.group(4)
    elif t=='-' and side=='o': a=m.group(2); ins=(m.group(3) or '')+' '+m.group(4) if m.group(3) else m.group(4)
    elif t=='+' and side=='c': a=m.group(2); ins=m.group(4) if not m.group(3) else m.group(3)+' '+m.group(4)
    else: continue
    rows.append((a,ins.strip(),t))
cur=[];out=[]
for r in rows:
    cur.append(r)
    if r[1].startswith('ja ') or r[1].startswith('exit'): out.append(cur);cur=[]
if cur: out.append(cur)
for k,c in enumerate(out):
    lines=[int(re.search(r'0x([0-9a-f]+)$',i).group(1),16) for a,i,t in c if re.match(r'stw \[r10 - 0x6b8\], 0x',i)]
    calls=sum(1 for a,i,t in c if i.startswith('call'))
    same=sum(1 for a,i,t in c if t==' ')
    print(k,c[0][0],len(c),'same',same,'calls',calls,'lines',lines, c[-1][1][:24])
