import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs/evidence/phase2/frt1r3-tester-rule-restoration/20260717T204540Z/packet.json"
SCRIPT = ROOT / "phase-0a-h/windows/phase2-tester-rule-restoration.ps1"


def packet():
    return json.loads(PACKET.read_text())


def test_restoration_packet_is_hash_bound_and_unexecuted():
    value = packet()
    assert value["execution_status"] == "NOT_EXECUTED"
    assert value["tester_rule_contract"]["name"] == "{AE6A1199-33B0-4109-B850-F1BB61AF0F6B}"
    assert value["tester_rule_contract"]["required_enabled_state"] is False
    for mode, command in value["commands"].items():
        assert f"-Mode {mode}" in command
        assert value["repository_commit"] in command
        assert value["helper_sha256"] in command
        assert value["packet_id"] in command
    assert "New-NetFirewallRule" in SCRIPT.read_text()
    assert "Remove-NetFirewallRule -PolicyStore PersistentStore -Name $Guid" in SCRIPT.read_text()
    assert "-DisplayName $DisplayName" not in SCRIPT.read_text().split("Remove-NetFirewallRule", 1)[1]


def test_restoration_script_authenticates_its_deployed_bytes_before_any_mode():
    source = SCRIPT.read_text()
    assert "[Parameter(Mandatory=$true)][string]$RestorationScriptSha256" in source
    assert "(Hash $PSCommandPath)-ne$RestorationScriptSha256" in source
    assert "deployed restoration script hash mismatch" in source
    assert source.index("deployed restoration script hash mismatch") < source.index("if($Mode-eq'preconditions')")


def test_restoration_reopens_complete_after_receipt_and_binds_full_semantics():
    source = SCRIPT.read_text()
    for token in (
        "policy_store_source-ne'PersistentStore'",
        "policy_store_source_type-ne'Local'",
        "Get-NetFirewallAddressFilter",
        "Get-NetFirewallServiceFilter",
        "Get-NetFirewallApplicationFilter",
        "Get-NetFirewallPortFilter",
        "Get-NetFirewallInterfaceFilter",
        "Get-NetFirewallInterfaceTypeFilter",
        "Get-NetFirewallSecurityFilter",
        "before_unrelated_digest",
        "after_unrelated_digest",
        "restoration after receipt identity mismatch",
        "restoration after receipt semantic mismatch",
    ):
        assert token in source
    postflight = source.split("if($Mode-eq'postflight')", 1)[1]
    assert "after.json" in postflight
    assert "ConvertFrom-Json" in postflight
    assert "Canonical $persistent" in postflight
    assert "Canonical $after.persistent" in postflight


def test_restoration_semantics_include_owner_interfaces_and_user_filters():
    text = SCRIPT.read_text()
    semantic = text.split("function SemanticRule", 1)[1].split("function UnrelatedDigest", 1)[0]
    for token in (
        "owner=[string]$R.Owner",
        "interface_alias=[string]$_.InterfaceAlias",
        "local_user=[string]$_.LocalUser",
        "remote_user=[string]$_.RemoteUser",
    ):
        assert token in semantic

    target = text.split("function Rule", 1)[1].split("function Canonical", 1)[0]
    for token in (
        "owner=[string]$r.Owner",
        "group=[string]$r.Group",
        "interface_alias=[string]$ifalias[0].InterfaceAlias",
        "local_user=[string]$sec[0].LocalUser",
        "remote_user=[string]$sec[0].RemoteUser",
        "$V.owner-ne''",
        "$V.group-ne''",
        "$V.interface_alias-ne'Any'",
        "$V.local_user-ne'Any'",
        "$V.remote_user-ne'Any'",
    ):
        assert token in target


def test_restoration_contract_is_exact_and_fail_closed():
    contract = packet()["tester_rule_contract"]
    assert contract["display_name"] == "MetaTrader 5 Strategy Tester Agent"
    assert contract["direction"] == "Inbound"
    assert contract["action"] == "Allow"
    assert contract["profiles"] == "Domain, Private"
    assert contract["protocol"] == "TCP"
    assert contract["program"].endswith("metatester64.exe")
    assert contract["authentication"] == "NotRequired"
    assert contract["encryption"] == "NotRequired"
    assert contract["override_block_rules"] is False
    assert "target GUID already exists" in SCRIPT.read_text()
    assert "target display name conflicts" in SCRIPT.read_text()
    assert "unrelated firewall semantic identity changed" in SCRIPT.read_text()
