#property strict
#property version   "1.0"
input string NoraProbeOutput="nora_phase2_offline_cache_probe.json";
input string NoraProbeStart="2020.07.01";
input string NoraProbeEnd="2026.07.01";

string J(string s){StringReplace(s,"\\","\\\\");StringReplace(s,"\"","\\\"");return s;}
string T(datetime v){return TimeToString(v,TIME_DATE|TIME_MINUTES|TIME_SECONDS);}
int OnInit(){
 datetime start=StringToTime(NoraProbeStart), finish=StringToTime(NoraProbeEnd);
 MqlRates rates[];ArraySetAsSeries(rates,false);ResetLastError();int copied=CopyRates(_Symbol,PERIOD_M1,start,finish,rates);int copy_error=GetLastError();
 int total=Bars(_Symbol,PERIOD_M1);datetime first=0,last=0;bool duplicate=false,nonmonotonic=false;
 if(copied>0){first=rates[0].time;last=rates[copied-1].time;for(int i=1;i<copied;i++){if(rates[i].time==rates[i-1].time)duplicate=true;if(rates[i].time<rates[i-1].time)nonmonotonic=true;}}
 long synchronized=0;SeriesInfoInteger(_Symbol,PERIOD_M1,SERIES_SYNCHRONIZED,synchronized);
 int handle=FileOpen(NoraProbeOutput,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON);if(handle==INVALID_HANDLE){Print("NORA_CACHE_PROBE_FAIL_FILE");return INIT_FAILED;}
 string json="{\"schema_version\":\"nora.phase2_mt5_cache_probe_v1\",\"symbol\":\""+J(_Symbol)+"\",\"timeframe\":\"M1\",\"requested_start\":\""+T(start)+"\",\"requested_end\":\""+T(finish)+"\",\"total_available_m1_bars\":"+(string)total+",\"returned_requested_interval_bars\":"+(string)copied+",\"first_returned_timestamp\":\""+T(first)+"\",\"last_returned_timestamp\":\""+T(last)+"\",\"duplicate_timestamps\":"+(duplicate?"true":"false")+",\"nonmonotonic_timestamps\":"+(nonmonotonic?"true":"false")+",\"copy_error\":"+(string)copy_error+",\"series_synchronized\":"+(synchronized!=0?"true":"false")+"}";FileWriteString(handle,json);FileClose(handle);Print("NORA_CACHE_PROBE_COMPLETE_V1");TesterStop();return INIT_SUCCEEDED;
}
