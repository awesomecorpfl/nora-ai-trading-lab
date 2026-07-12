"""Deterministic fixed-data Phase-2U MACD(2,4,3) MQL5 canary generation."""
from __future__ import annotations
import hashlib,json,os
from pathlib import Path
from . import GenerationError,_publish

VERSION="nora.phase2u.macd_v1"; RUNTIME="NoraPhase2MacdRuntimeV1.mqh"; TESTER="NoraPhase2MacdTesterCanaryV1.mq5"; EVIDENCE="phase2u_macd_rust_evidence.json"; PACKAGE="phase2u_macd_package.json"
TASK_ID="c1d1d4a1003a3c0bc8f6b8b3d3ec736349db90082647a349cebf89b6dd07cb1e"; INPUT_ID="5d10e5722faaf64f1b243bb27feb8a4f84940d46c4acb1697d6514cd4da94383"
CLOSE=[1.1003,1.1009,1.1006,1.1013,1.101,1.1017,1.1014,1.1021,1.1018,1.1025,1.1022,1.1029]
MACD=[None,None,None,.00029166666666657903,.000157222222222142,.00027507407407401097,.0001452913580246573,.0002672571193416129,.0001403817064473678,.0002642381688158224,.00013854594960549527,.0002631285858685217]
SIGNAL=[None,None,None,None,None,.000241320987654244,.00019330617283945067,.00023028164609053178,.0001853316762689498,.0002247849225423861,.0001816654360739407,.0002223970109712312]
HIST=[None,None,None,None,None,.00003375308641976696,-.00004801481481479336,.00003697547325108111,-.000044949969821582,.0000394532462734363,-.00004311948646844543,.00004073157489729051]
def _id(domain,*parts):
 h=hashlib.sha256();h.update(domain.encode())
 for p in parts:
  b=json.dumps(p,sort_keys=True,separators=(',',':')).encode();h.update(len(b).to_bytes(8,'big'));h.update(b)
 return h.hexdigest()
def generate(output_dir):
 out=Path(output_dir)
 if not out.is_dir():raise GenerationError('output directory must exist')
 names=[RUNTIME,TESTER,EVIDENCE,PACKAGE]
 if any((out/n).exists() for n in names):raise GenerationError('MACD output target already exists')
 evidence={'version':VERSION,'task_semantic_identity':TASK_ID,'input_fixture_identity':INPUT_ID,'source_series':'close','periods':{'fast':2,'slow':4,'signal':3},'ema_seed':'arithmetic_mean','ema_recurrence':'previous + 2/(period+1)*(input-previous)','signal_input':'compact ordered non-null MACD sequence realigned to original rows','histogram':'macd-signal','close':CLOSE,'macd':MACD,'signal':SIGNAL,'histogram_vector':HIST,'row_count':12}
 evidence['rust_macd_component_identity']=_id('nora.phase2u.macd.rust',evidence)
 runtime='#ifndef NORA_PHASE2_MACD_RUNTIME_V1_MQH\n#define NORA_PHASE2_MACD_RUNTIME_V1_MQH\n#include "NoraPhase2RuntimeV1.mqh"\n// MACD(2,4,3): arithmetic seeds; recurrence is frozen in Phase 2U evidence.\n#endif\n'.encode()
 rsha=hashlib.sha256(runtime).hexdigest(); rid=_id('nora.phase2u.macd.runtime',VERSION,rsha,evidence['periods'])
 tester=("#property strict\n#include \"NoraPhase2MacdRuntimeV1.mqh\"\n// Fixed committed close/MACD/signal/histogram vectors; no MT5 history.\n").encode();tsha=hashlib.sha256(tester).hexdigest();tid=_id('nora.phase2u.macd.tester',rid,evidence['rust_macd_component_identity'],tsha)
 package={'version':VERSION,'rust_macd_component_identity':evidence['rust_macd_component_identity'],'runtime_identity':rid,'tester_identity':tid,'runtime_sha256':rsha,'tester_sha256':tsha,'native_parity':False,'grammar_admitted':False,'searchable':False};package['package_identity']=_id('nora.phase2u.macd.package',package)
 payload={EVIDENCE:json.dumps(evidence,sort_keys=True,separators=(',',':')).encode()+b'\n',RUNTIME:runtime,TESTER:tester,PACKAGE:json.dumps(package,sort_keys=True,separators=(',',':')).encode()+b'\n'}
 written=[]
 try:
  for n in names:_publish(out,n,payload[n]);written.append(n)
 except Exception:
  for n in written:(out/n).unlink(missing_ok=True)
  raise
 return {'ok':True,**package}
