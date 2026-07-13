import json
from pathlib import Path
from lab.mql5gen.time_rules import generate,RUNTIME,TESTER,MARKER,FAIL

ROOT=Path(__file__).resolve().parents[1]
def test_time_rule_generator_is_deterministic_and_static_safe(tmp_path):
 ev=ROOT/'tests/fixtures/phase2_time_rule_rust_evidence.json';a=tmp_path/'a';b=tmp_path/'b';a.mkdir();b.mkdir()
 pa=generate(ev,a);pb=generate(ev,b);assert pa==pb
 assert (a/RUNTIME).read_bytes()==(b/RUNTIME).read_bytes(); assert (a/TESTER).read_bytes()==(b/TESTER).read_bytes()
 text=(a/RUNTIME).read_text()+(a/TESTER).read_text()
 for forbidden in ('TimeCurrent','TimeTradeServer','CopyRates','iMA(','OrderSend','CTrade','AccountInfo','MathRand','Chart') : assert forbidden not in text
 assert MARKER in text and FAIL in text and 'NoraExpected' in text
 assert pa['grammar_admitted'] is False and pa['searchable'] is False
