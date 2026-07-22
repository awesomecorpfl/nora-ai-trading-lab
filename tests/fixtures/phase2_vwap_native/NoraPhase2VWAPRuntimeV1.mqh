#ifndef NORA_PHASE2_VWAP_RUNTIME_V1_MQH
#define NORA_PHASE2_VWAP_RUNTIME_V1_MQH
bool NoraVWAPCompute(const string &sid[],const double &h[],const double &l[],const double &c[],const double &v[],const int n,double &out[]){ArrayResize(out,n);string cur="";double pv=0,vv=0;for(int i=0;i<n;i++){if(i==0||sid[i]!=cur){cur=sid[i];pv=0;vv=0;}pv+=(h[i]+l[i]+c[i])/3.*v[i];vv+=v[i];out[i]=(vv==0)?0:pv/vv;}return true;}
#endif
