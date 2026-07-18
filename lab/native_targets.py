"""Immutable descriptors for accepted Phase-2 native targets."""
from lab.native_target import NativeTargetDescriptor

MEMBERS=("compiler_record","compiler_log","execution_record","result_csv","bounded_journal","tester_report_substitute","completion_marker_state","failure_marker_state")

EXECUTION_TARGET=NativeTargetDescriptor(
 "nora.native_target_descriptor_v1","execution","nora.execution_compile_input_v1",
 "nora.execution_compiler_output_v1","nora.execution_compile_evidence_manifest_v1",
 "nora.execution_native_packet_v1","nora.phase2x.execution_native_batch_v5",
 "nora.execution_final_native_batch_v1","nora.execution_returned_package_v2",
 "NoraPhase2ExecutionRuntimeV1.mqh","NoraPhase2ExecutionTesterCanaryV1.mq5",
 "phase2_execution_executable_package.json","NoraPhase2ExecutionTesterCanaryV1.ex5",
 "execution_compile_input_v1.json","nora_phase2_execution_tester_v1.csv",
 "phase-0a-h/windows/compile-execution-tester-canary.ps1",
 "phase-0a-h/windows/execute-execution-tester-canary.ps1",
 "phase-0a-h/windows/build-execution-returned-package.ps1",
 "NORA_PHASE2_EXECUTION_COMPLETE_V1","NORA_PHASE2_EXECUTION_FAIL",
 "nora.execution_native_reconciliation_v1",
 ("GDAXI/M1:A1","GDAXI/M1:A2","AUDCAD/M1:B1","AUDCAD/M1:B2"),MEMBERS)

TIME_RULE_TARGET=NativeTargetDescriptor(
 "nora.native_target_descriptor_v1","time_rules","nora.time_rule_compile_input_v1",
 "nora.time_rule_compiler_output_v1","nora.time_rule_compile_evidence_manifest_v1",
 "nora.time_rule_native_packet_v1","nora.time_rule_precompile_batch_v1",
 "nora.time_rule_final_native_batch_v1","nora.time_rule_returned_package_v1",
 "NoraPhase2TimeRuleRuntimeV1.mqh","NoraPhase2TimeRuleTesterCanaryV1.mq5",
 "phase2_time_rule_executable_package.json","NoraPhase2TimeRuleTesterCanaryV1.ex5",
 "time_rule_compile_input_v1.json","nora_phase2_time_rule_tester_v1.csv",
 "phase-0a-h/windows/compile-time-rule-tester-canary.ps1",
 "phase-0a-h/windows/execute-time-rule-tester-canary.ps1",
 "phase-0a-h/windows/build-time-rule-returned-package.ps1",
 "NORA_PHASE2_TIME_RULE_COMPLETE_V1","NORA_PHASE2_TIME_RULE_FAIL_V1",
 "nora.time_rule_native_reconciliation_v1",
 ("GDAXI/M1:A1","GDAXI/M1:A2","AUDCAD/M1:B1","AUDCAD/M1:B2"),MEMBERS)

LAYER1_BATCH_TARGET=NativeTargetDescriptor(
 "nora.native_target_descriptor_v1","layer1_first_batch","nora.layer1_compile_input_v1",
 "nora.layer1_compiler_output_v1","nora.layer1_compile_evidence_manifest_v1",
 "nora.layer1_native_packet_v1","nora.layer1_precompile_batch_v1",
 "nora.layer1_final_native_batch_v1","nora.layer1_returned_package_v1",
 "NoraPhase2Layer1BatchRuntimeV1.mqh","NoraPhase2Layer1BatchTesterCanaryV1.mq5",
 "phase2_layer1_batch_executable_package.json","NoraPhase2Layer1BatchTesterCanaryV1.ex5",
 "layer1_compile_input_v1.json","nora_phase2_layer1_batch_v1.csv",
 "scripts/phase2-layer1-build-compile-input",
 "scripts/phase2-layer1-ingest-returned",
 "scripts/phase2-layer1-build-synthetic-package",
 "NORA_PHASE2_LAYER1_BATCH_COMPLETE_V1","NORA_PHASE2_LAYER1_BATCH_FAIL_V1",
 "nora.layer1_numeric_reconciliation_v1",
 ("GDAXI/M1:A1","GDAXI/M1:A2","AUDCAD/M1:B1","AUDCAD/M1:B2"),MEMBERS)

TEN_STRATEGY_TARGET=NativeTargetDescriptor(
 "nora.native_target_descriptor_v1","phase2_ten_strategy_suite","nora.ten_strategy_compile_input_v1",
 "nora.ten_strategy_compiler_output_v1","nora.ten_strategy_compile_evidence_manifest_v1",
 "nora.ten_strategy_native_packet_v1","nora.ten_strategy_precompile_batch_v1",
 "nora.ten_strategy_final_native_batch_v1","nora.ten_strategy_returned_package_v1",
 "NoraPhase2TenStrategyRuntimeV1.mqh","NoraPhase2TenStrategyTesterCanaryV1.mq5",
 "phase2_ten_strategy_executable_package.json","NoraPhase2TenStrategyTesterCanaryV1.ex5",
 "ten_strategy_compile_input_v1.json","nora_phase2_ten_strategy_v1.csv",
 "phase-0a-h/windows/compile-ten-strategy-tester-canary.ps1","scripts/phase2-ten-strategy-ingest-returned","scripts/phase2-ten-strategy-build-synthetic-package",
 "NORA_PHASE2_TEN_STRATEGY_COMPLETE_V1","NORA_PHASE2_TEN_STRATEGY_FAIL_V1","nora.ten_strategy_trade_reconciliation_v1",
 ("GDAXI/M1:A1","GDAXI/M1:A2","AUDCAD/M1:B1","AUDCAD/M1:B2"),MEMBERS)
