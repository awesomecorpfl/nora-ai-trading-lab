"""Filesystem-backed synthetic protocol evidence matrix; no native execution."""
import csv
import os
import tempfile
import unittest
from pathlib import Path

from lab.phase2y_ingest import MANIFEST_NAME, ingest
from lab.phase2y_reconcile import publish, reconcile
from tests._phase2y_package import build, rewrite


def _csv(root, manifest, target=0):
    return root / manifest['targets'][target]['runtime']['result_csv_reference']


def _row_id(root, manifest, value):
    path = _csv(root, manifest); lines = path.read_text().splitlines(); parts = lines[4].split(','); parts[0] = str(value); lines[4] = ','.join(parts); path.write_text('\n'.join(lines) + '\n')


class FilesystemProtocolMatrix(unittest.TestCase):
    def assert_fixture(self, name, mutate, expected, rehash=True):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); build(root)
            rewrite(root, mutate, rehash)
            before = {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            result = reconcile(root)
            self.assertEqual(result['classification'], expected, name)
            # Reconciliation is read-only: the mutation fixture remains byte-identical.
            after = {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            self.assertEqual(after, before)
            self.assertFalse(result.get('native_parity_updated'))
            return result

    def test_valid_and_execution_synthetic_protocol_evidence(self):
        scenarios = {
            'exact MACD': (lambda m, r: None, 'PASS_EXACT'), 'exact percentile': (lambda m, r: None, 'PASS_EXACT'), 'exact two-target batch': (lambda m, r: None, 'PASS_EXACT'),
            'MACD within tolerance': (lambda m, r: _csv(r, m).write_bytes(_csv(r, m).read_bytes().replace(b'0.00029166666666657903', b'0.00029166666676657903', 1)), 'PASS_WITHIN_TOLERANCE'),
            'percentile within tolerance': (lambda m, r: _csv(r, m, 1).write_bytes(_csv(r, m, 1).read_bytes().replace(b'1.0', b'1.0000000000001', 1)), 'PASS_WITHIN_TOLERANCE'),
            'compiler failure': (lambda m, r: m['targets'][0]['compiler'].update(success=False, exit_status=1), 'FAIL_COMPILE'),
            'runtime failure': (lambda m, r: m['targets'][0]['runtime'].update(success=False), 'FAIL_RUNTIME'),
            'interrupted run': (lambda m, r: m['targets'][0]['runtime'].update(success=False, interrupted=True), 'FAIL_INTERRUPTED'),
            'timeout': (lambda m, r: m['targets'][0]['runtime'].update(success=False, timeout=True), 'FAIL_INCOMPLETE'),
            'incomplete result': (lambda m, r: m['targets'][0]['runtime'].update(success=False, incomplete=True), 'FAIL_INCOMPLETE'),
            'missing completion marker': (lambda m, r: m['targets'][0]['runtime'].update(completion_marker_observed=False), 'FAIL_RUNTIME'),
            'explicit failure marker': (lambda m, r: m['targets'][0]['runtime'].update(success=False, completion_marker_observed=False, failure_marker_observed=True), 'FAIL_RUNTIME'),
        }
        for name, (mutate, expected) in scenarios.items():
            self.assert_fixture(name, mutate, expected)

    def test_contract_identity_and_csv_synthetic_protocol_evidence(self):
        scenarios = {
            'unsupported schema': (lambda m, r: m.update(schema_version='unsupported'), 'FAIL_CONTRACT'),
            'absolute path': (lambda m, r: m['files'][0].update(relative_path='/escape'), 'FAIL_CONTRACT', False),
            'parent traversal': (lambda m, r: m['files'][0].update(relative_path='../escape'), 'FAIL_CONTRACT', False),
            'duplicate inventory path': (lambda m, r: m['files'].append(dict(m['files'][0])), 'FAIL_CONTRACT'),
            'wrong declared target count': (lambda m, r: m.update(declared_target_count=1), 'FAIL_CONTRACT'),
            'duplicate target': (lambda m, r: m['targets'].append(dict(m['targets'][0])), 'FAIL_CONTRACT'),
            'unknown target': (lambda m, r: m['targets'][0].update(target_identifier='unknown'), 'FAIL_CONTRACT'),
            'missing target': (lambda m, r: m['targets'].pop(), 'FAIL_CONTRACT'),
            'wrong CSV filename': (lambda m, r: m['targets'][0].update(actual_result_filename='wrong.csv'), 'FAIL_IDENTITY'),
            'wrong delimiter': (lambda m, r: m['targets'][0]['csv_schema'].update(delimiter=';'), 'FAIL_CONTRACT'),
            'missing header': (lambda m, r: m['targets'][0]['csv_schema'].update(header_required=False), 'FAIL_CONTRACT'),
            'renamed column': (lambda m, r: m['targets'][0]['csv_schema']['columns'].__setitem__(1, 'renamed'), 'FAIL_CONTRACT'),
            'reordered column': (lambda m, r: m['targets'][0]['csv_schema']['columns'].reverse(), 'FAIL_CONTRACT'),
            'missing column': (lambda m, r: m['targets'][0]['csv_schema']['columns'].pop(), 'FAIL_CONTRACT'),
            'extra column': (lambda m, r: m['targets'][0]['csv_schema']['columns'].append('extra'), 'FAIL_CONTRACT'),
            'missing journal reference': (lambda m, r: m['targets'][0]['runtime'].update(journal_reference='missing.log'), 'FAIL_CONTRACT'),
            'missing report reference': (lambda m, r: m['targets'][0]['runtime'].update(report_reference='missing.json'), 'FAIL_CONTRACT'),
            'missing compiler-log reference': (lambda m, r: m['targets'][0]['compiler'].update(log_reference='missing.log'), 'FAIL_CONTRACT'),
            'conflicting completion and failure markers': (lambda m, r: m['targets'][0]['runtime'].update(failure_marker_observed=True), 'FAIL_CONTRACT'),
            'wrong batch identity': (lambda m, r: m.update(batch_identity='0'*64), 'FAIL_IDENTITY'),
            'wrong Rust task identity': (lambda m, r: m['targets'][0].update(rust_task_identity='0'*64), 'FAIL_IDENTITY'),
            'wrong Rust-component identity': (lambda m, r: m['targets'][0].update(rust_component_identity='0'*64), 'FAIL_IDENTITY'),
            'wrong expected-vector identity': (lambda m, r: m['targets'][0].update(expected_vector_identity='0'*64), 'FAIL_IDENTITY'),
            'stale runtime identity': (lambda m, r: m['targets'][0].update(runtime_identity='0'*64), 'FAIL_IDENTITY'),
            'stale tester identity': (lambda m, r: m['targets'][0].update(tester_identity='0'*64), 'FAIL_IDENTITY'),
            'stale package identity': (lambda m, r: m['targets'][0].update(package_identity='0'*64), 'FAIL_IDENTITY'),
            'inconsistent compiler success state': (lambda m, r: m['targets'][0]['compiler'].update(exit_status=1), 'FAIL_CONTRACT'),
            'disallowed warning state': (lambda m, r: m['targets'][0]['compiler'].update(warnings=['warning'], warning_count=1, warnings_allowed=False), 'FAIL_COMPILE'),
        }
        for name, item in scenarios.items():
            mutate, expected, *rehash = item
            self.assert_fixture(name, mutate, expected, rehash[0] if rehash else True)

    def test_filesystem_and_numeric_synthetic_protocol_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); build(root); (root / 'unexpected').write_text('x')
            self.assertEqual(reconcile(root)['classification'], 'FAIL_CONTRACT')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); build(root); (root / 'macd/compiler.log').unlink()
            self.assertEqual(reconcile(root)['classification'], 'FAIL_CONTRACT')
        scenarios = {
            'stale file hash': (lambda m, r: m['files'][0].update(sha256='0'*64), 'FAIL_CONTRACT', False),
            'wrong file size': (lambda m, r: m['files'][0].update(size=1), 'FAIL_CONTRACT', False),
            'malformed CSV': (lambda m, r: _csv(r, m).write_text('bad'), 'FAIL_CONTRACT', True),
            'invalid null token': (lambda m, r: _csv(r, m).write_bytes(_csv(r, m).read_bytes().replace(b'NULL', b'', 1)), 'FAIL_CONTRACT', True),
            'shifted row': (lambda m, r: _row_id(r, m, 4), 'FAIL_ROW_ALIGNMENT', True),
            'wrong row identifier': (lambda m, r: _row_id(r, m, 99), 'FAIL_ROW_ALIGNMENT', True),
            'NaN': (lambda m, r: _csv(r, m).write_bytes(_csv(r, m).read_bytes().replace(b'0.00029166666666657903', b'NaN', 1)), 'FAIL_CONTRACT', True),
            'positive infinity': (lambda m, r: _csv(r, m).write_bytes(_csv(r, m).read_bytes().replace(b'0.00029166666666657903', b'inf', 1)), 'FAIL_CONTRACT', True),
            'negative infinity': (lambda m, r: _csv(r, m).write_bytes(_csv(r, m).read_bytes().replace(b'0.00029166666666657903', b'-inf', 1)), 'FAIL_CONTRACT', True),
            'MACD outside tolerance': (lambda m, r: _csv(r, m).write_bytes(_csv(r, m).read_bytes().replace(b'0.00029166666666657903', b'1.0', 1)), 'FAIL_VALUE_MISMATCH', True),
        }
        for name, (mutate, expected, rehash) in scenarios.items():
            self.assert_fixture(name, mutate, expected, rehash)

    def test_atomicity_synthetic_protocol_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / 'source'; source.mkdir(); build(source)
            one = publish(source, root / 'one.json'); two = publish(source, root / 'two.json')
            self.assertEqual(one, two); self.assertEqual((root / 'one.json').read_bytes(), (root / 'two.json').read_bytes())
            with self.assertRaises(ValueError): publish(source, root / 'one.json')
            with self.assertRaises(RuntimeError): publish(source, root / 'bad.json', True)
            self.assertFalse((root / 'bad.tmp').exists())
