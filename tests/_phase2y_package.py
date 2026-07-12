"""Synthetic protocol evidence only; never native execution evidence."""
import csv
import hashlib
import json
from pathlib import Path

from lab.phase2x_batch import load
from lab.phase2y_ingest import MANIFEST_NAME
from lab.phase2y_return_contract import VERSION, returned_package_identity


def build(root, mutate=None):
    """Create a complete synthetic returned-result directory."""
    root = Path(root)
    batch = load(); targets = []; payloads = {}
    for target in batch['targets']:
        ident = target['id']; vectors = target['expected_vectors']
        refs = {'compiler': f'{ident}/compiler.log', 'journal': f'{ident}/journal.log', 'report': f'{ident}/report.json', 'result': f'{ident}/{target["result_filename"]}'}
        columns = vectors['columns']; numeric = [x for x in columns if x != 'pass']
        table = [columns]
        for index in vectors['rows']:
            row = []
            for column in columns:
                if column == 'row': value = index
                elif column in ('close', 'source'): value = vectors['vectors'][column][index]
                elif column.endswith('_null'): value = 1 if vectors['vectors']['null_masks'].get(column[:-5], [False] * vectors['row_count'])[index] else 0
                elif column == 'pass': value = '0'
                else: value = vectors['vectors'][column][index]
                row.append('NULL' if value is None else str(value))
            table.append(row)
        import io
        stream = io.StringIO(); csv.writer(stream, lineterminator='\n').writerows(table)
        payloads.update({refs['compiler']: b'compiler\n', refs['journal']: b'journal\n', refs['report']: b'{}\n', refs['result']: stream.getvalue().encode()})
        targets.append({'target_identifier': ident, 'rust_task_identity': target['rust_task_identity'], 'rust_component_identity': target['rust_component_identity'], 'expected_vector_identity': vectors['expected_vector_identity'], 'runtime_identity': target['runtime_identity'], 'tester_identity': target['tester_identity'], 'package_identity': target['package_identity'], 'expected_result_filename': target['result_filename'], 'actual_result_filename': target['result_filename'], 'compiler': {'invoked': True, 'exit_status': 0, 'success': True, 'warnings': [], 'warning_count': 0, 'warnings_allowed': True, 'errors': [], 'error_count': 0, 'log_reference': refs['compiler'], 'expected_ex5_reference': None}, 'runtime': {'invoked': True, 'completion_status': 'completed', 'success': True, 'interrupted': False, 'timeout': False, 'incomplete': False, 'completion_marker_observed': True, 'failure_marker_observed': False, 'journal_reference': refs['journal'], 'report_reference': refs['report'], 'result_csv_reference': refs['result']}, 'csv_schema': {'encoding': 'utf-8', 'delimiter': ',', 'header_required': True, 'columns': columns, 'row_identifier_column': 'row', 'numeric_columns': numeric, 'null_representation': 'NULL', 'expected_row_count': vectors['row_count'], 'target_binding': ident}})
    value = {'schema_version': VERSION, 'batch_identity': batch['batch_identity'], 'run_identifier': 'synthetic-protocol-evidence', 'declared_target_count': 2, 'targets': targets, 'batch_completion_state': 'completed', 'interrupted': False, 'timeout': False, 'incomplete': False, 'files': []}
    if mutate: mutate(value, payloads)
    for path, contents in payloads.items():
        target = next(t['target_identifier'] for t in targets if path.startswith(t['target_identifier'] + '/'))
        role = 'compiler_log' if path.endswith('compiler.log') else 'runtime_journal' if path.endswith('journal.log') else 'tester_report' if path.endswith('report.json') else 'result_csv'
        value['files'].append({'relative_path': path, 'role': role, 'required': True, 'target_binding': target, 'size': len(contents), 'sha256': hashlib.sha256(contents).hexdigest()})
    value['returned_package_semantic_identity'] = returned_package_identity(value)
    for path, contents in payloads.items():
        out = root / path; out.parent.mkdir(parents=True, exist_ok=True); out.write_bytes(contents)
    (root / MANIFEST_NAME).write_text(json.dumps(value, sort_keys=True))
    return value


def rewrite(root, mutate, rehash=True):
    """Mutate synthetic protocol evidence and optionally refresh its inventory."""
    root = Path(root); manifest_path = root / MANIFEST_NAME; value = json.loads(manifest_path.read_text())
    mutate(value, root)
    if rehash:
        for item in value['files']:
            data = (root / item['relative_path']).read_bytes()
            item['size'] = len(data); item['sha256'] = hashlib.sha256(data).hexdigest()
    value['returned_package_semantic_identity'] = returned_package_identity(value)
    manifest_path.write_text(json.dumps(value, sort_keys=True))
    return value
