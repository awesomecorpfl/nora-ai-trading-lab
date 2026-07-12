import csv
import json
import tempfile
import unittest
from pathlib import Path

from lab.phase2y_ingest import MANIFEST_NAME
from lab.phase2y_reconcile import publish, reconcile
from lab.phase2y_return_contract import returned_package_identity
from tests._phase2y_package import build


class Reconcile(unittest.TestCase):
    def test_exact_within_and_value_precedence(self):
        with tempfile.TemporaryDirectory() as directory:
            build(directory)
            self.assertEqual(reconcile(directory)['classification'], 'PASS_EXACT')
        def within(value, payloads):
            path = value['targets'][0]['runtime']['result_csv_reference']
            payloads[path] = payloads[path].replace(b'0.00029166666666657903', b'0.00029166666676657903', 1)
        with tempfile.TemporaryDirectory() as directory:
            build(directory, within)
            self.assertEqual(reconcile(directory)['classification'], 'PASS_WITHIN_TOLERANCE')

    def test_ingestion_failures_preserve_precedence(self):
        def bad_identity(value, payloads): value['targets'][0]['package_identity'] = '0' * 64
        def bad_compile(value, payloads): value['targets'][0]['compiler'].update(success=False, exit_status=1)
        with tempfile.TemporaryDirectory() as directory:
            build(directory)
            manifest = Path(directory, MANIFEST_NAME); value = json.loads(manifest.read_text()); value['files'][0]['sha256'] = '0' * 64; value['returned_package_semantic_identity'] = returned_package_identity(value); manifest.write_text(json.dumps(value))
            self.assertEqual(reconcile(directory)['classification'], 'FAIL_CONTRACT')
        for mutate, expected in ((bad_identity, 'FAIL_IDENTITY'), (bad_compile, 'FAIL_COMPILE')):
            with tempfile.TemporaryDirectory() as directory:
                build(directory, mutate)
                self.assertEqual(reconcile(directory)['classification'], expected)

    def test_atomic_immutable_evidence_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, 'source'); source.mkdir(); build(source)
            one = publish(source, Path(directory, 'one.json')); two = publish(source, Path(directory, 'two.json'))
            self.assertEqual(one, two)
            self.assertEqual(Path(directory, 'one.json').read_bytes(), Path(directory, 'two.json').read_bytes())
            with self.assertRaises(ValueError): publish(source, Path(directory, 'one.json'))
            with self.assertRaises(RuntimeError): publish(source, Path(directory, 'bad.json'), True)
            self.assertFalse(Path(directory, 'bad.tmp').exists())
