import sys,re
f,v=sys.argv[1:]
t=open(f).read()
new=open(v).read()
# replace from 'fn v3_buy_costs(' line through the line containing 'Ok((pool_quote,total_buyback,quote_transfer_fee))' + closing brace
a=t.index('#[inline(never)]\nfn v3_buy_costs(')
endmark='Ok((pool_quote,total_buyback,quote_transfer_fee))\n}\n'
b=t.index(endmark,a)+len(endmark)
old=t[a:b]
if old.count('\n')!=new.count('\n'):
    sys.exit('line count mismatch old=%d new=%d'%(old.count('\n'),new.count('\n')))
open(f,'w').write(t[:a]+new+t[b:])
