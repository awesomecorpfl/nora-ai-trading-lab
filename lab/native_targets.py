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
