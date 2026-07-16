import copy,json
from pathlib import Path
import pytest
from lab.phase2_firewall_preservation import FirewallError,compare,digest,evaluate,normalize,SCHEMA

def rule(**kw):
 d={"view":"effective","name":"safe","instance_id":"id1","group":"system","enabled":True,"direction":"inbound","action":"allow","profile":"any","policy_store":"activestore","policy_store_source_type":"local","policy_store_source":"local","edge_traversal":"none","interface_types":[],"owner":None,"programs":[],"services":[],"protocols":["tcp"],"local_ports":["22"],"remote_ports":[],"icmp_types":[],"local_addresses":[],"remote_addresses":[],"interfaces":[],"security":[],"packages":[],"local_users":[],"remote_users":[]};d.update(kw);return d
def inv():
 ps=[{"name":n,"enabled":True,"default_inbound":"block","default_outbound":"allow","allow_local_firewall_rules":"true","allow_local_ipsec_rules":"true","notify_on_listen":"false","policy_store_source":"local"} for n in ("Domain","Private","Public")]
 return {"schema_version":SCHEMA,"host_identity":"host","repository_commit":"a"*40,"captured_utc":"now","profiles":ps,"effective_rules":[rule()],"persistent_rules":[],"diagnostics":{}}

def test_canonical_order_key_and_filter_order_are_stable():
 a=inv();b=copy.deepcopy(a);b["profiles"].reverse();b["effective_rules"][0]["protocols"]=["udp","tcp","tcp"]
 a["effective_rules"][0]["protocols"]=["tcp","udp"]
 assert digest(normalize(a))==digest(normalize(b))
def test_null_empty_and_path_normalization():
 a=inv();b=copy.deepcopy(a);a["effective_rules"][0]["programs"]=["C:/X//terminal.exe"];b["effective_rules"][0]["programs"]=["c:\\x\\terminal.exe"]
 assert normalize(a)==normalize(b)
@pytest.mark.parametrize("field",["enabled","direction","action","profile","programs","services","protocols","local_ports","remote_ports","local_addresses","remote_addresses","policy_store","policy_store_source_type","edge_traversal","packages"])
def test_semantic_changes_fail_case_equality(field):
 a=inv();b=copy.deepcopy(a);r=b["effective_rules"][0];r[field]=False if field=="enabled" else (["changed"] if isinstance(r[field],list) else "changed")
 assert compare(a,b)["verdict"]=="FAIL"
def test_added_removed_and_profile_changes_fail():
 a=inv();b=copy.deepcopy(a);b["effective_rules"].append(rule(name="two",instance_id="id2"));assert compare(a,b)["verdict"]=="FAIL"
 b=copy.deepcopy(a);b["profiles"][0]["default_inbound"]="allow";assert compare(a,b)["verdict"]=="FAIL"
@pytest.mark.parametrize("program",[r"C:\\Program Files\\Darwinex MetaTrader 5\\terminal64.exe",r"C:\\x\\metatester64.exe"])
def test_unsafe_terminal_allows_fail(program):
 a=inv();a["effective_rules"][0]["programs"]=[program];assert evaluate(a)["verdict"]=="FAIL"
def test_safe_unrelated_allow_passes():assert evaluate(inv())["verdict"]=="PASS"
def test_stale_or_foreign_nora_identity_fails():
 a=inv();a["effective_rules"][0]["name"]="NoraPhase2Containment-foreign-1";assert evaluate(a)["verdict"]=="FAIL"
def test_profile_disabled_fails():
 a=inv();a["profiles"][0]["enabled"]=False;assert evaluate(a)["verdict"]=="FAIL"
def test_duplicate_identity_and_malformed_fail():
 a=inv();a["effective_rules"].append(copy.deepcopy(a["effective_rules"][0]));
 with pytest.raises(FirewallError,match="duplicate"):normalize(a)
 a=inv();a["schema_version"]="old"
 with pytest.raises(FirewallError,match="unsupported"):normalize(a)
def test_historical_drift_is_diagnostic_when_current_safe():
 r=evaluate(inv());assert r["verdict"]=="PASS" and r["legacy_digest"]
def test_windows_capture_is_read_only_and_dual_store():
 s=(Path(__file__).parents[1]/"phase-0a-h/windows/capture-phase2-firewall-inventory.ps1").read_text()
 for x in ("ActiveStore","PersistentStore","Get-NetFirewallApplicationFilter","Get-NetFirewallSecurityFilter","mutation_cmdlets_invoked=$false"):assert x in s
 assert "New-NetFirewallRule" not in s and "Remove-NetFirewallRule" not in s and "Set-NetFirewall" not in s
def test_exact_remediation_is_guid_store_and_executable_bound():
 s=(Path(__file__).parents[1]/"phase-0a-h/windows/disable-phase2-exact-firewall-rule.ps1").read_text()
 for x in ("{AE6A1199-33B0-4109-B850-F1BB61AF0F6B}","-PolicyStore PersistentStore","-Name $authorized","-Enabled False","only_enabled_changed=$true","rule_still_exists=$true","remote_address-ne'Any'","interface_type-ne'Any'"):assert x in s
 assert "Remove-NetFirewallRule" not in s and "DisplayName" not in s.split("Set-NetFirewallRule",1)[1]
def test_disabled_exact_rule_is_not_an_unsafe_enabled_allow():
 a=inv();a["effective_rules"][0].update(programs=[r"C:\Program Files\Darwinex MetaTrader 5\metatester64.exe"],enabled=False)
 assert evaluate(a)["verdict"]=="PASS"
