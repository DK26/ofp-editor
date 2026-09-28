<#
.SYNOPSIS
Deletes the Groq key stored by set-groq-key.ps1.

.DESCRIPTION
Overwrites the DPAPI key file with zeros and deletes it. This does not revoke the key at Groq: delete it at
https://console.groq.com/keys as well, which is what makes it useless everywhere.

Exit codes: 0 deleted or nothing to delete; 2 failed.

.PARAMETER SecretPath
The key file. Default: %LOCALAPPDATA%\plotroom-dev\secrets\groq.key.

.EXAMPLE
powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\remove-groq-key.ps1
#>
[CmdletBinding(PositionalBinding = $false)]
param(
    [string]$SecretPath = ''
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'secret-common.ps1')

try {
    if (-not $SecretPath) { $SecretPath = Join-Path (Split-Path -Parent (Get-DefaultSecretPath)) 'groq.key' }
    $full = Resolve-FullPath $SecretPath
    if (Test-Path -LiteralPath $full) {
        $length = (Get-Item -LiteralPath $full -Force).Length
        [System.IO.File]::WriteAllBytes($full, (New-Object byte[] $length))
        Remove-Item -LiteralPath $full -Force
        Write-Host "Deleted the stored Groq key at $full."
    } else {
        Write-Host "No stored Groq key at $full."
    }
    Write-Host 'Revoke the key at Groq too: https://console.groq.com/keys, delete it.'
    exit 0
} catch {
    [Console]::Error.WriteLine("remove-groq-key: $($_.Exception.Message)")
    exit 2
}
