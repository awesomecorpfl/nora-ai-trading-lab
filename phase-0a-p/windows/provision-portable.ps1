$ErrorActionPreference='Stop'
$src='C:\Program Files\Darwinex MetaTrader 5';$root="$env:USERPROFILE\NoraMt5Portable";$app="$root\app";New-Item -ItemType Directory -Force $root|Out-Null
function M($p){Get-ChildItem $p -File -Recurse|Sort FullName|%{[pscustomobject]@{p=$_.FullName;l=$_.Length;h=(Get-FileHash $_.FullName -Algorithm SHA256).Hash}}}
$orig=(Get-ChildItem "$env:APPDATA\MetaQuotes\Terminal" -Directory|?{Test-Path "$($_.FullName)\origin.txt"}|select -First 1).FullName;M $orig|ConvertTo-Json -Depth 3|Set-Content "$root\darwinex-before.json"
if(!(Test-Path "$app\terminal64.exe")){robocopy $src $app /E /COPY:DAT /R:1 /W:1 /NFL /NDL /NJH /NJS /NP;if($LASTEXITCODE -gt 7){throw "robocopy $LASTEXITCODE"}}
M $app|ConvertTo-Json -Depth 3|Set-Content "$root\portable-app-manifest.json";[pscustomobject]@{app=$app;terminal="$app\terminal64.exe";portable_data=$app;source_data=$orig;source_before=(Get-FileHash "$root\darwinex-before.json").Hash}|ConvertTo-Json|Set-Content "$root\provision.json";Get-Content "$root\provision.json"
