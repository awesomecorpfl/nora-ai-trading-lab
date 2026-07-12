"""Phase-2M MQL5 slope generator regression tests."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from lab.mql5gen import GenerationError
from lab.mql5gen.slope import (
    CSV_COLUMNS,
    EXPECTED_SLOPE,
    INPUT_IDENTITY,
    INPUT_VECTOR,
    LOOKBACK,
    RUNTIME_IDENTITY,
    SLOPE_IDENTITY,
    TESTER_SOURCE_FILENAME,
    TESTER_VERSION,
    _identity,
    _literal,
    generate_slope_runtime,
    generate_slope_runtime_identity,
    generate_slope_tester,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "tests/fixtures/phase2m_mql5_slope/slope_evidence.json"
RUNTIME_MANIFEST = ROOT / "tests/fixtures/phase2m_mql5_slope/NoraPhase2SlopeRuntimeV1.manifest.json"
TESTER_MANIFEST = ROOT / "tests/fixtures/phase2m_mql5_slope/NoraPhase2SlopeTesterCanaryV1.manifest.json"
TESTER_SOURCE = ROOT / "tests/fixtures/phase2m_mql5_slope/NoraPhase2SlopeTesterCanaryV1.mq5"


def _nums(values):
    return ", ".join("0.0" if v is None else _literal(float(v)) for v in values)


def _nulls(values):
    return ", ".join("true" if v is None else "false" for v in values)


def _compute_tester_identity(input_vec, expected_vec, runtime_id):
    """Compute tester identity from vectors (matches generator logic)."""
    numeric = (
        "const double NoraSlopeInput_Values[12] = {" + _nums(input_vec) + "};\n"
        "const bool NoraSlopeInput_NullMask[12] = {" + _nulls(input_vec) + "};\n"
    )
    expected_block = (
        "const double NoraExpectedSlope_Values[12] = {" + _nums(expected_vec) + "};\n"
        "const bool NoraExpectedSlope_NullMask[12] = {" + _nulls(expected_vec) + "};\n"
    )

    source_text = """#property strict

#include "NoraPhase2RuntimeV1.mqh"
#include "NoraPhase2SlopeRuntimeV1.mqh"

#define NORA_PHASE2M_ROW_COUNT 12

""" + numeric + expected_block + r'''
NoraNullableDoubleV1 NoraSlopeInputValue(const int row_index)
{
   if(row_index < 0 || row_index >= NORA_PHASE2M_ROW_COUNT || NoraSlopeInput_NullMask[row_index])
      return NoraNumericNullV1();
   return NoraNumericValueV1(NoraSlopeInput_Values[row_index]);
}

string NoraPhase2MNullableText(const NoraNullableDoubleV1 &value)
{
   if(value.is_null)
      return "null";
   return DoubleToString(value.value, 16);
}

int OnInit()
{
   const int handle = FileOpen("nora_phase2_slope_tester_v1.csv", FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON, ',');
   if(handle == INVALID_HANDLE)
      return INIT_FAILED;
   FileWrite(handle, "record_type", "row_index", "actual_slope", "expected_slope", "row_pass", "row_count", "passed_rows", "failed_rows", "overall_pass");
   int passed_rows = 0;
   int failed_rows = 0;
   for(int row_index = 0; row_index < NORA_PHASE2M_ROW_COUNT; row_index++)
   {
      NoraNullableDoubleV1 current = NoraSlopeInputValue(row_index);
      NoraNullableDoubleV1 previous = row_index == 0 ? NoraNumericNullV1() : NoraSlopeInputValue(row_index - 1);
      NoraNullableDoubleV1 actual_slope = NoraSlopeLookback1V1(current, previous);
      bool current_null = actual_slope.is_null;
      bool expected_null = NoraExpectedSlope_NullMask[row_index];
      bool row_pass = false;
      if(current_null && expected_null)
         row_pass = true;
      else if(!current_null && !expected_null)
         row_pass = MathAbs(actual_slope.value - NoraExpectedSlope_Values[row_index]) < 0.000000000000001;
      if(row_pass)
         passed_rows++;
      else
         failed_rows++;
      FileWrite(handle, "row", row_index, NoraPhase2MNullableText(actual_slope), expected_null ? "null" : DoubleToString(NoraExpectedSlope_Values[row_index], 16), row_pass ? "true" : "false", "", "", "", "");
   }
   bool overall_pass = passed_rows == NORA_PHASE2M_ROW_COUNT && failed_rows == 0;
   FileWrite(handle, "summary", -1, "", "", overall_pass ? "true" : "false", NORA_PHASE2M_ROW_COUNT, passed_rows, failed_rows, overall_pass ? "true" : "false");
   FileFlush(handle);
   FileClose(handle);
   TesterStop();
   return overall_pass ? INIT_SUCCEEDED : INIT_FAILED;
}
'''
    source = source_text.encode("utf-8")
    sha = hashlib.sha256(source).hexdigest()
    identity = _identity("nora.mql5.slope_tester_canary_v1.semantic.v1", [
        TESTER_VERSION,
        RUNTIME_IDENTITY,
        runtime_id,
        INPUT_IDENTITY,
        SLOPE_IDENTITY,
        LOOKBACK,
        input_vec,
        expected_vec,
        CSV_COLUMNS,
        "nora_phase2_slope_tester_v1.csv",
        source_text,
        sha
    ])
    return identity, sha, source_text


class Phase2MSlopeGeneratorTests(unittest.TestCase):
    """Regression tests for Phase-2M slope MQL5 generator."""

    def make_runtime(self, root: Path):
        root.mkdir(parents=True, exist_ok=True)
        out = root / "runtime"
        out.mkdir()
        result = generate_slope_runtime(out)
        return out, result

    def make_tester(self, root: Path, evidence_path=None):
        runtime_dir, _ = self.make_runtime(root)
        out = root / "tester"
        out.mkdir()
        if evidence_path is None:
            evidence_path = EVIDENCE
        result = generate_slope_tester(evidence_path, runtime_dir / "NoraPhase2SlopeRuntimeV1.manifest.json", out)
        return out, result

    def test_generation_is_byte_identical_and_manifest_has_no_paths(self):
        """Two separate temp dirs must produce byte-identical source, manifest, and identity."""
        with tempfile.TemporaryDirectory() as td:
            a = Path(td) / "a"
            b = Path(td) / "b"
            a.mkdir()
            b.mkdir()
            # Generate tester (which creates runtime internally)
            at, at_result = self.make_tester(a)
            bt, bt_result = self.make_tester(b)
            # Runtime directories are at a/runtime and b/runtime
            ar = a / "runtime"
            br = b / "runtime"

            # Runtime source and manifest byte-identical
            self.assertEqual(
                (ar / "NoraPhase2SlopeRuntimeV1.mqh").read_bytes(),
                (br / "NoraPhase2SlopeRuntimeV1.mqh").read_bytes(),
            )
            self.assertEqual(
                (ar / "NoraPhase2SlopeRuntimeV1.manifest.json").read_bytes(),
                (br / "NoraPhase2SlopeRuntimeV1.manifest.json").read_bytes(),
            )
            # Tester source byte-identical
            self.assertEqual(
                (at / TESTER_SOURCE_FILENAME).read_bytes(),
                (bt / TESTER_SOURCE_FILENAME).read_bytes(),
            )
            # Tester manifest semantically identical (JSON equality)
            self.assertEqual(
                json.loads((at / "NoraPhase2SlopeTesterCanaryV1.manifest.json").read_text()),
                json.loads((bt / "NoraPhase2SlopeTesterCanaryV1.manifest.json").read_text()),
            )
            # No absolute paths in manifests
            runtime_manifest_a = (ar / "NoraPhase2SlopeRuntimeV1.manifest.json").read_bytes()
            self.assertNotIn(str(a).encode(), runtime_manifest_a)
            self.assertNotIn(str(b).encode(), runtime_manifest_a)

    def test_reproduced_source_hashes_and_semantic_identities(self):
        """Reproduced artifacts match accepted fixture hashes and identities."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "run"
            tester_dir, tester_result = self.make_tester(root)
            runtime_dir, runtime_result = self.make_runtime(root / "runtime_only")

            # Runtime source SHA-256
            self.assertEqual(runtime_result["source_sha256"], "a3b2dc447b59e6800dee7c875e9d25ea2353fc32b04c73391871623c08842c80")
            # Runtime semantic identity
            self.assertEqual(runtime_result["slope_runtime_identity"], "cb9eee8e4c03d6c6d95c6ba384701187c93730f77fafe3a22a2f8902410c68ae")

            # Tester source SHA-256
            self.assertEqual(tester_result["source_sha256"], "6d4f2e9f0a7e1dcd33004500dfea8deaad4c5a4e9804e57ef8377369f67a4f53")
            # Tester semantic identity
            self.assertEqual(tester_result["slope_tester_identity"], "a25fe8a6b459499debdbc9d48c8d4dd498a9684bf67b196501ebed743b48b54d")

    def test_generated_content_has_no_temp_or_absolute_paths(self):
        """Generated source and manifests must not embed temporary or absolute paths."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "run"
            tester_dir, tester_result = self.make_tester(root)
            runtime_dir, runtime_result = self.make_runtime(root / "runtime_only")

            for path in [
                runtime_dir / "NoraPhase2SlopeRuntimeV1.mqh",
                runtime_dir / "NoraPhase2SlopeRuntimeV1.manifest.json",
                tester_dir / TESTER_SOURCE_FILENAME,
                tester_dir / "NoraPhase2SlopeTesterCanaryV1.manifest.json",
            ]:
                text = path.read_text()
                self.assertNotIn("/tmp", text)
                self.assertNotIn(td, text)
                self.assertNotIn(str(root), text)

    def test_sma3_fixture_index_5_mutation_changes_identity_and_slopes(self):
        """Changing SMA3 fixture value at index 5 changes identity and expected slopes."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "run"
            _, baseline_result = self.make_tester(root)

            # Mutate evidence: change input index 5
            evidence = json.loads(EVIDENCE.read_text())
            mutated = dict(evidence)
            mutated["input_vector"] = list(evidence["input_vector"])
            mutated["input_vector"][5] = 1.1014  # Changed from 1.101333...
            # Expected slope at index 5 changes accordingly
            mutated["expected_slope_vector"] = list(evidence["expected_slope_vector"])
            mutated["expected_slope_vector"][5] = 0.0004333333333334
            mutated["expected_slope_vector"][6] = -0.0000333333333334

            mutation_path = Path(td) / "mutated.json"
            mutation_path.write_text(json.dumps(mutated))

            root2 = Path(td) / "run2"
            _, mutated_result = self.make_tester(root2, mutation_path)

            self.assertNotEqual(baseline_result["source_sha256"], mutated_result["source_sha256"])
            self.assertNotEqual(baseline_result["slope_tester_identity"], mutated_result["slope_tester_identity"])

    def test_sma3_fixture_index_3_null_propagates_to_slopes_3_and_4(self):
        """Setting SMA3 index 3 to null propagates null to slope indices 3 and 4."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "run"
            _, baseline_result = self.make_tester(root)

            evidence = json.loads(EVIDENCE.read_text())
            mutated = dict(evidence)
            mutated["input_vector"] = list(evidence["input_vector"])
            mutated["input_vector"][3] = None  # Make index 3 null
            mutated["expected_slope_vector"] = list(evidence["expected_slope_vector"])
            # Index 3 becomes null (was 0.000333...)
            mutated["expected_slope_vector"][3] = None
            # Index 4 becomes null (current=4, previous=3 which is now null)
            mutated["expected_slope_vector"][4] = None

            mutation_path = Path(td) / "mutated.json"
            mutation_path.write_text(json.dumps(mutated))

            root2 = Path(td) / "run2"
            _, mutated_result = self.make_tester(root2, mutation_path)

            self.assertNotEqual(baseline_result["source_sha256"], mutated_result["source_sha256"])
            self.assertNotEqual(baseline_result["slope_tester_identity"], mutated_result["slope_tester_identity"])

            # Verify the generated source has null at indices 3 and 4 for expected slope
            source_text = (root2 / "tester" / TESTER_SOURCE_FILENAME).read_text()
            # Expected slope null mask should have true at indices 0,1,2,3,4
            self.assertIn("true, true, true, true, true, false", source_text)  # Expected slope null mask

    def test_unsupported_lookback_2_rejected_atomically(self):
        """Lookback 2 is an invalid-input failure; no partial outputs produced."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "run"
            runtime_dir, _ = self.make_runtime(root / "runtime")
            evidence = json.loads(EVIDENCE.read_text())
            mutated = dict(evidence)
            mutated["lookback"] = 2  # Unsupported
            bad_path = Path(td) / "bad.json"
            bad_path.write_text(json.dumps(mutated))

            tester_dir = root / "tester"
            with self.assertRaises(GenerationError):
                generate_slope_tester(bad_path, runtime_dir / "NoraPhase2SlopeRuntimeV1.manifest.json", tester_dir)

            # No partial outputs
            self.assertFalse((tester_dir / TESTER_SOURCE_FILENAME).exists())
            self.assertFalse((tester_dir / "NoraPhase2SlopeTesterCanaryV1.manifest.json").exists())

    def test_atomic_failure_missing_input(self):
        """Missing evidence file fails atomically with GenerationError."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "run"
            runtime_dir, _ = self.make_runtime(root / "runtime")
            missing = Path(td) / "missing.json"
            tester_dir = root / "tester"
            with self.assertRaisesRegex(GenerationError, "unreadable|malformed"):
                generate_slope_tester(missing, runtime_dir / "NoraPhase2SlopeRuntimeV1.manifest.json", tester_dir)
            self.assertFalse((tester_dir / TESTER_SOURCE_FILENAME).exists())

    def test_atomic_failure_non_finite_input(self):
        """Non-finite input (NaN) fails atomically with GenerationError."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "run"
            runtime_dir, _ = self.make_runtime(root / "runtime")
            evidence = json.loads(EVIDENCE.read_text())
            mutated = dict(evidence)
            mutated["input_vector"] = list(evidence["input_vector"])
            mutated["input_vector"][0] = float("nan")
            bad_path = Path(td) / "nan.json"
            bad_path.write_text(json.dumps(mutated))
            tester_dir = root / "tester"
            with self.assertRaisesRegex(GenerationError, "finite"):
                generate_slope_tester(bad_path, runtime_dir / "NoraPhase2SlopeRuntimeV1.manifest.json", tester_dir)
            self.assertFalse((tester_dir / TESTER_SOURCE_FILENAME).exists())

    def test_atomic_failure_expected_vector_length_mismatch(self):
        """Expected slope vector length mismatch fails atomically."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "run"
            runtime_dir, _ = self.make_runtime(root / "runtime")
            evidence = json.loads(EVIDENCE.read_text())
            mutated = dict(evidence)
            mutated["expected_slope_vector"] = [None] * 11  # Wrong length
            bad_path = Path(td) / "bad.json"
            bad_path.write_text(json.dumps(mutated))
            tester_dir = root / "tester"
            with self.assertRaisesRegex(GenerationError, "length"):
                generate_slope_tester(bad_path, runtime_dir / "NoraPhase2SlopeRuntimeV1.manifest.json", tester_dir)
            self.assertFalse((tester_dir / TESTER_SOURCE_FILENAME).exists())

    def test_atomic_failure_incorrect_rust_slope_identity(self):
        """Incorrect Rust slope identity fails atomically."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "run"
            runtime_dir, _ = self.make_runtime(root / "runtime")
            evidence = json.loads(EVIDENCE.read_text())
            mutated = dict(evidence)
            mutated["rust_slope_identity"] = "0" * 64
            bad_path = Path(td) / "bad.json"
            bad_path.write_text(json.dumps(mutated))
            tester_dir = root / "tester"
            with self.assertRaisesRegex(GenerationError, "identity|match"):
                generate_slope_tester(bad_path, runtime_dir / "NoraPhase2SlopeRuntimeV1.manifest.json", tester_dir)
            self.assertFalse((tester_dir / TESTER_SOURCE_FILENAME).exists())

    def test_atomic_failure_unsupported_lookback(self):
        """Unsupported lookback fails atomically (covered by test_unsupported_lookback_2_rejected_atomically)."""
        pass

    def test_atomic_failure_preexisting_output_target(self):
        """Pre-existing output target fails atomically on second generation."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "run"
            runtime_dir, _ = self.make_runtime(root / "runtime")
            tester_dir = root / "tester"
            tester_dir.mkdir()  # Create tester dir first

            # First generation succeeds
            generate_slope_tester(EVIDENCE, runtime_dir / "NoraPhase2SlopeRuntimeV1.manifest.json", tester_dir)
            self.assertTrue((tester_dir / TESTER_SOURCE_FILENAME).exists())

            # Second generation to same dir fails
            with self.assertRaisesRegex(GenerationError, "already exist|must not already exist"):
                generate_slope_tester(EVIDENCE, runtime_dir / "NoraPhase2SlopeRuntimeV1.manifest.json", tester_dir)


class Phase2MSlopeIdentityMutationTests(unittest.TestCase):
    """Mutation tests verifying identity sensitivity."""

    def test_input_mutation_changes_tester_identity(self):
        runtime_id = generate_slope_runtime_identity()
        id_base, sha_base, _ = _compute_tester_identity(INPUT_VECTOR, EXPECTED_SLOPE, runtime_id)

        # Mutation 1: Input value change at index 5
        mutated_input = INPUT_VECTOR.copy()
        mutated_input[5] = 1.1014
        mutated_expected = EXPECTED_SLOPE.copy()
        mutated_expected[5] = 0.0004333333333334
        mutated_expected[6] = -0.0000333333333334
        id1, sha1, _ = _compute_tester_identity(mutated_input, mutated_expected, runtime_id)
        self.assertNotEqual(id_base, id1)
        self.assertNotEqual(sha_base, sha1)

        # Mutation 2: Null propagation at index 3
        mutated_input2 = INPUT_VECTOR.copy()
        mutated_input2[3] = None
        mutated_expected2 = EXPECTED_SLOPE.copy()
        mutated_expected2[3] = None
        mutated_expected2[4] = None
        id2, sha2, _ = _compute_tester_identity(mutated_input2, mutated_expected2, runtime_id)
        self.assertNotEqual(id_base, id2)
        self.assertNotEqual(sha_base, sha2)

    def test_lookback_2_is_invalid_not_a_variant(self):
        """Lookback 2 is an invalid-input failure case, not a supported slope variant."""
        # Generator validates lookback == 1, rejects lookback 2 with deterministic error
        # This is tested in Phase2MSlopeGeneratorTests.test_unsupported_lookback_2_rejected_atomically
        pass


if __name__ == "__main__":
    unittest.main()