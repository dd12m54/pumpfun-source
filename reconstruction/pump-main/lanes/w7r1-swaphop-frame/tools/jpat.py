# jpat.py diff : list "jcc +0x1 ; ja" sites on orig and cand side with orig address context
import sys,re
rows=[]
for l in open(sys.argv[1]):
    m=re.match(r'^([-+ ]) +(0x[0-9a-f]+)\s+(0x[0-9a-f]+)?\s*(.*)$',l.rstrip())
    if m: rows.append(m.groups())
def seq(s):
    out=[];last='?'
    for t,a,b,ins in rows:
        if t==' ': oa=a; ca=b; i=ins
        elif t=='-': oa=a; ca=None; i=((b+' ') if b else '')+ins
        else: oa=None; ca=a; i=((b+' ') if b else '')+ins
        if t==' ' or (s=='o' and t=='-') or (s=='c' and t=='+'):
            if oa: last=oa
            out.append((last,re.sub(r'\s*<.*>$','',i.strip())))
    return out
for s in 'oc':
    q=seq(s); n=0
    for k in range(len(q)-1):
        if re.match(r'^j(?!a )\w+ .*, \+0x1$',q[k][1]) and q[k+1][1].startswith('ja '):
            n+=1; print(s,q[k][0],q[k][1],'|',q[k+1][1])
    print(s,'total',n)
