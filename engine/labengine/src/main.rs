//! Deterministic kernels plus the Phase 2A-1A Phase-1 canonical Parquet reader.
use std::{
    collections::{hash_map::DefaultHasher, HashSet},
    env, fs,
    hash::{Hash, Hasher},
    path::Path,
};
#[cfg(test)] use std::sync::Arc;

use arrow_array::{Array, Float64Array, RecordBatch, StringArray};
use chrono::NaiveDateTime;
use parquet::arrow::arrow_reader::ParquetRecordBatchReaderBuilder;
use serde_json::{Map, Value};
use sha2::{Digest, Sha256};

pub mod time;
pub mod aggregation;
pub mod task;
pub mod indicators;
pub mod series;
pub mod indicator_artifact;
pub mod ast;
pub mod exit_condition;
pub mod simulator;
pub mod closed_trade_metrics;
pub mod rng_stream;

/// Stable public boundary for the Phase-1 canonical reader.
pub mod data {
    pub use super::{CanonicalM1Bar, CanonicalM1Dataset, TimeContract, read_canonical_m1_parquet};
}

const PHASE1_METADATA_CONTRACT: &str = "nora.contract";
const PHASE1_METADATA_SOURCE_SHA256: &str = "nora.source_sha256";
const PHASE1_METADATA_TIMEFRAME: &str = "nora.timeframe";
const LEGACY_PHASE1_CONTRACT_VERSION: u32 = 1;

#[derive(Clone, Copy, Debug)] pub struct Bar { pub minute:i64, pub o:f64, pub h:f64, pub l:f64, pub c:f64, pub v:f64, pub spread:f64 }
pub fn aggregate(b:&[Bar], minutes:i64)->Vec<Bar>{let mut out=Vec::new();for x in b{let k=x.minute-x.minute.rem_euclid(minutes);if out.last().map(|z:&Bar|z.minute)!=Some(k){out.push(Bar{minute:k,o:x.o,h:x.h,l:x.l,c:x.c,v:x.v,spread:x.spread})}else{let z=out.last_mut().unwrap();z.h=z.h.max(x.h);z.l=z.l.min(x.l);z.c=x.c;z.v+=x.v;z.spread=x.spread}}out}
fn sma(x:&[f64],n:usize)->Vec<Option<f64>>{(0..x.len()).map(|i|if i+1<n{None}else{Some(x[i+1-n..=i].iter().sum::<f64>()/n as f64)}).collect()}
fn ema(x:&[f64],n:usize)->Vec<Option<f64>>{let mut o=vec![None;x.len()];if x.len()<n{return o}let a=2./(n as f64+1.);let mut e=x[..n].iter().sum::<f64>()/n as f64;o[n-1]=Some(e);for i in n..x.len(){e+=a*(x[i]-e);o[i]=Some(e)}o}
pub fn atr(b:&[Bar],n:usize)->Vec<Option<f64>>{let tr:Vec<_>=b.iter().enumerate().map(|(i,x)|if i==0{x.h-x.l}else{(x.h-x.l).max((x.h-b[i-1].c).abs()).max((x.l-b[i-1].c).abs())}).collect();ema(&tr,n)}
pub fn rsi(x:&[f64],n:usize)->Vec<Option<f64>>{let mut o=vec![None;x.len()];if x.len()<=n{return o}let(mut g,mut l)=(0.,0.);for i in 1..=n{let d=x[i]-x[i-1];g+=d.max(0.);l+=(-d).max(0.)}g/=n as f64;l/=n as f64;o[n]=Some(if l==0.{100.}else{100.-100./(1.+g/l)});for i in n+1..x.len(){let d=x[i]-x[i-1];g=(g*(n-1)as f64+d.max(0.))/n as f64;l=(l*(n-1)as f64+(-d).max(0.))/n as f64;o[i]=Some(if l==0.{100.}else{100.-100./(1.+g/l)})}o}
pub fn cross(a:&[f64],b:&[f64],i:usize)->bool{i>0&&a[i-1]<=b[i-1]&&a[i]>b[i]}
pub fn slope(a:&[f64],i:usize,n:usize)->Option<f64>{if i<n{None}else{Some((a[i]-a[i-n])/n as f64)}}
pub fn percentile(a:&[f64],x:f64)->f64{let mut v=a.to_vec();v.sort_by(|a,b|a.total_cmp(b));v.iter().filter(|q|**q<=x).count()as f64/v.len()as f64}
pub fn seed(parts:&[&str])->u64{let mut h=DefaultHasher::new();parts.hash(&mut h);h.finish()}
pub fn time_rules_identity(rows:&[Value])->String{let mut h=Sha256::new();h.update(b"nora.time_rules_v1");for row in rows{h.update(serde_json::to_string(row).unwrap().as_bytes());}format!("{:x}",h.finalize())}
#[derive(Clone,Copy)] pub enum Side{Long,Short} #[derive(Clone,Copy)] pub struct Trade{pub side:Side,pub entry:f64,pub exit:f64,pub costs:f64,pub bars:usize}
pub fn pnl(t:Trade)->f64{match t.side{Side::Long=>t.exit-t.entry-t.costs,Side::Short=>t.entry-t.exit-t.costs}}
pub fn pessimistic(side:Side,b:Bar,sl:f64,tp:f64)->Option<f64>{match side{Side::Long=>if b.l<=sl{Some(sl)}else if b.h>=tp{Some(tp)}else{None},Side::Short=>if b.h>=sl{Some(sl)}else if b.l<=tp{Some(tp)}else{None}}}

#[derive(Debug, Clone, PartialEq)]
pub struct TimeContract {
    /// `1` is the unversioned Phase-1 `nora.contract` representation.
    pub version: u32,
    pub provider: String,
    pub acquisition_tool: String,
    pub source_symbol: String,
    pub project_symbol: String,
    pub source_timestamp_semantics: String,
    pub bar_timestamp_semantics: String,
    pub timezone_identity: String,
    pub dst_regime: String,
    pub session_clock: String,
    pub strategy_clock: String,
    pub trading_day_boundary: Option<String>,
    pub higher_timeframe_anchoring: Option<String>,
    pub conversion_history: Vec<Value>,
    pub double_conversion_protection: Option<bool>,
    /// Only the original unversioned Phase-1 wire shape may use 1C's compatibility anchor.
    pub legacy_unversioned: bool,
    canonical_json: String,
}

impl TimeContract {
    /// Normalized source contract JSON used as provenance, never a timestamp conversion record.
    pub fn canonical_json(&self) -> &str { &self.canonical_json }
}

#[derive(Debug, Clone, PartialEq)]
pub struct CanonicalM1Bar {
    /// Original Phase-1 UTF-8 timestamp label. It is never timezone-converted.
    pub timestamp: String,
    /// Parsed only to enforce the Phase-1 local-label ordering contract.
    pub local_timestamp: NaiveDateTime,
    pub open: f64, pub high: f64, pub low: f64, pub close: f64,
    pub volume: Option<f64>, pub spread: Option<f64>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct CanonicalM1Dataset {
    pub contract: TimeContract,
    pub source_sha256: String,
    pub bars: Vec<CanonicalM1Bar>,
    /// SHA-256 over semantic Phase-1 input, not Parquet bytes. See `docs/PHASE_2A_1A.md`.
    pub content_identity: String,
}

type Result<T> = std::result::Result<T, String>;

pub fn read_canonical_m1_parquet(path: impl AsRef<Path>) -> Result<CanonicalM1Dataset> {
    let file = fs::File::open(path.as_ref()).map_err(|e| format!("open canonical Parquet: {e}"))?;
    let builder = ParquetRecordBatchReaderBuilder::try_new(file).map_err(|e| format!("read Parquet metadata: {e}"))?;
    let schema = builder.schema().clone();
    let metadata = schema.metadata();
    let timeframe = required_metadata(metadata, PHASE1_METADATA_TIMEFRAME)?;
    if timeframe != "M1" { return Err(format!("unsupported canonical timeframe {timeframe:?}; expected M1")); }
    let source_sha256 = required_metadata(metadata, PHASE1_METADATA_SOURCE_SHA256)?;
    if !is_sha256(&source_sha256) { return Err("nora.source_sha256 must be a 64-character hexadecimal SHA-256".into()); }
    let contract = parse_contract(&required_metadata(metadata, PHASE1_METADATA_CONTRACT)?)?;
    validate_schema(&schema)?;
    let reader = builder.with_batch_size(8_192).build().map_err(|e| format!("build Parquet reader: {e}"))?;
    let mut bars = Vec::new();
    for batch in reader {
        let batch = batch.map_err(|e| format!("read Parquet batch: {e}"))?;
        append_batch(&batch, &mut bars)?;
    }
    validate_bars(&bars)?;
    let content_identity = semantic_content_identity(&contract, &bars);
    Ok(CanonicalM1Dataset { contract, source_sha256, bars, content_identity })
}

fn required_metadata(metadata: &std::collections::HashMap<String, String>, key: &str) -> Result<String> {
    metadata.get(key).filter(|value| !value.trim().is_empty()).cloned().ok_or_else(|| format!("missing required Phase-1 metadata {key}"))
}

fn is_sha256(value: &str) -> bool { value.len() == 64 && value.bytes().all(|b| b.is_ascii_hexdigit()) }

fn parse_contract(raw: &str) -> Result<TimeContract> {
    let value: Value = serde_json::from_str(raw).map_err(|e| format!("malformed nora.contract JSON: {e}"))?;
    let object = value.as_object().ok_or("nora.contract must be a JSON object")?;
    let legacy_unversioned = !object.contains_key("contract_version") && !object.contains_key("schema_version");
    let version = contract_version(object)?;
    if version != LEGACY_PHASE1_CONTRACT_VERSION { return Err(format!("unsupported nora.contract version {version}")); }
    let get = |key| required_contract_string(object, key);
    let conversion_history = object.get("conversion_history").and_then(Value::as_array).cloned().ok_or("conversion_history must be an array")?;
    let mut targets = HashSet::new();
    for entry in &conversion_history {
        let entry = entry.as_object().ok_or("each conversion_history entry must be an object")?;
        let target = entry.get("target").and_then(Value::as_str).filter(|v| !v.trim().is_empty()).ok_or("each conversion_history entry requires a non-empty target")?;
        if !targets.insert(target) { return Err(format!("double conversion protection: repeated conversion target {target:?}")); }
    }
    let double_conversion_protection = match object.get("double_conversion_protection") {
        Some(Value::Bool(value)) => Some(*value), Some(_) => return Err("double_conversion_protection must be boolean".into()), None => None,
    };
    if !conversion_history.is_empty() && double_conversion_protection == Some(false) { return Err("conversion history exists but double_conversion_protection is false".into()); }
    let contract = TimeContract {
        version, provider:get("provider")?, acquisition_tool:get("acquisition_tool")?, source_symbol:get("source_symbol")?, project_symbol:get("project_symbol")?,
        source_timestamp_semantics:get("source_timestamp_semantics")?, bar_timestamp_semantics:get("bar_timestamp_semantics")?, timezone_identity:get("timezone_identity")?, dst_regime:get("dst_regime")?,
        session_clock:get("session_clock")?, strategy_clock:get("strategy_clock")?,
        trading_day_boundary: optional_contract_string(object, "trading_day_boundary")?, higher_timeframe_anchoring: optional_contract_string(object, "higher_timeframe_anchoring")?,
        conversion_history, double_conversion_protection, legacy_unversioned, canonical_json: serde_json::to_string(&value).expect("JSON values serialize"),
    };
    if contract.bar_timestamp_semantics != "start" { return Err("only Phase-1 M1 start-of-bar timestamps are supported".into()); }
    if is_ambiguous_clock(&contract.session_clock) || is_ambiguous_clock(&contract.strategy_clock) { return Err("session_clock and strategy_clock must be explicit declared clocks, not local/system/default".into()); }
    if contract.timezone_identity.eq_ignore_ascii_case("UTC") && (contract.session_clock != "UTC" || contract.strategy_clock != "UTC") && contract.conversion_history.is_empty() { return Err("UTC timezone with a distinct session/strategy clock requires explicit conversion_history".into()); }
    Ok(contract)
}

fn contract_version(object: &Map<String, Value>) -> Result<u32> {
    let version = match (object.get("contract_version"), object.get("schema_version")) {
        (Some(a), Some(b)) if a != b => return Err("contract_version and schema_version disagree".into()),
        (Some(v), _) | (_, Some(v)) => v.as_u64().and_then(|v| u32::try_from(v).ok()).ok_or("contract/schema version must be an unsigned integer")?,
        // Phase 1 did not serialize a version field; its metadata shape is the legacy v1 contract.
        (None, None) => LEGACY_PHASE1_CONTRACT_VERSION,
    };
    Ok(version)
}
fn required_contract_string(object: &Map<String, Value>, key: &str) -> Result<String> { object.get(key).and_then(Value::as_str).filter(|v| !v.trim().is_empty()).map(str::to_owned).ok_or_else(|| format!("missing or invalid nora.contract.{key}")) }
fn optional_contract_string(object: &Map<String, Value>, key: &str) -> Result<Option<String>> { match object.get(key) { None => Ok(None), Some(Value::String(v)) if !v.trim().is_empty() => Ok(Some(v.clone())), Some(_) => Err(format!("nora.contract.{key} must be a non-empty string when present")), } }
fn is_ambiguous_clock(value: &str) -> bool { matches!(value.to_ascii_lowercase().as_str(), "local" | "system" | "default" | "unknown" | "") }

fn validate_schema(schema: &arrow_schema::Schema) -> Result<()> {
    use arrow_schema::DataType;
    let expected = [("timestamp", DataType::Utf8), ("open", DataType::Float64), ("high", DataType::Float64), ("low", DataType::Float64), ("close", DataType::Float64), ("volume", DataType::Float64), ("spread", DataType::Float64)];
    for (name, datatype) in expected {
        let field = schema.field_with_name(name).map_err(|_| format!("missing required canonical column {name}"))?;
        if field.data_type() != &datatype { return Err(format!("canonical column {name} has type {:?}; expected {:?}", field.data_type(), datatype)); }
    }
    Ok(())
}

fn typed<'a, T: Array + 'static>(batch: &'a RecordBatch, name: &str) -> Result<&'a T> { batch.column_by_name(name).ok_or_else(|| format!("missing batch column {name}"))?.as_any().downcast_ref::<T>().ok_or_else(|| format!("invalid batch type for {name}")) }
fn append_batch(batch: &RecordBatch, bars: &mut Vec<CanonicalM1Bar>) -> Result<()> {
    let timestamp = typed::<StringArray>(batch, "timestamp")?; let open = typed::<Float64Array>(batch, "open")?; let high = typed::<Float64Array>(batch, "high")?; let low = typed::<Float64Array>(batch, "low")?; let close = typed::<Float64Array>(batch, "close")?; let volume = typed::<Float64Array>(batch, "volume")?; let spread = typed::<Float64Array>(batch, "spread")?;
    for row in 0..batch.num_rows() {
        if timestamp.is_null(row) { return Err(format!("timestamp is null at row {row}")); }
        let raw = timestamp.value(row).to_owned();
        let local_timestamp = NaiveDateTime::parse_from_str(&raw, "%Y.%m.%d %H:%M").map_err(|_| format!("timestamp {raw:?} is not a Phase-1 M1 label (%Y.%m.%d %H:%M)"))?;
        let required = |column: &Float64Array, name: &str| -> Result<f64> { if column.is_null(row) { Err(format!("{name} is null at row {row}")) } else { let value=column.value(row); if value.is_finite() { Ok(value) } else { Err(format!("{name} is non-finite at row {row}")) } } };
        let optional = |column: &Float64Array, name: &str| -> Result<Option<f64>> { if column.is_null(row) { Ok(None) } else { let value=column.value(row); if value.is_finite() { Ok(Some(value)) } else { Err(format!("{name} is non-finite at row {row}")) } } };
        bars.push(CanonicalM1Bar { timestamp:raw, local_timestamp, open:required(open,"open")?, high:required(high,"high")?, low:required(low,"low")?, close:required(close,"close")?, volume:optional(volume,"volume")?, spread:optional(spread,"spread")? });
    }
    Ok(())
}
fn validate_bars(bars: &[CanonicalM1Bar]) -> Result<()> {
    if bars.is_empty() { return Err("canonical M1 dataset has no bars".into()); }
    let mut previous = None;
    for bar in bars {
        if bar.low > bar.open.min(bar.high).min(bar.close) || bar.high < bar.open.max(bar.low).max(bar.close) { return Err(format!("malformed OHLC at timestamp {}", bar.timestamp)); }
        if let Some(prior) = previous { if bar.local_timestamp <= prior { return Err(format!("timestamps must be strictly increasing; found {} after {}", bar.timestamp, prior)); } }
        previous = Some(bar.local_timestamp);
    }
    Ok(())
}

fn write_part(hash: &mut Sha256, bytes: &[u8]) { hash.update((bytes.len() as u64).to_be_bytes()); hash.update(bytes); }
fn semantic_content_identity(contract: &TimeContract, bars: &[CanonicalM1Bar]) -> String {
    let mut hash = Sha256::new(); write_part(&mut hash, b"nora-canonical-m1-semantic-v1"); write_part(&mut hash, contract.canonical_json.as_bytes());
    for bar in bars { write_part(&mut hash, bar.timestamp.as_bytes()); for value in [bar.open,bar.high,bar.low,bar.close] { hash.update(value.to_bits().to_be_bytes()); } for value in [bar.volume,bar.spread] { match value { Some(v) => { hash.update([1]); hash.update(v.to_bits().to_be_bytes()); }, None => hash.update([0]), } } }
    format!("{:x}", hash.finalize())
}

fn main() {
    match task::run_cli(env::args().skip(1).collect()) {
        Ok(summary) => println!("{}", serde_json::to_string(&summary).expect("summary JSON")),
        Err(error) => {
            eprintln!("{}", serde_json::json!({"ok":false,"error":error}));
            std::process::exit(2);
        }
    }
}

#[cfg(test)] mod tests {
    use super::*;
    use arrow_array::{Float64Array, StringArray}; use arrow_schema::{DataType, Field, Schema}; use parquet::arrow::ArrowWriter;
    fn bars()->Vec<Bar>{(0..6).map(|i|Bar{minute:i,o:i as f64+1.,h:i as f64+2.,l:i as f64,c:i as f64+1.5,v:1.,spread:0.1}).collect()}
    #[test] fn aggregate_local(){let x=aggregate(&bars(),5);assert_eq!(x.len(),2);assert_eq!(x[0].v,5.)}
    #[test] fn indicators(){let x=[1.,2.,3.,4.,5.,6.];assert_eq!(sma(&x,3)[2],Some(2.));assert_eq!(ema(&x,3)[2],Some(2.));assert_eq!(rsi(&x,2)[2],Some(100.))}
    #[test] fn rules(){let b=Bar{minute:0,o:90.,h:110.,l:80.,c:90.,v:1.,spread:0.};assert_eq!(pessimistic(Side::Long,b,85.,105.),Some(85.));assert!(cross(&[1.,1.,3.],&[2.,2.,2.],2));assert_eq!(seed(&["e","a"]),seed(&["e","a"]));}
    #[test] fn costs(){assert_eq!(pnl(Trade{side:Side::Long,entry:1.,exit:2.,costs:0.2,bars:1}),0.8)}
    #[test] fn phase1_utc_fixture_loads_without_conversion_and_is_stable() { let path=Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures/phase1_utc_m1.parquet"); let first=read_canonical_m1_parquet(&path).unwrap(); let second=read_canonical_m1_parquet(&path).unwrap(); assert_eq!(first.contract.timezone_identity,"UTC"); assert_eq!(first.bars[0].timestamp,"2025.06.03 08:00"); assert_eq!(first.bars[0].local_timestamp,NaiveDateTime::parse_from_str("2025.06.03 08:00","%Y.%m.%d %H:%M").unwrap()); let model=crate::time::ClockModel::from_contract(&first.contract).unwrap(); assert_eq!(model.interpret_dataset_label(first.bars[0].local_timestamp).unwrap().local,first.bars[0].local_timestamp); assert_eq!(first.content_identity,second.content_identity); }
    #[test] fn contract_rejects_missing_malformed_unsupported_and_ambiguous() { for raw in ["{}", "{", r#"{\"provider\":\"p\",\"acquisition_tool\":\"a\",\"source_symbol\":\"s\",\"project_symbol\":\"s\",\"source_timestamp_semantics\":\"UTC\",\"bar_timestamp_semantics\":\"start\",\"timezone_identity\":\"UTC\",\"dst_regime\":\"none\",\"session_clock\":\"local\",\"strategy_clock\":\"UTC\",\"conversion_history\":[]}"#] { assert!(parse_contract(raw).is_err(), "{raw}"); } let unsupported=fixture_contract().replacen('{', "{\"contract_version\":2,", 1); assert!(parse_contract(&unsupported).unwrap_err().contains("unsupported")); }
    #[test] fn schema_and_ordering_fail_closed() { let good=fixture_contract(); let missing=write_fixture("missing", &good, false, false, false, true, false); assert!(read_canonical_m1_parquet(&missing).unwrap_err().contains("missing required canonical column volume")); let wrong=write_fixture("wrong", &good, true, false, false, false, false); assert!(read_canonical_m1_parquet(&wrong).unwrap_err().contains("type")); let unordered=write_fixture("unordered", &good, false, true, false, false, false); assert!(read_canonical_m1_parquet(&unordered).unwrap_err().contains("strictly increasing")); let duplicate=write_fixture("duplicate", &good, false, false, true, false, false); assert!(read_canonical_m1_parquet(&duplicate).unwrap_err().contains("strictly increasing")); }
    #[test] fn metadata_fails_closed() { let malformed=write_fixture("metadata-malformed", "{", false, false, false, false, false); assert!(read_canonical_m1_parquet(&malformed).unwrap_err().contains("malformed nora.contract")); let missing=write_fixture("metadata-missing", &fixture_contract(), false, false, false, false, true); assert!(read_canonical_m1_parquet(&missing).unwrap_err().contains("missing required Phase-1 metadata nora.contract")); }
    fn aggregate_dataset(start:&str, count:usize, contract:&str, missing:Option<usize>, nullable:bool)->CanonicalM1Dataset { let base=NaiveDateTime::parse_from_str(start,"%Y.%m.%d %H:%M").unwrap(); let bars=(0..count).filter(|i|Some(*i)!=missing).map(|i|{let t=base+chrono::Duration::minutes(i as i64);CanonicalM1Bar{timestamp:t.format("%Y.%m.%d %H:%M").to_string(),local_timestamp:t,open:i as f64+1.,high:i as f64+2.,low:i as f64,close:i as f64+1.5,volume:if nullable&&i==2{None}else{Some(1.)},spread:if nullable&&i==3{None}else{Some(0.1)}}}).collect();CanonicalM1Dataset{contract:parse_contract(contract).unwrap(),source_sha256:"0".repeat(64),bars,content_identity:"source-identity".into()} }
    #[test] fn contract_aware_m5_h1_partials_and_nullable_values() { let data=aggregate_dataset("2025.06.03 08:00",60,&fixture_contract(),None,true);let m5=crate::aggregation::aggregate_m1(&data,"M5",crate::aggregation::POLICY).unwrap();assert_eq!(m5.bars.len(),12);assert_eq!(m5.bars[0].timestamp,"2025.06.03 08:00");assert_eq!((m5.bars[0].open,m5.bars[0].high,m5.bars[0].low,m5.bars[0].close),(1.,6.,0.,5.5));assert_eq!(m5.bars[0].volume,None);assert_eq!(m5.bars[0].spread,None);let h1=crate::aggregation::aggregate_m1(&data,"H1",crate::aggregation::POLICY).unwrap();assert_eq!(h1.bars.len(),1);assert_eq!(h1.bars[0].timestamp,"2025.06.03 08:00");assert_eq!(m5.content_identity,crate::aggregation::aggregate_m1(&data,"M5",crate::aggregation::POLICY).unwrap().content_identity);let leading=aggregate_dataset("2025.06.03 08:02",8,&fixture_contract(),None,false);let lead=crate::aggregation::aggregate_m1(&leading,"M5",crate::aggregation::POLICY).unwrap();assert_eq!((lead.omitted_leading_windows,lead.bars[0].timestamp.as_str()),(1,"2025.06.03 08:05"));let trailing=aggregate_dataset("2025.06.03 08:00",8,&fixture_contract(),None,false);let tail=crate::aggregation::aggregate_m1(&trailing,"M5",crate::aggregation::POLICY).unwrap();assert_eq!((tail.omitted_trailing_windows,tail.bars.len()),(1,1));let gap=aggregate_dataset("2025.06.03 08:00",15,&fixture_contract(),Some(6),false);assert!(crate::aggregation::aggregate_m1(&gap,"M5",crate::aggregation::POLICY).unwrap_err().contains("internal incomplete")); }
    #[test] fn aggregation_honors_trading_boundary_and_broker_dst_clock() { let boundary=r#"{"provider":"manual","acquisition_tool":"manual","source_symbol":"EURUSD","project_symbol":"EURUSD","source_timestamp_semantics":"UTC","bar_timestamp_semantics":"start","timezone_identity":"UTC","dst_regime":"no_dst","session_clock":"UTC","strategy_clock":"UTC","trading_day_boundary":"00:02","higher_timeframe_anchoring":"session_clock","conversion_history":[]}"#;let d=aggregate_dataset("2025.06.03 00:00",12,boundary,None,false);let a=crate::aggregation::aggregate_m1(&d,"M5",crate::aggregation::POLICY).unwrap();assert_eq!(a.bars[0].timestamp,"2025.06.03 00:02");assert_eq!(a.omitted_leading_windows,1);let midnight=aggregate_dataset("2025.06.03 23:55",10,&fixture_contract(),None,false);let across=crate::aggregation::aggregate_m1(&midnight,"M5",crate::aggregation::POLICY).unwrap();assert_eq!(across.bars.iter().map(|b|b.timestamp.as_str()).collect::<Vec<_>>(),vec!["2025.06.03 23:55","2025.06.04 00:00"]);let broker=r#"{"provider":"manual","acquisition_tool":"manual","source_symbol":"EURUSD","project_symbol":"EURUSD","source_timestamp_semantics":"broker_local","bar_timestamp_semantics":"start","timezone_identity":"america_new_york_plus_7_v1","dst_regime":"new_york_dst_v1","session_clock":"broker","strategy_clock":"broker","higher_timeframe_anchoring":"strategy_clock","conversion_history":[]}"#;for start in ["2025.01.15 14:00","2025.06.03 15:00","2025.03.09 08:55","2025.03.09 10:00","2025.11.02 07:55","2025.11.02 09:00"] { let d=aggregate_dataset(start,5,broker,None,false);let a=crate::aggregation::aggregate_m1(&d,"M5",crate::aggregation::POLICY).unwrap();assert_eq!(a.bars[0].timestamp,start); }let bad=aggregate_dataset("2025.11.02 08:30",5,broker,None,false);assert!(crate::aggregation::aggregate_m1(&bad,"M5",crate::aggregation::POLICY).unwrap_err().contains("ambiguous")); }
    fn fixture_contract() -> String { r#"{"provider":"manual","acquisition_tool":"manual","source_symbol":"EURUSD","project_symbol":"EURUSD","source_timestamp_semantics":"UTC","bar_timestamp_semantics":"start","timezone_identity":"UTC","dst_regime":"no_dst","session_clock":"UTC","strategy_clock":"UTC","conversion_history":[]}"#.into() }
    fn write_fixture(name:&str, contract:&str, wrong_open:bool, unordered:bool, duplicate:bool, omit_volume:bool, omit_contract:bool)->std::path::PathBuf { let path=env::temp_dir().join(format!("labengine-{name}-{}.parquet",std::process::id())); let mut fields=vec![Field::new("timestamp",DataType::Utf8,false),Field::new("open",if wrong_open {DataType::Utf8}else{DataType::Float64},false),Field::new("high",DataType::Float64,false),Field::new("low",DataType::Float64,false),Field::new("close",DataType::Float64,false)]; if !omit_volume { fields.push(Field::new("volume",DataType::Float64,true)); } fields.push(Field::new("spread",DataType::Float64,true)); let mut metadata=std::collections::HashMap::new();if !omit_contract { metadata.insert(PHASE1_METADATA_CONTRACT.into(),contract.into()); }metadata.insert(PHASE1_METADATA_SOURCE_SHA256.into(),"0".repeat(64));metadata.insert(PHASE1_METADATA_TIMEFRAME.into(),"M1".into());let schema=Arc::new(Schema::new_with_metadata(fields,metadata)); let timestamps=if unordered {vec!["2025.06.03 08:01","2025.06.03 08:00"]}else if duplicate {vec!["2025.06.03 08:00","2025.06.03 08:00"]}else{vec!["2025.06.03 08:00","2025.06.03 08:01"]}; let mut arrays:Vec<Arc<dyn Array>>=vec![Arc::new(StringArray::from(timestamps))]; if wrong_open { arrays.push(Arc::new(StringArray::from(vec!["1","2"]))); }else{arrays.push(Arc::new(Float64Array::from(vec![1.,2.])));} arrays.extend([Arc::new(Float64Array::from(vec![2.,3.])) as Arc<dyn Array>,Arc::new(Float64Array::from(vec![0.5,1.])) as Arc<dyn Array>,Arc::new(Float64Array::from(vec![1.5,2.5])) as Arc<dyn Array>]);if !omit_volume{arrays.push(Arc::new(Float64Array::from(vec![Some(7.),Some(8.)])));}arrays.push(Arc::new(Float64Array::from(vec![Some(0.1),None])));let batch=RecordBatch::try_new(schema.clone(),arrays).unwrap();let file=fs::File::create(&path).unwrap();let mut writer=ArrowWriter::try_new(file,schema,None).unwrap();writer.write(&batch).unwrap();writer.close().unwrap();path }
}
