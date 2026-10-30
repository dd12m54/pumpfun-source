import json,sys
for l in open(sys.argv[1]):
  try: r=json.loads(l)
  except: print('!!',l[:200].strip()); continue
  c=r.get('calls'); c=sum(c) if c else None
  print(f"{r['name'][:34]:34s} {str(r.get('ok'))[:1]} {r.get('ratio')} {r.get('bytes')} c={c} rent={r.get('f_rent')} ev={r.get('f_event')} {str(r.get('error',''))[:160]} {'N=%s R=%s L=%s RL=%s'%(r.get('N'),r.get('R'),r.get('losses'),r.get('rlosses')) if 'N' in r else ''}")
