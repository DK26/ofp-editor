<#
.SYNOPSIS
Stores a Groq API key for tools/local-qual, encrypted with Windows DPAPI for the current Windows user.

.DESCRIPTION
Asks for the key with hidden input (Read-Host -AsSecureString): it never shows on screen and never enters a command
line, shell history or a transcript. The key is encrypted with DPAPI (only this Windows user on this machine can
decrypt it) and written to %LOCALAPPDATA%\plotroom-dev\secrets\groq.key, beside the OpenRouter key. The folder and
the file get an access list naming only the current user. A path inside any git working tree is refused.
run-cloud.ps1 --provider groq decrypts the key for one run; remove-groq-key.ps1 deletes it. Nothing is sent anywhere.

Groq keys start with gsk_ (the prefix is not in Groq's documentation; secret scanners use it). Create the key at
https://console.groq.com/keys while the organisation stays on the Free plan (no payment method): see
tools/local-qual/cloud/README.md.

Exit codes: 0 stored; 2 refused or failed (the message says why; it never contains the key).

.PARAMETER SecretPath
Where to store the encrypted key. Default: %LOCALAPPDATA%\plotroom-dev\secrets\groq.key.

.PARAMETER SecureKey
A SecureString holding the key, for automation and tests; without it the script asks.

.PARAMETER Force
Replace a key that is already stored.

.EXAMPLE
powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\set-groq-key.ps1
#>
[CmdletBinding(PositionalBinding = $false)]
param(
    [string]$SecretPath = '',
    [System.Security.SecureString]$SecureKey = $null,
    [switch]$Force
)
$ErrorActionPreference = 'Stop'
# Against the caller's session when run in-process: trace level 2 would print the key; a -Key default for
# ConvertFrom-SecureString would replace DPAPI with AES under a known key.
Microsoft.PowerShell.Core\Set-PSDebug -Off
$PSDefaultParameterValues = @{}
. (Join-Path $PSScriptRoot 'secret-common.ps1')

$plain = $null
$trimmed = $null
try {
    # Contract with run-cloud.ps1 --provider groq: the default file is groq.key in the same folder as openrouter.key.
    if (-not $SecretPath) { $SecretPath = Join-Path (Split-Path -Parent (Get-DefaultSecretPath)) 'groq.key' }
    $full = Assert-SafeSecretPath $SecretPath (Split-Path -Parent $PSScriptRoot)
    if ((Test-Path -LiteralPath $full) -and -not $Force) {
        throw "a key is already stored at $full; pass -Force to replace it, or run remove-groq-key.ps1 first"
    }
    $pasted = -not $SecureKey
    if ($pasted) {
        $SecureKey = Microsoft.PowerShell.Utility\Read-Host -AsSecureString -Prompt 'Paste the Groq API key (the input stays hidden)'
    }
    if (-not $SecureKey -or $SecureKey.Length -eq 0) { throw 'no key was entered; nothing was stored' }

    # -- Shape check without showing the key: gsk_ then letters and digits only --
    $plain = ConvertFrom-SecureToPlain $SecureKey
    $trimmed = $plain.Trim()
    if (-not $trimmed.StartsWith('gsk_') -or $trimmed -notmatch '^gsk_[A-Za-z0-9]{32,80}$') {
        throw 'this does not look like a Groq API key (gsk_ followed by letters and digits); nothing was stored'
    }
    if ($trimmed -ne $plain) {
        # A pasted trailing newline or space would break the Authorization header. A .NET call, never
        # ConvertTo-SecureString -AsPlainText: module logging records a cmdlet's arguments, the key included.
        $SecureKey = [System.Net.NetworkCredential]::new('', $trimmed).SecurePassword
    }
    $plain = $null
    $trimmed = $null

    # -- Folder first (user-only access), then the DPAPI blob --
    $dir = Split-Path -Parent $full
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    Set-UserOnlyAcl -Path $dir -Directory
    $blob = Microsoft.PowerShell.Security\ConvertFrom-SecureString -SecureString $SecureKey
    if (-not (Test-DpapiBlob $blob)) { throw 'ConvertFrom-SecureString did not produce a DPAPI blob; nothing was stored' }
    [System.IO.File]::WriteAllText($full, $blob, (New-Object System.Text.ASCIIEncoding))
    Set-UserOnlyAcl -Path $full
    if (-not (Test-UserOnlyAcl $full)) { throw "could not restrict access to $full to the current user" }
    Write-Host "Stored the Groq key, DPAPI-encrypted for the current Windows user, at $full (access: this user only)."
    if ($pasted) {
        Write-Host 'The key is probably still on the clipboard: copy something else now, and delete the entry from clipboard history (Win+V) if that is on.'
    }
    exit 0
} catch {
    [Console]::Error.WriteLine("set-groq-key: $($_.Exception.Message)")
    exit 2
} finally {
    $plain = $null
    $trimmed = $null
}
