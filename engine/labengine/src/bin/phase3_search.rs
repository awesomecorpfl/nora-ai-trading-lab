//! Deterministic Phase-3 sampler/evaluator. It accepts IS Parquet only.
use arrow_array::{Array, Float64Array, StringArray};
use parquet::arrow::arrow_reader::ParquetRecordBatchReaderBuilder;
use serde::{Deserialize, Serialize};
use serde_json::json;
use sha2::{Digest, Sha256};
use std::{collections::{BTreeMap, BTreeSet, HashMap}, env, fs::File, path::Path};

#[derive(Clone)] struct Market { ts: Vec<String>, o: Vec<f64>, h: Vec<f64>, l: Vec<f64>, c: Vec<f64> }
#[derive(Clone, Serialize)] struct Candidate { family: String, symbol: String, side: String, fast: usize, slow: usize, atr_period: usize, distance_limit: f64, slope_lookback: usize, lookback: usize, max_bars: usize, stop_atr: f64, target_atr: f64, breakout_buffer: f64 }
#[derive(Clone, Serialize, Deserialize)] struct ResultRow { trial: usize, candidate_index: usize, candidate_identity: String, family: String, symbol: String, state: String, duplicate_of: Option<String>, trades: usize, average_trade: Option<f64>, max_drawdown_fraction: Option<f64>, descriptor: BTreeMap<String,String>, archive_cell: String, lineage: BTreeMap<String,String> }

fn canon<T: serde::Serialize>(v: &T) -> String { serde_json::to_string(v).unwrap() }
fn id(domain: &str, value: &str) -> String { let mut h=Sha256::new(); h.update(domain.as_bytes()); h.update([0]); h.update(value.as_bytes()); format!("{:x}",h.finalize()) }
fn read(path: &Path) -> Result<Market,String> {
    let s=path.to_string_lossy().to_ascii_lowercase(); if s.contains("lockbox")||s.contains("lock_box"){return Err("Phase-3 evaluator refuses lockbox input".into())}
    let b=ParquetRecordBatchReaderBuilder::try_new(File::open(path).map_err(|e|e.to_string())?).map_err(|e|e.to_string())?;
    let mut ts=Vec::new(); let(mut o,mut h,mut l,mut c)=(Vec::new(),Vec::new(),Vec::new(),Vec::new());
    for batch in b.with_batch_size(8192).build().map_err(|e|e.to_string())? { let b=batch.map_err(|e|e.to_string())?;
        let t=b.column_by_name("timestamp").and_then(|x|x.as_any().downcast_ref::<StringArray>()).ok_or("missing timestamp")?;
        let cols=|n:&str|b.column_by_name(n).and_then(|x|x.as_any().downcast_ref::<Float64Array>()).ok_or_else(||format!("missing {n}"));
        let(oa,ha,la,ca)=(cols("open")?,cols("high")?,cols("low")?,cols("close")?);
        for i in 0..b.num_rows(){if t.is_null(i)||oa.is_null(i)||ha.is_null(i)||la.is_null(i)||ca.is_null(i){return Err("null market field".into())}ts.push(t.value(i).to_owned());o.push(oa.value(i));h.push(ha.value(i));l.push(la.value(i));c.push(ca.value(i));}
    }
    Ok(Market{ts,o,h,l,c})
}
fn ema(x:&[f64], n:usize)->Vec<f64>{let mut out=vec![f64::NAN;x.len()];if x.len()<n{return out}let mut v=x[..n].iter().sum::<f64>()/n as f64;out[n-1]=v;let a=2./(n as f64+1.);for i in n..x.len(){v+=a*(x[i]-v);out[i]=v}out}
fn atr(m:&Market,n:usize)->Vec<f64>{let mut tr=vec![0.;m.c.len()];for i in 1..m.c.len(){tr[i]=(m.h[i]-m.l[i]).max((m.h[i]-m.c[i-1]).abs()).max((m.l[i]-m.c[i-1]).abs())}let mut out=vec![f64::NAN;m.c.len()];if m.c.len()<n{return out}let mut v=tr[..n].iter().sum::<f64>()/n as f64;out[n-1]=v;for i in n..m.c.len(){v=(v*(n-1)as f64+tr[i])/n as f64;out[i]=v}out}
fn rolling_high(x:&[f64],n:usize, high:bool)->Vec<f64>{let mut o=vec![f64::NAN;x.len()];for i in n..x.len(){let w=&x[i-n..i];o[i]=if high{w.iter().copied().fold(f64::NEG_INFINITY,f64::max)}else{w.iter().copied().fold(f64::INFINITY,f64::min)}}o}
fn pick_usize(values:&[usize], n:usize)->usize{values[n%values.len()]}
fn pick_f64(values:&[f64], n:usize)->f64{values[n%values.len()]}
fn candidate(family:&str,symbol:&str,n:usize)->Candidate{
    if family=="trend-pullback" {let fast=[5,8,13,21,34];let slow=[34,55,89,144,233,377];let atrp=[7,14,21,28];let dist=[0.25,0.5,0.75,1.0];let slope=[1,3,5];let hold=[8,16,32];let stop=[0.5,1.0,1.5];let target=[1.0,2.0,3.0];Candidate{family:family.into(),symbol:symbol.into(),side:if n%2==0{"long".into()}else{"short".into()},fast:pick_usize(&fast,n/2),slow:pick_usize(&slow,n/10),atr_period:pick_usize(&atrp,n/60),distance_limit:dist[(n/240)%dist.len()],slope_lookback:pick_usize(&slope,n/960),lookback:0,max_bars:pick_usize(&hold,n/2880),stop_atr:pick_f64(&stop,n/8640),target_atr:pick_f64(&target,n/25920),breakout_buffer:0.0}
    } else {let lb=[5,10,20,40,80,120];let atrp=[7,14,21,28];let hold=[8,16,32];let stop=[0.5,1.0,1.5];let target=[1.0,2.0,3.0];let buf=[0.0,0.1,0.25,0.5];Candidate{family:family.into(),symbol:symbol.into(),side:if n%2==0{"long".into()}else{"short".into()},fast:0,slow:0,atr_period:pick_usize(&atrp,n/2),distance_limit:0.0,slope_lookback:0,lookback:pick_usize(&lb,n/8),max_bars:pick_usize(&hold,n/48),stop_atr:pick_f64(&stop,n/144),target_atr:pick_f64(&target,n/432),breakout_buffer:buf[(n/1296)%buf.len()]}}
}
fn refine(mut c: Candidate, step: usize) -> Candidate {
    if c.family == "trend-pullback" {
        match step % 4 { 0 => c.distance_limit = [0.25,0.5,0.75,1.0][step % 4], 1 => c.max_bars = [8,16,32][step % 3], 2 => c.stop_atr = [0.5,1.0,1.5][step % 3], _ => c.target_atr = [1.0,2.0,3.0][step % 3] }
    } else {
        match step % 4 { 0 => c.lookback = [5,10,20,40,80,120][step % 6], 1 => c.max_bars = [8,16,32][step % 3], 2 => c.stop_atr = [0.5,1.0,1.5][step % 3], _ => c.breakout_buffer = [0.0,0.1,0.25,0.5][step % 4] }
    }
    c
}
fn bucket(v:f64, a:f64,b:f64)->String{if v<a{"low".into()}else if v<b{"mid".into()}else{"high".into()}}
fn evaluate(m:&Market,c:&Candidate,emas:&mut HashMap<usize,Vec<f64>>,atrs:&mut HashMap<usize,Vec<f64>>,roll:&mut HashMap<(usize,bool),Vec<f64>>)->(usize,Option<f64>,Option<f64>,BTreeMap<String,String>,String){
    let atrs_v=atrs.entry(c.atr_period).or_insert_with(||atr(m,c.atr_period)).clone(); let (fast,slow)=if c.family=="trend-pullback"{(emas.entry(c.fast).or_insert_with(||ema(&m.c,c.fast)).clone(),emas.entry(c.slow).or_insert_with(||ema(&m.c,c.slow)).clone())}else{(Vec::new(),Vec::new())}; let levels=if c.family!="trend-pullback"{Some((roll.entry((c.lookback,true)).or_insert_with(||rolling_high(&m.c,c.lookback,true)).clone(),roll.entry((c.lookback,false)).or_insert_with(||rolling_high(&m.c,c.lookback,false)).clone()))}else{None};
    let mut open:Option<(usize,f64,f64)>=None; let mut pnls=Vec::new(); let mut holds=Vec::new(); let mut longs=0usize; let mut hours:HashMap<String,usize>=HashMap::new();
    for i in 1..m.c.len(){let valid=atrs_v[i].is_finite();if !valid{continue}let entry=if c.family=="trend-pullback"{let slope=if i>=c.slope_lookback{(slow[i]-slow[i-c.slope_lookback])/c.slope_lookback as f64}else{f64::NAN};let d=(m.c[i]-fast[i]).abs()/atrs_v[i];if !fast[i].is_finite()||!slow[i].is_finite()||!slope.is_finite(){false}else if c.side=="long"{m.c[i-1]<=fast[i-1]&&m.c[i]>fast[i]&&fast[i]>slow[i]&&slope>0.&&d<=c.distance_limit}else{m.c[i-1]>=fast[i-1]&&m.c[i]<fast[i]&&fast[i]<slow[i]&&slope<0.&&d<=c.distance_limit}}else{let (hi,lo)=levels.as_ref().unwrap();if !hi[i].is_finite(){false}else if c.side=="long"{m.c[i-1]<=hi[i-1]&&m.c[i]>hi[i]*(1.+c.breakout_buffer/10000.)}else{m.c[i-1]>=lo[i-1]&&m.c[i]<lo[i]*(1.-c.breakout_buffer/10000.)}};
        if let Some((ei,price,entry_atr))=open {let mut close=None;if i-ei>=c.max_bars{close=Some(price*0.+m.o[i])}else{let(stop,target)=if c.side=="long"{(price-entry_atr*c.stop_atr,price+entry_atr*c.target_atr)}else{(price+entry_atr*c.stop_atr,price-entry_atr*c.target_atr)};if c.side=="long"{if m.o[i]<=stop{close=Some(m.o[i])}else if m.o[i]>=target{close=Some(m.o[i])}else if m.l[i]<=stop{close=Some(stop)}else if m.h[i]>=target{close=Some(target)}else if !entry{continue}}else if m.o[i]>=stop{close=Some(m.o[i])}else if m.o[i]<=target{close=Some(m.o[i])}else if m.h[i]>=stop{close=Some(stop)}else if m.l[i]<=target{close=Some(target)}else if !entry{continue}}if let Some(exit)=close{let pnl=if c.side=="long"{exit-price}else{price-exit};pnls.push(pnl);holds.push(i-ei);*hours.entry(m.ts[ei].get(11..13).unwrap_or("00").to_string()).or_insert(0)+=1;if c.side=="long"{longs+=1}open=None;}}
        if open.is_none()&&entry{open=Some((i,m.o[i],atrs_v[i]));}
    }
    if pnls.is_empty(){return (0,None,None,BTreeMap::new(),"empty".into())}let avg=pnls.iter().sum::<f64>()/pnls.len()as f64;let mut equity: f64=0.;let mut peak: f64=0.;let mut dd: f64=0.;for p in &pnls{equity+=p;peak=peak.max(equity);dd=dd.max(peak-equity)}let dd_frac=dd/m.o[0].abs();let n=pnls.len();let hold=holds.iter().sum::<usize>()as f64/n as f64;let long_frac=longs as f64/n as f64;let months=(m.ts.last().map(|x|x.get(0..7).unwrap_or("2024")).unwrap_or("2024"),m.ts.first().map(|x|x.get(0..7).unwrap_or("2024")).unwrap_or("2024"));let months_count=if months.0==months.1{1.}else{12.};let trades_month=n as f64/months_count;let top_session=hours.values().copied().max().unwrap_or(0)as f64/n as f64;let mut d=BTreeMap::new();d.insert("trades_per_month".into(),bucket(trades_month,2.,8.));d.insert("holding_period".into(),bucket(hold,5.,20.));d.insert("long_short_balance".into(),bucket(long_frac,0.33,0.67));d.insert("session_concentration".into(),bucket(top_session,0.10,0.25));let cell=canon(&d);(n,Some(avg),Some(dd_frac),d,cell)
}
fn main(){
    let a:Vec<String>=env::args().collect(); let get=|k:&str|a.iter().position(|x|x==k).and_then(|i|a.get(i+1)).cloned().unwrap_or_default();
    let input=get("--input"); let family=get("--family"); let symbol=get("--symbol"); let mode=get("--mode"); let output=get("--output"); let checkpoint=get("--checkpoint");
    let trials:usize=get("--trials").parse().unwrap_or(0); let sampled:usize=get("--sampled-trials").parse().unwrap_or(trials); let refinement:usize=get("--refinement-trials").parse().unwrap_or(0); let batch:usize=get("--batch-size").parse().unwrap_or(100); let interrupt:usize=get("--interrupt-after").parse().unwrap_or(usize::MAX);
    if input.is_empty()||output.is_empty()||checkpoint.is_empty()||trials==0||!(family=="trend-pullback"||family=="close-confirmed-breakout")||symbol.is_empty(){eprintln!("invalid Phase-3 search arguments");std::process::exit(2)}
    let market=match read(Path::new(&input)){Ok(x)=>x,Err(e)=>{eprintln!("{e}");std::process::exit(2)}};
    let mut rows:Vec<ResultRow>=Vec::new(); if Path::new(&checkpoint).is_file(){if let Ok(v)=std::fs::read_to_string(&checkpoint){if let Ok(x)=serde_json::from_str::<Vec<ResultRow>>(&v){rows=x}}}
    let mut seen:HashMap<String,String>=rows.iter().map(|r|(r.candidate_identity.clone(),r.candidate_identity.clone())).collect(); let mut emas=HashMap::new();let mut atrs=HashMap::new();let mut roll=HashMap::new();
    let total=sampled+refinement; if trials!=0 && trials!=total{eprintln!("--trials must equal sampled plus refinement trials");std::process::exit(2)}
    let start=rows.len(); for trial in start..total {let (idx,c,parent)=if trial<sampled{let idx=if mode=="random"{(trial.wrapping_mul(7919).wrapping_add(104729))%100000}else{trial};(idx,candidate(&family,&symbol,idx),None)}else{let step=trial-sampled;let parent_idx=if mode=="random"{(step.wrapping_mul(7919).wrapping_add(104729))%sampled.max(1)}else{step%sampled.max(1)};let parent=candidate(&family,&symbol,parent_idx);let parent_id=id("nora.phase3.strategy.v1",&canon(&parent));(100000+step,refine(parent,step),Some(parent_id))};let cid=id("nora.phase3.strategy.v1",&canon(&c));if let Some(prior)=seen.get(&cid){rows.push(ResultRow{trial,candidate_index:idx,candidate_identity:cid,family:family.clone(),symbol:symbol.clone(),state:"duplicate_rejected".into(),duplicate_of:Some(prior.clone()),trades:0,average_trade:None,max_drawdown_fraction:None,descriptor:BTreeMap::new(),archive_cell:"".into(),lineage:BTreeMap::new()});}else{let(n,avg,dd,desc,cell)=evaluate(&market,&c,&mut emas,&mut atrs,&mut roll);let pass=n>=30&&dd.map(|x|x<=0.10).unwrap_or(false);let mut lineage=BTreeMap::new();lineage.insert("template_identity".into(),id("nora.phase3.template.v1",&family));lineage.insert("parent_identity".into(),parent.unwrap_or_else(||"root_stratified_template".into()));lineage.insert("sampler_mode".into(),mode.clone());lineage.insert("stage".into(),if trial<sampled{"stratified_sample_v1".into()}else{"local_refinement_v1".into()});rows.push(ResultRow{trial,candidate_index:idx,candidate_identity:cid.clone(),family:family.clone(),symbol:symbol.clone(),state:if pass{"accepted".into()}else{"rejected_threshold".into()},duplicate_of:None,trades:n,average_trade:avg,max_drawdown_fraction:dd,descriptor:desc,archive_cell:cell,lineage});seen.insert(cid.clone(),cid);}
        if (trial+1)%batch==0||trial+1==trials{std::fs::write(&checkpoint,serde_json::to_string(&rows).unwrap()).unwrap();}
        if trial+1>=interrupt{std::process::exit(75)}
    }
    let accepted:Vec<&ResultRow>=rows.iter().filter(|r|r.state=="accepted").collect();let cells:BTreeSet<String>=accepted.iter().map(|r|r.archive_cell.clone()).collect();let best=accepted.iter().filter_map(|r|r.average_trade).fold(None,|a,x|Some(a.map_or(x,|v:f64|v.max(x))));let summary=json!({"schema_version":"nora.phase3.search_result_v1","family":family,"symbol":symbol,"mode":mode,"trials":rows.len(),"unique_evaluated":rows.iter().filter(|r|r.duplicate_of.is_none()).count(),"duplicate_rejected":rows.iter().filter(|r|r.duplicate_of.is_some()).count(),"accepted":accepted.len(),"archive_cells":cells.len(),"best_average_trade":best,"trade_floor":30,"max_drawdown_fraction":0.10,"rows":rows});std::fs::write(&output,serde_json::to_string(&summary).unwrap()).unwrap();std::fs::remove_file(&checkpoint).ok();
}
