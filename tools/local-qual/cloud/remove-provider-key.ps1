<#
.SYNOPSIS
Deletes one provider's stored key: remove-provider-key.ps1 -Provider openrouter|groq|cloudflare.

.DESCRIPTION
One entry point for the three removers: it runs remove-openrouter-key.ps1, remove-groq-key.ps1 or
remove-cloudflare-token.ps1 (which also deletes the account id file), each of which overwrites the file with zeros
and deletes it. This does not revoke the key at the provider: delete it there as well (each script names where),
which is what makes it useless everywhere.

Exit codes: the provider script's (0 deleted or nothing to delete; 2 failed), or 2 for an unknown provider.

.PARAMETER Provider
openrouter, groq or cloudflare.

.PARAMETER SecretPath
The key file. Default: the provider's file under %LOCALAPPDATA%\plotroom-dev\secrets.

.EXAMPLE
powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\remove-provider-key.ps1 -Provider groq
#>
[CmdletBinding(PositionalBinding = $false)]
param(
    [string]$Provider = '',
    [string]$SecretPath = ''
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'secret-common.ps1')

try {
    if (-not $Provider) { throw '-Provider is required: openrouter, groq or cloudflare' }
    $spec = Get-ProviderSpec $Provider.ToLowerInvariant()
} catch {
    [Console]::Error.WriteLine("remove-provider-key: $($_.Exception.Message)")
    exit 2
}
$params = @{}
if ($SecretPath) { $params['SecretPath'] = $SecretPath }
& (Join-Path $PSScriptRoot $spec.Remove) @params
exit $LASTEXITCODE
