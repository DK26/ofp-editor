# Shared helpers for the key scripts in this folder (set-openrouter-key.ps1, set-provider-key.ps1, run-cloud.ps1,
# remove-openrouter-key.ps1, remove-provider-key.ps1). Dot-sourced by them; it only defines functions.
#
# One store per provider, all in %LOCALAPPDATA%\plotroom-dev\secrets: openrouter.key, groq.key and cloudflare.key
# (DPAPI blobs), and for Cloudflare cloudflare-account.key beside the token (the account id, a DPAPI blob too: not a
# secret, but it identifies the owner's account, so it is kept out of command lines, records and the repository).
# set-openrouter-key.ps1, set-groq-key.ps1 and set-cloudflare-token.ps1 write them (set-provider-key.ps1 -Provider
# <name> calls the matching one); run-cloud.ps1 --provider <name> reads them.
#
# How the key is protected (Windows only):
# * At rest it is a DPAPI blob. ConvertFrom-SecureString without -Key encrypts with the Windows Data Protection API
#   in the current user's scope, so only this Windows user on this machine can decrypt it; the file holds no
#   plaintext. The file and its folder get an access list that names only the current user (inheritance off).
# * It never sits in a git working tree: every script refuses a secret path with a .git folder or file above it.
# * In use it is decrypted in memory and placed only in the environment block of the one child process that runs
#   run.py (System.Diagnostics.ProcessStartInfo), never in this PowerShell session's environment, a command line,
#   a file or the console.
# * The plaintext is never an argument of a cmdlet or function: PowerShell module logging (event 800, when a policy
#   turns it on) records every parameter binding verbatim. It passes only through .NET calls.
# * The scripts that handle the key start with two lines against a caller's session settings when run in-process:
#   Set-PSDebug -Off (trace level 2 prints each variable assignment with its value) and an empty script-scope
#   $PSDefaultParameterValues (a -Key default would swap DPAPI for AES under a known key).
#
# This file is ASCII only: Windows PowerShell 5.1 reads a script without a byte-order mark in the system code page.

function Get-DefaultSecretPath {
    # %LOCALAPPDATA% is per user and outside every repository.
    if (-not $env:LOCALAPPDATA) { throw 'LOCALAPPDATA is not set; pass -SecretPath' }
    return (Join-Path $env:LOCALAPPDATA 'plotroom-dev\secrets\openrouter.key')
}

function Resolve-FullPath([string]$Path) {
    return [System.IO.Path]::GetFullPath($Path)
}

function Get-ProviderSpec([string]$Provider) {
    # The store's settings per provider: the key file's name, the variable run-cloud.ps1 sets for run.py, whether an
    # account id is stored beside the key, and the scripts that store and remove it. Names are lower case, as run.py's
    # --provider takes them. The message never repeats the value, which could be a pasted key.
    switch -CaseSensitive ($Provider) {
        'openrouter' {
            return @{ Name = 'openrouter'; Title = 'OpenRouter'; File = 'openrouter.key'; EnvName = 'OPENROUTER_API_KEY'
                Account = $false; Store = 'set-openrouter-key.ps1'; Remove = 'remove-openrouter-key.ps1' }
        }
        'groq' {
            return @{ Name = 'groq'; Title = 'Groq'; File = 'groq.key'; EnvName = 'GROQ_API_KEY'; Account = $false
                Store = 'set-groq-key.ps1'; Remove = 'remove-groq-key.ps1' }
        }
        'cloudflare' {
            return @{ Name = 'cloudflare'; Title = 'Cloudflare'; File = 'cloudflare.key'; EnvName = 'CLOUDFLARE_API_TOKEN'
                Account = $true; AccountEnv = 'CLOUDFLARE_ACCOUNT_ID'; Store = 'set-cloudflare-token.ps1'
                Remove = 'remove-cloudflare-token.ps1' }
        }
    }
    throw 'unknown provider: use openrouter, groq or cloudflare (lower case)'
}

function Get-ProviderSecretPath([string]$Provider) {
    # %LOCALAPPDATA% is per user and outside every repository; openrouter.key is Get-DefaultSecretPath's file.
    if (-not $env:LOCALAPPDATA) { throw 'LOCALAPPDATA is not set; pass -SecretPath' }
    return (Join-Path $env:LOCALAPPDATA ('plotroom-dev\secrets\' + (Get-ProviderSpec $Provider).File))
}

function Get-AccountPath([string]$KeyPath) {
    # The Cloudflare account id's DPAPI file: cloudflare-account.key in the token file's folder (the contract of
    # set-cloudflare-token.ps1 and remove-cloudflare-token.ps1).
    return (Join-Path (Split-Path -Parent $KeyPath) 'cloudflare-account.key')
}

function Test-AccountIdShape([string]$Id) {
    # A Cloudflare account id as stored: 32 lower-case hexadecimal characters.
    return ($Id -cmatch '^[0-9a-f]{32}$')
}

function Find-GitTree([string]$Path) {
    # The nearest ancestor folder of $Path that holds a .git entry (a git working tree or worktree), else $null.
    $dir = [System.IO.Path]::GetDirectoryName((Resolve-FullPath $Path))
    while ($dir) {
        if (Test-Path -LiteralPath (Join-Path $dir '.git')) { return $dir }
        $parent = [System.IO.Path]::GetDirectoryName($dir)
        if (-not $parent -or $parent -eq $dir) { break }
        $dir = $parent
    }
    return $null
}

function Assert-SafeSecretPath([string]$Path, [string]$ToolDir) {
    # Refuse a secret path inside any git working tree or inside the tool's own folder; return the full path.
    $full = Resolve-FullPath $Path
    $tree = Find-GitTree $full
    if ($tree) {
        throw "refusing $full`: it is inside the git working tree $tree. Keep the key outside every repository (default: %LOCALAPPDATA%\plotroom-dev\secrets)."
    }
    if ($ToolDir) {
        $tool = (Resolve-FullPath $ToolDir).TrimEnd('\') + '\'
        if ($full.StartsWith($tool, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "refusing $full`: it is inside the tool folder $tool."
        }
    }
    return $full
}

function Get-CurrentUserSid {
    return [System.Security.Principal.WindowsIdentity]::GetCurrent().User
}

function Set-UserOnlyAcl([string]$Path, [switch]$Directory) {
    # Replace the access list of $Path with one rule, full control for the current user, and switch inheritance from
    # the parent folder off. A fresh security object carries only the access list, so no owner change (which would
    # need extra privileges) is attempted.
    $sid = Get-CurrentUserSid
    if ($Directory) {
        $acl = New-Object System.Security.AccessControl.DirectorySecurity
        $inherit = [System.Security.AccessControl.InheritanceFlags]'ContainerInherit,ObjectInherit'
        $rule = New-Object System.Security.AccessControl.FileSystemAccessRule($sid, 'FullControl', $inherit, 'None', 'Allow')
    } else {
        $acl = New-Object System.Security.AccessControl.FileSecurity
        $rule = New-Object System.Security.AccessControl.FileSystemAccessRule($sid, 'FullControl', 'Allow')
    }
    $acl.SetAccessRuleProtection($true, $false)
    $acl.AddAccessRule($rule)
    (Get-Item -LiteralPath $Path -Force).SetAccessControl($acl)
}

function Test-UserOnlyAcl([string]$Path) {
    # True when inheritance is off and every rule allows the current user and nobody else.
    $sid = (Get-CurrentUserSid).Value
    $acl = Get-Acl -LiteralPath $Path
    if (-not $acl.AreAccessRulesProtected) { return $false }
    $rules = @($acl.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier]))
    if ($rules.Count -lt 1) { return $false }
    foreach ($r in $rules) {
        if ($r.IdentityReference.Value -ne $sid -or $r.AccessControlType -ne 'Allow') { return $false }
    }
    return $true
}

function Test-DpapiBlob([string]$Text) {
    # True when $Text is a blob ConvertFrom-SecureString made with DPAPI: hex that starts with the DPAPI blob version
    # (01000000) and the DPAPI provider GUID df9d8cd0-1501-11d1-8c7a-00c04fc297eb in its little-endian byte order. A
    # blob made with -Key (AES, decryptable by anyone holding that key) starts with 76492d11 instead.
    return ($Text -match '^[0-9a-fA-F]+$') -and $Text.StartsWith('01000000d08c9ddf0115d1118c7a00c04fc297eb',
        [System.StringComparison]::OrdinalIgnoreCase)
}

function ConvertFrom-SecureToPlain([System.Security.SecureString]$Secure) {
    # The plaintext of a SecureString; the unmanaged copy is zeroed and freed at once.
    $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($Secure)
    try { return [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
    finally { [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}

function ConvertTo-CommandLineArgument([string]$Arg) {
    # Quote one argument for a Windows command line so the child (Python's C runtime) reads it back unchanged:
    # wrap it in double quotes when it is empty or holds spaces or quotes, escape each quote with a backslash, and
    # double the backslashes that come right before a quote or the closing quote.
    if ($Arg.Length -gt 0 -and $Arg -notmatch '[\s"]') { return $Arg }
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.Append('"')
    $slashes = 0
    foreach ($ch in $Arg.ToCharArray()) {
        if ($ch -eq '\') { $slashes++; continue }
        if ($ch -eq '"') {
            [void]$sb.Append('\' * (2 * $slashes + 1)).Append('"')
        } else {
            [void]$sb.Append('\' * $slashes).Append($ch)
        }
        $slashes = 0
    }
    [void]$sb.Append('\' * (2 * $slashes)).Append('"')
    return $sb.ToString()
}
