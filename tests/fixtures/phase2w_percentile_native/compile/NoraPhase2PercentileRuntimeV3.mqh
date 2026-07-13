#ifndef NORA_PHASE2_PERCENTILE_RUNTIME_V3_MQH
#define NORA_PHASE2_PERCENTILE_RUNTIME_V3_MQH
bool NoraPhase2Percentile(const double &data[],const bool &data_null[],const int count,const int lookback,double &output[],bool &output_null[]){
 if(lookback<2||count<0)return false;for(int i=0;i<count;i++){output[i]=0.0;output_null[i]=true;}for(int row=lookback-1;row<count;row++){bool complete=true;for(int j=row-lookback+1;j<=row;j++){if(data_null[j]||!MathIsValidNumber(data[j])){complete=false;break;}}if(!complete)continue;double less=0.0,equal=0.0,current=data[row];for(int j=row-lookback+1;j<=row;j++){if(data[j]<current)less++;if(data[j]==current)equal++;}output[row]=(less+(equal-1.0)/2.0)/(lookback-1.0);output_null[row]=false;}return true;
}
#endif
