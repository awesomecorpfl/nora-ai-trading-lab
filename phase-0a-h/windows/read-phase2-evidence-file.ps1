[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$LiteralPath,
    [switch]$MetadataOnly,
    # Test mode is deliberately limited to a fixed synthetic-root family.  Normal
    # operation has no caller-selectable evidence root.
    [switch]$SyntheticTest,
    [string]$SyntheticRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$schemaVersion = 'nora.phase2_evidence_raw_read_v2'
$evidenceRoot = 'C:\NoraEvidence\Phase2'
$directorySeparator = [char]0x5c

function Throw-PathError {
    param([Parameter(Mandatory = $true)][string]$Reason)
    throw ("NORA_PATH_REJECTED:{0}" -f $Reason)
}

function Get-CanonicalFilesystemPath {
    param(
        [Parameter(Mandatory = $true)][string]$Value,
        [Parameter(Mandatory = $true)][string]$ParameterName
    )

    if ([string]::IsNullOrWhiteSpace($Value)) { Throw-PathError "$ParameterName.empty" }
    if ($Value.IndexOf([char]0) -ge 0) { Throw-PathError "$ParameterName.null" }
    if ($Value -match '^(\\\\[?.]|\\\\|//)') { Throw-PathError "$ParameterName.unc_or_device" }
    if ($Value -notmatch '^[A-Za-z]:[\\/]') { Throw-PathError "$ParameterName.not_absolute_drive_path" }
    if ($Value.IndexOf(':', 2) -ge 0) { Throw-PathError "$ParameterName.alternate_data_stream" }
    if ($Value -match '(^|[\\/])\.\.([\\/]|$)') { Throw-PathError "$ParameterName.traversal" }

    try {
        $full = [System.IO.Path]::GetFullPath($Value.Replace('/', [string]$directorySeparator))
    } catch {
        Throw-PathError "$ParameterName.malformed"
    }
    if ($full -match '^(\\\\[?.]|\\\\)') { Throw-PathError "$ParameterName.unc_or_device" }
    if ($full -notmatch '^[A-Za-z]:\\') { Throw-PathError "$ParameterName.not_filesystem_path" }
    return $full
}

function Assert-NoReparsePointInPath {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Candidate
    )

    $rootItem = Get-Item -LiteralPath $Root -Force -ErrorAction Stop
    if (($rootItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        Throw-PathError 'root.reparse_point'
    }
    $suffix = $Candidate.Substring($Root.Length).TrimStart($directorySeparator)
    $current = $Root
    foreach ($component in @($suffix.Split($directorySeparator, [System.StringSplitOptions]::RemoveEmptyEntries))) {
        $current = Join-Path -Path $current -ChildPath $component
        $item = Get-Item -LiteralPath $current -Force -ErrorAction Stop
        if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            Throw-PathError 'component.reparse_point'
        }
    }
}

function Get-ApprovedRoot {
    if ($SyntheticTest) {
        if ([string]::IsNullOrWhiteSpace($SyntheticRoot)) { Throw-PathError 'synthetic_root.empty' }
        $synthetic = Get-CanonicalFilesystemPath -Value $SyntheticRoot -ParameterName 'synthetic_root'
        $fixtureBase = 'C:\NoraTransportFixture'
        if ((-not [string]::Equals($synthetic, $fixtureBase, [System.StringComparison]::OrdinalIgnoreCase)) -and
            (-not $synthetic.StartsWith(($fixtureBase + [string]$directorySeparator), [System.StringComparison]::OrdinalIgnoreCase))) {
            Throw-PathError 'synthetic_root.not_permitted'
        }
        return $synthetic.TrimEnd($directorySeparator)
    }
    if (-not [string]::IsNullOrWhiteSpace($SyntheticRoot)) { Throw-PathError 'synthetic_root.without_test_mode' }
    return (Get-CanonicalFilesystemPath -Value $evidenceRoot -ParameterName 'evidence_root').TrimEnd($directorySeparator)
}

try {
    $root = Get-ApprovedRoot
    $candidate = Get-CanonicalFilesystemPath -Value $LiteralPath -ParameterName 'literal_path'
    $rootDrive = [System.IO.Path]::GetPathRoot($root)
    $candidateDrive = [System.IO.Path]::GetPathRoot($candidate)
    if (-not [string]::Equals($rootDrive, $candidateDrive, [System.StringComparison]::OrdinalIgnoreCase)) {
        Throw-PathError 'literal_path.drive_mismatch'
    }
    $rootWithSeparator = $root + [string]$directorySeparator
    if (-not $candidate.StartsWith($rootWithSeparator, [System.StringComparison]::OrdinalIgnoreCase)) {
        Throw-PathError 'literal_path.outside_root'
    }
    Assert-NoReparsePointInPath -Root $root -Candidate $candidate
    $item = Get-Item -LiteralPath $candidate -Force -ErrorAction Stop
    if ($item.PSIsContainer) { Throw-PathError 'literal_path.directory' }
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { Throw-PathError 'literal_path.reparse_point' }

    $metadata = [ordered]@{
        schema_version = $schemaVersion
        canonical_path = $item.FullName
        size = [int64]$item.Length
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $item.FullName -ErrorAction Stop).Hash.ToLowerInvariant()
    }
    if ($MetadataOnly) {
        [Console]::Out.Write(($metadata | ConvertTo-Json -Compress -Depth 4))
        exit 0
    }

    $input = [System.IO.File]::Open($item.FullName, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)
    try {
        $output = [Console]::OpenStandardOutput()
        $buffer = New-Object byte[] 65536
        while (($read = $input.Read($buffer, 0, $buffer.Length)) -gt 0) { $output.Write($buffer, 0, $read) }
        $output.Flush()
    } finally {
        $input.Dispose()
    }
    exit 0
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
