"""Local evidence builders for the first Layer-1 parity batch."""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from lab.phase2_execution import sha
from lab.numeric_parity import failure_vocabulary, protocol
from lab.phase2_layer1_inventory import batch_plan, dependency_map, matrix

ROOT=Path(__file__).resolve().parents[1]
SCENARIOS=ROOT/"tests/fixtures/phase2_layer1_first_batch_scenarios.json"
ENGINE=ROOT/"engine/target/debug/labengine"
CSV_SCHEMA=["scenario_id","node","output","row","timestamp","value","null","classification","reason_code"]


def load_scenarios(): return json.loads(SCENARIOS.read_text())


def rust_evidence(engine:Path=ENGINE)->dict:
    source=load_scenarios();task={"task_version":1,"task_type":"layer1_parity_v1","scenarios":source["scenarios"]}
    with tempfile.TemporaryDirectory() as directory:
        path=Path(directory)/"task.json";path.write_text(json.dumps(task,separators=(",",":")))
        run=subprocess.run([str(engine),str(path)],check=True,capture_output=True,text=True)
    output=json.loads(run.stdout)
    node_matrix=matrix();ids={x["canonical_id"]:x["canonical_identity"] for x in node_matrix["nodes"] if x["first_batch"]}
    value={"schema_version":"nora.layer1_rust_evidence_v1","task":task,"task_identity":sha(task),
           "scenario_identities":{x["id"]:sha(x) for x in source["scenarios"]},
           "rust_output":output,"rust_task_output_identity":sha(output),"expected_vector_identity":sha(output["rows"]),
           "output_schema":CSV_SCHEMA,"output_schema_identity":sha(CSV_SCHEMA),"selected_node_identities":ids,
           "timestamp_preserved":True,"grammar_admitted":False,"searchable":False}
    value["rust_evidence_identity"]=sha(value);return value


def contracts(engine:Path=ENGINE)->dict:
    m=matrix();ids={x["canonical_id"]:x["canonical_identity"] for x in m["nodes"] if x["first_batch"]}
    value={"matrix":m,"dependencies":dependency_map(),"batch_plan":batch_plan(ids),
           "numeric_protocol":protocol(),"failure_vocabulary":failure_vocabulary(),"rust_evidence":rust_evidence(engine)}
    value["contract_bundle_identity"]=sha(value);return value


def freeze(destination:Path, engine:Path=ENGINE)->dict:
    from lab.mql5gen.layer1_batch import generate
    destination=Path(destination)
    if destination.exists(): raise ValueError("occupied freeze destination")
    destination.mkdir()
    value=contracts(engine)
    for name,key in (("authoritative_matrix.json","matrix"),("dependency_map.json","dependencies"),
                     ("batch_plan.json","batch_plan"),("numeric_protocol.json","numeric_protocol"),
                     ("failure_vocabulary.json","failure_vocabulary"),("rust_evidence.json","rust_evidence")):
        (destination/name).write_text(json.dumps(value[key],sort_keys=True,separators=(",",":"))+"\n")
    generated=destination/"generated";generated.mkdir()
    package=generate(generated,value["rust_evidence"],value["batch_plan"],value["numeric_protocol"])
    result={"contract_bundle_identity":value["contract_bundle_identity"],"matrix_identity":value["matrix"]["matrix_identity"],
            "dependency_map_identity":value["dependencies"]["dependency_map_identity"],"batch_plan_identity":value["batch_plan"]["batch_plan_identity"],
            "parity_protocol_identity":value["numeric_protocol"]["parity_protocol_identity"],"rust_evidence_identity":value["rust_evidence"]["rust_evidence_identity"],
            "package_identity":package["package_identity"]}
    (destination/"freeze_manifest.json").write_text(json.dumps(result,sort_keys=True,separators=(",",":"))+"\n")
    return result
