//! Strict, typed Phase 2C exit-condition document model.
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

pub type Result<T> = std::result::Result<T, String>;

pub const SEMANTIC_IDENTITY_DOMAIN: &str = "nora-exit-condition-semantic-v1";

#[derive(Clone, Copy, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum Side { Long, Short }

#[derive(Clone, Copy, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum SignalType { Boolean }

#[derive(Clone, Copy, Debug, Deserialize, Serialize, PartialEq, Eq)]
pub enum Timing {
    #[serde(rename = "next_open")]
    NextOpen,
}

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct BooleanSignalReference {
    pub series: String,
    #[serde(rename = "type")]
    pub signal_type: SignalType,
}

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct Exit {
    pub signal: BooleanSignalReference,
    pub timing: Timing,
}

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ExitCondition {
    pub schema_version: u32,
    pub side: Side,
    pub exit: Exit,
}

/// Parses and validates the complete JSON document. The returned document is typed.
pub fn parse_json(raw: &str) -> Result<ExitCondition> {
    let document: ExitCondition = serde_json::from_str(raw)
        .map_err(|error| format!("malformed exit condition: {error}"))?;
    validate(document)
}

/// Parses a JSON value at an API boundary without retaining untyped semantic state.
pub fn parse(value: &serde_json::Value) -> Result<ExitCondition> {
    let document: ExitCondition = serde_json::from_value(value.clone())
        .map_err(|error| format!("malformed exit condition: {error}"))?;
    validate(document)
}

fn validate(document: ExitCondition) -> Result<ExitCondition> {
    if document.schema_version != 1 {
        return Err(format!("unsupported exit condition schema_version {}", document.schema_version));
    }
    if document.exit.signal.series.is_empty() {
        return Err("exit condition signal series must be a non-empty string".into());
    }
    Ok(document)
}

/// Stable compact JSON representation generated only from the typed document.
pub fn canonical_json(document: &ExitCondition) -> String {
    serde_json::to_string(document).expect("exit-condition document serializes")
}

/// SHA-256 identity over the versioned domain prefix and canonical document bytes.
pub fn semantic_identity(document: &ExitCondition) -> String {
    let mut hash = Sha256::new();
    hash.update(SEMANTIC_IDENTITY_DOMAIN.as_bytes());
    hash.update(canonical_json(document).as_bytes());
    format!("{:x}", hash.finalize())
}

#[cfg(test)]
mod tests {
    use super::*;

    const LONG: &str = r#"{"schema_version":1,"side":"long","exit":{"signal":{"series":"entry_signal","type":"boolean"},"timing":"next_open"}}"#;
    const SHORT: &str = r#"{"schema_version":1,"side":"short","exit":{"signal":{"series":"entry_signal","type":"boolean"},"timing":"next_open"}}"#;

    #[test]
    fn valid_long_and_short_conditions_are_typed() {
        let long = parse_json(LONG).unwrap();
        let short = parse_json(SHORT).unwrap();
        assert_eq!(long.side, Side::Long);
        assert_eq!(short.side, Side::Short);
        assert_eq!(long.exit.signal.signal_type, SignalType::Boolean);
        assert_eq!(long.exit.timing, Timing::NextOpen);
    }

    #[test]
    fn strict_parsing_rejects_each_validation_path() {
        let cases = [
            (r#"{}"#, "missing field `schema_version`"),
            (r#"{"schema_version":2,"side":"long","exit":{"signal":{"series":"x","type":"boolean"},"timing":"next_open"}}"#, "unsupported exit condition schema_version 2"),
            (r#"{"schema_version":1.5,"side":"long","exit":{"signal":{"series":"x","type":"boolean"},"timing":"next_open"}}"#, "invalid type"),
            (r#"{"schema_version":1,"exit":{"signal":{"series":"x","type":"boolean"},"timing":"next_open"}}"#, "missing field `side`"),
            (r#"{"schema_version":1,"side":3,"exit":{"signal":{"series":"x","type":"boolean"},"timing":"next_open"}}"#, "expected value"),
            (r#"{"schema_version":1,"side":"flat","exit":{"signal":{"series":"x","type":"boolean"},"timing":"next_open"}}"#, "unknown variant `flat`"),
            (r#"{"schema_version":1,"side":"long"}"#, "missing field `exit`"),
            (r#"{"schema_version":1,"side":"long","exit":false}"#, "invalid type"),
            (r#"{"schema_version":1,"side":"long","exit":{"timing":"next_open"}}"#, "missing field `signal`"),
            (r#"{"schema_version":1,"side":"long","exit":{"signal":false,"timing":"next_open"}}"#, "invalid type"),
            (r#"{"schema_version":1,"side":"long","exit":{"signal":{"type":"boolean"},"timing":"next_open"}}"#, "missing field `series`"),
            (r#"{"schema_version":1,"side":"long","exit":{"signal":{"series":1,"type":"boolean"},"timing":"next_open"}}"#, "invalid type"),
            (r#"{"schema_version":1,"side":"long","exit":{"signal":{"series":"x"},"timing":"next_open"}}"#, "missing field `type`"),
            (r#"{"schema_version":1,"side":"long","exit":{"signal":{"series":"x","type":"numeric"},"timing":"next_open"}}"#, "unknown variant `numeric`"),
            (r#"{"schema_version":1,"side":"long","exit":{"signal":{"series":"x","type":"boolean"}}}"#, "missing field `timing`"),
            (r#"{"schema_version":1,"side":"long","exit":{"signal":{"series":"x","type":"boolean"},"timing":true}}"#, "expected value"),
            (r#"{"schema_version":1,"side":"long","exit":{"signal":{"series":"x","type":"boolean"},"timing":"same_close"}}"#, "unknown variant `same_close`"),
            (r#"{"schema_version":1,"side":"long","exit":{"signal":{"series":"","type":"boolean"},"timing":"next_open"}}"#, "non-empty string"),
            (r#"{"schema_version":1,"side":"long","exit":{"signal":{"series":"x","type":"boolean","extra":true},"timing":"next_open"}}"#, "unknown field `extra`"),
            (r#"{"schema_version":1,"side":"long","exit":{"signal":{"series":"x","type":"boolean"},"timing":"next_open","extra":true}}"#, "unknown field `extra`"),
            (r#"{"schema_version":1,"side":"long","exit":{"signal":{"series":"x","type":"boolean"},"timing":"next_open"},"extra":true}"#, "unknown field `extra`"),
        ];
        for (raw, expected) in cases {
            let error = parse_json(raw).unwrap_err();
            assert!(error.contains(expected), "{raw}: {error}");
        }
    }

    #[test]
    fn canonical_output_and_round_trip_are_stable() {
        let document = parse_json(LONG).unwrap();
        let canonical = canonical_json(&document);
        assert_eq!(canonical, r#"{"schema_version":1,"side":"long","exit":{"signal":{"series":"entry_signal","type":"boolean"},"timing":"next_open"}}"#);
        let reparsed = parse_json(&canonical).unwrap();
        assert_eq!(canonical_json(&reparsed), canonical);
        assert_eq!(semantic_identity(&reparsed), semantic_identity(&document));
    }

    #[test]
    fn reordered_and_formatted_json_preserve_identity() {
        let reordered = r#"{ "exit": { "timing": "next_open", "signal": { "type": "boolean", "series": "entry_signal" } }, "side": "long", "schema_version": 1 }"#;
        assert_eq!(semantic_identity(&parse_json(LONG).unwrap()), semantic_identity(&parse_json(reordered).unwrap()));
    }

    #[test]
    fn identity_is_deterministic_and_semantically_sensitive() {
        let baseline = parse_json(LONG).unwrap();
        let short = parse_json(SHORT).unwrap();
        let signal_changed = parse_json(r#"{"schema_version":1,"side":"long","exit":{"signal":{"series":"exit_signal","type":"boolean"},"timing":"next_open"}}"#).unwrap();
        let identity = semantic_identity(&baseline);
        assert_eq!(identity, semantic_identity(&baseline));
        assert_ne!(identity, semantic_identity(&short));
        assert_ne!(identity, semantic_identity(&signal_changed));
    }
}
