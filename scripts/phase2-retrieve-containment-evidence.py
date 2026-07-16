#!/usr/bin/env python3
"""Atomically retrieve a Phase 2 containment package through the Windows reader.

The Windows reader is the only component allowed to read package bytes from the
authoritative Windows evidence root.  This program owns the Fedora-side
transaction: path confinement, partial-file verification, atomic publication,
and immutable receipts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "nora.phase2_containment_retrieval_receipt_v1"
DEFAULT_ROOT = Path("/tmp/nora-phase2-containment-retrieval")
WINDOWS_ROOT = r"C:\NoraEvidence\Phase2"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
IDENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")


class RetrievalError(Exception):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def confined(root: Path, candidate: Path, *, leaf: bool = False) -> Path:
    if not candidate.is_absolute():
        raise RetrievalError("destination_not_absolute")
    root_real = root.resolve(strict=False)
    target = candidate.resolve(strict=False)
    try:
        target.relative_to(root_real)
    except ValueError as exc:
        raise RetrievalError("destination_outside_root") from exc
    parent = target.parent
    if parent.exists() and parent.is_symlink():
        raise RetrievalError("destination_parent_symlink")
    if leaf and target.exists() and target.is_dir():
        raise RetrievalError("destination_is_directory")
    return target


def atomic_json(path: Path, value: dict) -> None:
    if path.exists():
        raise RetrievalError("conflicting_receipt")
    payload = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".partial.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        # O_EXCL semantics are required for immutable receipt publication.
        os.link(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ssh-config", required=True, type=Path)
    parser.add_argument("--ssh-alias", required=True)
    parser.add_argument("--windows-host-identity", required=True)
    parser.add_argument("--reader-path", required=True)
    parser.add_argument("--reader-sha256", required=True)
    parser.add_argument("--deployed-reader-sha256", required=True)
    parser.add_argument("--windows-source", required=True)
    parser.add_argument("--expected-size", required=True, type=int)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--destination-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--repository-commit", required=True)
    parser.add_argument("--receipt-id", required=True)
    args = parser.parse_args(argv)
    started = utc_now()
    if args.expected_size < 0 or not HEX64.fullmatch(args.expected_sha256):
        raise SystemExit("invalid expected package identity")
    if not HEX64.fullmatch(args.reader_sha256) or not HEX64.fullmatch(args.deployed_reader_sha256):
        raise SystemExit("invalid reader hash")
    if (not re.fullmatch(r"[0-9a-f]{40}", args.repository_commit) or not IDENT.fullmatch(args.receipt_id)
            or any(ch in args.windows_host_identity for ch in "\x00\r\n")):
        raise SystemExit("invalid receipt identity")
    if not args.windows_source.startswith(WINDOWS_ROOT + "\\") or any(x in args.windows_source for x in ("..", "\x00")):
        raise SystemExit("invalid Windows source")
    root = args.destination_root.resolve(strict=False)
    if root != DEFAULT_ROOT:
        raise SystemExit("destination root is not the canonical Fedora retrieval root")
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    destination = confined(root, args.destination, leaf=True)
    receipts = root / "receipts"; receipts.mkdir(mode=0o700, exist_ok=True)
    stderr_path = receipts / (args.receipt_id + ".ssh-stderr")
    success_receipt = receipts / (args.receipt_id + ".json")
    failure_receipt = receipts / (args.receipt_id + ".failure.json")
    if success_receipt.exists() or failure_receipt.exists() or stderr_path.exists():
        raise SystemExit("conflicting retrieval receipt artifacts")
    partial = destination.with_name(destination.name + ".partial." + args.receipt_id)
    if partial.exists():
        raise SystemExit("stale partial destination")
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if destination.parent.resolve(strict=True) != destination.parent:
        raise SystemExit("destination parent symlink")
    result: dict = {"schema_version": SCHEMA, "receipt_id": args.receipt_id,
                    "repository_commit": args.repository_commit, "windows_host_identity": args.windows_host_identity,
                    "ssh_route": {"alias": args.ssh_alias, "config": str(args.ssh_config)},
                    "windows_reader": {"path": args.reader_path, "committed_sha256": args.reader_sha256, "deployed_sha256": args.deployed_reader_sha256},
                    "windows_source": args.windows_source, "expected": {"size": args.expected_size, "sha256": args.expected_sha256},
                    "fedora_destination_root": str(root), "fedora_destination": str(destination), "started_utc": started}
    stage = "reader"
    try:
        command = ["ssh", "-F", str(args.ssh_config), "-n", "-o", "BatchMode=yes", args.ssh_alias,
                   "powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", args.reader_path,
                   "-LiteralPath", args.windows_source]
        with partial.open("xb") as output, stderr_path.open("xb") as errors:
            completed = subprocess.run(command, stdout=output, stderr=errors, check=False)
            output.flush(); os.fsync(output.fileno())
        result["reader_ssh_exit_code"] = completed.returncode
        result["stderr"] = {"path": str(stderr_path), "size": stderr_path.stat().st_size, "sha256": sha256_file(stderr_path)}
        if completed.returncode != 0:
            raise RetrievalError("reader_or_ssh_nonzero")
        stage = "verify"
        observed_size = partial.stat().st_size; observed_hash = sha256_file(partial)
        result["partial"] = {"path": str(partial), "size": observed_size, "sha256": observed_hash}
        if observed_size != args.expected_size:
            raise RetrievalError("size_mismatch")
        if observed_hash != args.expected_sha256:
            raise RetrievalError("sha256_mismatch")
        stage = "publish"
        if destination.exists():
            if destination.is_dir():
                raise RetrievalError("destination_is_directory")
            if destination.stat().st_size != observed_size or sha256_file(destination) != observed_hash:
                raise RetrievalError("conflicting_destination")
            partial.unlink(); result["publication_result"] = "identical_existing"
        else:
            os.replace(partial, destination); result["publication_result"] = "published"
        result["final"] = {"path": str(destination), "size": destination.stat().st_size, "sha256": sha256_file(destination)}
        if result["final"]["size"] != args.expected_size or result["final"]["sha256"] != args.expected_sha256:
            raise RetrievalError("final_verification_mismatch")
        result.update({"wrapper_exit_code": 0, "finished_utc": utc_now(), "failure_stage": None, "failure_reason": None, "partial_cleanup": "not_needed"})
        atomic_json(success_receipt, result)
        return 0
    except Exception as exc:
        cleanup = "not_needed"
        if partial.exists():
            try:
                partial.unlink(); cleanup = "removed"
            except OSError:
                cleanup = "failed"
        result.update({"wrapper_exit_code": 1, "finished_utc": utc_now(), "failure_stage": stage, "failure_reason": str(exc), "partial_cleanup": cleanup, "publication_result": "failed"})
        if stderr_path.exists():
            result["stderr"] = {"path": str(stderr_path), "size": stderr_path.stat().st_size, "sha256": sha256_file(stderr_path)}
        try:
            atomic_json(failure_receipt, result)
        except Exception:
            pass
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
