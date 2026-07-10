#property strict
input string CustomName="NORA_FIXED";
input string FixtureName="NoraPhase0AH\\fixture.csv";
string out="NoraPhase0AH\\import.json";
void Fail(string m){int h=FileOpen(out,FILE_WRITE|FILE_TXT|FILE_COMMON);if(h!=INVALID_HANDLE){FileWriteString(h,"{\"ok\":false,\"error\":\""+m+"\"}");FileClose(h);} TerminalClose(0);}
void OnStart(){
 int f=FileOpen(FixtureName,FILE_READ|FILE_CSV|FILE_COMMON,','); if(f==INVALID_HANDLE){Fail("fixture_open");return;}
 MqlRates r[]; ArrayResize(r,0); while(!FileIsEnding(f)){string t=FileReadString(f); if(t=="time") {for(int i=0;i<7;i++)FileReadString(f);continue;} int n=ArraySize(r);ArrayResize(r,n+1);r[n].time=StringToTime(t);r[n].open=StringToDouble(FileReadString(f));r[n].high=StringToDouble(FileReadString(f));r[n].low=StringToDouble(FileReadString(f));r[n].close=StringToDouble(FileReadString(f));r[n].tick_volume=(long)StringToInteger(FileReadString(f));r[n].spread=(int)StringToInteger(FileReadString(f));r[n].real_volume=0;} FileClose(f);
 if(ArraySize(r)<5){Fail("fixture_short");return;} ResetLastError(); if(!CustomSymbolCreate(CustomName,"NoraPhase0AH",NULL) && GetLastError()!=5304){Fail("create");return;}
 CustomSymbolSetInteger(CustomName,SYMBOL_DIGITS,2); CustomSymbolSetDouble(CustomName,SYMBOL_POINT,0.01); CustomSymbolSetDouble(CustomName,SYMBOL_TRADE_TICK_SIZE,0.01); CustomSymbolSetDouble(CustomName,SYMBOL_TRADE_TICK_VALUE,1.0); CustomSymbolSetInteger(CustomName,SYMBOL_TRADE_CALC_MODE,SYMBOL_CALC_MODE_CFD); CustomSymbolSetString(CustomName,SYMBOL_CURRENCY_BASE,"USD"); CustomSymbolSetString(CustomName,SYMBOL_CURRENCY_PROFIT,"USD"); CustomSymbolSetString(CustomName,SYMBOL_CURRENCY_MARGIN,"USD"); SymbolSelect(CustomName,true);
 int changed=CustomRatesReplace(CustomName,r[0].time,r[ArraySize(r)-1].time,r); if(changed!=ArraySize(r)){Fail("replace");return;} int h=FileOpen(out,FILE_WRITE|FILE_TXT|FILE_COMMON);FileWriteString(h,"{\"ok\":true,\"symbol\":\""+CustomName+"\",\"bars\":"+(string)changed+"}");FileClose(h); TerminalClose(0);
}
