<#
.SYNOPSIS
Stores an OpenRouter API key for tools/local-qual, encrypted with Windows DPAPI for the current Windows user.

.DESCRIPTION
Asks for the key with hidden input (Read-Host -AsSecureString): it never shows on screen and never enters a command
line, shell history or a transcript. The key is encrypted with DPAPI (ConvertFrom-SecureString without -Key, so only
this Windows user on this machine can decrypt it) and written to
%LOCALAPPDATA%\plotroom-dev\secrets\openrouter.key. The folder and the file get an access list naming only the
current user. A path inside any git working tree is refused. run-cloud.ps1 decrypts the key for one run;
remove-openrouter-key.ps1 deletes it. Nothing is sent anywhere.

Exit codes: 0 stored; 2 refused or failed (the message says why; it never contains the key).

.PARAMETER SecretPath
Where to store the encrypted key. Default: %LOCALAPPDATA%\plotroom-dev\secrets\openrouter.key.

.PARAMETER SecureKey
A SecureString holding the key, for automation and tests; without it the script asks. PowerShell does not turn text
into a SecureString parameter, so a plain key cannot be passed here by mistake.

.PARAMETER Force
Replace a key that is already stored.

.EXAMPLE
powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\set-openrouter-key.ps1
#>
[CmdletBinding(PositionalBinding = $false)]
param(
    [string]$SecretPath = '',
    [System.Security.SecureString]$SecureKey = $null,
    [switch]$Force
)
$ErrorActionPreference = 'Stop'
# Against the caller's session when this runs in-process (& .\set-openrouter-key.ps1), before any key is read:
# trace level 2 would print the key with every assignment, so tracing goes off for the session; a -Key default for
# ConvertFrom-SecureString would silently replace DPAPI with AES under a known key, so this script sees no defaults.
Microsoft.PowerShell.Core\Set-PSDebug -Off
$PSDefaultParameterValues = @{}
. (Join-Path $PSScriptRoot 'secret-common.ps1')

$plain = $null
try {
    if (-not $SecretPath) { $SecretPath = Get-DefaultSecretPath }
    $full = Assert-SafeSecretPath $SecretPath (Split-Path -Parent $PSScriptRoot)
    if ((Test-Path -LiteralPath $full) -and -not $Force) {
        throw "a key is already stored at $full; pass -Force to replace it, or run remove-openrouter-key.ps1 first"
    }
    $pasted = -not $SecureKey
    if ($pasted) {
        $SecureKey = Microsoft.PowerShell.Utility\Read-Host -AsSecureString -Prompt 'Paste the OpenRouter API key (the input stays hidden)'
    }
    if (-not $SecureKey -or $SecureKey.Length -eq 0) { throw 'no key was entered; nothing was stored' }

    # -- Shape check without showing the key: OpenRouter keys start with sk-or- and hold no spaces --
    $plain = ConvertFrom-SecureToPlain $SecureKey
    $trimmed = $plain.Trim()
    if (-not $trimmed.StartsWith('sk-or-') -or $trimmed -match '\s' -or $trimmed.Length -lt 20) {
        throw 'this does not look like an OpenRouter API key (sk-or-..., no spaces); nothing was stored'
    }
    if ($trimmed -ne $plain) {
        # A pasted trailing newline or space would break the Authorization header later. A .NET call, never
        # ConvertTo-SecureString -AsPlainText: module logging records a cmdlet's arguments, the key included.
        $SecureKey = [System.Net.NetworkCredential]::new('', $trimmed).SecurePassword
    }
    $plain = $null
    $trimmed = $null

    # -- Folder first (user-only access, so the file never exists with a wider list), then the DPAPI blob --
    $dir = Split-Path -Parent $full
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    Set-UserOnlyAcl -Path $dir -Directory
    $blob = Microsoft.PowerShell.Security\ConvertFrom-SecureString -SecureString $SecureKey
    if (-not (Test-DpapiBlob $blob)) {
        # Belt and braces for the defaults line above: never write anything but a DPAPI blob.
        throw 'ConvertFrom-SecureString did not produce a DPAPI blob; nothing was stored'
    }
    [System.IO.File]::WriteAllText($full, $blob, (New-Object System.Text.ASCIIEncoding))
    Set-UserOnlyAcl -Path $full
    if (-not (Test-UserOnlyAcl $full)) { throw "could not restrict access to $full to the current user" }
    Write-Host "Stored the key, DPAPI-encrypted for the current Windows user, at $full (access: this user only)."
    if ($pasted) {
        Write-Host 'The key is probably still on the clipboard: copy something else now, and delete the entry from clipboard history (Win+V) if that is on.'
    }
    Write-Host 'Next: a dry run, then the first run (see tools/local-qual/cloud/README.md).'
    exit 0
} catch {
    [Console]::Error.WriteLine("set-openrouter-key: $($_.Exception.Message)")
    exit 2
} finally {
    $plain = $null
    $trimmed = $null
}
