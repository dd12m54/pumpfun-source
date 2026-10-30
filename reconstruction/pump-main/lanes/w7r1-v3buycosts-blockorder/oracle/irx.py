#!/usr/bin/env python3
"""Diagnostic only. irx.py <base_dir> <fn.ll> [name]: put fn.ll into base_dir/one.ll, llc, diff vs original (jumps/calls/lddw normalized)."""
import sys,subprocess,re,os,difflib
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w7r1-v3buycosts-blockorder')
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools')
bd,fnf=sys.argv[1],sys.argv[2]; name=sys.argv[3] if len(sys.argv)>3 else os.path.basename(fnf)
t=open(bd+'/one.ll').read()
m=re.search(r'^define[^\n]*12v3_buy_costs[^\n]*\{\n.*?^\}\n',t,re.M|re.S)
sym=re.search(r'@(\S+?)\(',m.group(0)).group(1)
f2=open(fnf).read()
d=O+'/irx/'+name; os.makedirs(d,exist_ok=True)
open(d+'/m.ll','w').write(t[:m.start()]+f2+t[m.end():])
r=subprocess.run([SDK+'/llvm/bin/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext',d+'/m.ll','-filetype=obj','-o',d+'/m.o']+sys.argv[4:],capture_output=True,text=True)
if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
open(d+'/stderr.txt','w').write(r.stderr)
fn=subprocess.run(['sh',O+'/bin/fn.sh',d+'/m.o',sym],capture_output=True,text=True).stdout
def norm(l):
    l=l.strip(); l=re.sub(r'call -?0x[0-9a-f]+','call X',l); l=re.sub(r'lddw (r\d+), 0x[0-9a-f]+',r'lddw \1, X',l)
    if re.match(r'(ja |j[a-z]+ )',l): l=re.sub(r'([+-]0x[0-9a-f]+)$','J',l)
    return l
c=[norm(l) for l in fn.splitlines()]
o=[norm(l.split(None,1)[1]) for l in open(O+'/orig.txt').read().splitlines() if l.startswith('0x')]
open(d+'/fn.txt','w').write('\n'.join(c)+'\n')
diff=list(difflib.unified_diff(o,c,'orig','cand',n=0,lineterm=''))
mi=sum(1 for l in diff if l[:1]=='-' and l[:3]!='---'); pl=sum(1 for l in diff if l[:1]=='+' and l[:3]!='+++')
sz=sum(16 if l.startswith('lddw') else 8 for l in c)
print(f'{name}: bytes={sz} -{mi} +{pl}')
if os.environ.get('V'): print('\n'.join(diff))
