Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'

function New-NoraFreshVerifierArgumentVector {
 param(
  [Parameter(Mandatory=$true)][string]$VerifierPath,
  [Parameter(Mandatory=$true)][string]$FinalRecordPath,
  [Parameter(Mandatory=$true)][string]$ExpectedFinalRecordSha256,
  [Parameter(Mandatory=$true)][string]$EvidenceRoot
 )
 if([string]::IsNullOrWhiteSpace($VerifierPath) -or [string]::IsNullOrWhiteSpace($FinalRecordPath) -or [string]::IsNullOrWhiteSpace($EvidenceRoot)){throw 'fresh verifier argument value missing'}
 if($ExpectedFinalRecordSha256 -notmatch '^[0-9a-fA-F]{64}$'){throw 'fresh verifier hash invalid'}
 [string[]]$tokens=@('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',$VerifierPath,'-FinalRecordPath',$FinalRecordPath,'-ExpectedFinalRecordSha256',$ExpectedFinalRecordSha256.ToLowerInvariant(),'-EvidenceRoot',$EvidenceRoot)
 Assert-NoraFreshVerifierArgumentVector -Tokens $tokens -ExpectedFinalRecordPath $FinalRecordPath
 return $tokens
}

function Assert-NoraFreshVerifierArgumentVector {
 param(
  [Parameter(Mandatory=$true)][string[]]$Tokens,
  [Parameter(Mandatory=$true)][string]$ExpectedFinalRecordPath
 )
 $pathIndexes=@(for($i=0;$i-lt$tokens.Count;$i++){if($tokens[$i]-eq '-FinalRecordPath'){$i}})
 if($pathIndexes.Count-ne 1){throw 'fresh verifier path binding is not unique'}
 if($pathIndexes[0]+1-ge$tokens.Count -or [string]::IsNullOrWhiteSpace($tokens[$pathIndexes[0]+1]) -or $tokens[$pathIndexes[0]+1] -ne $ExpectedFinalRecordPath){throw 'fresh verifier path value missing or mismatched'}
 if(@($tokens|Where-Object{$_ -eq '-LiteralPath'}).Count-ne 0){throw 'unexpected LiteralPath token in child invocation'}
}
