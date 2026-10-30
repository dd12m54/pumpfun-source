# irdiff.py sh.ll [edit.py] out.diff : llc (fastbuild flags) the (edited) IR, diff swap_hop vs orig (win.py-like --full diff); prints ratios
import sys,os,re,subprocess,difflib,runpy,struct,tempfile
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w7r1-swaphop-frame')
ir=sys.argv[1]; ed=sys.argv[2] if len(sys.argv)>3 else None; out=sys.argv[-1]
t=open(ir).read()
if ed:
    i=t.index('define '); 
    m=re.search(r'^define [^\n]*8swap_hop17h[^\n]*\{$',t,re.M); i=m.start(); j=t.index('\n}\n',i)+3
    t=t[:i]+runpy.run_path(ed)['edit'](t[i:j])+t[j:]
d=tempfile.mkdtemp(dir=O+'/tmp') if os.path.isdir(O+'/tmp') else tempfile.mkdtemp()
open(d+'/e.ll','w').write(t)
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext',d+'/e.ll','-filetype=obj','-o',d+'/e.o'],capture_output=True,text=True)
if r.returncode: sys.exit(r.stderr[-2000:])
dis=subprocess.check_output([SDK+'/llvm-objdump','-d','--no-show-raw-insn','-r',d+'/e.o'],text=True)
# take swap_hop function
lines=dis.splitlines(); k=next(n for n,l in enumerate(lines) if re.search(r'<_ZN.*8swap_hop17h[0-9a-f]+E>:',l))
cand=[]
for l in lines[k+1:]:
    if re.match(r'^[0-9a-f]+ <',l) and not re.match(r'^[0-9a-f]+ <LBB',l): break
    m=None if 'R_SBF' in l else re.match(r'^\s*(\d+):\s+(.*)$',l)
    if m: cand.append((0x1000000+8*int(m.group(1)),re.sub(r'\s+<.*>','',m.group(2).strip())))
orig=[]
for l in open(O+'/orig.txt'):
    a,ins=l.rstrip('\n').split(None,1); orig.append((int(a,16),ins.strip()))
def norm(s):
    s=re.sub(r'^call -?0x[0-9a-f]+','call X',s); s=re.sub(r'^call -?\d+','call X',s)
    s=re.sub(r'^lddw (r\d+), .*',r'lddw \1, X',s)
    return s
ot=[norm(x[1]) for x in orig]; ct=[norm(x[1]) for x in cand]
sm=difflib.SequenceMatcher(None,ot,ct,autojunk=False)
with open(out,'w') as f:
    f.write(f'ratio {sm.ratio():.4f} bytes {8*len(ct)+8*sum(1 for x in ct if x.startswith("lddw"))}\n')
    for tag,i1,i2,j1,j2 in sm.get_opcodes():
        if tag=='equal':
            for q in range(i2-i1): f.write(f'  {orig[i1+q][0]:#07x} {cand[j1+q][0]:#07x}  {orig[i1+q][1]}\n')
            continue
        for q in range(i1,i2): f.write(f'- {orig[q][0]:#07x}          {orig[q][1]}\n')
        for q in range(j1,j2): f.write(f'+         {cand[q][0]:#07x}  {cand[q][1]}\n')
def mask(s):
    s=re.sub(r'r10 - 0x[0-9a-f]+','r10 - X',s); s=re.sub(r'add64 (r\d), -0x[0-9a-f]+',r'add64 \1, -X',s)
    s=re.sub(r'^(j\w+ .*?)[-+]0x[0-9a-f]+$',r'\1J',s); s=re.sub(r'^(ja )[-+]?0x[0-9a-f]+',r'\1J',s); return s
sm2=difflib.SequenceMatcher(None,[mask(x) for x in ot],[mask(x) for x in ct],autojunk=False)
print(f'ratio {sm.ratio():.4f} abs {sm2.ratio():.4f} n {len(ct)}')
subprocess.run(['rm','-rf',d])
