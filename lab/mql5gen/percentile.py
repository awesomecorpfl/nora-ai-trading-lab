"""Deterministic executable-source Phase-2W rolling percentile canary."""
import hashlib,json,math
from pathlib import Path
from . import GenerationError,_publish
VERSION='nora.phase2w.percentile_executable_v3';RUNTIME='NoraPhase2PercentileRuntimeV3.mqh';TESTER='NoraPhase2PercentileTesterCanaryV3.mq5';EVIDENCE='phase2w_percentile_executable_rust_evidence.json';PACKAGE='phase2w_percentile_executable_package.json';CSV='nora_phase2w_percentile_tester_v3.csv';COMPLETION='NORA_PHASE2W_PERCENTILE_COMPLETE_V3';NULL_TOKEN='NULL'
TASK_ID='943765d83d115309867fa8da768fc2a69500e7292f6048ed87541f4e26e63775';INPUT_ID='5d10e5722faaf64f1b243bb27feb8a4f84940d46c4acb1697d6514cd4da94383';RUST_ID='3e05d035eed7e607a8107c3e2c66b54c386da9adb4bf0f213a19dc5e6e8193f8'
CONTRACT_DOMAIN='nora.phase2w.percentile.contract';RUNTIME_DOMAIN='nora.phase2w.percentile.runtime.v3';TESTER_DOMAIN='nora.phase2w.percentile.tester.v3';PACKAGE_DOMAIN='nora.phase2w.percentile.package.v3'
STALE_CONTENT_BINDING_IDENTITIES={'runtime_identity_claim':'44ec82c7c8173fd6fee6db7c538794ef6f9c3e2d9d928962af2dded8ac1e05be','tester_identity_claim':'75c340fa4ca6555dc5b1f4e89f4afacaef18107eb0013095b09c1892d11299cf','package_identity':'cd14eae8e51d73da1300a6743ccdb62f09dfccf75a74d2c7109b52f03eb96bc9','defect':'runtime/tester content changed before native execution but package was not regenerated'}
INPUT=[None,None,1.1006,1.1009333333333335,1.1009666666666666,1.1013333333333335,1.1013666666666666,1.1017333333333335,1.1017666666666666,1.1021333333333334,1.1021666666666665,1.1025333333333334];OUTPUT=[None,None,None,None,None,1.,1.,1.,1.,1.,1.,1.]
def _id(d,*x):
 h=hashlib.sha256();h.update(d.encode())
 for v in x:
  b=json.dumps(v,sort_keys=True,separators=(',',':')).encode();h.update(len(b).to_bytes(8,'big'));h.update(b)
 return h.hexdigest()
def _values(v):return ','.join('0.0' if x is None else repr(x) for x in v)
def _mask(v):return ','.join('true' if x is None else 'false' for x in v)
def _runtime():return b'''#ifndef NORA_PHASE2_PERCENTILE_RUNTIME_V3_MQH
#define NORA_PHASE2_PERCENTILE_RUNTIME_V3_MQH
bool NoraPhase2Percentile(const double &data[],const bool &data_null[],const int count,const int lookback,double &output[],bool &output_null[]){
 if(lookback<2||count<0)return false;for(int i=0;i<count;i++){output[i]=0.0;output_null[i]=true;}for(int row=lookback-1;row<count;row++){bool complete=true;for(int j=row-lookback+1;j<=row;j++){if(data_null[j]||!MathIsValidNumber(data[j])){complete=false;break;}}if(!complete)continue;double less=0.0,equal=0.0,current=data[row];for(int j=row-lookback+1;j<=row;j++){if(data[j]<current)less++;if(data[j]==current)equal++;}output[row]=(less+(equal-1.0)/2.0)/(lookback-1.0);output_null[row]=false;}return true;
}
#endif
'''
def _tester():return ('''#property strict
#include "NoraPhase2PercentileRuntimeV3.mqh"
#define NORA_PERCENTILE_ROWS 12
const string NORA_PERCENTILE_CSV="'''+CSV+'''";
double values[NORA_PERCENTILE_ROWS]={'''+_values(INPUT)+'''};bool value_nulls[NORA_PERCENTILE_ROWS]={'''+_mask(INPUT)+'''};double expected[NORA_PERCENTILE_ROWS]={'''+_values(OUTPUT)+'''};bool expected_null[NORA_PERCENTILE_ROWS]={'''+_mask(OUTPUT)+'''};
string NoraPercentileCsv(const double value,const bool is_null){if(is_null)return "NULL";return DoubleToString(value,17);}
int OnInit(){double actual[];bool actual_null[];ArrayResize(actual,NORA_PERCENTILE_ROWS);ArrayResize(actual_null,NORA_PERCENTILE_ROWS);if(!NoraPhase2Percentile(values,value_nulls,NORA_PERCENTILE_ROWS,4,actual,actual_null)){Print("NORA_PHASE2W_PERCENTILE_FAIL");return INIT_FAILED;}int f=FileOpen(NORA_PERCENTILE_CSV,FILE_WRITE|FILE_CSV|FILE_ANSI);if(f==INVALID_HANDLE)return INIT_FAILED;FileWrite(f,"row","source","percentile","pass");for(int i=0;i<NORA_PERCENTILE_ROWS;i++){bool ok=actual_null[i]==expected_null[i]&&(actual_null[i]||MathAbs(actual[i]-expected[i])<=1e-12);FileWrite(f,i,NoraPercentileCsv(values[i],value_nulls[i]),NoraPercentileCsv(actual[i],actual_null[i]),ok?"true":"false");if(!ok){FileClose(f);Print("NORA_PHASE2W_PERCENTILE_FAIL");return INIT_FAILED;}}FileClose(f);Print("'''+COMPLETION+'''");return INIT_SUCCEEDED;}
void OnDeinit(const int reason){}
''').encode()
def generate(out_dir):
 out=Path(out_dir);names=[RUNTIME,TESTER,EVIDENCE,PACKAGE]
 if not out.is_dir() or any((out/n).exists() for n in names):raise GenerationError('percentile output target invalid')
 if any(v is not None and not math.isfinite(v) for v in INPUT):raise GenerationError('percentile source values must be finite or null')
 evidence={'version':VERSION,'task_semantic_identity':TASK_ID,'input_fixture_identity':INPUT_ID,'source_series':'sma3','lookback':4,'formula':'(less + (equal-1)/2)/(lookback-1)','tie_handling':'average zero-based rank','null_policy':'null until complete non-null window','finite_source_policy':'finite or null only','input_vector':INPUT,'percentile_vector':OUTPUT,'row_count':12,'csv_schema':['row','source','percentile','pass'],'csv_null_token':NULL_TOKEN,'completion_marker':COMPLETION,'rust_percentile_identity':RUST_ID};evidence['executable_contract_identity']=_id(CONTRACT_DOMAIN,evidence)
 runtime=_runtime();rs=hashlib.sha256(runtime).hexdigest();ri=_id(RUNTIME_DOMAIN,VERSION,rs,evidence['executable_contract_identity'])
 tester=_tester();ts=hashlib.sha256(tester).hexdigest();ti=_id(TESTER_DOMAIN,ri,ts,evidence['executable_contract_identity'])
 package={'version':VERSION,'historical_scaffold_identities':{'runtime':'b98e1664b592c4f7c627b8c39c98f8a9748a568ca6055f59283895319ca76fb2','tester':'ffe33f1281175b62ca3b68f9189ab6fed8ce8890b7fbdc7932fdf5b430fd7189','package':'bf255f2d0f626b0c83a235a8b272bd507a668e4154f12fdc8dd463b7701ca1d9'},'stale_content_binding_identities':STALE_CONTENT_BINDING_IDENTITIES,'rust_percentile_identity':RUST_ID,'runtime_identity':ri,'tester_identity':ti,'runtime_sha256':rs,'tester_sha256':ts,'csv_filename':CSV,'csv_null_token':NULL_TOKEN,'completion_marker':COMPLETION,'native_parity':False,'grammar_admitted':False,'searchable':False};package['package_identity']=_id(PACKAGE_DOMAIN,package)
 data={EVIDENCE:json.dumps(evidence,sort_keys=True,separators=(',',':')).encode()+b'\n',RUNTIME:runtime,TESTER:tester,PACKAGE:json.dumps(package,sort_keys=True,separators=(',',':')).encode()+b'\n'};done=[]
 try:
  for n in names:_publish(out,n,data[n]);done.append(n)
 except Exception:
  for n in done:(out/n).unlink(missing_ok=True)
  raise
 return {'ok':True,'executable_contract_identity':evidence['executable_contract_identity'],**package}
def verify_package_binding(package,runtime_bytes,tester_bytes,contract_identity):
 errors=[];rs=hashlib.sha256(runtime_bytes).hexdigest();ts=hashlib.sha256(tester_bytes).hexdigest()
 if package.get('runtime_sha256')!=rs:errors.append('runtime_sha256')
 if package.get('tester_sha256')!=ts:errors.append('tester_sha256')
 ri=_id(RUNTIME_DOMAIN,VERSION,rs,contract_identity)
 if package.get('runtime_identity')!=ri:errors.append('runtime_identity')
 ti=_id(TESTER_DOMAIN,ri,ts,contract_identity)
 if package.get('tester_identity')!=ti:errors.append('tester_identity')
 pkg=dict(package);stored=pkg.pop('package_identity',None)
 if stored!=_id(PACKAGE_DOMAIN,pkg):errors.append('package_identity')
 return errors
