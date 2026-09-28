<#
.SYNOPSIS
Runs tools/local-qual/run.py with one provider's stored key, decrypted only into the child process's environment.

.DESCRIPTION
The provider is run.py's own --provider argument: openrouter (the default, so every earlier command works unchanged),
groq or cloudflare. The script reads that provider's DPAPI blob (written by set-openrouter-key.ps1, set-groq-key.ps1
or set-cloudflare-token.ps1, or by set-provider-key.ps1 -Provider <name>, which calls them), decrypts it in memory,
and starts python run.py with the key in that one child process's environment variable (OPENROUTER_API_KEY,
GROQ_API_KEY or CLOUDFLARE_API_TOKEN); for Cloudflare it also decrypts the account id stored beside the token
(cloudflare-account.key) into CLOUDFLARE_ACCOUNT_ID, so the id never enters a command line. The key never enters this PowerShell session's environment, a command line, a file or the console, and it is
dropped when the run ends, whether it succeeds, fails or is interrupted. Every argument after this script's own
parameters goes to run.py unchanged (--provider included); --api-key-env is added when missing.

Refusals, before any key is decrypted (exit 2): a secret path inside a git working tree or the tool folder; a key or
account file whose access list names anyone but the current user, or that is not a DPAPI blob; an argument
holding a key prefix of any provider (sk-or-, gsk_, cfat_, cfut_, cfk_), --api-key, or the stored Cloudflare account
id; an unknown or repeated --provider; for OpenRouter, no --free-only unless -AllowPaid or --key-status is given; for
Groq and Cloudflare, -AllowPaid (their runs are always held to the free tier). After decrypting in memory: an argument
containing the stored key, or a key stored for another provider in the same folder.

--key-status (run.py reads the key's own record, or Groq's model list, or Cloudflare's token verify and model search,
and prints what the key allows) sends no model request, writes no ledger, takes no lock and uses no quota.

Run in-process (& .\run-cloud.ps1) it switches Set-PSDebug tracing off for the session, since trace level 2 would
print the key; powershell -File (as in the runbook) starts a fresh session anyway.

Exit codes: run.py's own code (0 ok; 4 budget; 5 configuration or key check; 9 free-only guard; 10 daily quota or
rate limit: resume later with --resume; see the README), or 2 when this script refused.

JSON arguments lose their quotes on the way through powershell -File, so pass --extra-body as @file
(for example @tools/local-qual/cloud/provider-zdr.json). Name the output file with --output, run.py's alias of --out:
powershell -File reads --out as an abbreviation of its common parameters -OutVariable and -OutBuffer and stops
("the parameter name 'out' is ambiguous") before this script runs.

.PARAMETER SecretPath
The DPAPI key file. Default: %LOCALAPPDATA%\plotroom-dev\secrets\<provider>.key.

.PARAMETER EnvName
The environment variable the child reads (run.py's --api-key-env). Default: the provider's (OPENROUTER_API_KEY,
GROQ_API_KEY, CLOUDFLARE_API_TOKEN).

.PARAMETER Python
The Python executable. Default: python on the PATH.

.PARAMETER RunPy
The script to run. Default: run.py in the folder above this one.

.PARAMETER AllowPaid
OpenRouter only: allow a run without --free-only (a paid round, which run.py caps with its own --max-usd).

.EXAMPLE
powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\run-cloud.ps1 --key-status

.EXAMPLE
powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\run-cloud.ps1 --provider groq --key-status

.EXAMPLE
powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\run-cloud.ps1 --backend openai --free-only --base-url https://openrouter.ai/api/v1 --model qwen/qwen3.8-27b:free --reasoning low --drop-params seed --ledger tools/local-qual/results/free-ledger.jsonl --suite pick --items PW01 --k 1
#>
# PositionalBinding off: this script's own parameters bind only by name, so run.py's arguments (--suite pick ...)
# can never be taken for them; everything else lands in $RunArgs unchanged. There is deliberately no -Provider
# parameter: powershell -File would bind run.py's --provider to it and swallow it.
[CmdletBinding(PositionalBinding = $false)]
param(
    [string]$SecretPath = '',
    [string]$EnvName = '',
    [string]$Python = 'python',
    [string]$RunPy = '',
    [switch]$AllowPaid,
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$RunArgs = @()
)
$ErrorActionPreference = 'Stop'
# Against the caller's session when this runs in-process (& .\run-cloud.ps1), before the key is decrypted: trace
# level 2 would print the key with every assignment, so tracing goes off for the session; a -Key default for
# ConvertTo-SecureString would decrypt with AES instead of DPAPI, so this script sees no defaults.
Microsoft.PowerShell.Core\Set-PSDebug -Off
$PSDefaultParameterValues = @{}
. (Join-Path $PSScriptRoot 'secret-common.ps1')

$runArgs = @($RunArgs | Where-Object { $null -ne $_ } | ForEach-Object { [string]$_ })
$providers = @('openrouter', 'groq', 'cloudflare')
$plain = $null
$secure = $null
$otherSecure = $null
$accountId = $null
$spec = $null
$psi = $null
$code = 2
try {
    # -- The provider: run.py's --provider <name> or --provider=<name>; OpenRouter when absent --
    $provider = 'openrouter'
    $seen = 0
    for ($i = 0; $i -lt $runArgs.Count; $i++) {
        if ($runArgs[$i] -ceq '--provider') {
            $seen++
            $provider = if ($i + 1 -lt $runArgs.Count) { $runArgs[$i + 1] } else { '' }
        } elseif ($runArgs[$i].StartsWith('--provider=', [System.StringComparison]::Ordinal)) {
            $seen++
            $provider = $runArgs[$i].Substring(11)
        }
    }
    if ($seen -gt 1) { throw '--provider is given more than once; nothing was run' }
    if ($providers -cnotcontains $provider) { throw '--provider must be openrouter, groq or cloudflare (lower case); nothing was run' }
    $spec = Get-ProviderSpec $provider
    $storeHint = $spec.Store
    if (-not $EnvName) { $EnvName = $spec.EnvName }
    if (-not $SecretPath) { $SecretPath = Get-ProviderSecretPath $provider }
    $toolDir = Split-Path -Parent $PSScriptRoot
    if (-not $RunPy) { $RunPy = Join-Path $toolDir 'run.py' }
    $full = Assert-SafeSecretPath $SecretPath $toolDir
    if ($EnvName -cnotmatch '^[A-Z][A-Z0-9_]{2,63}$') { throw '-EnvName must be an upper-case environment variable name' }

    # -- Argument rules, checked before any key is touched --
    foreach ($a in $runArgs) {
        if ($a -match '(sk-or-|gsk_|cfat_|cfut_|cfk_)') {
            throw 'an argument contains a key prefix (sk-or-, gsk_, cfat_, cfut_ or cfk_): never put a key on the command line (it would be visible in the process list and shell history); nothing was run'
        }
        if ($a -eq '--api-key' -or $a.StartsWith('--api-key=')) {
            throw '--api-key is refused: the key comes from the DPAPI store through the environment; nothing was run'
        }
    }
    # --key-status makes run.py read the key's record and nothing else (no model request, no ledger, no lock, no
    # quota), so it cannot spend and needs no --free-only. Exact, case-sensitive match: argparse is case-sensitive, so
    # any other spelling is not the flag and falls under the --free-only rule.
    $keyStatus = $runArgs -ccontains '--key-status'
    if ($provider -ceq 'openrouter') {
        if (-not $AllowPaid -and -not $keyStatus -and ($runArgs -notcontains '--free-only')) {
            throw 'this launcher runs free-only rounds: add --free-only (or --key-status to check the key, or pass -AllowPaid for a paid round capped by run.py''s --max-usd); nothing was run'
        }
    } elseif ($AllowPaid) {
        throw "-AllowPaid is for paid OpenRouter rounds; a --provider $provider run is always held to its free tier and needs no switch; nothing was run"
    }
    $at = [Array]::IndexOf($runArgs, '--api-key-env')
    if ($at -ge 0) {
        if ($at + 1 -ge $runArgs.Count -or $runArgs[$at + 1] -cne $EnvName) {
            throw "--api-key-env must name $EnvName (the variable this script sets), or be left out"
        }
    } else {
        $runArgs += @('--api-key-env', $EnvName)
    }
    if (-not (Test-Path -LiteralPath $full)) { throw "no stored key at $full; run $storeHint first" }
    if (-not (Test-UserOnlyAcl $full)) {
        throw "the key file $full is open to more than the current user; store the key again with $storeHint -Force"
    }

    # -- Cloudflare: the account id stored beside the token (a DPAPI blob, cloudflare-account.key), decrypted for the
    #    child's environment only --
    if ($spec.Account) {
        $at = [Array]::IndexOf($runArgs, '--account-id-env')
        if ($at -ge 0 -and ($at + 1 -ge $runArgs.Count -or $runArgs[$at + 1] -cne $spec.AccountEnv)) {
            throw "--account-id-env must name $($spec.AccountEnv) (the variable this script sets), or be left out"
        }
        $accountPath = Get-AccountPath $full
        if (-not (Test-Path -LiteralPath $accountPath)) { throw "no stored account id at $accountPath; run $storeHint -Force" }
        if (-not (Test-UserOnlyAcl $accountPath)) {
            throw "the account id file $accountPath is open to more than the current user; store it again with $storeHint -Force"
        }
        $accountBlob = ([string](Microsoft.PowerShell.Management\Get-Content -LiteralPath $accountPath -Raw)).Trim()
        if (-not (Test-DpapiBlob $accountBlob)) {
            throw "the file $accountPath is not a DPAPI blob written by $storeHint; store it again with $storeHint -Force"
        }
        $otherSecure = Microsoft.PowerShell.Security\ConvertTo-SecureString -String $accountBlob
        $accountId = (ConvertFrom-SecureToPlain $otherSecure).Trim().ToLowerInvariant()
        $otherSecure.Dispose()
        $otherSecure = $null
        if (-not (Test-AccountIdShape $accountId)) {
            throw "the file $accountPath does not hold a Cloudflare account id; store it again with $storeHint -Force"
        }
        foreach ($a in $runArgs) {
            if ($a.IndexOf($accountId, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
                throw 'an argument contains the stored Cloudflare account id: it names your account and stays out of command lines; nothing was run'
            }
        }
    }
    $pyCmd = Get-Command $Python -CommandType Application -ErrorAction Stop | Select-Object -First 1

    # -- Keys stored for the other providers in the same folder: decrypted in memory only to compare, then dropped;
    #    a file that is missing, open to others or not a DPAPI blob is no key this user stored, and is skipped --
    $folder = Split-Path -Parent $full
    foreach ($otherName in $providers) {
        if ($otherName -ceq $provider) { continue }
        $otherPath = Join-Path $folder (Get-ProviderSpec $otherName).File
        if (-not (Test-Path -LiteralPath $otherPath)) { continue }
        if (-not (Test-UserOnlyAcl $otherPath)) { continue }
        $otherBlob = ([string](Microsoft.PowerShell.Management\Get-Content -LiteralPath $otherPath -Raw)).Trim()
        if (-not (Test-DpapiBlob $otherBlob)) { continue }
        try {
            $otherSecure = Microsoft.PowerShell.Security\ConvertTo-SecureString -String $otherBlob
        } catch {
            continue
        }
        $plain = ConvertFrom-SecureToPlain $otherSecure
        $otherSecure.Dispose()
        $otherSecure = $null
        foreach ($a in $runArgs) {
            if ($plain -and $a.Contains($plain)) { throw 'an argument contains a key stored for another provider; nothing was run' }
        }
        $plain = $null
    }

    # -- Decrypt (DPAPI, current user) into memory only; anything but a DPAPI blob is refused unread --
    $blob = ([string](Microsoft.PowerShell.Management\Get-Content -LiteralPath $full -Raw)).Trim()
    if (-not (Test-DpapiBlob $blob)) {
        throw "the key file $full is not a DPAPI blob written by $storeHint; store the key again with $storeHint -Force"
    }
    $secure = Microsoft.PowerShell.Security\ConvertTo-SecureString -String $blob
    $blob = $null
    $plain = ConvertFrom-SecureToPlain $secure
    foreach ($a in $runArgs) {
        if ($plain -and $a.Contains($plain)) { throw 'an argument contains the stored key; nothing was run' }
    }

    # -- One child process with the key (and the account id) in its own environment block only --
    # ProcessStartInfo.EnvironmentVariables starts as a copy of this process's environment; adding the key there
    # changes the child's copy, not this session's. The other providers' variables are taken out of the copy, so the
    # child holds one key only. UseShellExecute false lets the child share this console.
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $pyCmd.Source
    $psi.Arguments = (@($RunPy) + $runArgs | ForEach-Object { ConvertTo-CommandLineArgument $_ }) -join ' '
    $psi.UseShellExecute = $false
    foreach ($otherName in $providers) {
        $otherSpec = Get-ProviderSpec $otherName
        if ($otherSpec.EnvName -cne $EnvName) { [void]$psi.EnvironmentVariables.Remove($otherSpec.EnvName) }
        if ($otherSpec.Account -and -not $spec.Account) { [void]$psi.EnvironmentVariables.Remove($otherSpec.AccountEnv) }
    }
    $psi.EnvironmentVariables[$EnvName] = $plain
    $plain = $null
    if ($spec.Account) { $psi.EnvironmentVariables[$spec.AccountEnv] = $accountId }
    $proc = [System.Diagnostics.Process]::Start($psi)
    [void]$psi.EnvironmentVariables.Remove($EnvName)
    if ($spec.Account) { [void]$psi.EnvironmentVariables.Remove($spec.AccountEnv) }
    $proc.WaitForExit()
    $code = $proc.ExitCode
} catch {
    [Console]::Error.WriteLine("run-cloud: $($_.Exception.Message)")
    $code = 2
} finally {
    # Drop every copy this script holds, on success, failure or Ctrl+C.
    if ($psi) {
        [void]$psi.EnvironmentVariables.Remove($EnvName)
        if ($spec -and $spec.Account) { [void]$psi.EnvironmentVariables.Remove($spec.AccountEnv) }
    }
    if ($secure) { $secure.Dispose() }
    if ($otherSecure) { $otherSecure.Dispose() }
    $plain = $null
    $secure = $null
    $otherSecure = $null
    $accountId = $null
}
exit $code
