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
