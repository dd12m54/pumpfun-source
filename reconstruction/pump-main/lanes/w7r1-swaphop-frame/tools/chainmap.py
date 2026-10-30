# chainmap.py file.diff : split orig and cand into chains (ending at ja/exit), match chains by content similarity, print orig chain order with cand index
import sys,re,difflib
def side(path,s):
    rows=[]
    for l in open(path):
        l=l.rstrip('\n')
        m=re.match(r'^([-+ ]) +(0x[0-9a-f]+)\s+(0x[0-9a-f]+)?\s*(.*)$',l)
        if not m: continue
        t=m.group(1)
        if t==' ': a=m.group(2) if s=='o' else m.group(3); ins=m.group(4)
        elif t=='-' and s=='o': a=m.group(2); ins=((m.group(3)+' ') if m.group(3) else '')+m.group(4)
        elif t=='+' and s=='c': a=m.group(2); ins=((m.group(3)+' ') if m.group(3) else '')+m.group(4)
        else: continue
        ins=re.sub(r'\s*<.*>$','',ins.strip()); rows.append((a,ins))
    ch=[];cur=[]
    for r in rows:
        cur.append(r)
        if r[1].startswith('ja ') or r[1]=='exit': ch.append(cur);cur=[]
    if cur: ch.append(cur)
    return ch
def norm(i):
    i=re.sub(r'r10 - 0x[0-9a-f]+','r10-X',i); i=re.sub(r'(add64 r\d+), -0x[0-9a-f]+',r'\1, -X',i)
    i=re.sub(r'([-+]0x[0-9a-f]+)$','J',i) if i.startswith('j') else i
    i=re.sub(r'^call .*','call',i); i=re.sub(r'^lddw (r\d+).*',r'lddw \1',i); return i
O=side(sys.argv[1],'o'); C=side(sys.argv[1],'c')
on=[[norm(x[1]) for x in c] for c in O]; cn=[[norm(x[1]) for x in c] for c in C]
used=set(); res=[]
for i,c in enumerate(on):
    best=(0,None)
    for j,d in enumerate(cn):
        if abs(len(c)-len(d))>max(len(c),len(d))*0.6: continue
        r=difflib.SequenceMatcher(None,c,d,autojunk=False).ratio()
        if r>best[0]: best=(r,j)
    res.append((i,best[1],best[0]))
for i,j,r in res:
    print(f"o{i:3d} {O[i][0][0]} n{len(O[i]):3d} -> c{j if j is not None else -1:3d} {C[j][0][0] if j is not None else '':>8} n{len(C[j]) if j is not None else 0:3d} r={r:.2f} {'' if j==i else '<<' if j is not None else ''}")
