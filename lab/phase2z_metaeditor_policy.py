"""Strict build-5836 MetaEditor CLI exit normalization."""
VERSION="nora.metaeditor_cli_success_v1"
def evaluate(record):
    required=("version","source","log_complete","zero_errors","zero_warnings","fresh_ex5","expected_ex5_path","hashes_match")
    checks=record.get("checks",{})
    if any(checks.get(key) is not True for key in required): return False,"missing or failed corroboration"
    exit_code=record.get("exit")
    if exit_code==0:return True,"accepted_zero"
    if exit_code==1 and record.get("metaeditor_version")=="5.0.0.5836":return True,"accepted_metaeditor_5836_one"
    return False,"unexpected exit"
