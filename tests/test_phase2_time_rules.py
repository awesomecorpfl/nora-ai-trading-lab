import copy,json
from pathlib import Path
from lab.phase2_time_rules import evidence,task,plan_identity
from lab.phase2_time_contracts import identity
ROOT=Path(__file__).resolve().parents[1]
def test_time_rules_run_real_rust_boundary_and_cover_frozen_clock_edges():
 e=evidence(ROOT/'engine/target/debug/labengine'); assert len(e['expected_vectors'])==18
 rows={x['scenario_id']:x for x in e['expected_vectors']}
 assert rows['winter_utc']['utc_offset_seconds']==7200
 assert rows['summer_utc']['utc_offset_seconds']==10800
 assert rows['spring_before']['utc_offset_seconds']==7200
 assert rows['spring_after']['utc_offset_seconds']==10800
 assert rows['spring_before']['source_epoch'] < rows['spring_after']['source_epoch']
 assert rows['fall_first_hour']['broker']==rows['fall_second_hour']['broker']
 assert rows['fall_first_hour']['source_epoch']!=rows['fall_second_hour']['source_epoch']
 assert rows['friday_pre']['friday_close'] is False
 assert rows['friday_exact']['friday_close'] is True
 assert rows['friday_post']['friday_close'] is True
 assert rows['friday_winter']['friday_close'] is True
 assert rows['rollover_before']['rollover'] is False
 assert rows['rollover_start']['rollover'] is True
 assert rows['rollover_end']['rollover'] is False
 assert rows['monday_delay']['monday_delay'] is True
 assert rows['monday_permitted']['monday_delay'] is False
 assert rows['orb_open']['orb'] is True
 assert rows['orb_end']['orb'] is False
 assert rows['already_converted_rejected']['reason_code']=='conversion_rejected'
 assert rows['already_converted_rejected']['session_member'] is False

def test_time_rule_plan_identity_mutates_for_all_decision_inputs():
 baseline=task()
 mutations=[
  (('rules','friday_close'),'16:26'), (('rules','session','start'),'09:31'),
  (('rules','rollover','end'),'00:11'), (('rules','monday_delay','end'),'00:16'),
  (('rules','orb','end'),'10:01'), (('scenarios',0,'epoch'),1736942401),
  (('scenarios',0,'source_clock'),'broker'), (('scenarios',0,'conversion_state'),'already_converted'),
  (('contract_identities','dst'),'changed'), (('contract_identities','anchoring'),'changed'),
 ]
 for path,value in mutations:
  changed=copy.deepcopy(baseline); node=changed
  for key in path[:-1]: node=node[key]
  node[path[-1]]=value
  assert identity(changed)!=identity(baseline)
 assert plan_identity()==evidence(ROOT/'engine/target/debug/labengine')['time_rule_plan_identity']
