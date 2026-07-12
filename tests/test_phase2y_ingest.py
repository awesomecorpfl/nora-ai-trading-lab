import tempfile
import unittest
from pathlib import Path

from lab.phase2y_ingest import ingest
from tests._phase2y_package import build


class FilesystemIngestion(unittest.TestCase):
    def test_valid_package_is_normalized(self):
        with tempfile.TemporaryDirectory() as directory:
            value = ingest(build(directory) and directory)
            self.assertTrue(value['accepted'])
            self.assertTrue(value['file_inventory_valid'])
            self.assertEqual(set(value['targets']), {'macd', 'percentile'})

    def test_filesystem_claims_are_not_trusted(self):
        with tempfile.TemporaryDirectory() as directory:
            build(directory)
            Path(directory, 'macd', 'compiler.log').write_text('mutated')
            self.assertEqual(ingest(directory)['classification'], 'FAIL_CONTRACT')
        with tempfile.TemporaryDirectory() as directory:
            build(directory)
            Path(directory, 'extra').write_text('x')
            self.assertEqual(ingest(directory)['classification'], 'FAIL_CONTRACT')
        with tempfile.TemporaryDirectory() as directory:
            build(directory)
            Path(directory, 'macd', 'journal.log').unlink()
            self.assertEqual(ingest(directory)['classification'], 'FAIL_CONTRACT')

    def test_execution_outcomes_are_evidenced(self):
        cases = ((lambda v, p: v['targets'][0]['compiler'].update(success=False, exit_status=1), 'FAIL_COMPILE'), (lambda v, p: v['targets'][0]['runtime'].update(interrupted=True, success=False), 'FAIL_INTERRUPTED'), (lambda v, p: v['targets'][0]['runtime'].update(timeout=True, success=False), 'FAIL_INCOMPLETE'), (lambda v, p: v['targets'][0]['runtime'].update(success=False), 'FAIL_RUNTIME'))
        for mutate, expected in cases:
            with tempfile.TemporaryDirectory() as directory:
                build(directory, mutate)
                self.assertEqual(ingest(directory)['classification'], expected)
