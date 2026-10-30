# rel.py <dis.txt> <base> <lo> <hi> : print with function-relative offsets and resolved jumps
import re,sys
f,base,lo,hi=sys.argv[1],int(sys.argv[2],0),int(sys.argv[3],0),int(sys.argv[4],0)
for l in open(f):
    m=re.match(r'\s*(?:[-+]\s+)?(?:0x[0-9a-f]+\s+)?0x([0-9a-f]+)\s+(.*)',l) if False else re.match(r'0x([0-9a-f]+)\s+(.*)',l.strip())
    if not m: continue
    a=int(m.group(1),16)-base
    if lo<=a<=hi:
        s=m.group(2); j=re.search(r'([+-]0x[0-9a-f]+)$',s)
        if j and s.startswith('j'): s+=f'   -> {a+8+int(j.group(1),16)*8:#x}'
        print(f'{a:#06x} {s}')
