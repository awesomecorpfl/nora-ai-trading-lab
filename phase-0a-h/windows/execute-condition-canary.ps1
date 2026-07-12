param(
  [Parameter(Mandatory=$true)][string]$IncomingRoot,
  [Parameter(Mandatory=$true)][string]$RunId,
  [int]$TimeoutSeconds=300
)
$ErrorActionPreference='Stop'
$root="$env:USERPROFILE\NoraPhase2J";$run=Join-Path $root $RunId;New-Item -ItemType Directory -Force $run|Out-Null
$terminal='C:\Program Files\Darwinex MetaTrader 5\terminal64.exe';if(!(Test-Path $terminal)){throw 'configured terminal64.exe absent'}
$data=(Get-ChildItem "$env:APPDATA\MetaQuotes\Terminal" -Directory|?{Test-Path "$($_.FullName)\origin.txt"}|select -First 1).FullName;if(!$data){throw 'terminal data root absent'}
$scriptDir=Join-Path $data 'MQL5\Scripts\NoraPhase2J';$filesDir=Join-Path $data 'MQL5\Files';New-Item -ItemType Directory -Force $scriptDir|Out-Null;New-Item -ItemType Directory -Force $filesDir|Out-Null
$ex5Name='NoraPhase2ConditionFixtureV1.ex5';$resultName='nora_phase2_condition_fixture_v1.csv';$ex5=Join-Path $scriptDir $ex5Name;$result=Join-Path $filesDir $resultName
if(Test-Path $result){Remove-Item $result -Force}
Copy-Item (Join-Path $IncomingRoot $ex5Name) $ex5 -Force
$config=Join-Path $run 'execute.ini';@"
[Common]
Login=0
ProxyEnable=0
NewsEnable=0

[StartUp]
Script=NoraPhase2J\\NoraPhase2ConditionFixtureV1
Symbol=EURUSD
Period=M1
"@|Set-Content $config -Encoding ascii
$before=(Get-Date).ToUniversalTime();$process=Start-Process $terminal -ArgumentList ('/config:"'+$config+'"') -PassThru
$found=$false;$stable=0;$size=0
try {
  $deadline=(Get-Date).AddSeconds($TimeoutSeconds)
  while((Get-Date) -lt $deadline){
    if(Test-Path $result){$item=Get-Item $result;if($item.Length -gt 0 -and $item.LastWriteTimeUtc -ge $before){$newSize=$item.Length;if($newSize -eq $size){$stable++}else{$stable=0};$size=$newSize;if($stable -ge 2){$found=$true;break}}}
    if($process.HasExited){throw 'terminal exited before fresh result CSV was created'}
    Start-Sleep -Milliseconds 250
  }
  if(!$found){throw 'fresh result CSV was not created before timeout'}
  Start-Sleep -Milliseconds 250
  Copy-Item $result (Join-Path $run $resultName) -Force
  $csvSize=(Get-Item (Join-Path $run $resultName)).Length;$csvSha=(Get-FileHash (Join-Path $run $resultName) -Algorithm SHA256).Hash.ToLowerInvariant()
  if($process -and !$process.HasExited){Stop-Process -Id $process.Id -Force}
  $terminalVersion=(Get-Item $terminal).VersionInfo.FileVersion
  $log="terminal_path=$terminal`nterminal_version=$terminalVersion`nprocess_exit_code=$($process.ExitCode)`nresult_fresh=true`nresult_size_bytes=$csvSize`nresult_sha256=$csvSha`n"
  Set-Content (Join-Path $run 'execution.log') $log -Encoding utf8
  $payload=[ordered]@{status='completed';terminal_path=$terminal;terminal_version=$terminalVersion;process_exit_code=$process.ExitCode;result_filename=$resultName;result_size_bytes=$csvSize;result_sha256=$csvSha;result_fresh=$true}
  $payload|ConvertTo-Json -Compress|Set-Content (Join-Path $run 'execution.json') -Encoding utf8
}
catch {
  if($process -and !$process.HasExited){Stop-Process -Id $process.Id -Force}
  $message=$_.Exception.Message;Set-Content (Join-Path $run 'execution.log') ("terminal_path=$terminal`nerror=$message`nresult_fresh=false`n") -Encoding utf8
  $payload=[ordered]@{status='failed';terminal_path=$terminal;terminal_version=(Get-Item $terminal).VersionInfo.FileVersion;process_exit_code=if($process){$process.ExitCode}else{-1};error=$message;result_filename=$resultName;result_fresh=$false}
  $payload|ConvertTo-Json -Compress|Set-Content (Join-Path $run 'execution.json') -Encoding utf8
  exit 2
}
finally {
  Remove-Item $ex5 -Force -ErrorAction SilentlyContinue
  Remove-Item $result -Force -ErrorAction SilentlyContinue
  Remove-Item $scriptDir -Recurse -Force -ErrorAction SilentlyContinue
}
