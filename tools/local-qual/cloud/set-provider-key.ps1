<#
.SYNOPSIS
Stores one provider's key for tools/local-qual: set-provider-key.ps1 -Provider openrouter|groq|cloudflare.

.DESCRIPTION
One entry point for the three key stores. It runs the provider's own script in this session, which asks for the key
with hidden input, checks its shape without showing it, encrypts it with Windows DPAPI for the current Windows user
and writes it with an access list naming only that user, outside every git working tree:
  openrouter  set-openrouter-key.ps1   secrets\openrouter.key (sk-or-...)
  groq        set-groq-key.ps1         secrets\groq.key (gsk_...)
  cloudflare  set-cloudflare-token.ps1 secrets\cloudflare.key (a cfat_ account token or a cfut_ user token; the
                                       Global API Key cfk_ is refused) and secrets\cloudflare-account.key (the account
                                       id, asked with hidden input too)
all under %LOCALAPPDATA%\plotroom-dev. run-cloud.ps1 --provider <name> decrypts the key for one run;
remove-provider-key.ps1 -Provider <name> deletes it. Nothing is sent anywhere.

Exit codes: the provider script's (0 stored; 2 refused or failed), or 2 for an unknown provider.

.PARAMETER Provider
openrouter, groq or cloudflare.

.PARAMETER SecretPath
Where to store the encrypted key (default: the provider's file under %LOCALAPPDATA%\plotroom-dev\secrets). The
Cloudflare account id goes to cloudflare-account.key in the same folder.

.PARAMETER SecureKey
A SecureString holding the key, for automation and tests; without it the provider's script asks.

.PARAMETER SecureAccountId
Cloudflare only: a SecureString holding the account id, for automation and tests; without it the script asks.

.PARAMETER Force
Replace a key (and account id) that is already stored.

.EXAMPLE
powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\set-provider-key.ps1 -Provider groq
#>
[CmdletBinding(PositionalBinding = $false)]
param(
    [string]$Provider = '',
    [string]$SecretPath = '',
    [System.Security.SecureString]$SecureKey = $null,
    [System.Security.SecureString]$SecureAccountId = $null,
    [switch]$Force
)
$ErrorActionPreference = 'Stop'
# Against the caller's session when this runs in-process, before the provider's script reads any key: trace level 2
# would print the key with every assignment; a -Key default for ConvertFrom-SecureString would swap DPAPI for AES.
Microsoft.PowerShell.Core\Set-PSDebug -Off
$PSDefaultParameterValues = @{}
. (Join-Path $PSScriptRoot 'secret-common.ps1')

try {
    if (-not $Provider) { throw '-Provider is required: openrouter, groq or cloudflare; nothing was stored' }
    $spec = Get-ProviderSpec $Provider.ToLowerInvariant()
    if ($SecureAccountId -and -not $spec.Account) { throw '-SecureAccountId applies to -Provider cloudflare; nothing was stored' }
} catch {
    [Console]::Error.WriteLine("set-provider-key: $($_.Exception.Message)")
    exit 2
}
# Only the parameters given are passed on, so the provider's script keeps its own defaults and prompts. A SecureString
# reaches it as an object: module logging records its type, never its text.
$params = @{}
if ($SecretPath) { $params['SecretPath'] = $SecretPath }
if ($SecureKey) { $params['SecureKey'] = $SecureKey }
if ($SecureAccountId) { $params['SecureAccountId'] = $SecureAccountId }
if ($Force) { $params['Force'] = $true }
& (Join-Path $PSScriptRoot $spec.Store) @params
exit $LASTEXITCODE
