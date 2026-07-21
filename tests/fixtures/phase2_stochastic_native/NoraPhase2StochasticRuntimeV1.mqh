#ifndef NORA_PHASE2_STOCHASTIC_RUNTIME_V1_MQH
#define NORA_PHASE2_STOCHASTIC_RUNTIME_V1_MQH
bool NoraStochasticCompute(const double &h[],const double &l[],const double &c[],const bool &n[],const int count,const int period,const int dperiod,double &k[],double &d[],bool &kn[],bool &dn[]){
 if(period<1||dperiod<1)return false;ArrayResize(k,count);ArrayResize(d,count);ArrayResize(kn,count);ArrayResize(dn,count);for(int i=0;i<count;i++){k[i]=0.0;d[i]=0.0;kn[i]=true;dn[i]=true;}
 for(int i=period-1;i<count;i++){double hi=-DBL_MAX,lo=DBL_MAX;bool missing=false;for(int j=i+1-period;j<=i;j++){if(n[j]){missing=true;break;}hi=MathMax(hi,h[j]);lo=MathMin(lo,l[j]);}if(missing)continue;k[i]=(hi==lo?50.0:100.0*(c[i]-lo)/(hi-lo));kn[i]=false;}
 for(int i=0;i<count;i++){if(i+1<dperiod)continue;double total=0.0;bool missing=false;for(int j=i+1-dperiod;j<=i;j++){if(kn[j]){missing=true;break;}total+=k[j];}if(!missing){d[i]=total/dperiod;dn[i]=false;}}
 return true;}
#endif
