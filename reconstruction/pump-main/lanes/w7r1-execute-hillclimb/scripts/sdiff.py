#!/usr/bin/env python3
"""sdiff.py cand.so [mode]: structural diff of execute vs original. mode: regs (mask regs), stack (mask regs+stack), none"""
import sys,subprocess,re,json,difflib,os
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w7r1-execute-hillclimb'
H=WT+'/reconstruction/harness'; OBJ=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin/llvm-objdump')
so=sys.argv[1]; mode=sys.argv[2] if len(sys.argv)>2 else 'regs'
tm=json.loads(subprocess.run(['python3',H+'/target_metric.py',so,'0x72810','--sym',r'sweep::execute$','--top','1'],capture_output=True,text=True).stdout.splitlines()[0])
s=int(tm['cand_start'],16); e=s+tm['cand_bytes']
d=subprocess.run([OBJ,'-d','--no-show-raw-insn','--no-leading-addr',f'--start-address={s}',f'--stop-address={e}',so],capture_output=True,text=True).stdout
c=[l.strip() for l in d.splitlines() if l.startswith((' ','\t')) and l.strip() and not l.strip().endswith(':')]
c=[re.sub(r'\s*<[^>]*>','',x) for x in c]
o=[re.sub(r'^0x[0-9a-f]+\s+','',l).strip() for l in open(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w7r1-execute-hillclimb/orig.txt')).read().splitlines() if re.match(r'^0x[0-9a-f]+\s',l)]
def norm(x):
    x=re.sub(r'\s+',' ',x)
    x=re.sub(r'call -?0x[0-9a-f]+','call X',x); x=re.sub(r'lddw (r\d+), 0x[0-9a-f]+',r'lddw \1, X',x)
    x=re.sub(r'(ja|j\w+ r\d+, (r\d+|-?0x[0-9a-f]+),) [+-]0x[0-9a-f]+',r'\1 J',x); x=re.sub(r'^ja [+-]0x[0-9a-f]+','ja J',x)
    if mode in('regs','stack'): x=re.sub(r'\br\d\b','r',x)
    if mode=='stack': x=re.sub(r'r10 - 0x[0-9a-f]+','r10-S',x)
    return x
O=[norm(x) for x in o]; C=[norm(x) for x in c]
sm=difflib.SequenceMatcher(None,O,C,autojunk=False)
print('orig',len(O),'cand',len(C),'ratio',round(sm.ratio(),5))
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    print(f'--- {tag} orig[{i1}:{i2}] cand[{j1}:{j2}]')
    for k in range(i1,min(i2,i1+12)): print('  -',o[k])
    for k in range(j1,min(j2,j1+12)): print('  +',c[k])
