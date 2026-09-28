<#
.SYNOPSIS
Stores a Cloudflare Workers AI API token and the account id for tools/local-qual, encrypted with Windows DPAPI.

.DESCRIPTION
Asks for the token with hidden input and for the account id (an identifier, not a password, but it identifies the
owner's account, so it is kept out of the repository, records and command lines too). Both are encrypted with DPAPI
(only this Windows user on this machine can decrypt them) and written to %LOCALAPPDATA%\plotroom-dev\secrets\
cloudflare.key and cloudflare-account.key, beside the OpenRouter key, with an access list naming only the current
user. A path inside any git working tree is refused. run-cloud.ps1 --provider cloudflare decrypts them for one run;
remove-cloudflare-token.ps1 deletes them. Nothing is sent anywhere.

Use a least-privilege token: Manage account -> Account API tokens -> Create Token -> Custom token, permission
Account - Workers AI - Read only, this account only, with an end date (an account token starts with cfat_; a user
token from My Profile -> API Tokens starts with cfut_). The Global API Key (cfk_) has full access and is refused.
The account id is 32 hexadecimal characters (Account home -> Ctrl+K -> "Copy account ID").

Exit codes: 0 stored; 2 refused or failed (the message says why; it never contains the token or the account id).

.PARAMETER SecretPath
Where to store the encrypted token. Default: %LOCALAPPDATA%\plotroom-dev\secrets\cloudflare.key. The account id goes
to cloudflare-account.key in the same folder.

.PARAMETER SecureKey
A SecureString holding the token, for automation and tests; without it the script asks.

.PARAMETER SecureAccountId
A SecureString holding the account id, for automation and tests; without it the script asks.

.PARAMETER Force
Replace a token and account id that are already stored.

.EXAMPLE
powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\set-cloudflare-token.ps1
#>
[CmdletBinding(PositionalBinding = $false)]
param(
    [string]$SecretPath = '',
    [System.Security.SecureString]$SecureKey = $null,
    [System.Security.SecureString]$SecureAccountId = $null,
    [switch]$Force
)
$ErrorActionPreference = 'Stop'
Microsoft.PowerShell.Core\Set-PSDebug -Off
$PSDefaultParameterValues = @{}
. (Join-Path $PSScriptRoot 'secret-common.ps1')

$plain = $null
$trimmed = $null
$acct = $null
try {
    # Contract with run-cloud.ps1 --provider cloudflare: cloudflare.key and cloudflare-account.key in the key folder.
    if (-not $SecretPath) { $SecretPath = Join-Path (Split-Path -Parent (Get-DefaultSecretPath)) 'cloudflare.key' }
    $full = Assert-SafeSecretPath $SecretPath (Split-Path -Parent $PSScriptRoot)
    $acctFull = Assert-SafeSecretPath (Join-Path (Split-Path -Parent $full) 'cloudflare-account.key') (Split-Path -Parent $PSScriptRoot)
    if (((Test-Path -LiteralPath $full) -or (Test-Path -LiteralPath $acctFull)) -and -not $Force) {
        throw "a Cloudflare token or account id is already stored beside $full; pass -Force to replace them, or run remove-cloudflare-token.ps1 first"
    }

    # -- Account id first (hidden input as well, so it does not land in the console buffer) --
    if (-not $SecureAccountId) {
        $SecureAccountId = Microsoft.PowerShell.Utility\Read-Host -AsSecureString -Prompt 'Paste the Cloudflare account id (32 hexadecimal characters; input hidden)'
    }
    if (-not $SecureAccountId -or $SecureAccountId.Length -eq 0) { throw 'no account id was entered; nothing was stored' }
    $acct = (ConvertFrom-SecureToPlain $SecureAccountId).Trim().ToLowerInvariant()
    if ($acct -notmatch '^[0-9a-f]{32}$') { throw 'this does not look like a Cloudflare account id (32 hexadecimal characters); nothing was stored' }
    $SecureAccountId = [System.Net.NetworkCredential]::new('', $acct).SecurePassword
    $acct = $null

    # -- Token: cfat_ (account token) or cfut_ (user token); the Global API Key is refused --
    $pasted = -not $SecureKey
    if ($pasted) {
        $SecureKey = Microsoft.PowerShell.Utility\Read-Host -AsSecureString -Prompt 'Paste the Cloudflare API token (Workers AI Read; the input stays hidden)'
    }
    if (-not $SecureKey -or $SecureKey.Length -eq 0) { throw 'no token was entered; nothing was stored' }
    $plain = ConvertFrom-SecureToPlain $SecureKey
    $trimmed = $plain.Trim()
    if ($trimmed.StartsWith('cfk_')) {
        throw 'this is the Global API Key (cfk_), which has full access to the account; create a Workers AI Read token instead (see the help); nothing was stored'
    }
    if ($trimmed -notmatch '^cf(at|ut)_[A-Za-z0-9_-]{40,}$') {
        throw 'this does not look like a Cloudflare API token (cfat_ or cfut_ followed by at least 40 characters); nothing was stored'
    }
    if ($trimmed -ne $plain) { $SecureKey = [System.Net.NetworkCredential]::new('', $trimmed).SecurePassword }
    $plain = $null
    $trimmed = $null

    # -- Folder first (user-only access), then both DPAPI blobs --
    $dir = Split-Path -Parent $full
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    Set-UserOnlyAcl -Path $dir -Directory
    foreach ($pair in @(@($full, $SecureKey), @($acctFull, $SecureAccountId))) {
        $blob = Microsoft.PowerShell.Security\ConvertFrom-SecureString -SecureString $pair[1]
        if (-not (Test-DpapiBlob $blob)) { throw 'ConvertFrom-SecureString did not produce a DPAPI blob; nothing was stored' }
        [System.IO.File]::WriteAllText($pair[0], $blob, (New-Object System.Text.ASCIIEncoding))
        Set-UserOnlyAcl -Path $pair[0]
        if (-not (Test-UserOnlyAcl $pair[0])) { throw "could not restrict access to $($pair[0]) to the current user" }
    }
    Write-Host "Stored the Cloudflare token and account id, DPAPI-encrypted for the current Windows user, in $dir (access: this user only)."
    if ($pasted) {
        Write-Host 'The token is probably still on the clipboard: copy something else now, and delete the entry from clipboard history (Win+V) if that is on.'
    }
    exit 0
} catch {
    [Console]::Error.WriteLine("set-cloudflare-token: $($_.Exception.Message)")
    exit 2
} finally {
    $plain = $null
    $trimmed = $null
    $acct = $null
}
