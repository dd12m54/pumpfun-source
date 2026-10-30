import sys,re
H=sys.argv[1]; sys.path.insert(0,H); cand=sys.argv[2]; pat=sys.argv[3]; sys.argv=sys.argv[:1]
import coords,score
from pathlib import Path
o=[]
for w in coords.original_windows():
    try: ss=coords.sites(coords.ORIG,coords.OS,w['start'],w['raw'])
    except Exception: continue
    for s in ss:
        if pat in s['path']: o.append((s['line'],hex(w['start'])))
CP=Path(cand); blob=CP.read_bytes(); cs=score.sections(blob); c=[]
for st,n,nm in score.candidate_functions(CP):
    try: ss=coords.sites(blob,cs,st,score.body(blob,cs,st,n))
    except Exception: continue
    for s in ss:
        if pat in s['path']: c.append((s['line'],re.sub(r'17h[0-9a-f]{16}E$','',nm)[-50:]))
ol=sorted(o); cl=sorted(c)
from collections import Counter
oc=Counter(l for l,_ in ol); cc=Counter(l for l,_ in cl)
print('orig',len(ol),'cand',len(cl))
for l in sorted(set(oc)|set(cc)):
    mark='' if oc[l]==cc[l] else '  <-- DIFF'
    print(l,oc[l],cc[l],[w for x,w in ol if x==l][:4],[w for x,w in cl if x==l][:3],mark)
