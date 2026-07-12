"""Deterministic executable-source Phase-2U MACD(2,4,3) canary generation."""
from __future__ import annotations
import hashlib,json,math
from pathlib import Path
from . import GenerationError,_publish

VERSION="nora.phase2u.macd_executable_v2"; RUNTIME="NoraPhase2MacdRuntimeV2.mqh"; TESTER="NoraPhase2MacdTesterCanaryV2.mq5"; EVIDENCE="phase2u_macd_executable_rust_evidence.json"; PACKAGE="phase2u_macd_executable_package.json"; COMPLETION="nora_phase2u_macd_complete_v2.json"; CSV="nora_phase2u_macd_tester_v2.csv"
TASK_ID="c1d1d4a1003a3c0bc8f6b8b3d3ec736349db90082647a349cebf89b6dd07cb1e"; INPUT_ID="5d10e5722faaf64f1b243bb27feb8a4f84940d46c4acb1697d6514cd4da94383"
RUST_COMPONENT_ID="fef4a9583d0a12d5f067be9d977015a4f6d441e20232d2e8241b6a5539eee6f9"
CLOSE=[1.1003,1.1009,1.1006,1.1013,1.101,1.1017,1.1014,1.1021,1.1018,1.1025,1.1022,1.1029]
MACD=[None,None,None,.00029166666666657903,.000157222222222142,.00027507407407401097,.0001452913580246573,.0002672571193416129,.0001403817064473678,.0002642381688158224,.00013854594960549527,.0002631285858685217]
SIGNAL=[None,None,None,None,None,.000241320987654244,.00019330617283945067,.00023028164609053178,.0001853316762689498,.0002247849225423861,.0001816654360739407,.0002223970109712312]
HIST=[None,None,None,None,None,.00003375308641976696,-.00004801481481479336,.00003697547325108111,-.000044949969821582,.0000394532462734363,-.00004311948646844543,.00004073157489729051]
def _id(domain,*parts):
 h=hashlib.sha256();h.update(domain.encode())
 for p in parts:
  b=json.dumps(p,sort_keys=True,separators=(',',':')).encode();h.update(len(b).to_bytes(8,'big'));h.update(b)
 return h.hexdigest()
def _mql(values): return ','.join('0.0' if v is None else repr(v) for v in values)
def _mask(values): return ','.join('true' if v is None else 'false' for v in values)
def _runtime(): return b'''#ifndef NORA_PHASE2_MACD_RUNTIME_V2_MQH
#define NORA_PHASE2_MACD_RUNTIME_V2_MQH
bool NoraMacdFinite(const double value){return MathIsValidNumber(value);}
bool NoraMacdEma(const double &input[],const bool &input_null[],const int count,const int period,double &output[],bool &output_null[]){
  if(period<1 || count<0) return false;
  for(int i=0;i<count;i++){output_null[i]=true;output[i]=0.0;}
  for(int end=period-1;end<count;end++){
    if(end==period-1){double sum=0.0;for(int j=0;j<period;j++){if(input_null[j]||!NoraMacdFinite(input[j])) return false;sum+=input[j];}output[end]=sum/period;output_null[end]=false;}
    else {if(input_null[end]||output_null[end-1]||!NoraMacdFinite(input[end])) return false;output[end]=output[end-1]+(2.0/(period+1.0))*(input[end]-output[end-1]);output_null[end]=false;}
  } return true;
}
bool NoraPhase2MacdCompute(const double &close[],const bool &close_null[],const int count,double &macd[],bool &macd_null[],double &signal[],bool &signal_null[],double &hist[],bool &hist_null[]){
  double fast[],slow[],compact[],compact_signal[];bool fast_null[],slow_null[],compact_null[],compact_signal_null[];
  ArrayResize(fast,count);ArrayResize(slow,count);ArrayResize(compact,count);ArrayResize(compact_signal,count);ArrayResize(fast_null,count);ArrayResize(slow_null,count);ArrayResize(compact_null,count);ArrayResize(compact_signal_null,count);
  if(!NoraMacdEma(close,close_null,count,2,fast,fast_null)||!NoraMacdEma(close,close_null,count,4,slow,slow_null)) return false;
  int n=0;for(int i=0;i<count;i++){macd_null[i]=fast_null[i]||slow_null[i];signal_null[i]=true;hist_null[i]=true;macd[i]=0.0;signal[i]=0.0;hist[i]=0.0;if(!macd_null[i]){macd[i]=fast[i]-slow[i];compact[n]=macd[i];compact_null[n]=false;n++;}}
  if(!NoraMacdEma(compact,compact_null,n,3,compact_signal,compact_signal_null)) return false;
  int k=0;for(int row=0;row<count;row++){if(!macd_null[row]){if(!compact_signal_null[k]){signal[row]=compact_signal[k];signal_null[row]=false;hist[row]=macd[row]-signal[row];hist_null[row]=false;}k++;}}
  return true;
}
#endif
'''
def _tester():
 return ('''#property strict
#include "NoraPhase2MacdRuntimeV2.mqh"
#define NORA_MACD_ROWS 12
const string NORA_MACD_CSV="'''+CSV+'''";
const string NORA_MACD_COMPLETION="'''+COMPLETION+'''";
double close_values[NORA_MACD_ROWS]={'''+_mql(CLOSE)+'''};
bool close_null[NORA_MACD_ROWS]={'''+_mask(CLOSE)+'''};
double expected_macd[NORA_MACD_ROWS]={'''+_mql(MACD)+'''};
bool expected_macd_null[NORA_MACD_ROWS]={'''+_mask(MACD)+'''};
double expected_signal[NORA_MACD_ROWS]={'''+_mql(SIGNAL)+'''};
bool expected_signal_null[NORA_MACD_ROWS]={'''+_mask(SIGNAL)+'''};
double expected_hist[NORA_MACD_ROWS]={'''+_mql(HIST)+'''};
bool expected_hist_null[NORA_MACD_ROWS]={'''+_mask(HIST)+'''};
int OnInit(){double macd[],signal[],hist[];bool mn[],sn[],hn[];ArrayResize(macd,NORA_MACD_ROWS);ArrayResize(signal,NORA_MACD_ROWS);ArrayResize(hist,NORA_MACD_ROWS);ArrayResize(mn,NORA_MACD_ROWS);ArrayResize(sn,NORA_MACD_ROWS);ArrayResize(hn,NORA_MACD_ROWS);if(!NoraPhase2MacdCompute(close_values,close_null,NORA_MACD_ROWS,macd,mn,signal,sn,hist,hn)){Print("NORA_PHASE2U_MACD_FAIL");return INIT_FAILED;}int f=FileOpen(NORA_MACD_CSV,FILE_WRITE|FILE_CSV|FILE_ANSI);if(f==INVALID_HANDLE){Print("NORA_PHASE2U_MACD_FAIL");return INIT_FAILED;}FileWrite(f,"row","close","macd_null","macd","signal_null","signal","histogram_null","histogram","pass");for(int i=0;i<NORA_MACD_ROWS;i++){bool ok=(mn[i]==expected_macd_null[i]&&sn[i]==expected_signal_null[i]&&hn[i]==expected_hist_null[i]&& (mn[i]||MathAbs(macd[i]-expected_macd[i])<=1e-12)&& (sn[i]||MathAbs(signal[i]-expected_signal[i])<=1e-12)&& (hn[i]||MathAbs(hist[i]-expected_hist[i])<=1e-12));FileWrite(f,i,close_values[i],mn[i],macd[i],sn[i],signal[i],hn[i],hist[i],ok);if(!ok){FileClose(f);Print("NORA_PHASE2U_MACD_FAIL");return INIT_FAILED;}}FileClose(f);Print("NORA_PHASE2U_MACD_COMPLETE_V2");return INIT_SUCCEEDED;}
void OnDeinit(const int reason){}
''').encode()
def generate(output_dir):
 out=Path(output_dir);names=[RUNTIME,TESTER,EVIDENCE,PACKAGE]
 if not out.is_dir() or any((out/n).exists() for n in names):raise GenerationError('MACD output target already exists')
 if any(not math.isfinite(x) for x in CLOSE):raise GenerationError('MACD close values must be finite')
 evidence={'version':VERSION,'task_semantic_identity':TASK_ID,'input_fixture_identity':INPUT_ID,'source_series':'close','periods':{'fast':2,'slow':4,'signal':3},'ema_seed':'arithmetic_mean','ema_recurrence':'previous + 2/(period+1)*(input-previous)','signal_input':'compact ordered non-null MACD sequence realigned to original rows','histogram':'macd-signal','close':CLOSE,'macd':MACD,'signal':SIGNAL,'histogram_vector':HIST,'row_count':12,'csv_schema':['row','close','macd_null','macd','signal_null','signal','histogram_null','histogram','pass'],'completion_marker':'NORA_PHASE2U_MACD_COMPLETE_V2','rust_macd_component_identity':RUST_COMPONENT_ID};evidence['executable_contract_identity']=_id('nora.phase2u.macd.executable_contract',evidence)
 runtime=_runtime();rsha=hashlib.sha256(runtime).hexdigest();rid=_id('nora.phase2u.macd.runtime.v2',VERSION,rsha,evidence['periods'],evidence['executable_contract_identity'])
 tester=_tester();tsha=hashlib.sha256(tester).hexdigest();tid=_id('nora.phase2u.macd.tester.v2',rid,evidence['executable_contract_identity'],tsha)
 package={'version':VERSION,'historical_scaffold_identities':{'runtime':'5b78e5c7e4f8f0e7ce72e5aff72d930139e0e6f9050d8900cfa1564be9c136ee','tester':'4b2a22a94539d6c989e93173c581ae71963a0ad7896cdca36b00e6abba957ffc','package':'52d53fc3300eca2db3646eaab52ddaa2d0ae862632f60e6dac42c3ad5e6ac7ca'},'rust_macd_component_identity':evidence['rust_macd_component_identity'],'runtime_identity':rid,'tester_identity':tid,'runtime_sha256':rsha,'tester_sha256':tsha,'csv_filename':CSV,'completion_marker':evidence['completion_marker'],'native_parity':False,'grammar_admitted':False,'searchable':False};package['package_identity']=_id('nora.phase2u.macd.package.v2',package)
 payload={EVIDENCE:json.dumps(evidence,sort_keys=True,separators=(',',':')).encode()+b'\n',RUNTIME:runtime,TESTER:tester,PACKAGE:json.dumps(package,sort_keys=True,separators=(',',':')).encode()+b'\n'};written=[]
 try:
  for n in names:_publish(out,n,payload[n]);written.append(n)
 except Exception:
  for n in written:(out/n).unlink(missing_ok=True)
  raise
 return {'ok':True,'executable_contract_identity':evidence['executable_contract_identity'],**package}
