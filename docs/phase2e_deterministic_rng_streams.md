# Phase 2E: deterministic named RNG streams

Phase 2E adds one standalone `labengine` task. It does not feed randomness into simulation, metrics, strategy generation, Monte Carlo, or search.

## Task schema

The strict v1 task has exactly these fields (unknown fields are rejected and no field has an implicit default):

```json
{
  "task_version": 1,
  "task_type": "generate_named_rng_stream_v1",
  "experiment_id": "experiment-fixture-a",
  "stage_id": "phase2e",
  "task_id": "rng-fixture-001",
  "stream_name": "fixture.primary",
  "draw_count": 8,
  "output_path": "artifacts/rng_stream.parquet"
}
```

The four identity values are non-empty JSON UTF-8 strings, `draw_count` is a strictly positive unsigned integer, and `output_path` is non-empty. The output parent must already exist and the final path must not exist. Publication is write/validate/rename through a task-owned `.partial` file.

## Frozen algorithm and seed

The stream uses `ChaCha20Rng` from the pinned Rust crate `rand_chacha = "=0.9.0"` (lockfile version 0.9.0), with a full 32-byte seed and exactly `next_u64()` once for each draw. No OS entropy, clocks, process/thread identity, paths, or execution ordering participates in the stream.

Seed derivation is SHA-256 over this ordered encoding:

```text
domain = nora.rng.named_chacha20_v1.seed.v1
fields = experiment_id, stage_id, task_id, stream_name
```

The domain and every field are encoded as `u64` big-endian byte length followed by the exact UTF-8 bytes. The resulting 32 digest bytes are the ChaCha20 seed. The successful summary exposes the digest as lowercase 64-character `seed_hex`.

## Stream identity contract

`stream_identity` is SHA-256 over domain `nora.rng.named_chacha20_v1.semantic.v1`, followed by length-prefixed UTF-8 values `named_chacha20_v1`, `chacha20`, and the seed-derivation domain; the four ordered identity fields; a length-prefixed 32-byte derived seed; fixed-width big-endian `draw_count`; and each canonical row's big-endian `(draw_index, value_u64)` pair in order. It therefore binds protocol, algorithm, seed protocol, identities, seed, draw count, and complete content. It excludes output/task paths, temporary directories, and unrelated Parquet metadata.

## Artifact and summary

The atomically published Parquet file has exactly two non-null columns, in order:

```text
draw_index: UInt64
value_u64: UInt64
```

Rows are contiguous from index 0 and count equals `draw_count`. The summary reports `task_type`, `rng_version` (`named_chacha20_v1`), `algorithm` (`chacha20`), all four identity fields, `draw_count`, `seed_hex`, `stream_identity`, and `output_path`.

## Committed baseline

The committed task is `engine/labengine/tests/fixtures/phase2e_rng_stream_task.json`. Running it with the real CLI:

```bash
cargo build --manifest-path engine/Cargo.toml
engine/target/debug/labengine engine/labengine/tests/fixtures/phase2e_rng_stream_task.json
```

produces:

```text
seed_hex = ada6b7c486f979d5accb0edb4e5b57928f514985f0bfd5765bd426e183181c57
draw 0 = 15683671983959346999
draw 1 = 17675346156240728563
draw 2 = 9059889430460492925
draw 3 = 17956420554887779641
draw 4 = 14995845127018178684
draw 5 = 324214738316669255
draw 6 = 1627427474117293339
draw 7 = 4198829781091559740
stream_identity = e8c1364bca46d45610dca7db0c55776dfa2afb1bfd4550dc40c5fd37bbd8aa6e
```

The frozen values and identity are regression assertions in the Rust test module.

## Repeatability, prefix stability, and sensitivity

The baseline was run in `/tmp/phase2e-run-a` and `/tmp/phase2e-run-b`, with different task-file and output paths. Both summaries had the seed above, all eight ordered values above, and the stream identity above. After stripping `output_path`, the summaries were equal; canonical rows were equal. Parquet container bytes are intentionally not a contract.

For the same identity tuple, `draw_count = 4` has the first four baseline values and identity `0f770f7022c4842e99d65457f9ef1407aa0ba448c334b117d0429ab3fac3a3c2`. `draw_count = 8` has the baseline identity; the seed is unchanged and the four-row artifact is its prefix.

Appending `x` independently to one identity field gives these frozen sensitivity results:

| changed field | seed | stream identity |
|---|---|---|
| `experiment_id` (`experiment-fixture-ax`) | `75c907fbb2c34eaa8216fd4d8ddf63ccbc3e96c0aecc0e718fe51aa1e6d401d1` | `52943bb73a860b0ba1214180f6715513d73fa34e5ff88a167813c10eed9d24d7` |
| `stage_id` (`phase2ex`) | `e115db3b94c324e429412d7624cc2ec7058ac851a512d4efbf36a5183a9038a9` | `19fee63f89a4d31bd27a99a0bec3582b6dea298956952aa3e8ce9e14984fb952` |
| `task_id` (`rng-fixture-001x`) | `2e62b1801db2c6fd57822c6bab78af7745f5e68d1f230bda7fb016058824131e` | `8bcc3e959c5d2d63c45abd93c3a6a412979f999726b4169ddca8645bcf995317` |
| `stream_name` (`fixture.primaryx`) | `c5eb05cc0ffa5fd129aff3d751a3e0d2a9e61b6d78be22db6266b44b7fd399c2` | `4debd1ed3e6b179975ed207ad42c2bc28cd6090d092e86700255b2516139c6f2` |

For `draw_count = 9`, the seed remains the baseline seed, the first eight values remain unchanged, draw 8 is `14340693636365067419`, and the identity is `9862209c908d5487ef7bade38080b35387319cbc97bdefd49235aeae577f7233`.

## Atomic failure cases

These real-CLI commands use a fresh output path for each case:

```bash
engine/target/debug/labengine /tmp/phase2e-fail-empty-stream/task.json
engine/target/debug/labengine /tmp/phase2e-fail-zero-count/task.json
engine/target/debug/labengine /tmp/phase2e-fail-unknown-field/task.json
```

Each exits 2, emits no stdout success summary, and leaves no final Parquet artifact (and no seed or stream identity publication). The deterministic errors are respectively `missing or invalid task field stream_name`, `draw_count must be a strictly positive integer`, and `unknown task field "extra"`.

## Regression command

```bash
cargo test --manifest-path engine/Cargo.toml
pytest -q
```

All Phase 2A–2D fixtures and identities remain unchanged, including the baseline closed-trade metrics, combined simulator, combined bracket execution, combined time exit, and the committed indicator/transform/AST/signal/condition/intent/time-contract/UTC anchors.
