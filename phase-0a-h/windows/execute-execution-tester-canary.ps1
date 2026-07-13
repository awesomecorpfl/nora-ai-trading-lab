param([string]$IncomingRoot,[string]$RunId,[string]$Symbol='GDAXI')
# Contract-only fixed-path execution tester handoff. GDAXI/AUDCAD are inert host contexts.
$target='execution';$csv='nora_phase2_execution_tester_v1.csv';$complete='NORA_PHASE2_EXECUTION_COMPLETE_V1';$fail='NORA_PHASE2_EXECUTION_FAIL'
@{target_identifier=$target;symbol=$Symbol;timeframe='M1';result_filename=$csv;completion_marker=$complete;failure_marker=$fail;no_trading_deployment=$true;require_journal=$true;require_report=$true}|ConvertTo-Json -Compress
