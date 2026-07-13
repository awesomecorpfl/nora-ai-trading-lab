# Execution compile-evidence contracts

The execution canary uses one directed identity graph:

`source/package → compile input → compiler output → execution packet → final batch`

`nora.execution_compile_input_v1` owns pre-compilation facts only. It cannot contain an EX5, compiler output, log hash, timestamp, returned package, packet, or final-batch identity. `nora.execution_compiler_output_v1` owns observed compiler and EX5 evidence and points only to its compile input. `nora.execution_native_packet_v1` owns the post-compile runnable handoff. `nora.execution_final_native_batch_v1` owns staging and native-state gates. Graph validation rejects reverse, self, mixed-stage, and indirect dependencies.

The current repository state is precompile-only: precompile ready, compiler evidence pending, compiler evidence not imported, final packet not ready, native execution not attempted, native parity not accepted, grammar not admitted, and not searchable.

Next native workflow:

1. Generate and stage the compile-input packet.
2. Compile on Windows with the target-specific script.
3. Return the EX5, compiler record, complete log, evidence manifest, and inventory.
4. Import with `python -m lab.phase2_execution_compile_contract import --evidence-dir DIR --destination NEW_DIR`.
5. Commit and push the generated final packet and batch.
6. Stage the final packet.
7. Run four native executions.
8. Return, ingest, and reconcile four independent packages.
