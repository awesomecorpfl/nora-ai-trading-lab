import copy
import json
import tempfile
import unittest
from pathlib import Path

from lab.phase2_execution import canon, sha
from lab.phase2_execution_compile_contract import (
    BUILD, COMPILER_OUTPUT_VERSION, EDITOR, POLICY, ROOT, build_compile_input,
    compiler_output_identity, import_evidence, raw_sha, validate_compiler_output,
    validate_graph,
)


def synthetic(root: Path):
    ci=build_compile_input();log=b"execution compile\nResult: 0 errors, 0 warnings\n";ex5=b"synthetic-ex5-not-native"
    (root/"compile.log").write_bytes(log);(root/"NoraPhase2ExecutionTesterCanaryV1.ex5").write_bytes(ex5)
    record={"schema_version":COMPILER_OUTPUT_VERSION,"target_identifier":"execution","compile_input_identity":ci["compile_input_identity"],"runtime_sha256":ci["runtime_sha256"],"tester_sha256":ci["tester_sha256"],"metaeditor_executable":EDITOR,"observed_metaeditor_build":BUILD,"exact_command":"MetaEditor64.exe /compile:tester /log:compile.log","invocation_start_utc":"2040-01-01T00:00:00Z","invocation_completion_utc":"2040-01-01T00:00:01Z","raw_process_exit":1,"normalized_result":"success","compiler_policy":POLICY,"policy_decision":"accepted_metaeditor_5836_one","log_path":"compile.log","log_size":len(log),"log_sha256":raw_sha(log),"warning_count":0,"warnings":[],"error_count":0,"errors":[],"ex5_path":"NoraPhase2ExecutionTesterCanaryV1.ex5","ex5_size":len(ex5),"ex5_modification_utc":"2040-01-01T00:00:01Z","ex5_sha256":raw_sha(ex5),"stale_ex5_disposition":"none_present","freshness_proof":{"preexisting_ex5_removed_or_isolated":True,"produced_after_invocation_start":True,"single_unambiguous_ex5":True},"completion_state":"completed","failure_reason":None}
    record["compiler_output_identity"]=compiler_output_identity(record)
    (root/"compiler_record.json").write_text(canon(record)+"\n")
    manifest={"schema_version":"nora.execution_compile_evidence_manifest_v1","target_identifier":"execution","compile_input_identity":ci["compile_input_identity"]}
    (root/"compile_evidence_manifest.json").write_text(canon(manifest)+"\n")
    inventory=[{"path":p,"role":r,"sha256":raw_sha((root/p).read_bytes())} for p,r in (("compiler_record.json","compiler_record"),("compile.log","compiler_log"),("NoraPhase2ExecutionTesterCanaryV1.ex5","ex5"),("compile_evidence_manifest.json","compile_evidence_manifest"))]
    (root/"inventory.json").write_text(canon(inventory)+"\n");return ci,record


class CompileContracts(unittest.TestCase):
    def test_compile_input_is_deterministic_acyclic_and_sensitive(self):
        base=build_compile_input();self.assertEqual(base,build_compile_input())
        forbidden={"ex5_sha256","compiler_output_identity","compiler_log_sha256","final_batch_identity","returned_package_identity"};self.assertFalse(forbidden & set(base))
        for key in [k for k in base if k != "compile_input_identity"]:
            changed=copy.deepcopy(base);changed[key]=str(changed[key])+"x";changed.pop("compile_input_identity")
            self.assertNotEqual(base["compile_input_identity"],sha(changed))

    def test_valid_import_is_atomic_and_two_directory_deterministic(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as d:
            root=Path(d);e=root/"e";e.mkdir();ci,record=synthetic(e)
            a=import_evidence(e,root/"a");b=import_evidence(e,root/"b");self.assertEqual(a,b)
            for name in ("compile_input.json","execution_packet.json","final_batch.json"):
                self.assertEqual((root/"a"/name).read_bytes(),(root/"b"/name).read_bytes())
            self.assertEqual(a["compile_input_identity"],ci["compile_input_identity"]);self.assertEqual(a["compiler_output_identity"],record["compiler_output_identity"])

    def test_output_rejections(self):
        cases={"target":lambda r:r.__setitem__("target_identifier","macd"),"runtime":lambda r:r.__setitem__("runtime_sha256","0"*64),"tester":lambda r:r.__setitem__("tester_sha256","0"*64),"input":lambda r:r.__setitem__("compile_input_identity","0"*64),"build":lambda r:r.__setitem__("observed_metaeditor_build","1"),"exit":lambda r:r.__setitem__("raw_process_exit",2),"warning":lambda r:(r.__setitem__("warning_count",1),r.__setitem__("warnings",["w"])),"error":lambda r:(r.__setitem__("error_count",1),r.__setitem__("errors",["e"])),"stale":lambda r:r.__setitem__("freshness_proof",{}),"hash":lambda r:r.__setitem__("ex5_sha256","0"*64)}
        with tempfile.TemporaryDirectory(dir=ROOT) as d:
            root=Path(d);ci,record=synthetic(root)
            for mutate in cases.values():
                bad=copy.deepcopy(record);mutate(bad);bad["compiler_output_identity"]=compiler_output_identity(bad)
                self.assertTrue(validate_compiler_output(bad,ci,root))

    def test_import_rejects_missing_unexpected_traversal_occupied_and_interruption(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as d:
            root=Path(d);e=root/"e";e.mkdir();synthetic(e);(root/"occupied").mkdir()
            with self.assertRaises(ValueError):import_evidence(e,root/"occupied")
            (e/"extra.ex5").write_bytes(b"x")
            with self.assertRaises(ValueError):import_evidence(e,root/"out")
            self.assertFalse((root/"out").exists())
            (e/"extra.ex5").unlink();record=json.loads((e/"compiler_record.json").read_text());record["log_path"]="../compile.log";record["compiler_output_identity"]=compiler_output_identity(record);(e/"compiler_record.json").write_text(canon(record)+"\n")
            with self.assertRaises(ValueError):import_evidence(e,root/"out")

    def test_interrupted_import_never_publishes(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as d:
            root=Path(d);e=root/"e";e.mkdir();synthetic(e)
            with self.assertRaises(RuntimeError):import_evidence(e,root/"out",inject_failure=True)
            self.assertFalse((root/"out").exists())
            self.assertFalse(list(root.glob(".execution-compile-import-*")))

    def test_import_rejects_missing_log_ex5_and_cross_target_manifest(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as d:
            root=Path(d)
            for missing in ("compile.log","NoraPhase2ExecutionTesterCanaryV1.ex5"):
                e=root/("e-"+missing.replace(".","-"));e.mkdir();synthetic(e);(e/missing).unlink()
                with self.assertRaises(ValueError):import_evidence(e,root/("out-"+missing.replace(".","-")))
            e=root/"cross";e.mkdir();synthetic(e);manifest=json.loads((e/"compile_evidence_manifest.json").read_text());manifest["target_identifier"]="percentile";(e/"compile_evidence_manifest.json").write_text(canon(manifest)+"\n")
            with self.assertRaises(ValueError):import_evidence(e,root/"cross-out")

    def test_graph_rejects_reverse_self_and_indirect_cycles(self):
        self.assertFalse(validate_graph({"source":[],"compile_input":["source"],"compiler_output":["compile_input"],"execution_packet":["compiler_output"],"final_batch":["execution_packet"]}))
        self.assertTrue(validate_graph({"compile_input":["final_batch"],"final_batch":["compile_input"]}))
        self.assertTrue(validate_graph({"execution_packet":["execution_packet"]}))
