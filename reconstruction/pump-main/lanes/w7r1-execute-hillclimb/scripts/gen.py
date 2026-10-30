#!/usr/bin/env python3
"""Spelling-mutation generator for sweep::execute (lane w7r1-execute-hillclimb).
gen.py KEY=IDX ... -o out.rs   (unspecified keys use 0 = base spelling)
Every alternative keeps the line count of the region it replaces, so line!() sites stay put."""
import sys, os
BASE = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w7r1-execute-hillclimb/v/base.rs')
Q = 'a.bonding_curve.quote_mint'
TOK = ("  let quote_mint=a.quote_mint.key();let quote_token_program=a.quote_token_program.key();let quote_mint_info=a.quote_mint.to_account_info();let quote_token_program_info=a.quote_token_program.to_account_info();\n"
       "  admit_quote_pair(a,&quote_mint,&quote_token_program,&quote_mint_info,&quote_token_program_info)?;")
RENT = 'ensure_rent_exempt(&a.system_program,&a.payer,a.recipient.as_ref())?'
# region -> (first line, last line) in base.rs, alternatives as text (joined lines, must have same line count)
CH = {
 # native computation (line 151)
 'native': (151, 151, [
   f" let native={Q}==Pubkey::default();",
   f" let native={Q}.eq(&Pubkey::default());",
   f" let native=Pubkey::default()=={Q};",
   f" let native=!({Q}!=Pubkey::default());",
   f" let native={Q}.to_bytes()==[0u8;32];",
   f" let native={Q}.as_ref()==Pubkey::default().as_ref();",
   f" let native={Q}==Pubkey::new_from_array([0u8;32]);",
   f" let native=matches!({Q},q if q==Pubkey::default());",
   f" let native=if {Q}==Pubkey::default(){{true}}else{{false}};",
   f" let native={{let q={Q};q==Pubkey::default()}};",
   f" let native={Q}==Pubkey::default() as Pubkey;",
   f" let native=Pubkey::default().eq(&{Q});",
   f" let native={Q}.eq(&Pubkey::default())&&true;",
   f" let native:bool=PartialEq::eq(&{Q},&Pubkey::default());",
   f" let native=!{Q}.ne(&Pubkey::default());",
   f" let default=Pubkey::default();let native={Q}==default;",
   f" let native={Q}==Pubkey::from([0u8;32]);",
   f" let native=is_native({Q});",
   f" let native=is_native_ref(&{Q});",
   f" let native=quote_is_native(&a.bonding_curve);",
   f" let native=is_native_inl({Q});",
   f" let native=is_native_rev({Q});",
   f" let native=quote_is_native(a.bonding_curve.as_ref());",
 ]),
 # dispatch (lines 152-163, 12 lines)
 'disp': (152, 163, [
   None,  # base
   " if !native{\n\n\n\n\n" + TOK + "\n\n\n }else if creator{" + RENT + ";\n\n }",
   " if native{if creator{" + RENT + ";}\n\n\n\n\n }else{\n" + TOK + "\n\n\n }\n",
   " match native{true=>if creator{" + RENT + ";},\n\n\n\n  false=>{\n" + TOK + "\n\n  }\n\n\n }",
   " match (native,creator){\n  (true,true)=>" + RENT + ",\n\n\n\n  (false,_)=>{\n" + TOK + "\n\n  }\n  (true,false)=>{}\n }",
   " match (creator,native){\n  (true,true)=>{" + RENT + ";}\n\n\n\n  (_,false)=>{\n" + TOK + "\n\n  }\n  _=>{}\n }",
   " if creator&&native{" + RENT + ";}\n\n\n\n if !native{\n" + TOK + "\n\n }\n\n\n",
   " match (creator as u8,native){\n  (1,true)=>" + RENT + ",\n\n\n\n  (_,false)=>{\n" + TOK + "\n\n  }\n  _=>{}\n }",
   " if native{if creator{" + RENT + "}}else{\n\n\n\n\n" + TOK + "\n\n\n\n\n }",
 ]),
 # rent helper attribute (line 179)
 'attr': (179, 179, ["#[inline(always)]", "", "#[inline]", "#[inline(never)]"]),
 # rent helper body (lines 181-182)
 'rbody': (181, 182, [
   None,
   " let minimum=Rent::get()?.minimum_balance(0);\n if destination.lamports()<minimum{crate::legacy_buy::native_payments::transfer(system_program.as_ref(),payer,destination,minimum)}else{Ok(())}",
   " let rent=Rent::get()?;let minimum=rent.minimum_balance(0);\n if destination.lamports()<minimum{crate::legacy_buy::native_payments::transfer(system_program.as_ref(),payer,destination,minimum)}else{Ok(())}",
   " let minimum=Rent::get().map(|rent|rent.minimum_balance(0))?;\n if destination.lamports()>=minimum{return Ok(());}crate::legacy_buy::native_payments::transfer(system_program.as_ref(),payer,destination,minimum)",
   " let minimum=Rent::get().map(|rent|rent.minimum_balance(0))?;\n if destination.lamports()<minimum{crate::legacy_buy::native_payments::transfer(system_program.as_ref(),payer,destination,minimum)?;}Ok(())",
   " let minimum=Rent::get()?.minimum_balance(0);\n if destination.lamports()<minimum{crate::legacy_buy::native_payments::transfer(system_program.as_ref(),payer,destination,minimum)?;}Ok(())",
 ]),
 # amount==0 (line 150)
 'zero': (150, 150, [
   None,
   " if amount==0{msg!(\"Nothing to sweep for fee bucket {}\",creator as u8);return Ok(())}",
   " if amount<1{msg!(\"Nothing to sweep for fee bucket {}\",creator as u8);return Ok(());}",
   " if amount==0u64{msg!(\"Nothing to sweep for fee bucket {}\",creator as u8);return Ok(());}",
 ]),
 # amount take (line 148)
 'take': (148, 148, [
   None,
   " let amount=if creator{core::mem::take(&mut a.bonding_curve.creator_fee)}else{core::mem::take(&mut a.bonding_curve.protocol_fees)};",
   " let amount=if creator{core::mem::replace(&mut a.bonding_curve.creator_fee,0)}else{core::mem::replace(&mut a.bonding_curve.protocol_fees,0)};",
   " let amount=match creator{true=>{let v=a.bonding_curve.creator_fee;a.bonding_curve.creator_fee=0;v}false=>{let v=a.bonding_curve.protocol_fees;a.bonding_curve.protocol_fees=0;v}};",
   " let slot=if creator{&mut a.bonding_curve.creator_fee}else{&mut a.bonding_curve.protocol_fees};let amount=*slot;*slot=0;",
   " let amount=if creator as u8==1{let v=a.bonding_curve.creator_fee;a.bonding_curve.creator_fee=0;v}else{let v=a.bonding_curve.protocol_fees;a.bonding_curve.protocol_fees=0;v};",
 ]),
}

EXTRA = {('native', 17): "fn is_native(quote_mint:Pubkey)->bool{quote_mint==Pubkey::default()}",
         ('native', 18): "fn is_native_ref(quote_mint:&Pubkey)->bool{*quote_mint==Pubkey::default()}",
         ('native', 19): "fn quote_is_native(curve:&BondingCurve)->bool{curve.quote_mint==Pubkey::default()}",
         ('native', 20): "#[inline]\nfn is_native_inl(quote_mint:Pubkey)->bool{quote_mint==Pubkey::default()}",
         ('native', 21): "fn is_native_rev(quote_mint:Pubkey)->bool{Pubkey::default()==quote_mint}",
         ('native', 22): "fn quote_is_native(curve:&BondingCurve)->bool{curve.quote_mint==Pubkey::default()}",
}
BASECALL = 'ensure_rent_exempt(&a.system_program,&a.payer,a.recipient.as_ref())'
SIG0 = "fn ensure_rent_exempt<'info>(system_program:&Program<'info,System>,payer:&Signer<'info>,destination:&AccountInfo<'info>)->Result<()>{"
RSIG = [  # (signature line, call text, body transform)
 (SIG0, BASECALL, None),
 (SIG0, 'ensure_rent_exempt(&a.system_program,&a.payer,&a.recipient)', None),
 ("fn ensure_rent_exempt<'info>(a:&SweepFees<'info>)->Result<()>{let system_program=&a.system_program;let payer=&a.payer;let destination=a.recipient.as_ref();", 'ensure_rent_exempt(a)', None),
 ("fn ensure_rent_exempt<'info>(a:&mut SweepFees<'info>)->Result<()>{let system_program=&a.system_program;let payer=&a.payer;let destination=a.recipient.as_ref();", 'ensure_rent_exempt(a)', None),
 ("fn ensure_rent_exempt<'info>(system_program:&AccountInfo<'info>,payer:&Signer<'info>,destination:&AccountInfo<'info>)->Result<()>{", 'ensure_rent_exempt(a.system_program.as_ref(),&a.payer,a.recipient.as_ref())', lambda b: b.replace('system_program.as_ref()', 'system_program')),
 ("fn ensure_rent_exempt<'info>(payer:&Signer<'info>,destination:&AccountInfo<'info>,system_program:&Program<'info,System>)->Result<()>{", 'ensure_rent_exempt(&a.payer,a.recipient.as_ref(),&a.system_program)', None),
 ("fn ensure_rent_exempt<'info>(destination:&AccountInfo<'info>,system_program:&Program<'info,System>,payer:&Signer<'info>)->Result<()>{", 'ensure_rent_exempt(a.recipient.as_ref(),&a.system_program,&a.payer)', None),
 ("fn ensure_rent_exempt<'info>(system_program:&Program<'info,System>,payer:&Signer<'info>,destination:&UncheckedAccount<'info>)->Result<()>{", 'ensure_rent_exempt(&a.system_program,&a.payer,&a.recipient)', None),
 ("fn ensure_rent_exempt<'info>(a:&SweepFees<'info>)->Result<()>{let destination=a.recipient.as_ref();let system_program=&a.system_program;let payer=&a.payer;", 'ensure_rent_exempt(a)', None),
 ("fn ensure_rent_exempt<'info>(a:&SweepFees<'info>)->Result<()>{", 'ensure_rent_exempt(a)', lambda b: b.replace('system_program.as_ref()', 'a.system_program.as_ref()').replace('destination.lamports()', 'a.recipient.lamports()').replace('payer,destination', '&a.payer,a.recipient.as_ref()')),
]
def make(choice):
    lines = open(BASE).read().split('\n')
    tail = [EXTRA[(k, v)] for k, v in sorted(choice.items()) if (k, v) in EXTRA]
    # apply from bottom to top so line numbers stay valid
    for key in sorted(CH, key=lambda k: -CH[k][0]):
        i = choice.get(key, 0)
        lo, hi, alts = CH[key]
        alt = alts[i]
        if alt is None: continue
        new = alt.split('\n')
        assert len(new) == hi - lo + 1, (key, i, len(new), hi - lo + 1)
        lines[lo - 1:hi] = new
    rs = RSIG[choice.get('rsig', 0)]
    assert lines[179] == SIG0, lines[179]
    lines[179] = rs[0]
    if rs[2]:
        lines[180] = rs[2](lines[180]); lines[181] = rs[2](lines[181])
    txt = '\n'.join(lines)
    assert txt.count(BASECALL) == 1
    lines = txt.replace(BASECALL, rs[1]).split('\n')
    if tail:
        while lines and lines[-1] == '': lines.pop()
        lines += tail + ['']
    return '\n'.join(lines)

if __name__ == '__main__':
    args = sys.argv[1:]; o = args[args.index('-o') + 1]; args = [x for x in args if x != '-o' and x != o]
    ch = {k: int(v) for k, v in (x.split('=') for x in args)}
    open(o, 'w').write(make(ch))
