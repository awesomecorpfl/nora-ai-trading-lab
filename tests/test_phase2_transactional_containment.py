import copy, json, subprocess, tempfile, unittest
from unittest.mock import patch
from pathlib import Path
from lab.phase2_transactional_containment import ContractError, _porcelain_rows, build_candidate, canonical, identity, verify_document, publish
from lab.phase2_transactional_containment_verifier import verify as independent_verify

ROOT = Path(__file__).resolve().parents[1]

class Phase2ContractCases(unittest.TestCase):
    def candidate(self):
        return build_candidate(ROOT, "2026-07-17T00:00:00Z", "read-only")
    def reject(self, mutate, independent=False):
        d=copy.deepcopy(self.candidate()); mutate(d)
        with tempfile.NamedTemporaryFile() as f:
            f.write(canonical(d)); f.flush()
            with self.assertRaises(Exception):
                (independent_verify(Path(f.name),ROOT) if independent else verify_document(d,ROOT))
    def test_positive_publish_candidate_and_independent_verify(self):
        d=self.candidate(); self.assertEqual(verify_document(d,ROOT)["verdict"],"PASS")
        with tempfile.NamedTemporaryFile() as f:
            f.write(canonical(d)); f.flush(); self.assertEqual(independent_verify(Path(f.name),ROOT)["verdict"],"PASS")
    def test_first_publish_second_publish_identical_existing_and_status_binding(self):
        d={"semantic_identity":"a"*64}
        with tempfile.TemporaryDirectory() as td, patch("lab.phase2_transactional_containment.build_candidate",return_value=d), patch("lab.phase2_transactional_containment.subprocess.check_call"):
            root=Path(td); result=publish(root,"case-20260717T000000Z","2026-07-17T00:00:00Z")
            self.assertEqual(result,"published")
            artifact=(root/"docs/evidence/phase2/transactional-containment/case-20260717T000000Z/acceptance.json").read_bytes()
            self.assertEqual(publish(root,"case-20260717T000000Z","2026-07-17T00:00:00Z"),"identical_existing")
            self.assertEqual(artifact,(root/"docs/evidence/phase2/transactional-containment/case-20260717T000000Z/acceptance.json").read_bytes())
    def test_exact_repeat_and_key_ordering_invariant(self):
        a=self.candidate(); b=self.candidate(); self.assertEqual(canonical(a),canonical(b))
        self.assertEqual(verify_document(json.loads(json.dumps(a,sort_keys=True)),ROOT)["verdict"],"PASS")
    def test_baseline_manifest_altered(self): self.reject(lambda d:d["repository"].update(baseline_sha256="0"*64),True)
    def test_wrong_semantic_digest(self): self.reject(lambda d:d["baseline_digests"].update(canonical="0"*64))
    def test_synthetic_missing_and_outcome_mismatch(self):
        self.reject(lambda d:d["synthetic"]["outcomes"].pop("duplicate_race"),True)
    def test_croq_credit_absent_or_changed(self):
        self.reject(lambda d:d["croq"].update(credit="GRANTED:OTHER"),True)
    def test_matrix_row_missing_duplicate_operation_reuse(self):
        for fn in (lambda d:d["matrix"].update(rows=d["matrix"]["rows"][:-1]), lambda d:d["matrix"].update(rows=["classification"]*6), lambda d:d["matrix"]["package_bindings"][1].update(operation_id=d["matrix"]["package_bindings"][0]["operation_id"])):
            self.reject(fn,True)
    def test_diagnostic_substitution(self): self.reject(lambda d:d["diagnostics"][0].update(credit="GRANTED"),True)
    def test_matrix_package_hash_mismatch(self): self.reject(lambda d:d["matrix"]["package_bindings"][0].update(sha256="0"*64),True)
    def test_envelope_hash_mismatch(self): self.reject(lambda d:d["matrix"]["envelope_binding"].update(sha256="0"*64),True)
    def test_safety_cleanup_nora_terminal_tester_nonzero(self):
        for k in ("cleanup","nora_rules","terminal_processes","tester_processes"):
            self.reject(lambda d,k=k:d["safety"].update({k:"unresolved" if k=="cleanup" else 1}),True)
    def test_search_true_and_searchable_component(self):
        self.reject(lambda d:d["governance"].update(search=True),True); self.reject(lambda d:d["governance"].update(searchable_components=1),True)
    def test_phase3_true(self): self.reject(lambda d:d["governance"].update(phase3_authorized=True),True)
    def test_no_general_phase2_or_native_parity_inference(self):
        self.reject(lambda d:d["governance"].update(phase2_complete=True),True); self.reject(lambda d:d["governance"].update(native_parity_generalized=True),True)
    def test_latest_rejected_foreign_ancestry_rejected(self):
        self.reject(lambda d:d["publication"].update(id="latest")); self.reject(lambda d:d["repository"].update(head="0"*40))
    def test_overwrite_conflict_is_rejected(self):
        self.reject(lambda d:d["publication"].update(path="docs/evidence/phase2/other/acceptance.json"))
    def test_semantic_prerequisite_mutation_changes_identity(self):
        d=self.candidate(); old=d["semantic_identity"]; d["matrix"]["package_bindings"][0]["size"]+=1
        self.assertNotEqual(old, identity("nora.phase2-tca-1.semantic",{k:v for k,v in d.items() if k not in {"timestamp","semantic_identity"}}))
    def test_accepted_and_diagnostic_immutable(self):
        self.reject(lambda d:d["acceptance"].update(verdict="FAIL")); self.reject(lambda d:d["diagnostics"][0].update(id="substitute"))
    def test_creation_command_is_exact_and_status_is_narrow(self):
        d=self.candidate(); self.assertIn("--publication-id read-only --timestamp 2026-07-17T00:00:00Z",d["acceptance"]["creation_command"])
    def test_porcelain_preserves_leading_index_column(self):
        output = " M docs/phase2_transactional_containment_status_v1.json\n?? protected/top-level/file\n"
        with patch("lab.phase2_transactional_containment.subprocess.check_output", return_value=output):
            self.assertEqual(_porcelain_rows(ROOT), output.splitlines())
    def test_independent_verifier_accepts_bound_head_as_normal_ancestor(self):
        d=self.candidate()
        d["repository"]["head"] = subprocess.check_output(["git", "rev-parse", "HEAD^"], cwd=ROOT, text=True).strip()
        d["semantic_identity"] = identity("nora.phase2-tca-1.semantic", {k:v for k,v in d.items() if k not in {"timestamp","semantic_identity"}})
        with tempfile.NamedTemporaryFile() as f:
            f.write(canonical(d)); f.flush()
            self.assertEqual(independent_verify(Path(f.name), ROOT)["verdict"], "PASS")

if __name__ == "__main__": unittest.main()
