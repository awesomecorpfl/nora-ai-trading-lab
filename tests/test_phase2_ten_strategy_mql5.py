from pathlib import Path
from lab.mql5gen.ten_strategy import *

def test_generation_is_byte_deterministic_and_expected_ledgers_are_absent(tmp_path):
 a=tmp_path/'a';b=tmp_path/'b';pa=generate(a);pb=generate(b);assert pa==pb
 for name in (RUNTIME,TESTER,PACKAGE):assert (a/name).read_bytes()==(b/name).read_bytes()
 text=(a/TESTER).read_text()+(a/RUNTIME).read_text();assert 'expected_ledger' not in text.lower()

def test_static_safety_has_no_market_clock_account_or_trade_dependency(tmp_path):
 generate(tmp_path);text=((tmp_path/RUNTIME).read_text()+(tmp_path/TESTER).read_text()).lower()
 forbidden=('copyrates','copybuffer','ihigh','ilow','iclose','iopen','symbolinfo','timecurrent','timeserver','timelocal','accountinfo','positions','orders','ctrade','buy(','sell(','mathrand','rand(')
 assert all(x not in text for x in forbidden)
 assert 'ontick(){}' in text and 'file_common' in text

def test_runtime_contains_independent_kernels_and_accepted_precedence(tmp_path):
 generate(tmp_path);text=(tmp_path/RUNTIME).read_text()
 for token in ('void Ema','void Atr','void ShiftedLevel','bool Cross','gap_stop','signal_exit','time_exit','pessimistic_dual_touch'):assert token in text
