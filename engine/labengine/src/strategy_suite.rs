//! Deterministic ten-strategy embedded-vector task. It deliberately reuses the
//! accepted Layer-1 kernels and the accepted one-position execution precedence.
use serde_json::{json,Map,Value};
use sha2::{Digest,Sha256};
use crate::indicators;

pub type Result<T>=std::result::Result<T,String>;

#[derive(Clone)] struct Bar{timestamp:String,open:f64,high:f64,low:f64,close:f64,session:bool,friday:bool,rollover:bool,monday:bool}
fn sha(value:&Value)->String{let mut h=Sha256::new();h.update(serde_json::to_vec(value).expect("json"));format!("{:x}",h.finalize())}
fn req<'a>(o:&'a Map<String,Value>,key:&str)->Result<&'a Value>{o.get(key).ok_or_else(||format!("missing {key}"))}
fn text(o:&Map<String,Value>,key:&str)->Result<String>{req(o,key)?.as_str().filter(|x|!x.is_empty()).map(str::to_owned).ok_or_else(||format!("invalid {key}"))}
fn number(o:&Map<String,Value>,key:&str)->Result<f64>{req(o,key)?.as_f64().filter(|x|x.is_finite()).ok_or_else(||format!("invalid {key}"))}
fn boolean(o:&Map<String,Value>,key:&str)->Result<bool>{req(o,key)?.as_bool().ok_or_else(||format!("invalid {key}"))}
fn bars(value:&Value)->Result<Vec<Bar>>{value.as_array().ok_or("bars must be array")?.iter().map(|v|{let o=v.as_object().ok_or("bar must be object")?;let b=Bar{timestamp:text(o,"timestamp")?,open:number(o,"open")?,high:number(o,"high")?,low:number(o,"low")?,close:number(o,"close")?,session:boolean(o,"session_member")?,friday:boolean(o,"friday_close")?,rollover:boolean(o,"rollover")?,monday:boolean(o,"monday_delay")?};if b.low>b.open.min(b.close)||b.high<b.open.max(b.close){return Err("malformed OHLC".into())}Ok(b)}).collect()}
fn cross(a:Option<f64>,b:Option<f64>,pa:Option<f64>,pb:Option<f64>,above:bool)->bool{match(a,b,pa,pb){(Some(x),Some(y),Some(px),Some(py))=>if above{px<=py&&x>y}else{px>=py&&x<y},_=>false}}
fn shifted_window(values:&[f64],period:usize,highest:bool)->Vec<Option<f64>>{let mut out=vec![None;values.len()];for i in period..values.len(){let w=&values[i-period..i];out[i]=Some(if highest{w.iter().copied().fold(f64::NEG_INFINITY,f64::max)}else{w.iter().copied().fold(f64::INFINITY,f64::min)})}out}

fn simulate(strategy:&Map<String,Value>,segment:&Map<String,Value>)->Result<Value>{
 let strategy_identity=text(strategy,"strategy_identity")?;if text(segment,"strategy_identity")?!=strategy_identity{return Err("strategy fixture binding".into())}
 let side=req(strategy,"direction_support")?.as_array().and_then(|x|x.first()).and_then(Value::as_str).ok_or("direction")?;let long=side=="long";if !long&&side!="short"{return Err("direction".into())}
 let family=text(strategy,"family")?;let params=req(strategy,"parameters")?.as_object().ok_or("parameters")?;let period=req(params,"period")?.as_u64().and_then(|x|usize::try_from(x).ok()).filter(|x|*x>0).ok_or("period")?;
 let bs=bars(req(segment,"bars")?)?;let close=bs.iter().map(|x|x.close).collect::<Vec<_>>();let high=bs.iter().map(|x|x.high).collect::<Vec<_>>();let low=bs.iter().map(|x|x.low).collect::<Vec<_>>();let atr=indicators::atr(&high,&low,&close,3)?;
 let (reference,signal,opposite)=if family=="trend-pullback"{let ema=indicators::ema(&close,period)?;let slope=indicators::transform_slope(&ema,1)?;let distance=indicators::transform_distance_atr(&close.iter().copied().map(Some).collect::<Vec<_>>(),&ema,&atr)?;let limit=req(params,"distance_atr_limit")?.as_f64().ok_or("distance limit")?;let mut signal=vec![false;bs.len()];let mut opposite=vec![false;bs.len()];for i in 1..bs.len(){let up=cross(Some(close[i]),ema[i],Some(close[i-1]),ema[i-1],true);let down=cross(Some(close[i]),ema[i],Some(close[i-1]),ema[i-1],false);let directional=if long{up}else{down};signal[i]=directional&&slope[i].map_or(false,|x|if long{x>0.0}else{x<0.0})&&distance[i].map_or(false,|x|x.abs()<=limit);opposite[i]=if long{down}else{up}}(ema,signal,opposite)}else{let level=shifted_window(if long{&high}else{&low},period,long);let mut signal=vec![false;bs.len()];let mut opposite=vec![false;bs.len()];for i in 1..bs.len(){signal[i]=cross(Some(close[i]),level[i],Some(close[i-1]),level[i-1],long);opposite[i]=cross(Some(close[i]),level[i],Some(close[i-1]),level[i-1],!long)}(level,signal,opposite)};
 let intent_identity=sha(&json!({"strategy_identity":strategy_identity,"entry":signal,"exit":opposite,"reference":reference}));let ast_identity=sha(req(strategy,"entry_ast")?);
 let max_hold=req(req(strategy,"exit_rule")?.as_object().ok_or("exit_rule")?,"maximum_holding_bars")?.as_u64().ok_or("max hold")? as usize;
 let bracket=req(strategy,"brackets")?.as_object().ok_or("brackets")?;let stop_mult=number(bracket,"stop_atr_multiple")?;let target_mult=number(bracket,"target_atr_multiple")?;
 let time=req(strategy,"time_session_rule")?.as_object().ok_or("time")?;let filter_roll=boolean(time,"rollover_filter")?;let filter_mon=boolean(time,"monday_delay")?;
 let mut trades=Vec::new();let mut pending:Option<usize>=None;let mut position:Option<(usize,usize,f64,f64,f64)>=None;let mut ordinal=0usize;let mut suppressed=false;let mut terminal=false;
 for i in 0..bs.len(){
  if let Some(source)=pending.take(){if position.is_none(){let entry=bs[i].open;let width=atr[source].ok_or("entry ATR unavailable")?;position=Some((source,i,entry,if long{entry-stop_mult*width}else{entry+stop_mult*width},if long{entry+target_mult*width}else{entry-target_mult*width}));}}
  if let Some((source,entry,entry_price,stop,target))=position{
   if i>entry{let b=&bs[i];let gap_stop=if long{b.open<=stop}else{b.open>=stop};let gap_target=if long{b.open>=target}else{b.open<=target};let signal_exit=opposite[i];let time_exit=b.friday||i-entry>=max_hold;let stop_hit=if long{b.low<=stop}else{b.high>=stop};let target_hit=if long{b.high>=target}else{b.low<=target};
    let exit=if gap_stop{Some((b.open,"gap_stop"))}else if gap_target{Some((b.open,"gap_target"))}else if signal_exit{Some((b.close,"signal_exit"))}else if time_exit{Some((b.close,if b.friday{"friday_close"}else{"time_exit"}))}else if stop_hit&&target_hit{Some((stop,"pessimistic_dual_touch"))}else if stop_hit{Some((stop,"stop"))}else if target_hit{Some((target,"target"))}else{None};
    if let Some((price,reason))=exit{ordinal+=1;trades.push(json!({"strategy_identity":strategy_identity,"trade_ordinal":ordinal,"direction":side,"signal_index":source,"signal_timestamp":bs[source].timestamp,"entry_index":entry,"entry_timestamp":bs[entry].timestamp,"entry_price":entry_price,"initial_stop":stop,"initial_target":target,"exit_index":i,"exit_timestamp":b.timestamp,"exit_price":price,"exit_reason":reason,"holding_bars":i-entry,"gross_price_return":if long{price-entry_price}else{entry_price-price},"no_trade_reason":null,"terminal_source_disposition":"not_executed"}));position=None;}
   }
  }
  if position.is_none()&&pending.is_none()&&signal[i]{let allowed=bs[i].session&&!(filter_roll&&bs[i].rollover)&&!(filter_mon&&bs[i].monday);if !allowed{suppressed=true}else if i+1==bs.len(){terminal=true}else{pending=Some(i)}}
 }
 if trades.is_empty(){trades.push(json!({"strategy_identity":strategy_identity,"trade_ordinal":null,"direction":side,"signal_index":null,"signal_timestamp":null,"entry_index":null,"entry_timestamp":null,"entry_price":null,"initial_stop":null,"initial_target":null,"exit_index":null,"exit_timestamp":null,"exit_price":null,"exit_reason":null,"holding_bars":null,"gross_price_return":null,"no_trade_reason":if terminal{"terminal_source"}else if suppressed{"outside_session"}else{"none"},"terminal_source_disposition":if terminal{"not_executed"}else{"none"}}));}
 let simulator_identity=sha(&Value::Array(trades.clone()));Ok(json!({"strategy_identifier":text(strategy,"strategy_identifier")?,"strategy_identity":strategy_identity,"evaluated_ast_identity":ast_identity,"intent_identity":intent_identity,"simulator_output_identity":simulator_identity,"ledger_vector_identity":simulator_identity,"trades":trades}))
}

pub fn task(o:&Map<String,Value>)->Result<Value>{
 for key in o.keys(){if !["task_version","task_type","suite","fixtures","rng_identity"].contains(&key.as_str()){return Err(format!("unknown task field {key:?}"))}}
 let suite=req(o,"suite")?.as_object().ok_or("suite")?;if text(suite,"schema_version")?!="nora.phase2_ten_strategy_suite_v1"{return Err("suite schema".into())}let strategies=req(suite,"strategies")?.as_array().filter(|x|x.len()==10).ok_or("exactly ten strategies required")?;
 let fixtures=req(o,"fixtures")?.as_object().ok_or("fixtures")?;let segments=req(fixtures,"segments")?.as_array().filter(|x|x.len()==10).ok_or("exactly ten fixtures required")?;let mut outputs=Vec::new();for(strategy,segment)in strategies.iter().zip(segments){outputs.push(simulate(strategy.as_object().ok_or("strategy")?,segment.as_object().ok_or("segment")?)?)}
 let combined=sha(&Value::Array(outputs.clone()));Ok(json!({"ok":true,"task_type":"phase2_ten_strategy_suite_v1","schema_version":"nora.phase2_ten_strategy_rust_output_v1","suite_identity":text(suite,"suite_identity")?,"rng_identity":text(o,"rng_identity")?,"strategy_outputs":outputs,"combined_rust_evidence_identity":combined}))
}

#[cfg(test)]mod tests{use super::*;#[test]fn shifted_level_excludes_decision_bar(){assert_eq!(shifted_window(&[1.,2.,9.,4.],2,true),vec![None,None,Some(2.),Some(9.)])}#[test]fn cross_is_edge_only(){assert!(cross(Some(2.),Some(1.),Some(1.),Some(1.),true));assert!(!cross(Some(3.),Some(1.),Some(2.),Some(1.),true));}}
