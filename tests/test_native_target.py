import copy
from pathlib import Path
import pytest
from lab.native_target import NativeTargetDescriptor, atomic_publish, safe_relative, validate_dependency_graph

def descriptor(target="time_rules"):
 return NativeTargetDescriptor("nora.native_target_descriptor_v1",target,"ci","co","ce","packet","pre","final","returned","r.mqh","t.mq5","p.json","t.ex5","ci.json","r.csv","compile.ps1","execute.ps1","collect.ps1","DONE","FAIL","time_rules_exact_v1",("GDAXI/M1:A1","AUDCAD/M1:B1"),("execution_record","result_csv"))

def test_descriptor_is_deterministic_typed_and_semantically_sensitive():
 a=descriptor();assert a.identity==descriptor().identity;assert a.identity!=descriptor("execution").identity
 assert "expected" not in str(a.value()).lower()

def test_graph_path_and_atomic_mechanics_fail_closed(tmp_path):
 assert not validate_dependency_graph({"source":[],"compile_input":["source"],"compiler_output":["compile_input"],"execution_packet":["compiler_output"],"final_batch":["execution_packet"]})
 assert validate_dependency_graph({"compile_input":["final_batch"],"final_batch":["compile_input"]})
 assert safe_relative("compile/a.ex5") and not safe_relative("../a") and not safe_relative("C:\\a")
 with pytest.raises(RuntimeError): atomic_publish(tmp_path/"out",".native-",lambda p:(p/"x").write_text("x"),inject_failure=True)
 assert not (tmp_path/"out").exists()
