# Mutation catalogue for hc.py: name -> (description, [(old, new), ...], helper text appended to trade_v3.rs)
FIT_OLD = 'Some(mut post)=>fit_post_complete(a.global.buyback_basis_points,curve.is_mayhem_mode,&quote_fee,quote,curve_fees.protocol_fee,curve_fees.creator_fee,&mut post,spendable_quote_in)?,'
EST_OLD = 'estimate_post_complete(&curve.creator,pool_base,pool_quote,fees.protocol_fee_bps,fees.creator_fee_bps,rest,false)?}else{None};'
BO_OLD = 'match &post{Some(p)=>p.base_out,None=>0}'
EX_OLD = 'let (buyback,post_buyback)=v3_execute_buy(a,ctx.bumps.bonding_curve,is_sol,amount,quote,fees.protocol_fee,fees.creator_fee,post.as_ref(),costs.0,costs.1,&quote_fee)?;'
EM_OLD = 'emit_exact_quote(&mut ctx,amount,quote,fees,buyback,costs.2,post,post_buyback)\n}'
FEE_T = 'quote_fee:&Option<native_transfer_fee::Fee>'
FIT_R = 'Result<(Option<PostComplete>,(u64,u64,u64))>'

MUTS = {}


def m(name, desc, reps, extra=''):
    MUTS[name] = (desc, reps, extra)


# --- fit_post_complete call spellings (post23 lifetime) ---
m('fitv', 'Some(post)=>plain helper fit_owned(.., post by value, ..) wrapping fit_post_complete(&mut post)',
  [(FIT_OLD, FIT_OLD.replace('Some(mut post)=>fit_post_complete(', 'Some(post)=>fit_owned(').replace('&mut post', 'post'))],
  f'fn fit_owned(buyback_bps:u64,is_mayhem:bool,{FEE_T},quote:u64,protocol_fee:u64,creator_fee:u64,mut post:PostComplete,budget:u64)->{FIT_R}{{fit_post_complete(buyback_bps,is_mayhem,quote_fee,quote,protocol_fee,creator_fee,&mut post,budget)}}\n')
m('fitf', 'fit via plain helper fit_fees(.., &curve_fees, &mut post, ..)',
  [(FIT_OLD, FIT_OLD.replace('fit_post_complete(', 'fit_fees(').replace('curve_fees.protocol_fee,curve_fees.creator_fee', '&curve_fees'))],
  f'fn fit_fees(buyback_bps:u64,is_mayhem:bool,{FEE_T},quote:u64,fees:&TradeFees,post:&mut PostComplete,budget:u64)->{FIT_R}{{fit_post_complete(buyback_bps,is_mayhem,quote_fee,quote,fees.protocol_fee,fees.creator_fee,post,budget)}}\n')
m('fitfv', 'fit via plain helper fit_fees_v(.., curve_fees by value, &mut post, ..)',
  [(FIT_OLD, FIT_OLD.replace('fit_post_complete(', 'fit_fees_v(').replace('curve_fees.protocol_fee,curve_fees.creator_fee', 'curve_fees'))],
  f'fn fit_fees_v(buyback_bps:u64,is_mayhem:bool,{FEE_T},quote:u64,fees:TradeFees,post:&mut PostComplete,budget:u64)->{FIT_R}{{fit_post_complete(buyback_bps,is_mayhem,quote_fee,quote,fees.protocol_fee,fees.creator_fee,post,budget)}}\n')
m('fitvv', 'fit via plain helper fit_vv(.., curve_fees by value, post by value, ..)',
  [(FIT_OLD, FIT_OLD.replace('Some(mut post)=>fit_post_complete(', 'Some(post)=>fit_vv(').replace('curve_fees.protocol_fee,curve_fees.creator_fee', 'curve_fees').replace('&mut post', 'post'))],
  f'fn fit_vv(buyback_bps:u64,is_mayhem:bool,{FEE_T},quote:u64,fees:TradeFees,mut post:PostComplete,budget:u64)->{FIT_R}{{fit_post_complete(buyback_bps,is_mayhem,quote_fee,quote,fees.protocol_fee,fees.creator_fee,&mut post,budget)}}\n')
m('fita', 'fit via plain helper fit_a(a,&quote_fee,quote,&curve_fees,&mut post,budget) like net_costs',
  [(FIT_OLD, 'Some(mut post)=>fit_a(a,&quote_fee,quote,&curve_fees,&mut post,spendable_quote_in)?,')],
  f'fn fit_a(a:&SellV3,{FEE_T},quote:u64,fees:&TradeFees,post:&mut PostComplete,budget:u64)->{FIT_R}{{let curve:&BondingCurve=&a.bonding_curve;fit_post_complete(a.global.buyback_basis_points,curve.is_mayhem_mode,quote_fee,quote,fees.protocol_fee,fees.creator_fee,post,budget)}}\n')
m('fitq', 'match arms yield Result, single ? after the match',
  [(FIT_OLD, FIT_OLD[:-2] + ','), ('                None=>(None,costs),\n            };', '                None=>Ok((None,costs)),\n            }?;')])
m('fitblk', 'Some(mut post)=>{let r=fit(..)?;r}',
  [(FIT_OLD, 'Some(mut post)=>{let r=' + FIT_OLD[len('Some(mut post)=>'):-1] + ';r},')])
m('armswap', 'None arm first in the fit match',
  [(FIT_OLD + '\n                None=>(None,costs),', '                None=>(None,costs),\n' + FIT_OLD)])
m('fitref', 'Some(ref mut post)=>fit(.., post, ..)',
  [(FIT_OLD, FIT_OLD.replace('Some(mut post)', 'Some(ref mut post)').replace('&mut post', 'post'))])
# --- estimate spellings ---
m('estf', 'estimate via plain helper estimate_with(curve,pool_base,pool_quote,&fees,rest)',
  [(EST_OLD, 'estimate_with(curve,pool_base,pool_quote,&fees,rest)?}else{None};')],
  'fn estimate_with(curve:&BondingCurve,pool_base:u64,pool_quote:u64,fees:&TradeFees,budget:u64)->Result<Option<PostComplete>>{estimate_post_complete(&curve.creator,pool_base,pool_quote,fees.protocol_fee_bps,fees.creator_fee_bps,budget,false)}\n')
m('estcf', 'estimate uses curve_fees bps instead of fees bps (same bps source)',
  [(EST_OLD, EST_OLD.replace('fees.protocol_fee_bps,fees.creator_fee_bps', 'curve_fees.protocol_fee_bps,curve_fees.creator_fee_bps'))])
# --- slippage base_out spellings ---
m('bo1', 'post.as_ref().map_or(0,|p|p.base_out)', [(BO_OLD, 'post.as_ref().map_or(0,|p|p.base_out)')])
m('bo2', 'post.map_or(0,|p|p.base_out)', [(BO_OLD, 'post.map_or(0,|p|p.base_out)')])
m('bo3', 'if let Some(p)=&post{p.base_out}else{0}', [(BO_OLD, 'if let Some(p)=&post{p.base_out}else{0}')])
m('bo4', 'match post{Some(p)=>p.base_out,None=>0} (copy)', [(BO_OLD, 'match post{Some(p)=>p.base_out,None=>0}')])
m('bo5', 'post.map(|p|p.base_out).unwrap_or(0)', [(BO_OLD, 'post.map(|p|p.base_out).unwrap_or(0)')])
m('bo6', 'match post{Some(PostComplete{base_out,..})=>base_out,None=>0}', [(BO_OLD, 'match post{Some(PostComplete{base_out,..})=>base_out,None=>0}')])
m('bo7', 'match &post{Some(p)=>p.base_out,_=>0}', [(BO_OLD, 'match &post{Some(p)=>p.base_out,_=>0}')])
# --- tail spellings ---
m('ex1', 'let r=v3_execute_buy(..)?; emit(..r.0..r.1)',
  [(EX_OLD, EX_OLD.replace('let (buyback,post_buyback)=', 'let r=')), (EM_OLD, EM_OLD.replace('buyback,costs.2,post,post_buyback', 'r.0,costs.2,post,r.1'))])
m('ex2', 'post arg as match &post{Some(p)=>Some(p),None=>None}',
  [(EX_OLD, EX_OLD.replace('post.as_ref()', 'match &post{Some(p)=>Some(p),None=>None}'))])
m('ex3', 'destructure TradeFees{protocol_fee,creator_fee,..}=fees before execute',
  [(EX_OLD, 'let TradeFees{protocol_fee,creator_fee,..}=fees;' + EX_OLD.replace('fees.protocol_fee,fees.creator_fee', 'protocol_fee,creator_fee'))])
m('ex4', 'bind transfer fee costs.2 before execute',
  [(EX_OLD, 'let transfer_fee=costs.2;' + EX_OLD), (EM_OLD, EM_OLD.replace('costs.2', 'transfer_fee'))])
m('ex5', 'post_ref=post.as_ref() bound before execute',
  [(EX_OLD, 'let post_ref=post.as_ref();' + EX_OLD.replace('post.as_ref()', 'post_ref'))])
m('ex6', 'emit helper param order (ctx,fees,post,...)',
  [(EM_OLD, 'emit_exact_quote2(&mut ctx,fees,post,amount,quote,buyback,costs.2,post_buyback)\n}')],
  'fn emit_exact_quote2(ctx:&mut Context<SellV3>,fees:TradeFees,post:Option<PostComplete>,amount:u64,quote:u64,buyback_fee:u64,quote_transfer_fee:u64,post_buyback_fee:u64)->Result<()>{v3_emit_buy(ctx,amount,quote,&fees,buyback_fee,quote_transfer_fee,"buy_exact_quote_in",&post,post_buyback_fee)}\n')
m('ex7', 'execute + emit in one plain helper finish_exact_quote(ctx by value, fees/post by value)',
  [(EX_OLD + '\n    ' + EM_OLD, 'let bump=ctx.bumps.bonding_curve;\n    finish_exact_quote(ctx,bump,is_sol,amount,quote,fees,post,costs,&quote_fee)\n}')],
  f'fn finish_exact_quote(mut ctx:Context<SellV3>,bump:u8,is_sol:bool,amount:u64,quote:u64,fees:TradeFees,post:Option<PostComplete>,costs:(u64,u64,u64),{FEE_T})->Result<()>{{let (buyback,post_buyback)=v3_execute_buy(&mut ctx.accounts,bump,is_sol,amount,quote,fees.protocol_fee,fees.creator_fee,post.as_ref(),costs.0,costs.1,quote_fee)?;emit_exact_quote(&mut ctx,amount,quote,fees,buyback,costs.2,post,post_buyback)}}\n')
m('ex8', 'emit returns via ?;Ok(())',
  [(EM_OLD, 'emit_exact_quote(&mut ctx,amount,quote,fees,buyback,costs.2,post,post_buyback)?;Ok(())\n}')])
m('ex9', 'execute via plain helper exec_v(.., fees by value, ..)',
  [(EX_OLD, 'let (buyback,post_buyback)=exec_v(a,ctx.bumps.bonding_curve,is_sol,amount,quote,fees,post.as_ref(),costs,&quote_fee)?;')],
  f"fn exec_v<'info>(a:&mut SellV3<'info>,bump:u8,is_sol:bool,amount:u64,quote:u64,fees:TradeFees,post:Option<&PostComplete>,costs:(u64,u64,u64),{FEE_T})->Result<(u64,u64)>{{v3_execute_buy(a,bump,is_sol,amount,quote,fees.protocol_fee,fees.creator_fee,post,costs.0,costs.1,quote_fee)}}\n")
# --- cross arm result spelling ---
m('cr1', 'cross arm binds let fees=curve_fees before the tuple',
  [('        (amount,quote,curve_fees,post,costs)\n', '        let fees=curve_fees;(amount,quote,fees,post,costs)\n')])
m('cr2', 'cross arm fees by struct update TradeFees{..curve_fees}',
  [('        (amount,quote,curve_fees,post,costs)\n', '        (amount,quote,TradeFees{..curve_fees},post,costs)\n')])
