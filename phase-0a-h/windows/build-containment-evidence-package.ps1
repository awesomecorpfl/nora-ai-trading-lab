[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$SourceRoot,
    [Parameter(Mandatory=$true)][string]$SummaryPath,
    [Parameter(Mandatory=$true)][string]$DestinationPath,
    [Parameter(Mandatory=$true)][string]$EvidenceRoot,
    [Parameter(Mandatory=$true)][string]$ExpectedRunId
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$schema = 'nora.phase2_containment_atomic_evidence_v1'
$required = @('stdout.txt','stderr.txt','pre_state.json','post_state.json','firewall_pre.json','firewall_post.json','processes.json','recovery.json','cleanup.json')
$sep = [char]0x5c
function Fail([string]$Message) { throw "NORA_EVIDENCE_PACKAGE:$Message" }
function Hash([string]$Path) { (Get-FileHash -Algorithm SHA256 -LiteralPath $Path -ErrorAction Stop).Hash.ToLowerInvariant() }
function Canonical([string]$Value,[string]$Name) {
    if ([string]::IsNullOrWhiteSpace($Value) -or $Value.IndexOf([char]0) -ge 0) { Fail "$Name.invalid" }
    if ($Value -match '^(\\\\|//|\\\\\?\\)' -or $Value -notmatch '^[A-Za-z]:[\\/]') { Fail "$Name.not_absolute" }
    if ($Value -match '(^|[\\/])\.\.([\\/]|$)' -or $Value.IndexOf(':',2) -ge 0) { Fail "$Name.unsafe" }
    try { $full=[IO.Path]::GetFullPath($Value.Replace('/',[string]$sep)) } catch { Fail "$Name.malformed" }
    return $full.TrimEnd($sep)
}
function Inside([string]$Root,[string]$Candidate) {
    $drive=[IO.Path]::GetPathRoot($Root); $candidateDrive=[IO.Path]::GetPathRoot($Candidate)
    if (-not [string]::Equals($drive,$candidateDrive,[StringComparison]::OrdinalIgnoreCase)) { Fail 'drive_mismatch' }
    if (-not $Candidate.StartsWith($Root + [string]$sep,[StringComparison]::OrdinalIgnoreCase)) { Fail 'outside_root' }
    $item=Get-Item -LiteralPath $Root -Force -ErrorAction Stop
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { Fail 'root_reparse' }
    $suffix=$Candidate.Substring($Root.Length).TrimStart($sep); $current=$Root
    foreach($component in @($suffix.Split($sep,[StringSplitOptions]::RemoveEmptyEntries))) {
        $current=Join-Path $current $component; $part=Get-Item -LiteralPath $current -Force -ErrorAction Stop
        if (($part.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { Fail 'component_reparse' }
    }
}
function CanonicalJson([object]$Value) { $Value | ConvertTo-Json -Compress -Depth 64 }

$root=Canonical $EvidenceRoot 'EvidenceRoot'; $source=Canonical $SourceRoot 'SourceRoot'; $summaryFile=Canonical $SummaryPath 'SummaryPath'; $destination=Canonical $DestinationPath 'DestinationPath'
Inside $root $source; Inside $root $summaryFile; if ($destination -notlike "$root$sep*") { Fail 'destination_outside_root' }
if (-not (Test-Path -LiteralPath $source -PathType Container)) { Fail 'source_missing' }
if (-not (Test-Path -LiteralPath $summaryFile -PathType Leaf)) { Fail 'summary_missing' }
$summary=Get-Content -LiteralPath $summaryFile -Raw | ConvertFrom-Json
$summary | Add-Member -NotePropertyName schema -NotePropertyValue $schema -Force
foreach($field in @('run_id','case_id','operation_id','repository_commit','transaction_identity')) { if ([string]::IsNullOrWhiteSpace([string]$summary.$field)) { Fail "summary_$field" } }
if ($ExpectedRunId -and $summary.run_id -ne $ExpectedRunId) { Fail 'summary_run_id_mismatch' }
if ($summary.case_id -ne $summary.run_id) { Fail 'summary_case_run_mismatch' }
foreach($field in @('executable_paths','executable_hashes','rule_guids','rule_names','application_filters')) { if ($null -eq $summary.$field -or $summary.$field -is [string]) { Fail "summary_$field_array" } }
if ($summary.final_caller_exit_code -isnot [int]) { Fail 'summary_exit_code' }
$files=@(); foreach($item in @(Get-ChildItem -LiteralPath $source -Recurse -File -Force | Sort-Object FullName)) {
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { Fail 'member_reparse' }
    $rel=$item.FullName.Substring($source.Length).TrimStart($sep).Replace($sep,'/')
    if ($rel -in @('summary.json','manifest.json')) { Fail 'reserved_member' }
    $files += [pscustomobject]@{path=$rel;size=[int64]$item.Length;sha256=(Hash $item.FullName)}
}
foreach($need in $required) { if (-not @($files | Where-Object path -eq $need).Count) { Fail "missing_member_$need" } }
$manifest=[ordered]@{schema=$schema;run_id=[string]$summary.run_id;case_id=[string]$summary.case_id;operation_id=[string]$summary.operation_id;repository_commit=[string]$summary.repository_commit;members=@($files)}
$parent=[IO.Directory]::GetParent($destination).FullName; New-Item -ItemType Directory -Force -Path $parent | Out-Null
$partial="$destination.partial.$([guid]::NewGuid().ToString('N'))"; $zip=$null
try {
    $zip=[IO.File]::Open($partial,[IO.FileMode]::CreateNew,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
    $archive=New-Object IO.Compression.ZipArchive($zip,[IO.Compression.ZipArchiveMode]::Create,$true)
    foreach($entry in @([pscustomobject]@{path='summary.json';bytes=[Text.Encoding]::UTF8.GetBytes((CanonicalJson $summary)+"`n")},[pscustomobject]@{path='manifest.json';bytes=[Text.Encoding]::UTF8.GetBytes((CanonicalJson $manifest)+"`n")})) { $e=$archive.CreateEntry($entry.path,[IO.Compression.CompressionLevel]::NoCompression);$e.LastWriteTime=[DateTimeOffset]::new(1980,1,1,0,0,0,[TimeSpan]::Zero);$s=$e.Open();$s.Write($entry.bytes,0,$entry.bytes.Length);$s.Dispose() }
    foreach($file in $files) { $e=$archive.CreateEntry($file.path,[IO.Compression.CompressionLevel]::NoCompression);$e.LastWriteTime=[DateTimeOffset]::new(1980,1,1,0,0,0,[TimeSpan]::Zero);$input=[IO.File]::OpenRead((Join-Path $source ($file.path.Replace('/',[string]$sep))));$output=$e.Open();$input.CopyTo($output);$output.Dispose();$input.Dispose() }
    $archive.Dispose();$zip.Flush();$zip.Flush($true);$zip.Dispose();$zip=$null
    if (Test-Path -LiteralPath $destination) { if ((Hash $destination) -ne (Hash $partial)) { Fail 'conflicting_duplicate' }; Remove-Item -LiteralPath $partial -Force; Write-Output (Hash $destination); exit 0 }
    Move-Item -LiteralPath $partial -Destination $destination
    Write-Output (Hash $destination)
} finally { if ($zip) { $zip.Dispose() }; if (Test-Path -LiteralPath $partial) { Remove-Item -LiteralPath $partial -Force -ErrorAction SilentlyContinue } }
