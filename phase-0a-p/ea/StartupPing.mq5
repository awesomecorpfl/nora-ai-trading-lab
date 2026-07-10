#property strict
void OnStart(){int h=FileOpen("NoraPhase0AP\\startup.json",FILE_WRITE|FILE_TXT|FILE_COMMON);if(h!=INVALID_HANDLE){FileWriteString(h,"{\"ok\":true}");FileClose(h);}TerminalClose(0);}
