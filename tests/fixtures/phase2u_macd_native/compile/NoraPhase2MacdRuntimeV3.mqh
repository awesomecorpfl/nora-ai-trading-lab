#ifndef NORA_PHASE2_MACD_RUNTIME_V3_MQH
#define NORA_PHASE2_MACD_RUNTIME_V3_MQH
bool NoraMacdFinite(const double value){return MathIsValidNumber(value);}
bool NoraMacdEma(const double &values[],const bool &values_null[],const int count,const int period,double &output[],bool &output_null[]){
  if(period<1 || count<0) return false;
  for(int i=0;i<count;i++){output_null[i]=true;output[i]=0.0;}
  for(int end=period-1;end<count;end++){
    if(end==period-1){double sum=0.0;for(int j=0;j<period;j++){if(values_null[j]||!NoraMacdFinite(values[j])) return false;sum+=values[j];}output[end]=sum/period;output_null[end]=false;}
    else {if(values_null[end]||output_null[end-1]||!NoraMacdFinite(values[end])) return false;output[end]=output[end-1]+(2.0/(period+1.0))*(values[end]-output[end-1]);output_null[end]=false;}
  } return true;
}
bool NoraPhase2MacdCompute(const double &close[],const bool &source_null[],const int count,double &macd[],bool &macd_null[],double &signal[],bool &signal_null[],double &hist[],bool &hist_null[]){
  double fast[],slow[],compact[],compact_signal[];bool fast_null[],slow_null[],compact_null[],compact_signal_null[];
  ArrayResize(fast,count);ArrayResize(slow,count);ArrayResize(compact,count);ArrayResize(compact_signal,count);ArrayResize(fast_null,count);ArrayResize(slow_null,count);ArrayResize(compact_null,count);ArrayResize(compact_signal_null,count);
  if(!NoraMacdEma(close,source_null,count,2,fast,fast_null)||!NoraMacdEma(close,source_null,count,4,slow,slow_null)) return false;
  int n=0;for(int i=0;i<count;i++){macd_null[i]=fast_null[i]||slow_null[i];signal_null[i]=true;hist_null[i]=true;macd[i]=0.0;signal[i]=0.0;hist[i]=0.0;if(!macd_null[i]){macd[i]=fast[i]-slow[i];compact[n]=macd[i];compact_null[n]=false;n++;}}
  if(!NoraMacdEma(compact,compact_null,n,3,compact_signal,compact_signal_null)) return false;
  int k=0;for(int row=0;row<count;row++){if(!macd_null[row]){if(!compact_signal_null[k]){signal[row]=compact_signal[k];signal_null[row]=false;hist[row]=macd[row]-signal[row];hist_null[row]=false;}k++;}}
  return true;
}
#endif
