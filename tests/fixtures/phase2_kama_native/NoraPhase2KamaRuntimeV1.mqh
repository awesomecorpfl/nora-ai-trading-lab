#ifndef NORA_PHASE2_KAMA_RUNTIME_V1_MQH
#define NORA_PHASE2_KAMA_RUNTIME_V1_MQH
bool NoraKamaCompute(const double &x[],const int count,const int period,double &out[],bool &valid[]){if(period<1)return false;ArrayResize(out,count);ArrayResize(valid,count);for(int i=0;i<count;i++){out[i]=0.0;valid[i]=false;}if(count<=period)return true;double k=x[period];out[period]=k;valid[period]=true;double fc=2.0/(2.0+1.0),sc=2.0/(30.0+1.0);for(int i=period+1;i<count;i++){double path=0.0;for(int j=i-period+2;j<=i;j++)path+=MathAbs(x[j]-x[j-1]);double er=(path==0.0)?0.0:MathAbs(x[i]-x[i-period])/path;double a=MathPow(er*(fc-sc)+sc,2.0);k+=a*(x[i]-k);out[i]=k;valid[i]=true;}return true;}
#endif
