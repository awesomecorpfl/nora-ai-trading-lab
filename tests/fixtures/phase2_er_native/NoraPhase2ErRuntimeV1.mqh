#ifndef NORA_PHASE2_ER_RUNTIME_V1_MQH
#define NORA_PHASE2_ER_RUNTIME_V1_MQH
bool NoraErCompute(const double &x[],const int count,const int period,double &out[],bool &valid[]){if(period<1)return false;ArrayResize(out,count);ArrayResize(valid,count);for(int i=0;i<count;i++){out[i]=0.0;valid[i]=false;}for(int i=period;i<count;i++){double path=0.0;for(int j=i-period+2;j<=i;j++)path+=MathAbs(x[j]-x[j-1]);out[i]=(path==0.0)?0.0:MathAbs(x[i]-x[i-period])/path;valid[i]=true;}return true;}
#endif
