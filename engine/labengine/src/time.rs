//! Declared-clock interpretation and reusable session-time primitives.
//!
//! These functions do not alter a dataset. They resolve a declared local label
//! to an instant only when a caller asks them to, and reject DST gaps/folds.
use chrono::{DateTime, Datelike, Duration, FixedOffset, LocalResult, NaiveDate, NaiveDateTime, NaiveTime, Offset, TimeZone, Utc, Weekday};
use chrono_tz::{America::New_York, Tz};
use serde_json::Value;

use crate::TimeContract;

pub type Result<T> = std::result::Result<T, String>;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DeclaredClock { Utc, Iana(Tz), NewYorkPlusSeven }
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SourceTimestampSemantics { Utc, BrokerLocal }
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BarTimestampSemantics { StartOfBar }
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DstRegime { NoDst, IanaRules, NewYorkDstV1 }
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HigherTimeframeAnchoring { SessionClock, StrategyClock }
#[derive(Debug, Clone, PartialEq)]
pub struct ConversionState { pub history: Vec<ConversionStep>, pub double_conversion_guard: Option<bool> }
#[derive(Debug, Clone, PartialEq)]
pub struct ConversionStep { pub target: String }
#[derive(Debug, Clone, PartialEq)]
pub struct ClockModel {
    pub dataset_clock: DeclaredClock,
    pub dst_regime: DstRegime,
    pub source_timestamp_semantics: SourceTimestampSemantics,
    pub bar_timestamp_semantics: BarTimestampSemantics,
    pub session_clock: DeclaredClock,
    pub strategy_clock: DeclaredClock,
    pub trading_day_boundary: Option<NaiveTime>,
    pub higher_timeframe_anchoring: Option<HigherTimeframeAnchoring>,
    pub conversion: ConversionState,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ResolvedTime { pub local: NaiveDateTime, pub utc: DateTime<Utc>, pub offset: FixedOffset }
impl ResolvedTime { pub fn weekday(&self) -> Weekday { self.local.weekday() } pub fn time(&self) -> NaiveTime { self.local.time() } }

impl ClockModel {
    /// Derives executable semantics only from declarations already carried by `nora.contract`.
    pub fn from_contract(contract: &TimeContract) -> Result<Self> {
        let dataset_clock = parse_dataset_clock(&contract.timezone_identity, &contract.dst_regime)?;
        let dst_regime = parse_dst_regime(&contract.dst_regime)?;
        let source_timestamp_semantics = match contract.source_timestamp_semantics.as_str() { "UTC" => SourceTimestampSemantics::Utc, "broker_local" => SourceTimestampSemantics::BrokerLocal, other => return Err(format!("unsupported source_timestamp_semantics {other:?}")), };
        let bar_timestamp_semantics = match contract.bar_timestamp_semantics.as_str() { "start" => BarTimestampSemantics::StartOfBar, other => return Err(format!("unsupported bar_timestamp_semantics {other:?}")), };
        let session_clock = parse_clock_reference(&contract.session_clock, &dataset_clock)?;
        let strategy_clock = parse_clock_reference(&contract.strategy_clock, &dataset_clock)?;
        let trading_day_boundary = contract.trading_day_boundary.as_deref().map(parse_time).transpose()?;
        let higher_timeframe_anchoring = match contract.higher_timeframe_anchoring.as_deref() { None => None, Some("session_clock") => Some(HigherTimeframeAnchoring::SessionClock), Some("strategy_clock") => Some(HigherTimeframeAnchoring::StrategyClock), Some(value) => return Err(format!("unsupported higher_timeframe_anchoring {value:?}")), };
        let history = contract.conversion_history.iter().map(parse_conversion_step).collect::<Result<Vec<_>>>()?;
        Ok(Self { dataset_clock, dst_regime, source_timestamp_semantics, bar_timestamp_semantics, session_clock, strategy_clock, trading_day_boundary, higher_timeframe_anchoring, conversion: ConversionState { history, double_conversion_guard: contract.double_conversion_protection } })
    }
    /// Resolves the source label in its declared dataset clock; it never rewrites the label.
    pub fn interpret_dataset_label(&self, label: NaiveDateTime) -> Result<ResolvedTime> { self.dataset_clock.resolve_local(label) }
    pub fn session_time(&self, dataset_time: &ResolvedTime) -> ResolvedTime { self.session_clock.from_utc(dataset_time.utc) }
    pub fn strategy_time(&self, dataset_time: &ResolvedTime) -> ResolvedTime { self.strategy_clock.from_utc(dataset_time.utc) }
    pub fn trading_day(&self, strategy_time: &ResolvedTime) -> Result<NaiveDate> { trading_day_identity(strategy_time.local, self.trading_day_boundary.ok_or("trading_day_boundary is not declared by this contract")?) }
}

impl DeclaredClock {
    pub fn resolve_local(&self, local: NaiveDateTime) -> Result<ResolvedTime> {
        match self {
            Self::Utc => Ok(ResolvedTime { local, utc: Utc.from_utc_datetime(&local), offset: FixedOffset::east_opt(0).expect("zero offset") }),
            Self::Iana(zone) => resolve_in_zone(*zone, local),
            // The convention shares New York's DST transitions, but its wall clock is NY + 7h.
            Self::NewYorkPlusSeven => resolve_in_zone(New_York, local - Duration::hours(7))
                .map(|resolved| ResolvedTime { local, utc: resolved.utc, offset: FixedOffset::east_opt(resolved.offset.local_minus_utc() + 7 * 3600).expect("NY+7 offset") }),
        }
    }
    pub fn from_utc(&self, utc: DateTime<Utc>) -> ResolvedTime {
        match self {
            Self::Utc => ResolvedTime { local: utc.naive_utc(), utc, offset: FixedOffset::east_opt(0).expect("zero offset") },
            Self::Iana(zone) => from_utc_zone(*zone, utc),
            Self::NewYorkPlusSeven => { let ny = from_utc_zone(New_York, utc); ResolvedTime { local: ny.local + Duration::hours(7), utc, offset: FixedOffset::east_opt(ny.offset.local_minus_utc() + 7 * 3600).expect("NY+7 offset") } }
        }
    }
}

fn resolve_in_zone(zone: Tz, local: NaiveDateTime) -> Result<ResolvedTime> {
    match zone.from_local_datetime(&local) {
        LocalResult::Single(value) => Ok(ResolvedTime { local, utc: value.with_timezone(&Utc), offset: value.offset().fix() }),
        LocalResult::Ambiguous(_, _) => Err(format!("ambiguous local time {local} in {zone}; explicit fold selection is required")),
        LocalResult::None => Err(format!("nonexistent local time {local} in {zone}; explicit gap policy is required")),
    }
}
fn from_utc_zone(zone: Tz, utc: DateTime<Utc>) -> ResolvedTime { let local = zone.from_utc_datetime(&utc.naive_utc()); ResolvedTime { local: local.naive_local(), utc, offset: local.offset().fix() } }
fn parse_dataset_clock(identity: &str, regime: &str) -> Result<DeclaredClock> {
    match identity {
        "UTC" if regime == "no_dst" => Ok(DeclaredClock::Utc),
        "america_new_york_plus_7_v1" if regime == "new_york_dst_v1" => Ok(DeclaredClock::NewYorkPlusSeven),
        "UTC" => Err("UTC dataset timezone requires dst_regime no_dst".into()),
        _ if regime == "iana" => identity.parse::<Tz>().map(DeclaredClock::Iana).map_err(|_| format!("unsupported IANA timezone identity {identity:?}")),
        _ => Err(format!("timezone identity {identity:?} and DST regime {regime:?} are not a supported declared clock")),
    }
}
fn parse_dst_regime(value: &str) -> Result<DstRegime> { match value { "no_dst" => Ok(DstRegime::NoDst), "iana" => Ok(DstRegime::IanaRules), "new_york_dst_v1" => Ok(DstRegime::NewYorkDstV1), other => Err(format!("unsupported dst_regime {other:?}")), } }
fn parse_clock_reference(value: &str, dataset: &DeclaredClock) -> Result<DeclaredClock> {
    match value { "UTC" => Ok(DeclaredClock::Utc), "broker" if *dataset == DeclaredClock::NewYorkPlusSeven => Ok(DeclaredClock::NewYorkPlusSeven), "dataset" => Ok(dataset.clone()), value if value == clock_identity(dataset) => Ok(dataset.clone()), value => value.parse::<Tz>().map(DeclaredClock::Iana).map_err(|_| format!("unsupported or ambiguous declared clock {value:?}")), }
}
fn clock_identity(clock: &DeclaredClock) -> &str { match clock { DeclaredClock::Utc => "UTC", DeclaredClock::Iana(zone) => zone.name(), DeclaredClock::NewYorkPlusSeven => "america_new_york_plus_7_v1", } }
fn parse_time(value: &str) -> Result<NaiveTime> { NaiveTime::parse_from_str(value, "%H:%M").or_else(|_| NaiveTime::parse_from_str(value, "%H:%M:%S")).map_err(|_| format!("invalid clock time {value:?}; expected HH:MM or HH:MM:SS")) }
fn parse_conversion_step(value: &Value) -> Result<ConversionStep> { let target = value.as_object().and_then(|o| o.get("target")).and_then(Value::as_str).filter(|v| !v.is_empty()).ok_or("invalid conversion history entry")?; Ok(ConversionStep { target: target.into() }) }

#[derive(Debug, Clone, Copy, PartialEq, Eq)] pub struct TimeWindow { pub start: NaiveTime, pub end: NaiveTime }
impl TimeWindow { pub fn new(start: NaiveTime, end: NaiveTime) -> Result<Self> { if start == end { Err("a session window may not have equal start and end".into()) } else { Ok(Self { start, end }) } } pub fn contains(&self, time: NaiveTime) -> bool { if self.start < self.end { time >= self.start && time < self.end } else { time >= self.start || time < self.end } } }
pub fn trading_day_identity(local: NaiveDateTime, boundary: NaiveTime) -> Result<NaiveDate> { if local.time() < boundary { local.date().pred_opt().ok_or_else(|| "trading day underflow".into()) } else { Ok(local.date()) } }
pub fn friday_close_due(strategy: &ResolvedTime, close: NaiveTime) -> bool { strategy.weekday() == Weekday::Fri && strategy.time() >= close }
pub fn opening_range_contains(strategy: &ResolvedTime, window: TimeWindow) -> bool { window.contains(strategy.time()) }
pub fn rollover_avoidance_contains(strategy: &ResolvedTime, window: TimeWindow) -> bool { window.contains(strategy.time()) }
pub fn daily_reset_crossed(previous: &ResolvedTime, current: &ResolvedTime, boundary: NaiveTime) -> Result<bool> { if current.utc < previous.utc { return Err("daily reset inputs must be chronological".into()); } Ok(trading_day_identity(previous.local, boundary)? != trading_day_identity(current.local, boundary)?) }
pub fn monday_open_contains(strategy: &ResolvedTime, window: TimeWindow) -> bool { strategy.weekday() == Weekday::Mon && window.contains(strategy.time()) }

#[cfg(test)] mod tests {
    use super::*;
    use chrono::NaiveDate;
    fn dt(day: &str, time: &str) -> NaiveDateTime { NaiveDateTime::new(NaiveDate::parse_from_str(day, "%Y-%m-%d").unwrap(), parse_time(time).unwrap()) }
    fn utc(day: &str, time: &str) -> DateTime<Utc> { Utc.from_utc_datetime(&dt(day,time)) }
    fn broker() -> DeclaredClock { DeclaredClock::NewYorkPlusSeven }
    #[test] fn utc_labels_are_unchanged() { let model=ClockModel { dataset_clock:DeclaredClock::Utc,dst_regime:DstRegime::NoDst,source_timestamp_semantics:SourceTimestampSemantics::Utc,bar_timestamp_semantics:BarTimestampSemantics::StartOfBar,session_clock:DeclaredClock::Utc,strategy_clock:DeclaredClock::Utc,trading_day_boundary:None,higher_timeframe_anchoring:None,conversion:ConversionState{history:vec![],double_conversion_guard:None}}; let label=dt("2025-06-03","08:00"); let resolved=model.interpret_dataset_label(label).unwrap(); assert_eq!(resolved.local,label); assert_eq!(resolved.utc,utc("2025-06-03","08:00")); assert_eq!(model.strategy_time(&resolved).local,label); }
    #[test] fn new_york_transitions_and_broker_offsets_are_explicit() { let winter=broker().from_utc(utc("2025-01-15","12:00")); assert_eq!((winter.local, winter.offset.local_minus_utc()),(dt("2025-01-15","14:00"),7200)); let before=broker().from_utc(utc("2025-03-09","06:59")); let after=broker().from_utc(utc("2025-03-09","07:00")); assert_eq!((before.local,before.offset.local_minus_utc()),(dt("2025-03-09","08:59"),7200)); assert_eq!((after.local,after.offset.local_minus_utc()),(dt("2025-03-09","10:00"),10800)); let autumn_before=broker().from_utc(utc("2025-11-02","05:30")); let autumn_after=broker().from_utc(utc("2025-11-02","06:30")); assert_eq!((autumn_before.local,autumn_before.offset.local_minus_utc()),(dt("2025-11-02","08:30"),10800)); assert_eq!((autumn_after.local,autumn_after.offset.local_minus_utc()),(dt("2025-11-02","08:30"),7200)); }
    #[test] fn dst_gap_and_fold_fail_closed() { assert!(broker().resolve_local(dt("2025-03-09","09:30")).unwrap_err().contains("nonexistent")); assert!(broker().resolve_local(dt("2025-11-02","08:30")).unwrap_err().contains("ambiguous")); }
    #[test] fn declared_clock_primitives_use_strategy_time() { let ny=DeclaredClock::Iana("America/New_York".parse().unwrap()); let friday=ny.from_utc(utc("2025-06-06","21:05")); assert_eq!(friday.local,dt("2025-06-06","17:05")); assert!(friday_close_due(&friday,parse_time("17:00").unwrap())); let orb=TimeWindow::new(parse_time("09:30").unwrap(),parse_time("10:00").unwrap()).unwrap(); let orb_time=ny.from_utc(utc("2025-06-03","13:35")); assert_eq!(orb_time.local,dt("2025-06-03","09:35")); assert!(opening_range_contains(&orb_time,orb)); let rollover=TimeWindow::new(parse_time("23:50").unwrap(),parse_time("00:10").unwrap()).unwrap(); let late=DeclaredClock::Utc.from_utc(utc("2025-06-03","23:55")); let early=DeclaredClock::Utc.from_utc(utc("2025-06-04","00:05")); assert!(rollover_avoidance_contains(&late,rollover)); assert!(rollover_avoidance_contains(&early,rollover)); }
    #[test] fn trading_day_reset_monday_and_repeatability() { let boundary=parse_time("17:00").unwrap(); let before=DeclaredClock::Utc.from_utc(utc("2025-06-03","16:59")); let after=DeclaredClock::Utc.from_utc(utc("2025-06-03","17:00")); assert_eq!(trading_day_identity(before.local,boundary).unwrap(),NaiveDate::from_ymd_opt(2025,6,2).unwrap()); assert!(daily_reset_crossed(&before,&after,boundary).unwrap()); let monday=DeclaredClock::Utc.from_utc(utc("2025-06-02","09:05")); let open=TimeWindow::new(parse_time("09:00").unwrap(),parse_time("09:15").unwrap()).unwrap(); assert!(monday_open_contains(&monday,open)); assert_eq!(daily_reset_crossed(&before,&after,boundary),daily_reset_crossed(&before,&after,boundary)); }
    #[test] fn contract_is_typed_without_defaulting_missing_boundary() { let contract=TimeContract { version:1,provider:"p".into(),acquisition_tool:"a".into(),source_symbol:"s".into(),project_symbol:"s".into(),source_timestamp_semantics:"broker_local".into(),bar_timestamp_semantics:"start".into(),timezone_identity:"america_new_york_plus_7_v1".into(),dst_regime:"new_york_dst_v1".into(),session_clock:"broker".into(),strategy_clock:"broker".into(),trading_day_boundary:None,higher_timeframe_anchoring:None,conversion_history:vec![],double_conversion_protection:None,canonical_json:"{}".into() }; let model=ClockModel::from_contract(&contract).unwrap(); assert_eq!(model.dataset_clock,DeclaredClock::NewYorkPlusSeven); let time=model.interpret_dataset_label(dt("2025-01-15","14:00")).unwrap(); assert_eq!(time.utc,utc("2025-01-15","12:00")); assert!(model.trading_day(&time).is_err()); }
    #[test] fn generic_iana_contract_is_typed_with_all_optional_declarations() { let contract=TimeContract { version:1,provider:"p".into(),acquisition_tool:"a".into(),source_symbol:"s".into(),project_symbol:"s".into(),source_timestamp_semantics:"UTC".into(),bar_timestamp_semantics:"start".into(),timezone_identity:"America/New_York".into(),dst_regime:"iana".into(),session_clock:"America/New_York".into(),strategy_clock:"America/New_York".into(),trading_day_boundary:Some("17:00".into()),higher_timeframe_anchoring:Some("strategy_clock".into()),conversion_history:vec![serde_json::json!({"target":"America/New_York"})],double_conversion_protection:Some(true),canonical_json:"{}".into() }; let model=ClockModel::from_contract(&contract).unwrap(); assert_eq!(model.dst_regime,DstRegime::IanaRules); assert_eq!(model.trading_day_boundary,Some(parse_time("17:00").unwrap())); assert_eq!(model.higher_timeframe_anchoring,Some(HigherTimeframeAnchoring::StrategyClock)); assert_eq!(model.conversion.history[0].target,"America/New_York"); let resolved=model.interpret_dataset_label(dt("2025-06-03","09:30")).unwrap(); assert_eq!(resolved.utc,utc("2025-06-03","13:30")); assert_eq!(model.strategy_time(&resolved),model.strategy_time(&resolved)); }
}
