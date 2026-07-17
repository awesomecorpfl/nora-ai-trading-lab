#!/usr/bin/env python3
"""Repository-owned end-to-end abandoned multi-operation case orchestration."""
from __future__ import annotations

import argparse, base64, hashlib, json, re, shlex, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

from lab.phase2_case_envelope import sha256 as file_hash, verify as verify_envelope
from lab.phase2_containment_evidence import verify as verify_operation

SEQUENCE = (
    ("classification", "classification", 0, "runner-operation", "abandon-fixture", None),
    ("same-before", "reuse_attempt", 1, "stage", None, r"C:\Windows\System32\notepad.exe"),
    ("changed-before", "reuse_attempt", 1, "stage", None, r"C:\Windows\System32\cmd.exe"),
    ("cleanup", "cleanup", 0, "runner-operation", "abandon-fixture-cleanup", None),
    ("same-after", "reuse_attempt", 1, "stage", None, r"C:\Windows\System32\notepad.exe"),
    ("changed-after", "reuse_attempt", 1, "stage", None, r"C:\Windows\System32\cmd.exe"),
)


def run(command, *, stdout=None, stderr=None, check=True, env=None):
    result=subprocess.run(command,stdout=stdout or subprocess.PIPE,stderr=stderr or subprocess.PIPE,check=False,env=env)
    if check and result.returncode: raise RuntimeError(f"command failed {result.returncode}: {command!r}")
    return result


def utc(): return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")


def encoded_powershell(script: str) -> list[str]:
    encoded=base64.b64encode(script.encode("utf-16le")).decode("ascii")
    return ["powershell.exe","-NoProfile","-NonInteractive","-EncodedCommand",encoded]


def main(argv=None):
    p=argparse.ArgumentParser();
    for name in ("case-id","repository-commit","ssh-config","ssh-alias","runner-path","runner-sha256","containment-path","containment-sha256","publisher-path","publisher-sha256","reader-path","reader-sha256","verifier-sha256","retrieval-wrapper-sha256","native-execution-identity","case-builder-path","case-builder-sha256","firewall-capture-path","firewall-capture-sha256","deployment-helper"):
        p.add_argument("--"+name,required=True)
    p.add_argument("--output-root",type=Path,required=True);a=p.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{2,127}",a.case_id) or not re.fullmatch(r"[0-9a-f]{40}",a.repository_commit): raise SystemExit("invalid case identity")
    root=a.output_root.resolve();root.mkdir(parents=True,exist_ok=False)
    ssh=["ssh","-F",a.ssh_config,"-n","-o","BatchMode=yes",a.ssh_alias]
    helper=Path(__file__).with_name("phase2-exit-propagation-batch")
    retrieval=Path(__file__).with_name("phase2-retrieve-containment-evidence.py")
    operations=[];operation_ids=[]
    for index,(label,op_type,expected,action,runner_mode,exe) in enumerate(SEQUENCE):
        op_id=f"{a.case_id}-{label}";operation_ids.append(op_id)
        windows_package=rf"C:\NoraEvidence\Phase2\case-operations\{a.case_id}\{op_id}.zip"
        remote=ssh+["powershell.exe","-NoProfile","-NonInteractive","-ExecutionPolicy","Bypass","-File",a.runner_path,
                    "-Mode","capture-containment-command","-RunId",a.case_id,"-ContainmentAction",action,
                    "-ContainmentToolPath",a.containment_path,"-ContainmentToolSha256",a.containment_sha256,
                    "-ContainmentCaseId",op_id,"-ContainmentExpectedVerdict","PASS","-RepositoryCommit",a.repository_commit,
                    "-ContainmentDestinationPath",windows_package,"-PublisherPath",a.publisher_path,"-PublisherSha256",a.publisher_sha256,
                    "-FirewallCaptureToolPath",a.firewall_capture_path,"-FirewallCaptureToolSha256",a.firewall_capture_sha256]
        if runner_mode: remote += ["-RunnerOperationMode",runner_mode]
        if exe: remote += ["-ContainmentExecutablePath",exe]
        out=root/f"{op_id}.helper.stdout";err=root/f"{op_id}.helper.stderr"
        spec=f"{expected}:{shlex.join(remote)}"
        with out.open("wb") as so,err.open("wb") as se: helper_result=run([str(helper),spec],stdout=so,stderr=se,check=False)
        if helper_result.returncode: raise RuntimeError(f"operation helper verdict failed: {op_id}")
        match=re.search(rb"CASE=1 EXIT=(\d+) EXPECTED=(\d+)",out.read_bytes())
        if not match or int(match.group(1))!=expected or int(match.group(2))!=expected: raise RuntimeError(f"operation exit capture mismatch: {op_id}")
        meta_script=f"$p='{windows_package}';[ordered]@{{size=(Get-Item -LiteralPath $p).Length;sha256=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}}|ConvertTo-Json -Compress"
        meta=run(ssh+encoded_powershell(meta_script))
        package_meta=json.loads(next(line for line in meta.stdout.decode().splitlines() if line.startswith("{")));local_package=root/f"{op_id}.zip";receipt_id=f"{a.case_id}-{op_id}"
        receipt_root=Path("/tmp/nora-phase2-containment-retrieval");receipt=receipt_root/"receipts"/(receipt_id+".json")
        retrieve=[sys.executable,str(retrieval),"--ssh-config",a.ssh_config,"--ssh-alias",a.ssh_alias,
                  "--windows-host-identity","DESKTOP-21I1FJP","--reader-path",a.reader_path,"--reader-sha256",a.reader_sha256,
                  "--deployed-reader-sha256",a.reader_sha256,"--windows-source",windows_package,"--expected-size",str(package_meta["size"]),
                  "--expected-sha256",package_meta["sha256"],"--destination",str(receipt_root/"cases"/a.case_id/(op_id+".zip")),
                  "--repository-commit",a.repository_commit,"--receipt-id",receipt_id]
        rr=run(retrieve,check=False)
        if rr.returncode: raise RuntimeError(f"retrieval failed: {op_id}: {rr.stderr.decode(errors='replace')}")
        receipt_value=json.loads(receipt.read_bytes());local_package=Path(receipt_value["fedora_destination"])
        verified=verify_operation(local_package,package_meta["sha256"])
        operations.append({"operation_id":op_id,"operation_type":op_type,"package_path":str(local_package),"windows_path":windows_package,
            "package_size":package_meta["size"],"package_sha256":package_meta["sha256"],"original_child_exit":expected,"helper_exit":0,
            "expected_exit":expected,"operation_verdict":"PASS","predecessor_operation_id":None if index==0 else operation_ids[index-1],
            "causal_relationship":"ordered_after_predecessor","cleanup_recovery_relationship":"cleanup_boundary" if op_type=="cleanup" else ("after_cleanup:cleanup" if index>3 else None),
            "retrieval":{"receipt_path":str(receipt),"receipt_sha256":file_hash(receipt),"fedora_package_sha256":verified["package_sha256"],"verification_result":"PASS"}})
    plan={"case_id":a.case_id,"case_type":"abandoned_reuse","repository_commit":a.repository_commit,
          "identities":{"native_execution":a.native_execution_identity,"runner":a.runner_sha256,"containment":a.containment_sha256,
                        "publisher":a.publisher_sha256,"verifier":a.verifier_sha256,"retrieval_wrapper":a.retrieval_wrapper_sha256},
          "declared_sequence":operation_ids,"operations":operations,
          "case_invariants":{"classification":"ABANDONED_PRE_LAUNCH_NO_CONTAINMENT","non_reusable":True,"final_nora_rules":0},"published_utc":utc()}
    plan_path=root/"case-plan.json";plan_path.write_text(json.dumps(plan,sort_keys=True,separators=(",",":"))+"\n")
    windows_plan=rf"C:\NoraEvidence\Phase2\case-plans\{a.case_id}.json";plan_hash=file_hash(plan_path)
    env=dict(**__import__('os').environ,NORA_SSH_CONFIG=a.ssh_config)
    deployment_stdout=root/"case-plan-deployment.stdout";deployment_stderr=root/"case-plan-deployment.stderr"
    with deployment_stdout.open("wb") as so,deployment_stderr.open("wb") as se:
        deployed=run([a.deployment_helper,str(plan_path),windows_plan,plan_hash],check=False,stdout=so,stderr=se,env=env)
    if deployed.returncode: raise RuntimeError("case plan deployment failed")
    windows_envelope=rf"C:\NoraEvidence\Phase2\case-envelopes\{a.case_id}.json"
    builder_stdout=root/"case-envelope-builder.stdout";builder_stderr=root/"case-envelope-builder.stderr"
    with builder_stdout.open("wb") as so,builder_stderr.open("wb") as se:
        build=run(ssh+["powershell.exe","-NoProfile","-NonInteractive","-ExecutionPolicy","Bypass","-File",a.case_builder_path,
                       "-Mode","publish","-PlanPath",windows_plan,"-EnvelopePath",windows_envelope,"-EvidenceRoot",r"C:\NoraEvidence\Phase2","-ExpectedCaseId",a.case_id],stdout=so,stderr=se,check=False)
    if build.returncode: raise RuntimeError("case envelope build failed")
    built=json.loads(next(line for line in builder_stdout.read_text().splitlines() if line.startswith("{")));envelope_receipt_id=f"{a.case_id}-envelope";receipt_root=Path("/tmp/nora-phase2-containment-retrieval")
    envelope_local=receipt_root/"cases"/a.case_id/"case-envelope.json"
    retrieve=run([sys.executable,str(retrieval),"--ssh-config",a.ssh_config,"--ssh-alias",a.ssh_alias,"--windows-host-identity","DESKTOP-21I1FJP",
        "--reader-path",a.reader_path,"--reader-sha256",a.reader_sha256,"--deployed-reader-sha256",a.reader_sha256,"--windows-source",windows_envelope,
        "--expected-size",str(built["size"]),"--expected-sha256",built["sha256"],"--destination",str(envelope_local),
        "--repository-commit",a.repository_commit,"--receipt-id",envelope_receipt_id])
    result=verify_envelope(envelope_local,built["sha256"]);(root/"case-result.json").write_text(json.dumps(result,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True));return 0

if __name__=="__main__": raise SystemExit(main())
