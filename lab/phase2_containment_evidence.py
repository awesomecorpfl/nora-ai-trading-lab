"""Atomic, deterministic evidence packages for Phase-2 containment cases.

This module is deliberately independent of firewall mutation.  It packages
already-captured, read-only artifacts and verifies them from bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any

SCHEMA = "nora.phase2_containment_atomic_evidence_v1"
REQUIRED_METADATA = {
    "case_id", "expected_verdict", "run_id", "repository_commit",
    "script_hashes", "windows_hashes", "host_identity", "evidence_root",
    "transaction_identity", "executable_paths", "executable_hashes",
    "fault_injection_point", "started_at", "finished_at", "command",
    "wrapper_identity", "final_caller_exit_code", "recovery_result",
    "cleanup_result", "unrelated_firewall_result", "final_invariants",
}
REQUIRED_MEMBERS = (
    "stdout.txt", "stderr.txt", "pre_state.json", "post_state.json",
    "firewall_pre.json", "firewall_post.json", "processes.json",
    "recovery.json", "cleanup.json",
)
ARRAY_FIELDS = {
    "executable_paths", "executable_hashes", "rule_guids", "rule_names",
    "application_filters",
}


class EvidenceError(ValueError):
    pass


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_member(path: Path, root: Path) -> str:
    if path.is_symlink():
        raise EvidenceError(f"symlink member: {path}")
    relative = path.relative_to(root).as_posix()
    if not relative or relative.startswith("/") or ".." in Path(relative).parts:
        raise EvidenceError(f"unsafe member path: {relative}")
    return relative


def _metadata(value: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(REQUIRED_METADATA - value.keys())
    if missing:
        raise EvidenceError("missing metadata: " + ",".join(missing))
    if not isinstance(value.get("run_id"), str) or not value["run_id"]:
        raise EvidenceError("invalid run_id")
    if not isinstance(value.get("repository_commit"), str) or len(value["repository_commit"]) != 40:
        raise EvidenceError("invalid repository_commit")
    for field in ARRAY_FIELDS:
        if not isinstance(value.get(field), list):
            raise EvidenceError(f"{field} must be an array")
    if not isinstance(value["final_caller_exit_code"], int):
        raise EvidenceError("final_caller_exit_code must be an integer")
    return value


def _members(source: Path) -> list[tuple[str, int, str]]:
    found: list[tuple[str, int, str]] = []
    for path in sorted(source.rglob("*")):
        if path.is_dir():
            continue
        name = _safe_member(path, source)
        if name in {"manifest.json", "summary.json"}:
            continue
        found.append((name, path.stat().st_size, sha256(path)))
    names = {item[0] for item in found}
    missing = [name for name in REQUIRED_MEMBERS if name not in names]
    if missing:
        raise EvidenceError("missing members: " + ",".join(missing))
    return found


def _write_zip(destination: Path, source: Path, summary: dict[str, Any], members: list[tuple[str, int, str]]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=destination.name + ".partial.", dir=destination.parent)
    os.close(fd)
    temporary_path = Path(temporary)
    try:
        manifest = {
            "schema": SCHEMA, "run_id": summary["run_id"],
            "case_id": summary["case_id"], "repository_commit": summary["repository_commit"],
            "members": [{"path": n, "size": s, "sha256": h} for n, s, h in members],
        }
        with zipfile.ZipFile(temporary_path, "w", compression=zipfile.ZIP_STORED) as archive:
            for name, data in (("summary.json", _canonical(summary)), ("manifest.json", _canonical(manifest))):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0)); info.external_attr = 0o600 << 16
                archive.writestr(info, data)
            for name, _, _ in members:
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0)); info.external_attr = 0o600 << 16
                archive.writestr(info, (source / Path(name)).read_bytes())
        with temporary_path.open("rb") as stream:
            os.fsync(stream.fileno())
        if destination.exists():
            if sha256(destination) != sha256(temporary_path):
                raise EvidenceError("conflicting duplicate publication")
            return
        os.replace(temporary_path, destination)
        dir_fd = os.open(destination.parent, os.O_RDONLY)
        try: os.fsync(dir_fd)
        finally: os.close(dir_fd)
    finally:
        temporary_path.unlink(missing_ok=True)


def publish(source: Path, destination: Path, summary: dict[str, Any]) -> str:
    if not source.is_dir():
        raise EvidenceError("source is not a directory")
    summary = dict(summary); summary["schema"] = SCHEMA
    summary = _metadata(summary); members = _members(source)
    _write_zip(destination, source, summary, members)
    return sha256(destination)


def verify(package: Path, expected_sha256: str | None = None) -> dict[str, Any]:
    if not package.is_file():
        raise EvidenceError("package is missing")
    actual = sha256(package)
    if expected_sha256 is not None and actual != expected_sha256.lower():
        raise EvidenceError("package hash mismatch")
    with zipfile.ZipFile(package) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or any(name.startswith("/") or ".." in Path(name).parts for name in names):
            raise EvidenceError("unsafe or duplicate archive member")
        try:
            summary = json.loads(archive.read("summary.json"))
            manifest = json.loads(archive.read("manifest.json"))
        except (KeyError, json.JSONDecodeError) as exc:
            raise EvidenceError("invalid package JSON") from exc
        if summary.get("schema") != SCHEMA or manifest.get("schema") != SCHEMA or summary.get("run_id") != manifest.get("run_id"):
            raise EvidenceError("schema or identity mismatch")
        listed = {item["path"]: item for item in manifest.get("members", [])}
        if set(listed) != set(names) - {"summary.json", "manifest.json"}:
            raise EvidenceError("manifest member set mismatch")
        for name, item in listed.items():
            data = archive.read(name)
            if len(data) != item.get("size") or hashlib.sha256(data).hexdigest() != item.get("sha256"):
                raise EvidenceError(f"member hash mismatch: {name}")
        _metadata(summary)
    return {"schema": SCHEMA, "run_id": summary["run_id"], "package_sha256": actual, "member_count": len(listed)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="phase2-containment-evidence")
    sub = parser.add_subparsers(dest="action", required=True)
    package_parser = sub.add_parser("package"); package_parser.add_argument("--source", type=Path, required=True); package_parser.add_argument("--summary", type=Path, required=True); package_parser.add_argument("--destination", type=Path, required=True)
    verify_parser = sub.add_parser("verify"); verify_parser.add_argument("--package", type=Path, required=True); verify_parser.add_argument("--sha256")
    args = parser.parse_args(argv)
    try:
        if args.action == "package":
            print(publish(args.source, args.destination, json.loads(args.summary.read_bytes())))
        else:
            print(json.dumps(verify(args.package, args.sha256), sort_keys=True))
        return 0
    except (EvidenceError, OSError, json.JSONDecodeError) as exc:
        print(f"evidence-error: {exc}", file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
