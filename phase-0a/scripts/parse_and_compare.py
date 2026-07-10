#!/usr/bin/env python3
"""Parse Phase 0A MT5 outputs and compare their semantic content."""
from __future__ import annotations
import csv, hashlib, json, sys
from html.parser import HTMLParser
from pathlib import Path

FIELDS = ('entry', 'type', 'volume', 'price', 'profit', 'commission', 'swap', 'symbol', 'magic')

class TextExtractor(HTMLParser):
    def __init__(self): super().__init__(); self.text = []
    def handle_data(self, data):
        if data.strip(): self.text.append(data.strip())

def load_csv(path: Path):
    with path.open(newline='', encoding='utf-8-sig') as f: return list(csv.DictReader(f, delimiter=';'))

def semantic_trades(path: Path):
    rows = load_csv(path)
    return [{key: row[key] for key in FIELDS} for row in rows]

def parse_report(path: Path):
    parser = TextExtractor(); parser.feed(path.read_text(encoding='utf-16', errors='ignore') if path.read_bytes()[:2] in (b'\xff\xfe', b'\xfe\xff') else path.read_text(encoding='utf-8', errors='ignore'))
    return {'path': path.name, 'text_tokens': len(parser.text), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

def main():
    if len(sys.argv) != 4: raise SystemExit('usage: parse_and_compare.py RUN1 RUN2 OUTPUT_JSON')
    runs = [Path(sys.argv[1]), Path(sys.argv[2])]
    payload = {'runs': []}
    for run in runs:
        trade_file = next(run.glob('*_trades.csv')); metrics_file = next(run.glob('*_metrics.csv'))
        report = run / 'report.htm'
        trades = semantic_trades(trade_file)
        metrics = {row['metric']: row['value'] for row in load_csv(metrics_file)}
        payload['runs'].append({'run': run.name, 'trades': trades, 'metrics': metrics, 'report': parse_report(report)})
    a, b = payload['runs']
    payload['comparison'] = {
        'semantic_trades_equal': a['trades'] == b['trades'],
        'decision_metrics_equal': a['metrics'] == b['metrics'],
        'normalization': 'Deal tickets and timestamps are deliberately excluded: they are operational identifiers/timing metadata, not reconciliation semantics for this deterministic probe.',
    }
    Path(sys.argv[3]).write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    if not all(payload['comparison'][k] for k in ('semantic_trades_equal','decision_metrics_equal')): raise SystemExit(2)

if __name__ == '__main__': main()

