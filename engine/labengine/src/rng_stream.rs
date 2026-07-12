//! Frozen, named deterministic ChaCha20 streams (Phase 2E).
use std::{fs, path::Path};

use arrow_array::{Array, ArrayRef, RecordBatch, UInt64Array};
use arrow_schema::{DataType, Field, Schema};
use parquet::arrow::{arrow_reader::ParquetRecordBatchReaderBuilder, ArrowWriter};
use rand_chacha::{rand_core::{RngCore, SeedableRng}, ChaCha20Rng};
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};
use std::sync::Arc;

pub type Result<T> = std::result::Result<T, String>;

pub const RNG_VERSION: &str = "named_chacha20_v1";
pub const ALGORITHM: &str = "chacha20";
pub const SEED_DOMAIN: &str = "nora.rng.named_chacha20_v1.seed.v1";
pub const SEMANTIC_DOMAIN: &str = "nora.rng.named_chacha20_v1.semantic.v1";
const COLUMNS: [(&str, DataType); 2] = [
    ("draw_index", DataType::UInt64),
    ("value_u64", DataType::UInt64),
];

#[derive(Debug, Clone)]
struct Spec {
    experiment_id: String,
    stage_id: String,
    task_id: String,
    stream_name: String,
    draw_count: u64,
    output_path: std::path::PathBuf,
}

fn only(object: &Map<String, Value>) -> Result<()> {
    let allowed = [
        "task_version", "task_type", "experiment_id", "stage_id", "task_id",
        "stream_name", "draw_count", "output_path",
    ];
    for key in object.keys() {
        if !allowed.contains(&key.as_str()) {
            return Err(format!("unknown task field {key:?}"));
        }
    }
    Ok(())
}

fn string(object: &Map<String, Value>, key: &str) -> Result<String> {
    object.get(key).and_then(Value::as_str)
        .filter(|value| !value.is_empty())
        .map(ToOwned::to_owned)
        .ok_or_else(|| format!("missing or invalid task field {key}"))
}

fn parse(object: &Map<String, Value>) -> Result<Spec> {
    only(object)?;
    if object.get("task_version").and_then(Value::as_u64) != Some(1) {
        return Err("unsupported task_version; expected 1".into());
    }
    if object.get("task_type").and_then(Value::as_str) != Some("generate_named_rng_stream_v1") {
        return Err("unsupported task_type; expected generate_named_rng_stream_v1".into());
    }
    let draw_count = object.get("draw_count").and_then(Value::as_u64)
        .filter(|value| *value > 0)
        .ok_or("draw_count must be a strictly positive integer")?;
    let output_path = crate::task::task_output(&string(object, "output_path")?)?;
    Ok(Spec {
        experiment_id: string(object, "experiment_id")?,
        stage_id: string(object, "stage_id")?,
        task_id: string(object, "task_id")?,
        stream_name: string(object, "stream_name")?,
        draw_count,
        output_path,
    })
}

fn part(hash: &mut Sha256, bytes: &[u8]) {
    hash.update((bytes.len() as u64).to_be_bytes());
    hash.update(bytes);
}

/// SHA-256 over a domain and four ordered, length-prefixed UTF-8 fields.
fn seed_hex(spec: &Spec) -> String {
    let mut hash = Sha256::new();
    part(&mut hash, SEED_DOMAIN.as_bytes());
    for value in [&spec.experiment_id, &spec.stage_id, &spec.task_id, &spec.stream_name] {
        part(&mut hash, value.as_bytes());
    }
    format!("{:x}", hash.finalize())
}

fn seed_bytes(seed_hex: &str) -> [u8; 32] {
    let mut seed = [0u8; 32];
    for (index, byte) in seed.iter_mut().enumerate() {
        *byte = u8::from_str_radix(&seed_hex[index * 2..index * 2 + 2], 16).expect("SHA-256 hex");
    }
    seed
}

fn draws(spec: &Spec, seed_hex: &str) -> Result<Vec<u64>> {
    let count = usize::try_from(spec.draw_count).map_err(|_| "draw_count exceeds platform capacity".to_string())?;
    let mut rng = ChaCha20Rng::from_seed(seed_bytes(seed_hex));
    Ok((0..count).map(|_| rng.next_u64()).collect())
}

/// SHA-256 over the complete canonical stream contract, excluding paths/container metadata.
fn stream_identity(spec: &Spec, seed_hex: &str, values: &[u64]) -> String {
    let mut hash = Sha256::new();
    part(&mut hash, SEMANTIC_DOMAIN.as_bytes());
    for value in [RNG_VERSION, ALGORITHM, SEED_DOMAIN] {
        part(&mut hash, value.as_bytes());
    }
    for value in [&spec.experiment_id, &spec.stage_id, &spec.task_id, &spec.stream_name] {
        part(&mut hash, value.as_bytes());
    }
    part(&mut hash, &seed_bytes(seed_hex));
    hash.update(spec.draw_count.to_be_bytes());
    for (index, value) in values.iter().enumerate() {
        hash.update((index as u64).to_be_bytes());
        hash.update(value.to_be_bytes());
    }
    format!("{:x}", hash.finalize())
}

fn write(path: &Path, values: &[u64], seed_hex: &str, identity: &str) -> Result<()> {
    let indices = UInt64Array::from((0..values.len()).map(|i| i as u64).collect::<Vec<_>>());
    let values = UInt64Array::from(values.to_vec());
    let fields = COLUMNS.iter().map(|(name, datatype)| Field::new(*name, datatype.clone(), false)).collect::<Vec<_>>();
    let mut metadata = std::collections::HashMap::new();
    metadata.insert("nora.rng_version".into(), RNG_VERSION.into());
    metadata.insert("nora.rng_algorithm".into(), ALGORITHM.into());
    metadata.insert("nora.rng_seed_hex".into(), seed_hex.into());
    metadata.insert("nora.rng_stream_identity".into(), identity.into());
    let schema = Arc::new(Schema::new_with_metadata(fields, metadata));
    let batch = RecordBatch::try_new(schema.clone(), vec![Arc::new(indices) as ArrayRef, Arc::new(values) as ArrayRef])
        .map_err(|error| format!("build RNG stream record batch: {error}"))?;
    let mut writer = ArrowWriter::try_new(fs::File::create(path).map_err(|error| format!("create RNG stream Parquet: {error}"))?, schema, None)
        .map_err(|error| format!("open RNG stream Parquet writer: {error}"))?;
    writer.write(&batch).map_err(|error| format!("write RNG stream Parquet: {error}"))?;
    writer.close().map_err(|error| format!("close RNG stream Parquet: {error}"))?;
    Ok(())
}

fn validate(path: &Path, expected_count: u64, identity: &str) -> Result<()> {
    let builder = ParquetRecordBatchReaderBuilder::try_new(fs::File::open(path).map_err(|error| format!("open completed RNG stream: {error}"))?)
        .map_err(|error| format!("read completed RNG stream: {error}"))?;
    let schema = builder.schema();
    if schema.fields().len() != COLUMNS.len() {
        return Err("RNG stream schema must contain exactly draw_index and value_u64".into());
    }
    for (index, (name, datatype)) in COLUMNS.iter().enumerate() {
        let field = schema.field(index);
        if field.name() != *name || field.data_type() != datatype || field.is_nullable() {
            return Err(format!("RNG stream schema mismatch for {name}"));
        }
    }
    if schema.metadata().get("nora.rng_stream_identity").map(String::as_str) != Some(identity) {
        return Err("RNG stream identity metadata validation failed".into());
    }
    let mut rows = 0u64;
    for batch in builder.build().map_err(|error| format!("build RNG stream reader: {error}"))? {
        let batch = batch.map_err(|error| format!("read RNG stream rows: {error}"))?;
        let indices = batch.column(0).as_any().downcast_ref::<UInt64Array>().ok_or("draw_index type mismatch")?;
        let values = batch.column(1).as_any().downcast_ref::<UInt64Array>().ok_or("value_u64 type mismatch")?;
        for row in 0..batch.num_rows() {
            if indices.is_null(row) || values.is_null(row) || indices.value(row) != rows {
                return Err("RNG stream rows are not contiguous, ordered, and non-null".into());
            }
            rows += 1;
        }
    }
    if rows != expected_count { return Err(format!("RNG stream row count {rows} does not equal draw_count {expected_count}")); }
    Ok(())
}

pub fn task(object: &Map<String, Value>) -> Result<Value> {
    let spec = parse(object)?;
    let seed = seed_hex(&spec);
    let values = draws(&spec, &seed)?;
    let identity = stream_identity(&spec, &seed, &values);
    let temp = spec.output_path.with_file_name(format!(".{}.partial", spec.output_path.file_name().and_then(|name| name.to_str()).ok_or("malformed output_path")?));
    if temp.exists() { return Err("task-owned temporary output already exists".into()); }
    let result = (|| { write(&temp, &values, &seed, &identity)?; validate(&temp, spec.draw_count, &identity) })();
    if let Err(error) = result { let _ = fs::remove_file(&temp); return Err(error); }
    fs::rename(&temp, &spec.output_path).map_err(|error| format!("atomic publish RNG stream Parquet: {error}"))?;
    Ok(json!({
        "ok": true, "task_type": "generate_named_rng_stream_v1", "rng_version": RNG_VERSION,
        "algorithm": ALGORITHM, "experiment_id": spec.experiment_id, "stage_id": spec.stage_id,
        "task_id": spec.task_id, "stream_name": spec.stream_name, "draw_count": spec.draw_count,
        "seed_hex": seed, "stream_identity": identity, "output_path": spec.output_path,
    }))
}

#[cfg(test)]
mod tests {
    use super::*;
    fn spec(count: u64) -> Spec { Spec { experiment_id: "experiment-fixture-a".into(), stage_id: "phase2e".into(), task_id: "rng-fixture-001".into(), stream_name: "fixture.primary".into(), draw_count: count, output_path: "/tmp/unused.parquet".into() } }

    #[test]
    fn prefix_and_domain_sensitivity() {
        let s = spec(8); let seed = seed_hex(&s); let values = draws(&s, &seed).unwrap();
        let short = spec(4);
        assert_eq!(seed, "ada6b7c486f979d5accb0edb4e5b57928f514985f0bfd5765bd426e183181c57");
        assert_eq!(values, vec![15683671983959346999,17675346156240728563,9059889430460492925,17956420554887779641,14995845127018178684,324214738316669255,1627427474117293339,4198829781091559740]);
        assert_eq!(stream_identity(&s, &seed, &values), "e8c1364bca46d45610dca7db0c55776dfa2afb1bfd4550dc40c5fd37bbd8aa6e");
        assert_eq!(stream_identity(&short, &seed, &draws(&short, &seed).unwrap()), "0f770f7022c4842e99d65457f9ef1407aa0ba448c334b117d0429ab3fac3a3c2");
        let nine = spec(9); let nine_values = draws(&nine, &seed).unwrap();
        assert_eq!(nine_values[8], 14340693636365067419);
        assert_eq!(stream_identity(&nine, &seed, &nine_values), "9862209c908d5487ef7bade38080b35387319cbc97bdefd49235aeae577f7233");
        assert_eq!(seed, seed_hex(&short));
        assert_eq!(&values[..4], &draws(&short, &seed).unwrap()[..]);
        assert_ne!(stream_identity(&s, &seed, &values), stream_identity(&short, &seed, &values[..4]));
        for mutate in 0..4 {
            let mut changed = s.clone();
            match mutate { 0 => changed.experiment_id.push('x'), 1 => changed.stage_id.push('x'), 2 => changed.task_id.push('x'), _ => changed.stream_name.push('x') }
            let changed_seed = seed_hex(&changed); let changed_values = draws(&changed, &changed_seed).unwrap();
            assert_ne!(seed, changed_seed); assert_ne!(values, changed_values); assert_ne!(stream_identity(&s, &seed, &values), stream_identity(&changed, &changed_seed, &changed_values));
        }
    }
}
