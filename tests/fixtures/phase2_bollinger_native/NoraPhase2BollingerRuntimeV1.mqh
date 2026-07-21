#ifndef NORA_PHASE2_BOLLINGER_RUNTIME_V1_MQH
#define NORA_PHASE2_BOLLINGER_RUNTIME_V1_MQH
bool NoraBollingerCompute(const double &x[],const int count,const int period,const double k,const int which,double &value[],bool &valid[]){if(period<=0)return false;ArrayResize(value,count);ArrayResize(valid,count);for(int i=0;i<count;i++){value[i]=0.0;valid[i]=false;}for(int i=period-1;i<count;i++){double m=0.0;for(int j=0;j<period;j++)m+=x[i-period+1+j];m/=period;double ss=0.0;for(int j=0;j<period;j++){double d=x[i-period+1+j]-m;ss+=d*d;}double s=MathSqrt(ss/period);if(which==0)value[i]=m;else if(which==1)value[i]=m+k*s;else if(which==2)value[i]=m-k*s;else value[i]=(m==0.0)?0.0:(2.0*k*s)/m;valid[i]=true;}return true;}
#endif
