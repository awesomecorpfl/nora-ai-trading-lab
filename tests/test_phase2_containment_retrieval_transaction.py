import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "phase2-retrieve-containment-evidence.py"
SPEC = importlib.util.spec_from_file_location("retrieval", SCRIPT)
retrieval = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(retrieval)


def test_contract_has_fixed_root_and_binary_subprocess_boundary():
    source = SCRIPT.read_text()
    assert 'DEFAULT_ROOT = Path("/tmp/nora-phase2-containment-retrieval")' in source
    assert 'windows_host_identity' in source
    assert 'stdout=output, stderr=errors' in source
    assert 'os.replace(partial, destination)' in source
    assert 'sha256_mismatch' in source
    assert 'conflicting_destination' in source
    assert 'partial_cleanup' in source


def test_confined_rejects_relative_and_sibling_escape(tmp_path):
    root = tmp_path / "root"; root.mkdir()
    try:
        retrieval.confined(root, Path("relative"))
    except retrieval.RetrievalError as error:
        assert str(error) == "destination_not_absolute"
    else:
        raise AssertionError("relative destination accepted")
    try:
        retrieval.confined(root, tmp_path / "root-sibling" / "x")
    except retrieval.RetrievalError as error:
        assert str(error) == "destination_outside_root"
    else:
        raise AssertionError("sibling destination accepted")


def test_receipt_publication_is_immutable(tmp_path):
    target = tmp_path / "receipt.json"
    retrieval.atomic_json(target, {"v": 1})
    assert json.loads(target.read_text()) == {"v": 1}
    try:
        retrieval.atomic_json(target, {"v": 2})
    except retrieval.RetrievalError as error:
        assert str(error) == "conflicting_receipt"
    else:
        raise AssertionError("receipt overwrite accepted")


def test_sha256_file_handles_all_byte_values(tmp_path):
    payload = bytes(range(256)) + b"\r\n\x00tail"
    path = tmp_path / "payload"; path.write_bytes(payload)
    assert retrieval.sha256_file(path) == hashlib.sha256(payload).hexdigest()
