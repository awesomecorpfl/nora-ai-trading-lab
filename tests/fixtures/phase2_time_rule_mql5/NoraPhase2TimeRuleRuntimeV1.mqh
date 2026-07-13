#ifndef NORA_PHASE2_TIME_RULE_RUNTIME_V1_MQH
#define NORA_PHASE2_TIME_RULE_RUNTIME_V1_MQH
bool NoraLeap(const int y){return (y%4==0 && (y%100!=0 || y%400==0));}
int NoraDays(const int y,const int m){int d[12]={31,28,31,30,31,30,31,31,30,31,30,31};return m==2&&NoraLeap(y)?29:d[m-1];}
int NoraSunday(const int y,const int m,const int nth){MqlDateTime q;ZeroMemory(q);q.year=y;q.mon=m;q.day=1;datetime t=StructToTime(q);TimeToStruct(t,q);return 1+((7-q.day_of_week)%7)+7*(nth-1);}
bool NoraDst(const long epoch){MqlDateTime u;TimeToStruct((datetime)epoch,u);int start=NoraSunday(u.year,3,2),end=NoraSunday(u.year,11,1);MqlDateTime q;ZeroMemory(q);q.year=u.year;q.mon=3;q.day=start;q.hour=7;long a=(long)StructToTime(q);ZeroMemory(q);q.year=u.year;q.mon=11;q.day=end;q.hour=6;long b=(long)StructToTime(q);return epoch>=a&&epoch<b;}
void NoraCivil(const long epoch,const int offset,MqlDateTime &o){TimeToStruct((datetime)(epoch+offset),o);}
bool NoraWindow(const MqlDateTime &x,const int sh,const int sm,const int eh,const int em){int z=x.hour*60+x.min,a=sh*60+sm,b=eh*60+em;return a<=b?(z>=a&&z<b):(z>=a||z<b);}
string NoraStamp(const MqlDateTime &x){return StringFormat("%04d-%02d-%02d %02d:%02d",x.year,x.mon,x.day,x.hour,x.min);}
#endif
