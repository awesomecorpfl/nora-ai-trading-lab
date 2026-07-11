//! Contract-aware deterministic M1 aggregation.  Grouping never rewrites source labels.
use std::{collections::BTreeMap, fs, path::Path, sync::Arc};
use arrow_array::{ArrayRef, Float64Array, RecordBatch, StringArray};
use arrow_schema::{DataType, Field, Schema};
use chrono::{Duration, NaiveDateTime, NaiveTime};
use parquet::arrow::ArrowWriter;
use parquet::arrow::arrow_reader::ParquetRecordBatchReaderBuilder;
use serde_json::json;
use sha2::{Digest, Sha256};

use crate::{CanonicalM1Bar, CanonicalM1Dataset};
use crate::time::{ClockModel, DeclaredClock, HigherTimeframeAnchoring, ResolvedTime};

pub type Result<T> = std::result::Result<T, String>;
pub const POLICY: &str = "omit_edge_partials_v1";
pub const DERIVED_CONTRACT_VERSION: u32 = 1;

#[derive(Debug, Clone, PartialEq)]
pub struct DerivedBar { pub timestamp: String, pub open: f64, pub high: f64, pub low: f64, pub close: f64, pub volume: Option<f64>, pub spread: Option<f64> }
#[derive(Debug, Clone)]
pub struct AggregationResult { pub bars: Vec<DerivedBar>, pub content_identity: String, pub omitted_leading_windows: u64, pub omitted_trailing_windows: u64, pub anchor: String }

pub fn timeframe_minutes(value: &str) -> Result<i64> { match value { "M5" => Ok(5), "H1" => Ok(60), _ => Err(format!("unsupported target_timeframe {value:?}; supported values are M5 and H1")), } }

#[derive(Clone)]
struct Member<'a> { bar: &'a CanonicalM1Bar, resolved: ResolvedTime, key: NaiveDateTime }

pub fn aggregate_m1(dataset: &CanonicalM1Dataset, target: &str, policy: &str) -> Result<AggregationResult> {
    if policy != POLICY { return Err(format!("unsupported completeness_policy {policy:?}")); }
    let minutes = timeframe_minutes(target)?;
    let model = ClockModel::from_contract(&dataset.contract)?;
    let anchor_clock = match model.higher_timeframe_anchoring {
        Some(HigherTimeframeAnchoring::StrategyClock) => model.strategy_clock.clone(),
        Some(HigherTimeframeAnchoring::SessionClock) | None => model.session_clock.clone(),
    };
    let anchor_name = match model.higher_timeframe_anchoring { Some(HigherTimeframeAnchoring::StrategyClock) => "strategy_clock", Some(HigherTimeframeAnchoring::SessionClock) => "session_clock", None => "session_clock (legacy default)" }.to_string();
    let mut groups: BTreeMap<NaiveDateTime, Vec<Member<'_>>> = BTreeMap::new();
    let mut previous = None;
    for bar in &dataset.bars {
        let resolved = model.interpret_dataset_label(bar.local_timestamp)?;
        if let Some(prior) = previous { if resolved.utc <= prior { return Err(format!("timestamps are not strictly increasing instants at {}", bar.timestamp)); } }
        previous = Some(resolved.utc);
        let anchor = anchor_clock.from_utc(resolved.utc);
        let base = aggregation_base(&model, &anchor_clock, &resolved, &anchor)?;
        let elapsed = anchor.local.signed_duration_since(base).num_minutes();
        if elapsed < 0 { return Err(format!("aggregation anchor precedes declared trading day at {}", bar.timestamp)); }
        let key = base + Duration::minutes((elapsed / minutes) * minutes);
        groups.entry(key).or_default().push(Member { bar, resolved, key });
    }
    let count = groups.len();
    let mut output = Vec::new(); let mut leading = 0; let mut trailing = 0;
    for (index, (_key, members)) in groups.into_iter().enumerate() {
        if members.len() != minutes as usize {
            if index == 0 { leading += 1; continue; }
            if index + 1 == count { trailing += 1; continue; }
            return Err(format!("internal incomplete aggregation window beginning at {}", members[0].bar.timestamp));
        }
        for pair in members.windows(2) { if pair[1].resolved.utc - pair[0].resolved.utc != Duration::minutes(1) { return Err(format!("internal missing M1 minute between {} and {}", pair[0].bar.timestamp, pair[1].bar.timestamp)); } }
        let first = &members[0].bar; let last = &members[members.len()-1].bar;
        let volume = members.iter().map(|m| m.bar.volume).collect::<Option<Vec<_>>>().map(|v| v.into_iter().sum());
        let spread = members.iter().map(|m| m.bar.spread).collect::<Option<Vec<_>>>().map(|v| v.into_iter().sum::<f64>() / minutes as f64);
        // Key is an anchor-clock local label.  Convert its known instant back to the dataset
        // clock solely to select the output label; the source timestamps themselves are unchanged.
        let key_instant = anchor_clock.resolve_local(members[0].key)?;
        let output_time = model.dataset_clock.from_utc(key_instant.utc).local;
        output.push(DerivedBar { timestamp: output_time.format("%Y.%m.%d %H:%M").to_string(), open:first.open, high:members.iter().map(|m|m.bar.high).fold(f64::NEG_INFINITY,f64::max), low:members.iter().map(|m|m.bar.low).fold(f64::INFINITY,f64::min), close:last.close, volume, spread });
    }
    let identity = derived_identity(dataset, target, &anchor_name, &output);
    Ok(AggregationResult { bars:output, content_identity:identity, omitted_leading_windows:leading, omitted_trailing_windows:trailing, anchor:anchor_name })
}

fn aggregation_base(model: &ClockModel, anchor_clock: &DeclaredClock, source: &ResolvedTime, anchor: &ResolvedTime) -> Result<NaiveDateTime> {
    if let Some(boundary) = model.trading_day_boundary {
        let strategy = model.strategy_time(source); let day = model.trading_day(&strategy)?;
        let start = NaiveDateTime::new(day, boundary);
        let instant = model.strategy_clock.resolve_local(start)?;
        Ok(anchor_clock.from_utc(instant.utc).local)
    } else { Ok(NaiveDateTime::new(anchor.local.date(), NaiveTime::MIN)) }
}

fn part(hash:&mut Sha256, bytes:&[u8]) { hash.update((bytes.len() as u64).to_be_bytes()); hash.update(bytes); }
fn derived_identity(dataset:&CanonicalM1Dataset,target:&str,anchor:&str,bars:&[DerivedBar])->String { let mut h=Sha256::new(); part(&mut h,b"nora-derived-aggregation-semantic-v1");part(&mut h,dataset.content_identity.as_bytes());part(&mut h,target.as_bytes());part(&mut h,anchor.as_bytes());for b in bars {part(&mut h,b.timestamp.as_bytes());for v in [b.open,b.high,b.low,b.close]{h.update(v.to_bits().to_be_bytes())}for v in [b.volume,b.spread]{match v {Some(x)=>{h.update([1]);h.update(x.to_bits().to_be_bytes())},None=>h.update([0])}}}format!("{:x}",h.finalize()) }

pub fn write_derived_parquet(path:&Path, dataset:&CanonicalM1Dataset, target:&str, result:&AggregationResult) -> Result<()> {
    let derived = json!({"derived_contract_version":DERIVED_CONTRACT_VERSION,"source_content_identity":dataset.content_identity,"source_timeframe":"M1","derived_timeframe":target,"aggregation_policy":POLICY,"higher_timeframe_anchor":result.anchor,"aggregation_is_timezone_conversion":false,"dataset_timezone_identity":dataset.contract.timezone_identity,"dst_regime":dataset.contract.dst_regime,"timestamp_semantics":dataset.contract.bar_timestamp_semantics,"session_clock":dataset.contract.session_clock,"strategy_clock":dataset.contract.strategy_clock,"trading_day_boundary":dataset.contract.trading_day_boundary,"higher_timeframe_anchoring":dataset.contract.higher_timeframe_anchoring,"conversion_history":dataset.contract.conversion_history,"double_conversion_protection":dataset.contract.double_conversion_protection});
    let mut metadata=std::collections::HashMap::new(); metadata.insert("nora.contract".into(),dataset.contract.canonical_json().into()); metadata.insert("nora.source_sha256".into(),dataset.source_sha256.clone()); metadata.insert("nora.timeframe".into(),target.into()); metadata.insert("nora.derived_contract".into(),serde_json::to_string(&derived).expect("derived metadata")); metadata.insert("nora.semantic_sha256".into(),result.content_identity.clone());
    let schema=Arc::new(Schema::new_with_metadata(vec![Field::new("timestamp",DataType::Utf8,false),Field::new("open",DataType::Float64,false),Field::new("high",DataType::Float64,false),Field::new("low",DataType::Float64,false),Field::new("close",DataType::Float64,false),Field::new("volume",DataType::Float64,true),Field::new("spread",DataType::Float64,true)],metadata));
    let arrays:Vec<ArrayRef>=vec![Arc::new(StringArray::from(result.bars.iter().map(|b|b.timestamp.as_str()).collect::<Vec<_>>())),Arc::new(Float64Array::from(result.bars.iter().map(|b|b.open).collect::<Vec<_>>())),Arc::new(Float64Array::from(result.bars.iter().map(|b|b.high).collect::<Vec<_>>())),Arc::new(Float64Array::from(result.bars.iter().map(|b|b.low).collect::<Vec<_>>())),Arc::new(Float64Array::from(result.bars.iter().map(|b|b.close).collect::<Vec<_>>())),Arc::new(Float64Array::from(result.bars.iter().map(|b|b.volume).collect::<Vec<_>>())),Arc::new(Float64Array::from(result.bars.iter().map(|b|b.spread).collect::<Vec<_>>()))];
    let batch=RecordBatch::try_new(schema.clone(),arrays).map_err(|e|format!("build derived record batch: {e}"))?; let file=fs::File::create(path).map_err(|e|format!("create derived Parquet: {e}"))?;let mut writer=ArrowWriter::try_new(file,schema,None).map_err(|e|format!("open derived Parquet writer: {e}"))?;writer.write(&batch).map_err(|e|format!("write derived Parquet: {e}"))?;writer.close().map_err(|e|format!("close derived Parquet: {e}"))?; Ok(())
}

/// Minimal post-write guard before atomic publication; it verifies the output's wire contract.
pub fn validate_derived_parquet(path:&Path, target:&str, identity:&str) -> Result<()> {
    let file=fs::File::open(path).map_err(|e|format!("open completed derived Parquet: {e}"))?;
    let builder=ParquetRecordBatchReaderBuilder::try_new(file).map_err(|e|format!("read completed derived Parquet: {e}"))?;
    let schema=builder.schema(); let meta=schema.metadata();
    if meta.get("nora.timeframe").map(String::as_str)!=Some(target) || meta.get("nora.semantic_sha256").map(String::as_str)!=Some(identity) || !meta.contains_key("nora.derived_contract") { return Err("completed derived Parquet metadata validation failed".into()); }
    for (name, typ) in [("timestamp",DataType::Utf8),("open",DataType::Float64),("high",DataType::Float64),("low",DataType::Float64),("close",DataType::Float64),("volume",DataType::Float64),("spread",DataType::Float64)] { if schema.field_with_name(name).map_err(|_|format!("completed derived output missing {name}"))?.data_type()!=&typ { return Err(format!("completed derived output has invalid {name} type")); } }
    Ok(())
}
