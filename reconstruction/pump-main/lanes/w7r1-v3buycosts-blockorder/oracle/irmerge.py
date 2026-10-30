#!/usr/bin/env python3
"""Diagnostic: merge Err tail stores of chosen predecessor blocks into one shared block (IR-level oracle)."""
import re,sys,itertools,subprocess,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w7r1-v3buycosts-blockorder')
f=open(O+'/ir/base/fn.ll').read()
CL371='"_ZN14pump_recovered5trade12v3_buy_costs28_$u7b$$u7b$closure$u7d$$u7d$17h60893dbbd01db6f1E.exit"'
# err tails: name -> (w0, w1)
tails={'e371':(CL371,'%_56.0','%_56.1'),'bb20':('%bb20','%7','%_63.1'),'bb22':('%bb22','%28','%_68.1'),'bb34':('%bb34','%_37.sroa.6.0','%_37.sroa.11.0.in'),'bb36':('%bb36','%_95.0','%_95.1')}
def blockspan(f,label):
    lab=label.lstrip('%')
    m=re.search(r'^'+re.escape(lab)+r':.*?\n(.*?)(?=^[^\s;]|\Z)',f,re.M|re.S)
    return m
def merge(f,names,pos='end'):
    f2=f
    for n in names:
        lab,w0,w1=tails[n]
        m=blockspan(f2,lab)
        body=m.group(1)
        # remove the two stores + geps to _0 at offsets 8/16 and the br bb15
        body2=re.sub(r'  %\S+ = getelementptr inbounds i8, ptr %_0, i64 (8|16)\n','',body)
        body2=re.sub(r'  store (i64|ptr) \S+, ptr %\S+, align 8\n(?=(  store|  br label %bb15))','',body2)
        assert 'store' not in body2.split('\n')[-3] if False else True
        body2=body2.replace('br label %bb15','br label %errtail')
        f2=f2[:m.start(1)]+body2+f2[m.end(1):]
    preds=[tails[n][0] for n in names]
    phi0=', '.join('[ %s, %s ]'%(tails[n][1],tails[n][0]) for n in names)
    phi1=', '.join('[ %s, %s ]'%(tails[n][2],tails[n][0]) for n in names)
    blk=('errtail:\n  %et0 = phi i64 '+phi0+'\n  %et1 = phi ptr '+phi1+
         '\n  %etg0 = getelementptr inbounds i8, ptr %_0, i64 8\n  store i64 %et0, ptr %etg0, align 8\n  %etg1 = getelementptr inbounds i8, ptr %_0, i64 16\n  store ptr %et1, ptr %etg1, align 8\n  br label %bb15\n\n')
    # fix bb15 phi: replace entries of merged preds with one errtail entry
    m=re.search(r'%\.sink = phi i64 (.*)\n',f2)
    ents=re.findall(r'\[ [^\]]+ \]',m.group(1))
    keep=[e for e in ents if not any(e.endswith(', '+p+' ]') for p in preds)]
    keep.append('[ 1, %errtail ]')
    f2=f2[:m.start(1)]+', '.join(keep)+f2[m.end(1):]
    if pos=='end':
        i=f2.rindex('}')
        f2=f2[:i]+blk+f2[i:]
    else:
        i=f2.index('\nbb15:')+1
        f2=f2[:i]+blk+f2[i:]
    return f2
if __name__=='__main__':
    os.makedirs(O+'/irv',exist_ok=True)
    keys=list(tails)
    for r in range(2,6):
        for c in itertools.combinations(keys,r):
            for pos in ('end','before15'):
                nm='mg-'+'-'.join(c)+'-'+pos
                p=O+'/irv/'+nm+'.ll'; open(p,'w').write(merge(f,c,pos))
                out=subprocess.run(['python3',O+'/bin/irx.py',O+'/ir/base',p,nm],capture_output=True,text=True)
                print((out.stdout+out.stderr).strip()[:300])
