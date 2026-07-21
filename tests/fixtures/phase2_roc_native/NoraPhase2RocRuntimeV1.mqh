#ifndef NORA_PHASE2_ROC_RUNTIME_V1_MQH
#define NORA_PHASE2_ROC_RUNTIME_V1_MQH
bool NoraRocCompute(const double &s[],const bool &n[],const int c,const int p,double &o[],bool &z[]){if(p<=0)return false;ArrayResize(o,c);ArrayResize(z,c);for(int i=0;i<c;i++){z[i]=true;o[i]=0.0;if(i<p||n[i]||n[i-p]||s[i-p]==0.0)continue;o[i]=(s[i]/s[i-p]-1.0)*100.0;z[i]=false;}return true;}
#endif
