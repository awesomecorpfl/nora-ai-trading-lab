#ifndef NORA_PHASE2_LINEAR_REGRESSION_RUNTIME_V1_MQH
#define NORA_PHASE2_LINEAR_REGRESSION_RUNTIME_V1_MQH
bool NoraLinearRegressionCompute(const double &x[],const int count,const int period,double &value[],double &slope[],bool &valid[]){if(period<2)return false;ArrayResize(value,count);ArrayResize(slope,count);ArrayResize(valid,count);for(int i=0;i<count;i++){value[i]=0.0;slope[i]=0.0;valid[i]=false;}double sx=period*(period-1)/2.0;double sxx=period*(period-1)*(2*period-1)/6.0;double den=period*sxx-sx*sx;for(int i=period-1;i<count;i++){double sy=0.0,sxy=0.0;for(int j=0;j<period;j++){sy+=x[i-period+1+j];sxy+=j*x[i-period+1+j];}double b=(period*sxy-sx*sy)/den;double v=(sy-b*sx)/period+b*(period-1);value[i]=v;slope[i]=b;valid[i]=true;}return true;}
#endif
