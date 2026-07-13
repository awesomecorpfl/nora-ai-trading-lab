# Execution compile-evidence contracts

The execution canary uses one directed identity graph:

`source/package → compile input → compiler output → execution packet → final batch`

`nora.execution_compile_input_v1` owns pre-compilation facts only. It cannot contain an EX5, compiler output, log hash, timestamp, returned package, packet, or final-batch identity. `nora.execution_compiler_output_v1` owns observed compiler and EX5 evidence and points only to its compile input. `nora.execution_native_packet_v1` owns the post-compile runnable handoff. `nora.execution_final_native_batch_v1` owns staging and native-state gates. Graph validation rejects reverse, self, mixed-stage, and indirect dependencies.

The execution target has now completed this chain. Genuine compiler evidence is imported, the final packet is sealed, and four independent GDAXI/M1 and AUDCAD/M1 runs reconcile exactly. Native execution-model parity is accepted only for the frozen twelve-scenario contract. Grammar remains unadmitted, the target remains non-searchable, and the complete Phase-2 gate remains false.

Completed native workflow:

1. Generate and stage the compile-input packet.
2. Compile on Windows with the target-specific script.
3. Return the EX5, compiler record, complete log, evidence manifest, and inventory.
4. Import with `python -m lab.phase2_execution_compile_contract import --evidence-dir DIR --destination NEW_DIR`.
5. Commit and push the generated final packet and batch.
6. Stage the final packet.
7. Run four native executions.
8. Return, ingest, and reconcile four independent packages.

The immutable acceptance index is `tests/fixtures/phase2_execution_native_accepted/native_acceptance.json`. It preserves the compiler record and log, EX5, final packet and batch, four raw returned packages, four reconciliation records, repeatability, independence, and host-neutrality evidence.
