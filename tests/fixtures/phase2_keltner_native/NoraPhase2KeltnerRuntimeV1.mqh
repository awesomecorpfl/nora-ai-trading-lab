#ifndef NORA_PHASE2_KELTNER_RUNTIME_V1_MQH
#define NORA_PHASE2_KELTNER_RUNTIME_V1_MQH
bool NoraKeltner(const double &h[],const double &l[],const double &c[],int n,int p,double k,int which,double &v[],bool &ok[]){if(p<=0)return false;ArrayResize(v,n);ArrayResize(ok,n);for(int i=0;i<n;i++){v[i]=0;ok[i]=false;}double tr[],ee[],aa[];ArrayResize(tr,n);ArrayResize(ee,n);ArrayResize(aa,n);for(int i=0;i<n;i++){tr[i]=(i==0)?h[i]-l[i]:MathMax(h[i]-l[i],MathMax(MathAbs(h[i]-c[i-1]),MathAbs(l[i]-c[i-1])));ee[i]=0;aa[i]=0;}for(int i=p-1;i<n;i++){if(i==p-1){for(int j=0;j<p;j++){ee[i]+=c[j];aa[i]+=tr[j];}ee[i]/=p;aa[i]/=p;}else{ee[i]=ee[i-1]+(2.0/(p+1.0))*(c[i]-ee[i-1]);aa[i]=((aa[i-1]*(p-1))+tr[i])/p;}v[i]=(which==0)?ee[i]:((which==1)?ee[i]+k*aa[i]:ee[i]-k*aa[i]);ok[i]=true;}return true;}
#endif
