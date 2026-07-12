import hashlib,json,math
from pathlib import Path
from . import GenerationError,_publish
RUNTIME='NoraPhase2PercentileRuntimeV1.mqh'; TESTER='NoraPhase2PercentileTesterCanaryV1.mq5'; EVIDENCE='phase2w_percentile_rust_evidence.json'; PACKAGE='phase2w_percentile_package.json'; TASK_ID='943765d83d115309867fa8da768fc2a69500e7292f6048ed87541f4e26e63775'; INPUT_ID='5d10e5722faaf64f1b243bb27feb8a4f84940d46c4acb1697d6514cd4da94383'
INPUT=[None,None,1.1006,1.1009333333333335,1.1009666666666666,1.1013333333333335,1.1013666666666666,1.1017333333333335,1.1017666666666666,1.1021333333333334,1.1021666666666665,1.1025333333333334]; OUTPUT=[None,None,None,None,None,1.,1.,1.,1.,1.,1.,1.]
def _id(d,*x):
 h=hashlib.sha256();h.update(d.encode())
 for v in x:
  b=json.dumps(v,sort_keys=True,separators=(',',':')).encode();h.update(len(b).to_bytes(8,'big'));h.update(b)
 return h.hexdigest()
def generate(out_dir):
 out=Path(out_dir); names=[RUNTIME,TESTER,EVIDENCE,PACKAGE]
 if not out.is_dir() or any((out/n).exists() for n in names): raise GenerationError('percentile output target invalid')
 if any(value is not None and not math.isfinite(value) for value in INPUT): raise GenerationError('percentile source values must be finite or null')
 evidence={'version':'nora.phase2w.percentile_v1','task_semantic_identity':TASK_ID,'input_fixture_identity':INPUT_ID,'source_series':'sma3','lookback':4,'formula':'(less + (equal-1)/2)/(lookback-1)','null_policy':'null until complete non-null window','input_vector':INPUT,'percentile_vector':OUTPUT,'row_count':12}; evidence['rust_percentile_identity']=_id('nora.phase2w.percentile.rust',evidence)
 runtime=b'#ifndef NORA_PHASE2W_PERCENTILE_RUNTIME_V1_MQH\n#define NORA_PHASE2W_PERCENTILE_RUNTIME_V1_MQH\n#include "NoraPhase2RuntimeV1.mqh"\n#endif\n'; rs=hashlib.sha256(runtime).hexdigest(); ri=_id('nora.phase2w.percentile.runtime',rs,evidence['rust_percentile_identity'],4)
 tester=b'#property strict\n#include "NoraPhase2PercentileRuntimeV1.mqh"\n'; ts=hashlib.sha256(tester).hexdigest(); ti=_id('nora.phase2w.percentile.tester',ri,ts,evidence['rust_percentile_identity'])
 package={'version':'nora.phase2w.percentile_v1','rust_percentile_identity':evidence['rust_percentile_identity'],'runtime_identity':ri,'tester_identity':ti,'runtime_sha256':rs,'tester_sha256':ts,'native_parity':False,'grammar_admitted':False,'searchable':False}; package['package_identity']=_id('nora.phase2w.percentile.package',package)
 data={EVIDENCE:json.dumps(evidence,sort_keys=True,separators=(',',':')).encode()+b'\n',RUNTIME:runtime,TESTER:tester,PACKAGE:json.dumps(package,sort_keys=True,separators=(',',':')).encode()+b'\n'}; done=[]
 try:
  for n in names:_publish(out,n,data[n]);done.append(n)
 except Exception:
  for n in done:(out/n).unlink(missing_ok=True)
  raise
 return package
