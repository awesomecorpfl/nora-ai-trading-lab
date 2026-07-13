#property strict
#include "NoraPhase2MacdRuntimeV3.mqh"
#define NORA_MACD_ROWS 12
const string NORA_MACD_CSV="nora_phase2u_macd_tester_v3.csv";
const string NORA_MACD_COMPLETION="NORA_PHASE2U_MACD_COMPLETE_V3";
double close_values[NORA_MACD_ROWS]={1.1003,1.1009,1.1006,1.1013,1.101,1.1017,1.1014,1.1021,1.1018,1.1025,1.1022,1.1029};
bool close_null[NORA_MACD_ROWS]={false,false,false,false,false,false,false,false,false,false,false,false};
double expected_macd[NORA_MACD_ROWS]={0.0,0.0,0.0,0.00029166666666657903,0.000157222222222142,0.00027507407407401097,0.0001452913580246573,0.0002672571193416129,0.0001403817064473678,0.0002642381688158224,0.00013854594960549527,0.0002631285858685217};
bool expected_macd_null[NORA_MACD_ROWS]={true,true,true,false,false,false,false,false,false,false,false,false};
double expected_signal[NORA_MACD_ROWS]={0.0,0.0,0.0,0.0,0.0,0.000241320987654244,0.00019330617283945067,0.00023028164609053178,0.0001853316762689498,0.0002247849225423861,0.0001816654360739407,0.0002223970109712312};
bool expected_signal_null[NORA_MACD_ROWS]={true,true,true,true,true,false,false,false,false,false,false,false};
double expected_hist[NORA_MACD_ROWS]={0.0,0.0,0.0,0.0,0.0,3.375308641976696e-05,-4.801481481479336e-05,3.697547325108111e-05,-4.4949969821582e-05,3.94532462734363e-05,-4.311948646844543e-05,4.073157489729051e-05};
bool expected_hist_null[NORA_MACD_ROWS]={true,true,true,true,true,false,false,false,false,false,false,false};
string NoraMacdCsv(const double value,const bool is_null){if(is_null)return "NULL";return DoubleToString(value,17);}
int OnInit(){double macd[],signal[],hist[];bool mn[],sn[],hn[];ArrayResize(macd,NORA_MACD_ROWS);ArrayResize(signal,NORA_MACD_ROWS);ArrayResize(hist,NORA_MACD_ROWS);ArrayResize(mn,NORA_MACD_ROWS);ArrayResize(sn,NORA_MACD_ROWS);ArrayResize(hn,NORA_MACD_ROWS);if(!NoraPhase2MacdCompute(close_values,close_null,NORA_MACD_ROWS,macd,mn,signal,sn,hist,hn)){Print("NORA_PHASE2U_MACD_FAIL");return INIT_FAILED;}int f=FileOpen(NORA_MACD_CSV,FILE_WRITE|FILE_CSV|FILE_ANSI);if(f==INVALID_HANDLE){Print("NORA_PHASE2U_MACD_FAIL");return INIT_FAILED;}FileWrite(f,"row","close","macd","signal","histogram","pass");for(int i=0;i<NORA_MACD_ROWS;i++){bool ok=(mn[i]==expected_macd_null[i]&&sn[i]==expected_signal_null[i]&&hn[i]==expected_hist_null[i]&& (mn[i]||MathAbs(macd[i]-expected_macd[i])<=1e-12)&& (sn[i]||MathAbs(signal[i]-expected_signal[i])<=1e-12)&& (hn[i]||MathAbs(hist[i]-expected_hist[i])<=1e-12));FileWrite(f,i,NoraMacdCsv(close_values[i],close_null[i]),NoraMacdCsv(macd[i],mn[i]),NoraMacdCsv(signal[i],sn[i]),NoraMacdCsv(hist[i],hn[i]),ok?"true":"false");if(!ok){FileClose(f);Print("NORA_PHASE2U_MACD_FAIL");return INIT_FAILED;}}FileClose(f);Print("NORA_PHASE2U_MACD_COMPLETE_V3");return INIT_SUCCEEDED;}
void OnDeinit(const int reason){}
