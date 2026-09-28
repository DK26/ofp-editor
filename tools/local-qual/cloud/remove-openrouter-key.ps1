<#
.SYNOPSIS
Deletes the OpenRouter key stored by set-openrouter-key.ps1.

.DESCRIPTION
Overwrites the DPAPI key file with zeros and deletes it. This does not revoke the key at OpenRouter: delete the key
in the OpenRouter dashboard as well (Settings, API Keys), which is what makes it useless everywhere.

Exit codes: 0 deleted or nothing to delete; 2 failed.

.PARAMETER SecretPath
The key file. Default: %LOCALAPPDATA%\plotroom-dev\secrets\openrouter.key.

.EXAMPLE
powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\remove-openrouter-key.ps1
#>
[CmdletBinding(PositionalBinding = $false)]
param(
    [string]$SecretPath = ''
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'secret-common.ps1')

try {
    if (-not $SecretPath) { $SecretPath = Get-DefaultSecretPath }
    $full = Resolve-FullPath $SecretPath
    if (Test-Path -LiteralPath $full) {
        # The blob is useless without this user's DPAPI keys; the overwrite just leaves nothing behind to copy.
        $length = (Get-Item -LiteralPath $full -Force).Length
        [System.IO.File]::WriteAllBytes($full, (New-Object byte[] $length))
        Remove-Item -LiteralPath $full -Force
        Write-Host "Deleted the stored key at $full."
    } else {
        Write-Host "No stored key at $full."
    }
    Write-Host 'Revoke the key at OpenRouter too: dashboard, Settings, API Keys, delete it.'
    exit 0
} catch {
    [Console]::Error.WriteLine("remove-openrouter-key: $($_.Exception.Message)")
    exit 2
}
