<#
.SYNOPSIS
Deletes the Cloudflare token and account id stored by set-cloudflare-token.ps1.

.DESCRIPTION
Overwrites both DPAPI files with zeros and deletes them. This does not revoke the token at Cloudflare: delete it under
Manage account -> Account API tokens (or My Profile -> API Tokens for a cfut_ token) as well.

Exit codes: 0 deleted or nothing to delete; 2 failed.

.PARAMETER SecretPath
The token file. Default: %LOCALAPPDATA%\plotroom-dev\secrets\cloudflare.key; cloudflare-account.key in the same folder
goes with it.

.EXAMPLE
powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\remove-cloudflare-token.ps1
#>
[CmdletBinding(PositionalBinding = $false)]
param(
    [string]$SecretPath = ''
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'secret-common.ps1')

try {
    if (-not $SecretPath) { $SecretPath = Join-Path (Split-Path -Parent (Get-DefaultSecretPath)) 'cloudflare.key' }
    $full = Resolve-FullPath $SecretPath
    foreach ($path in @($full, (Join-Path (Split-Path -Parent $full) 'cloudflare-account.key'))) {
        if (Test-Path -LiteralPath $path) {
            $length = (Get-Item -LiteralPath $path -Force).Length
            [System.IO.File]::WriteAllBytes($path, (New-Object byte[] $length))
            Remove-Item -LiteralPath $path -Force
            Write-Host "Deleted $path."
        } else {
            Write-Host "Nothing stored at $path."
        }
    }
    Write-Host 'Revoke the token at Cloudflare too: Manage account -> Account API tokens (or My Profile -> API Tokens), delete it.'
    exit 0
} catch {
    [Console]::Error.WriteLine("remove-cloudflare-token: $($_.Exception.Message)")
    exit 2
}
