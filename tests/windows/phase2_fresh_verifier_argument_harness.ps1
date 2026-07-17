[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$HelperPath)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. $HelperPath
$root=Join-Path ([IO.Path]::GetTempPath()) ('nora-frt1r2 argument '+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $root -Force|Out-Null
try {
  $verifier=Join-Path $root 'fresh verifier.ps1'
  @'
[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][string]$FinalRecordPath,
 [Parameter(Mandatory=$true)][string]$ExpectedFinalRecordSha256,
 [Parameter(Mandatory=$true)][string]$EvidenceRoot
)
Set-StrictMode -Version Latest
[ordered]@{final=$FinalRecordPath;hash=$ExpectedFinalRecordSha256;root=$EvidenceRoot}|ConvertTo-Json -Compress
'@ | Set-Content -LiteralPath $verifier -Encoding utf8
  $final=Join-Path $root 'final record.json'
  $evidence=Join-Path $root 'evidence root'
  New-Item -ItemType Directory -Path $evidence -Force|Out-Null
  $tokens=@(New-NoraFreshVerifierArgumentVector -VerifierPath $verifier -FinalRecordPath $final -ExpectedFinalRecordSha256 ('a'*64) -EvidenceRoot $evidence)
  $pathFlags=@(for($i=0;$i-lt$tokens.Count;$i++){if($tokens[$i] -eq '-FinalRecordPath'){$i}})
  if($pathFlags.Count-ne1 -or $tokens[$pathFlags[0]+1] -ne $final){throw 'argument vector path binding failed'}
  if(@($tokens|Where-Object{$_ -eq '-LiteralPath'}).Count-ne0){throw 'unexpected LiteralPath token'}
  $output=@(& powershell.exe @tokens 2>&1)
  if($LASTEXITCODE-ne0){throw ('synthetic verifier failed: '+($output -join "`n"))}
  $decoded=$output -join "`n"|ConvertFrom-Json
  if($decoded.final-ne$final -or $decoded.root-ne$evidence -or $decoded.hash-ne('a'*64)){throw 'synthetic verifier binding mismatch'}
  $conflicting=@($tokens[0..($tokens.Count-1)] + @('-LiteralPath',$final,'-LiteralPath',$evidence))
  $literalCount=@($conflicting|Where-Object{$_ -eq '-LiteralPath'}).Count
  if($literalCount-ne2){throw 'conflict fixture was not constructed'}
  $rejected=$false
  try { Assert-NoraFreshVerifierArgumentVector -Tokens $conflicting -ExpectedFinalRecordPath $final } catch { $rejected=$true }
  if(!$rejected){throw 'conflicting path vector was accepted'}
  [ordered]@{status='PASS';literal_path_tokens=$literalCount;authoritative_path_parameter_count=$pathFlags.Count;final_record_path=$final;conflicting_vector_rejected=$rejected}|ConvertTo-Json -Compress
} finally {
  if(Test-Path -LiteralPath $root){Remove-Item -LiteralPath $root -Recurse -Force}
}
