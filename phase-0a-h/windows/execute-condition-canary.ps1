param(
  [Parameter(Mandatory=$true)][string]$IncomingRoot,
  [Parameter(Mandatory=$true)][string]$RunId,
  [string]$RequestedSymbol='GDAXI',
  [string]$ProfileName='NoraPhase2ConditionCanaryV1',
  [int]$TimeoutSeconds=300
)
$ErrorActionPreference='Stop'
$root="$env:USERPROFILE\NoraPhase2J";$run=Join-Path $root $RunId
New-Item -ItemType Directory -Force $run|Out-Null
$terminal='C:\Program Files\Darwinex MetaTrader 5\terminal64.exe'
$resultName='nora_phase2_condition_fixture_v1.csv';$ex5Name='NoraPhase2ConditionFixtureV1.ex5'
$stages=[ordered]@{terminal_started=$false;startup_configuration_loaded=$false;requested_profile=$ProfileName;requested_symbol=$RequestedSymbol;chart_opened=$false;script_loaded=$false;script_started=$false;result_csv_created=$false;script_completed=$false;terminal_shutdown=$false}
function Save-Execution([string]$status,[string]$errorMessage='') {
  $payload=[ordered]@{status=$status;terminal_path=$terminal;terminal_version=(Get-Item $terminal).VersionInfo.FileVersion;profile_name=$ProfileName;requested_symbol=$RequestedSymbol;resolved_broker_symbol=$RequestedSymbol;period='M1';script_name='NoraPhase2ConditionFixtureV1';stages=$stages}
  if($script:process){$payload.terminal_process_id=$script:process.Id;$payload.process_exit_code=$script:process.ExitCode}
  if($errorMessage){$payload.error=$errorMessage}
  $payload|ConvertTo-Json -Depth 8|Set-Content (Join-Path $run 'execution.json') -Encoding utf8
}
function Find-DataRoot {
  $roots=Get-ChildItem "$env:APPDATA\MetaQuotes\Terminal" -Directory|?{(Test-Path (Join-Path $_.FullName 'origin.txt')) -and ((Get-Content (Join-Path $_.FullName 'origin.txt') -Raw).Trim() -eq 'C:\Program Files\Darwinex MetaTrader 5')}
  if(@($roots).Count -ne 1){throw "expected exactly one Darwinex terminal data root; found $(@($roots).Count)"}
  return $roots[0].FullName
}
function Find-Profile([string]$DataRoot) {
  $profileRoot=Join-Path $DataRoot 'MQL5\Profiles\Charts'
  $profile=Join-Path $profileRoot $ProfileName
  if(!(Test-Path $profile)){
    $sourceChart=Get-ChildItem $profileRoot -Directory -ErrorAction SilentlyContinue|%{Get-ChildItem $_.FullName -File -Filter '*.chr' -ErrorAction SilentlyContinue}|select -First 1
    if(!$sourceChart){throw 'no existing chart profile material is available'}
    New-Item -ItemType Directory -Force $profile|Out-Null
    Copy-Item $sourceChart.FullName (Join-Path $profile 'chart01.chr') -Force
    $sourceOrder=Join-Path $sourceChart.Directory.FullName 'order.wnd'
    if(Test-Path $sourceOrder){Copy-Item $sourceOrder (Join-Path $profile 'order.wnd') -Force}
    $script:profile_created=$true
  }
  $charts=@(Get-ChildItem $profile -File -Filter '*.chr' -ErrorAction SilentlyContinue)
  if($charts.Count -eq 0){throw "dedicated profile has no chart: $ProfileName"}
  return $profile
}
function Journal-Text([string]$DataRoot,[datetime]$Before) {
  $paths=@((Join-Path $DataRoot 'logs'),(Join-Path $DataRoot 'MQL5\Logs'))
  $files=$paths|%{Get-ChildItem $_ -File -ErrorAction SilentlyContinue}|sort LastWriteTimeUtc -Descending|select -First 8
  (($files|%{Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue}) -join "`n")
}
if(!(Test-Path $terminal)){throw 'configured terminal64.exe absent'}
$data=$null;$scriptDir=$null;$filesDir=$null;$ex5=$null;$result=$null;$config=Join-Path $run 'execute.ini';$ini=''
$before=(Get-Date).ToUniversalTime()
try {
  $data=Find-DataRoot;$profile=Find-Profile $data
  $scriptDir=Join-Path $data 'MQL5\Scripts\NoraPhase2J';$filesDir=Join-Path $data 'MQL5\Files';New-Item -ItemType Directory -Force $scriptDir,$filesDir|Out-Null
  $ex5=Join-Path $scriptDir $ex5Name;$result=Join-Path $filesDir $resultName
  $existing=@(Get-CimInstance Win32_Process -Filter "Name='terminal64.exe'"|?{$_.ExecutablePath -eq $terminal})
  if($existing.Count -gt 0){throw "unrelated terminal process already owns installation: $($existing.Id -join ',')"}
  if(Test-Path $result){Remove-Item $result -Force};Copy-Item (Join-Path $IncomingRoot $ex5Name) $ex5 -Force
  $ini="[Common]`r`nLogin=0`r`nProxyEnable=0`r`nNewsEnable=0`r`n`r`n[StartUp]`r`nScript=NoraPhase2J\NoraPhase2ConditionFixtureV1`r`nSymbol=$RequestedSymbol`r`nPeriod=M1`r`nShutdownTerminal=1`r`n"
  Set-Content $config $ini -Encoding ascii;$stages.startup_configuration_loaded=$true
  $script:process=Start-Process $terminal -ArgumentList @('/config:"'+$config+'"','/profile:"'+$ProfileName+'"') -PassThru;$stages.terminal_started=$true
  $stages.requested_profile=$ProfileName;$stages.requested_symbol=$RequestedSymbol
  $deadline=(Get-Date).AddSeconds($TimeoutSeconds);$found=$false;$stable=0;$size=0
  while((Get-Date)-lt $deadline){
    $journal=Journal-Text $data $before
    if($journal -match "(?i)(open chart|chart).*$([regex]::Escape($RequestedSymbol))" -and $journal -notmatch '(?i)failed'){ $stages.chart_opened=$true }
    if($journal -match '(?i)(script|NoraPhase2ConditionFixtureV1).*(load|start|run|attached)'){ $stages.script_loaded=$true }
    if($journal -match '(?i)NoraPhase2ConditionFixtureV1.*(start|OnStart)'){ $stages.script_started=$true }
    if(Test-Path $result){$item=Get-Item $result;if($item.Length -gt 0 -and $item.LastWriteTimeUtc -ge $before){$stages.result_csv_created=$true;$newSize=$item.Length;if($newSize -eq $size){$stable++}else{$stable=0};$size=$newSize;if($stable -ge 2){$found=$true;break}}}
    if($script:process.HasExited){$stages.terminal_shutdown=$true;throw 'terminal exited before fresh result CSV was created'}
    Start-Sleep -Milliseconds 250
  }
  if(!$found){throw 'fresh result CSV was not created before timeout'}
  Copy-Item $result (Join-Path $run $resultName) -Force
  $stages.script_completed=$true;$csvPath=Join-Path $run $resultName;$csvSize=(Get-Item $csvPath).Length;$csvSha=(Get-FileHash $csvPath -Algorithm SHA256).Hash.ToLowerInvariant()
  if(!$script:process.HasExited){$script:process.WaitForExit(5000)|Out-Null};$stages.terminal_shutdown=$script:process.HasExited
  if(!$stages.terminal_shutdown){throw 'automation-owned terminal did not honor ShutdownTerminal=1'}
  $journal=Journal-Text $data $before;$journal|Set-Content (Join-Path $run 'terminal-journal.log') -Encoding utf8
  $stages.chart_opened=$stages.chart_opened -or ($journal -match '(?i)chart.*'+[regex]::Escape($RequestedSymbol))
  $stages.script_loaded=$stages.script_loaded -or ($journal -match '(?i)NoraPhase2ConditionFixtureV1')
  $stages.script_started=$stages.script_started -or $stages.script_completed
  $payload=[ordered]@{status='completed';terminal_path=$terminal;terminal_version=(Get-Item $terminal).VersionInfo.FileVersion;terminal_process_id=$script:process.Id;process_exit_code=$script:process.ExitCode;profile_name=$ProfileName;requested_symbol=$RequestedSymbol;resolved_broker_symbol=$RequestedSymbol;period='M1';script_name='NoraPhase2ConditionFixtureV1';config_path=$config;result_filename=$resultName;result_size_bytes=$csvSize;result_sha256=$csvSha;result_fresh=$true;stages=$stages}
  $payload|ConvertTo-Json -Depth 8|Set-Content (Join-Path $run 'execution.json') -Encoding utf8
  "terminal_path=$terminal`nterminal_version=$($payload.terminal_version)`nterminal_process_id=$($script:process.Id)`nprofile_name=$ProfileName`nrequested_symbol=$RequestedSymbol`nresolved_broker_symbol=$RequestedSymbol`nperiod=M1`nscript_name=NoraPhase2ConditionFixtureV1`nconfig=$ini`nresult_fresh=true`nresult_size_bytes=$csvSize`nresult_sha256=$csvSha`nstages=$($stages|ConvertTo-Json -Compress)`n"|Set-Content (Join-Path $run 'execution.log') -Encoding utf8
}
catch { $message=$_.Exception.Message;if($script:process -and !$script:process.HasExited -and $stages.terminal_started){$script:process.CloseMainWindow()|Out-Null;$script:process.WaitForExit(5000)|Out-Null};if($script:process -and !$script:process.HasExited){$stages.terminal_shutdown=$false};if($data){$journal=Journal-Text $data $before;$journal|Set-Content (Join-Path $run 'terminal-journal.log') -Encoding utf8};Save-Execution 'failed' $message;Set-Content (Join-Path $run 'execution.log') ("terminal_path=$terminal`nprofile_name=$ProfileName`nrequested_symbol=$RequestedSymbol`nperiod=M1`nconfig=$ini`nerror=$message`nstages=$($stages|ConvertTo-Json -Compress)`n") -Encoding utf8;exit 2}
finally { if($ex5){Remove-Item $ex5 -Force -ErrorAction SilentlyContinue};if($result){Remove-Item $result -Force -ErrorAction SilentlyContinue};if($scriptDir){Remove-Item $scriptDir -Recurse -Force -ErrorAction SilentlyContinue};if($script:profile_created -and $data){$createdProfile=Join-Path $data ('MQL5\Profiles\Charts\'+$ProfileName);Remove-Item $createdProfile -Recurse -Force -ErrorAction SilentlyContinue} }
