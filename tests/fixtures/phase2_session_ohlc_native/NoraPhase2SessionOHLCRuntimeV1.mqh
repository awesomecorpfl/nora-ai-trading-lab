#ifndef NORA_SESSION_OHLC_RUNTIME_V1_MQH
#define NORA_SESSION_OHLC_RUNTIME_V1_MQH
bool NoraSessionOHLCCompute(const string &sid[],const double &o[],const double &h[],const double &l[],const double &c[],const int n,const int which,double &v[]){ArrayResize(v,n);string cur="";double so=0,sh=0,sl=0;for(int i=0;i<n;i++){if(i==0||sid[i]!=cur){cur=sid[i];so=o[i];sh=h[i];sl=l[i];}else{sh=MathMax(sh,h[i]);sl=MathMin(sl,l[i]);}if(which==0)v[i]=so;else if(which==1)v[i]=sh;else if(which==2)v[i]=sl;else v[i]=c[i];}return true;}
#endif
