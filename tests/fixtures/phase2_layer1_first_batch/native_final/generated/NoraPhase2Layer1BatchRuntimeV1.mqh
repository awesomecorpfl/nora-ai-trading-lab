#ifndef NORA_PHASE2_LAYER1_BATCH_RUNTIME_V1_MQH
#define NORA_PHASE2_LAYER1_BATCH_RUNTIME_V1_MQH
bool NoraLayer1Compute(const int kind,const double &source[],const bool &source_null[],const int count,const int period,double &out[],bool &out_null[]){
 if(period<1)return false;ArrayResize(out,count);ArrayResize(out_null,count);for(int i=0;i<count;i++){out[i]=0.0;out_null[i]=true;}
 if(kind==0){double seed=0.0,state=0.0;int seeded=0;bool ready=false;double alpha=2.0/(period+1.0);for(int i=0;i<count;i++){if(source_null[i]){seed=0.0;seeded=0;ready=false;continue;}if(ready){state=state+alpha*(source[i]-state);out[i]=state;out_null[i]=false;}else{seed+=source[i];seeded++;if(seeded==period){state=seed/period;ready=true;out[i]=state;out_null[i]=false;}}}return true;}
 for(int i=period-1;i<count;i++){bool missing=false;double value=(kind==1?-DBL_MAX:DBL_MAX);for(int j=i+1-period;j<=i;j++){if(source_null[j]){missing=true;break;}if(kind==1)value=MathMax(value,source[j]);else value=MathMin(value,source[j]);}if(!missing){out[i]=value;out_null[i]=false;}}return true;}
#endif
