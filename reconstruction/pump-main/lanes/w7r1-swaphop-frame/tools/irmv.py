# helpers for IR block moves with numeric-value renaming
import re
def _rename_defs(t, blk):
    defs=re.findall(r'^\s*%(\d+) = ',blk,re.M)
    for d in defs:
        t=re.sub(r'%'+d+r'\b(?![.\w])','%mv'+d,t)
    return t
def block_span(t,name):
    i=t.index('\n'+name+':'); j=t.index('\n\n',i+1); return i,j
def mv_end(t,name):
    i,j=block_span(t,name); blk=t[i:j]
    t=_rename_defs(t,blk); i,j=block_span(t,name); blk=t[i:j]
    t=t[:i]+t[j:]; k=t.rindex('\n}')
    return t[:k]+'\n'+blk+'\n'+t[k:]
def mv_after(t,name,after):
    i,j=block_span(t,name); blk=t[i:j]
    t=_rename_defs(t,blk); i,j=block_span(t,name); blk=t[i:j]
    t=t[:i]+t[j:]; a,b=block_span(t,after)
    return t[:b]+'\n'+blk+t[b:]
