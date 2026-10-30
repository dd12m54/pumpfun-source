#!/bin/bash
# trial.sh <name> <variant-file> <slot>
# variant file: replacement text for v3_buy_costs's body region between markers in trade_v3.rs
T=$1; V=$2; SLOT=${3:-a}
W=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w7r1-v3buycosts-blockorder
O=$HOME/.cache/pumpfun-reconstruction/lanes/w7r1-v3buycosts-blockorder
H=$W/reconstruction/harness
S=$O/src/$T; rm -rf $S; mkdir -p $S; rsync -a --exclude target $W/programs/pump/ $S/
python3 $O/bin/apply.py $S/src/trade_v3.rs $V || { echo "$T PATCH-FAILED"; exit 1; }
diff -u $W/programs/pump/src/trade_v3.rs $S/src/trade_v3.rs > $O/src/$T.diff
export PUMP_BUILD_SLOTS=10
D=$O/out/$T; rm -rf $D; mkdir -p $D
python3 $H/fastbuild.py --src $S --work $O/work-$SLOT --out $D > $D/build.log 2>&1
if [ ! -f $D/unstripped.so ]; then echo "$T BUILD-FAILED"; grep -m3 -A8 '^error' $D/build.log | head -30; exit 1; fi
python3 $H/score.py $D/unstripped.so --baseline $O/out/base/score.json --json $D/score.json --quiet > $D/score.txt 2>&1
python3 $H/target_metric.py $D/unstripped.so 0x80df8 --sym 'v3_buy_costs$' --top 1 > $D/metric.json 2>&1
python3 $H/win.py show 0x80df8 --cand $D/unstripped.so --sym 'v3_buy_costs$' --full > $D/diff.txt 2>&1
python3 - $D <<'PY'
import json,sys
D=sys.argv[1]
s=json.loads(open(D+'/score.txt').read().strip().splitlines()[-1])
m=json.loads(open(D+'/metric.json').read().strip().splitlines()[-1])
diff=open(D+'/diff.txt').read().splitlines()
print(json.dumps({'trial':D.split('/')[-1],'norm':s['normalized'],'raw':s['raw'],'gains':s['gains'],'losses':s['losses'],'raw_gains':len(s['raw_gains']),'raw_losses':s['raw_losses'],'bytes':m['cand_bytes'],'ratio':m['ratio'],'calls':m['calls_candidate'][0],'minus':sum(1 for l in diff if l.startswith('- ')),'plus':sum(1 for l in diff if l.startswith('+ ')),'sha':s['candidate_sha256'][:16]}))
PY
rm -rf $S/target
