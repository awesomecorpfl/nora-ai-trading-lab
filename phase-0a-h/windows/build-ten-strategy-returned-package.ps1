param([Parameter(Mandatory=$true)][string]$RunDirectory,[Parameter(Mandatory=$true)][string]$Destination)
$ErrorActionPreference='Stop'
function Hash([string]$Path){(Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()}
$required=@('execution.json','nora_phase2_ten_strategy_v1.csv','terminal-journal.log','tester-journal.log','tester.htm','completion-marker.json','failure-marker.json','environment-before.json','environment-after.json','environmental-evaluation.json')
foreach($name in $required){if(!(Test-Path -LiteralPath (Join-Path $RunDirectory $name) -PathType Leaf)){throw "missing returned artifact $name"}}
if(Test-Path -LiteralPath $Destination){throw 'occupied destination'}
$temporary=$Destination+'.partial.'+[guid]::NewGuid().ToString('N');New-Item -ItemType Directory -Path $temporary|Out-Null
try{
 $inventory=@()
 foreach($name in $required){$source=Join-Path $RunDirectory $name;Copy-Item -LiteralPath $source -Destination (Join-Path $temporary $name);$inventory += [ordered]@{path=$name;size=(Get-Item -LiteralPath $source).Length;sha256=Hash $source}}
 $inventory|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $temporary 'returned_inventory.json') -Encoding utf8
 $execution=Get-Content -LiteralPath (Join-Path $temporary 'execution.json') -Raw|ConvertFrom-Json
 $manifest=[ordered]@{schema_version='nora.ten_strategy_atomic_returned_package_v2';target_identifier='phase2_ten_strategy_suite';run_identifier=$execution.run_identifier;execution_packet_identity=$execution.execution_packet_identity;final_batch_identity=$execution.final_batch_identity;host_symbol=$execution.host_symbol;timeframe=$execution.timeframe;returned_inventory_sha256=Hash (Join-Path $temporary 'returned_inventory.json')}
 $manifest|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $temporary 'returned_result_manifest.json') -Encoding utf8
 Move-Item -LiteralPath $temporary -Destination $Destination
}catch{Remove-Item -LiteralPath $temporary -Recurse -Force -ErrorAction SilentlyContinue;throw}
