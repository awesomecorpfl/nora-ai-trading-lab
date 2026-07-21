#ifndef NORA_PHASE2_CCI_RUNTIME_V1_MQH
#define NORA_PHASE2_CCI_RUNTIME_V1_MQH
bool NoraCCICompute(const double &high[],const double &low[],const double &close[],const int count,const int period,double &value[],bool &valid[]){if(period<=0)return false;ArrayResize(value,count);ArrayResize(valid,count);for(int i=0;i<count;i++){value[i]=0.0;valid[i]=false;}for(int i=period-1;i<count;i++){double sum=0.0;for(int j=0;j<period;j++)sum+=(high[i-period+1+j]+low[i-period+1+j]+close[i-period+1+j])/3.0;double mean=sum/period;double dev=0.0;for(int j=0;j<period;j++){double tp=(high[i-period+1+j]+low[i-period+1+j]+close[i-period+1+j])/3.0;dev+=MathAbs(tp-mean);}dev/=period;double tp=(high[i]+low[i]+close[i])/3.0;value[i]=(dev==0.0)?0.0:(tp-mean)/(0.015*dev);valid[i]=true;}return true;}
#endif
