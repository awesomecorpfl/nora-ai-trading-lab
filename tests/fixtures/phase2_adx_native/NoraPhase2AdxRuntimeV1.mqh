#ifndef NORA_PHASE2_ADX_RUNTIME_V1_MQH
#define NORA_PHASE2_ADX_RUNTIME_V1_MQH
bool NoraAdxCompute(const double &h[],const double &l[],const double &c[],const int count,const int period,double &out[],bool &valid[]){
 if(period<1)return false;ArrayResize(out,count);ArrayResize(valid,count);double plus[],minus[],tr[],sp[],sm[],st[],dx[],dv[];ArrayResize(plus,count);ArrayResize(minus,count);ArrayResize(tr,count);ArrayResize(sp,count);ArrayResize(sm,count);ArrayResize(st,count);ArrayResize(dx,count);ArrayResize(dv,count);for(int i=0;i<count;i++){out[i]=0.0;valid[i]=false;plus[i]=0.0;minus[i]=0.0;tr[i]=0.0;sp[i]=0.0;sm[i]=0.0;st[i]=0.0;dx[i]=0.0;dv[i]=false;}
 for(int i=1;i<count;i++){double up=h[i]-h[i-1],dn=l[i-1]-l[i];plus[i]=(up>dn&&up>0.0)?up:0.0;minus[i]=(dn>up&&dn>0.0)?dn:0.0;tr[i]=MathMax(h[i]-l[i],MathMax(MathAbs(h[i]-c[i-1]),MathAbs(l[i]-c[i-1])));}
 if(count<period)return true;sp[period-1]=0.0;sm[period-1]=0.0;st[period-1]=0.0;for(int j=0;j<period;j++){sp[period-1]+=plus[j];sm[period-1]+=minus[j];st[period-1]+=tr[j];}sp[period-1]/=period;sm[period-1]/=period;st[period-1]/=period;
 for(int i=period;i<count;i++){sp[i]=(sp[i-1]*(period-1)+plus[i])/period;sm[i]=(sm[i-1]*(period-1)+minus[i])/period;st[i]=(st[i-1]*(period-1)+tr[i])/period;}
 for(int i=period-1;i<count;i++){if(st[i]==0.0)continue;double denom=sp[i]+sm[i];if(denom==0.0)continue;dx[i]=100.0*MathAbs(sp[i]-sm[i])/denom;dv[i]=true;}
 double seed=0.0;int seen=0;bool seeded=false;double state=0.0;for(int i=0;i<count;i++){if(!dv[i])continue;if(!seeded){seed+=dx[i];seen++;if(seen==period){state=seed/period;out[i]=state;valid[i]=true;seeded=true;}}else{state=(state*(period-1)+dx[i])/period;out[i]=state;valid[i]=true;}}
 return true;}
#endif
