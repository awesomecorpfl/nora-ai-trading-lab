import hashlib
import unittest

from lab.phase2x_batch import load
from lab.phase2y_return_contract import VERSION, returned_package_identity, validate


class ReturnContract(unittest.TestCase):
    def fixture(self):
        batch = load()
        files = []
        targets = []
        for target in batch['targets']:
            ident = target['id']
            refs = {'compiler': f'{ident}/compiler.log', 'journal': f'{ident}/journal.log', 'report': f'{ident}/report.json', 'result': f'{ident}/{target["result_filename"]}'}
            for key, role in (('compiler', 'compiler_log'), ('journal', 'runtime_journal'), ('report', 'tester_report'), ('result', 'result_csv')):
                contents = (ident + key).encode()
                files.append({'relative_path': refs[key], 'role': role, 'required': True, 'target_binding': ident, 'size': len(contents), 'sha256': hashlib.sha256(contents).hexdigest()})
            vectors = target['expected_vectors']
            numeric = [column for column in vectors['columns'] if column not in ('row', 'close', 'source', 'macd_null', 'signal_null', 'histogram_null', 'source_null', 'percentile_null', 'pass')]
            targets.append({'target_identifier': ident, 'rust_task_identity': target['rust_task_identity'], 'rust_component_identity': target['rust_component_identity'], 'expected_vector_identity': vectors['expected_vector_identity'], 'runtime_identity': target['runtime_identity'], 'tester_identity': target['tester_identity'], 'package_identity': target['package_identity'], 'expected_result_filename': target['result_filename'], 'actual_result_filename': target['result_filename'], 'compiler': {'invoked': True, 'exit_status': 0, 'success': True, 'warnings': [], 'warning_count': 0, 'errors': [], 'error_count': 0, 'log_reference': refs['compiler'], 'expected_ex5_reference': None}, 'runtime': {'invoked': True, 'completion_status': 'completed', 'success': True, 'interrupted': False, 'timeout': False, 'incomplete': False, 'completion_marker_observed': True, 'failure_marker_observed': False, 'journal_reference': refs['journal'], 'report_reference': refs['report'], 'result_csv_reference': refs['result']}, 'csv_schema': {'encoding': 'utf-8', 'delimiter': ',', 'header_required': True, 'columns': vectors['columns'], 'row_identifier_column': 'row', 'numeric_columns': numeric, 'null_representation': 'NULL', 'expected_row_count': vectors['row_count'], 'target_binding': ident}})
        value = {'schema_version': VERSION, 'batch_identity': batch['batch_identity'], 'run_identifier': 'synthetic-protocol-evidence', 'declared_target_count': len(targets), 'targets': targets, 'batch_completion_state': 'completed', 'interrupted': False, 'timeout': False, 'incomplete': False, 'files': files}
        value['returned_package_semantic_identity'] = returned_package_identity(value)
        return value

    def test_valid_two_target_contract(self):
        self.assertTrue(validate(self.fixture())['valid'])

    def test_schema_identity_and_target_set_rejected(self):
        cases = (lambda x: x.update(schema_version='bad'), lambda x: x.update(batch_identity='0'*64), lambda x: x['targets'].append(x['targets'][0]), lambda x: x['targets'].__setitem__(0, {**x['targets'][0], 'target_identifier': 'unknown'}), lambda x: x.update(declared_target_count=1))
        for mutate in cases:
            value = self.fixture(); mutate(value)
            self.assertFalse(validate(value)['valid'])

    def test_compiler_runtime_csv_and_inventory_consistency_rejected(self):
        cases = (
            lambda x: x['targets'][0]['compiler'].update(exit_status=1),
            lambda x: x['targets'][0]['compiler'].update(error_count=1),
            lambda x: x['targets'][0]['compiler'].update(warning_count=1),
            lambda x: x['targets'][0]['runtime'].update(completion_marker_observed=True, failure_marker_observed=True),
            lambda x: x['targets'][0]['csv_schema']['columns'].reverse(),
            lambda x: x['files'].__setitem__(0, {**x['files'][0], 'relative_path': '../escape'}),
            lambda x: x['files'].append(x['files'][0]),
            lambda x: x['files'].__setitem__(0, {**x['files'][0], 'role': 'unknown'}),
            lambda x: x['files'].__setitem__(0, {**x['files'][0], 'target_binding': 'percentile'}),
        )
        for mutate in cases:
            value = self.fixture(); mutate(value)
            self.assertFalse(validate(value)['valid'])
