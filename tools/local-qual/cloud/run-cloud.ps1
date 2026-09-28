<#
.SYNOPSIS
Runs tools/local-qual/run.py with the stored OpenRouter key, decrypted only into the child process's environment.

.DESCRIPTION
Reads the DPAPI blob written by set-openrouter-key.ps1, decrypts it in memory, and starts python run.py with the key
in that one child process's environment variable (default OPENROUTER_API_KEY). The key never enters this
PowerShell session's environment, a command line, a file or the console, and it is dropped when the run ends,
whether it succeeds, fails or is interrupted. Every argument after this script's own parameters goes to run.py
unchanged; --api-key-env is added when missing.

Refusals, before the key is decrypted (exit 2): a secret path inside a git working tree or the tool folder; a key
file whose access list names anyone but the current user, or that is not a DPAPI blob; an argument containing sk-or-
(a pasted key) or --api-key; no --free-only unless -AllowPaid or --key-status is given. After decrypting: an argument
containing the stored key.

--key-status (run.py reads GET /key once and prints the key's credit limit, usage and today's free-model requests)
needs no --free-only: it sends no model request, writes no ledger, takes no lock and uses no quota.

Run in-process (& .\run-cloud.ps1) it switches Set-PSDebug tracing off for the session, since trace level 2 would
print the key; powershell -File (as in the runbook) starts a fresh session anyway.

Exit codes: run.py's own code (0 ok; 4 budget; 5 configuration or key check; 9 free-only guard; 10 daily quota or
rate limit: resume later with --resume; see the README), or 2 when this script refused.

JSON arguments lose their quotes on the way through powershell -File, so pass --extra-body as @file
(for example @tools/local-qual/cloud/provider-zdr.json). Name the output file with --output, run.py's alias of --out:
powershell -File reads --out as an abbreviation of its common parameters -OutVariable and -OutBuffer and stops
("the parameter name 'out' is ambiguous") before this script runs.

.PARAMETER SecretPath
The DPAPI key file. Default: %LOCALAPPDATA%\plotroom-dev\secrets\openrouter.key.

.PARAMETER EnvName
The environment variable the child reads (run.py's --api-key-env). Default OPENROUTER_API_KEY.

.PARAMETER Python
The Python executable. Default: python on the PATH.

.PARAMETER RunPy
The script to run. Default: run.py in the folder above this one.

.PARAMETER AllowPaid
Allow a run without --free-only (a paid round, which run.py caps with its own --max-usd).

.EXAMPLE
powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\run-cloud.ps1 --key-status

.EXAMPLE
powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\run-cloud.ps1 --backend openai --free-only --base-url https://openrouter.ai/api/v1 --model qwen/qwen3.8-27b:free --reasoning low --drop-params seed --ledger tools/local-qual/results/free-ledger.jsonl --suite pick --items PW01 --k 1
#>
# PositionalBinding off: this script's own parameters bind only by name, so run.py's arguments (--suite pick ...)
# can never be taken for them; everything else lands in $RunArgs unchanged.
[CmdletBinding(PositionalBinding = $false)]
param(
    [string]$SecretPath = '',
    [string]$EnvName = 'OPENROUTER_API_KEY',
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
$plain = $null
$secure = $null
$psi = $null
$code = 2
try {
    if (-not $SecretPath) { $SecretPath = Get-DefaultSecretPath }
    $toolDir = Split-Path -Parent $PSScriptRoot
    if (-not $RunPy) { $RunPy = Join-Path $toolDir 'run.py' }
    $full = Assert-SafeSecretPath $SecretPath $toolDir
    if ($EnvName -cnotmatch '^[A-Z][A-Z0-9_]{2,63}$') { throw '-EnvName must be an upper-case environment variable name' }

    # -- Argument rules, checked before the key is touched --
    foreach ($a in $runArgs) {
        if ($a -match 'sk-or-') {
            throw 'an argument contains sk-or-: never put a key on the command line (it would be visible in the process list and shell history); nothing was run'
        }
        if ($a -eq '--api-key' -or $a.StartsWith('--api-key=')) {
            throw '--api-key is refused: the key comes from the DPAPI store through the environment; nothing was run'
        }
    }
    # --key-status makes run.py send one GET /key and nothing else (no model request, no ledger, no lock, no quota), so
    # it cannot spend and needs no --free-only. Exact, case-sensitive match: argparse is case-sensitive, so any other
    # spelling is not the flag and falls under the --free-only rule.
    $keyStatus = $runArgs -ccontains '--key-status'
    if (-not $AllowPaid -and -not $keyStatus -and ($runArgs -notcontains '--free-only')) {
        throw 'this launcher runs free-only rounds: add --free-only (or --key-status to check the key, or pass -AllowPaid for a paid round capped by run.py''s --max-usd); nothing was run'
    }
    $at = [Array]::IndexOf($runArgs, '--api-key-env')
    if ($at -ge 0) {
        if ($at + 1 -ge $runArgs.Count -or $runArgs[$at + 1] -cne $EnvName) {
            throw "--api-key-env must name $EnvName (the variable this script sets), or be left out"
        }
    } else {
        $runArgs += @('--api-key-env', $EnvName)
    }
    if (-not (Test-Path -LiteralPath $full)) { throw "no stored key at $full; run set-openrouter-key.ps1 first" }
    if (-not (Test-UserOnlyAcl $full)) {
        throw "the key file $full is open to more than the current user; store the key again with set-openrouter-key.ps1 -Force"
    }
    $pyCmd = Get-Command $Python -CommandType Application -ErrorAction Stop | Select-Object -First 1

    # -- Decrypt (DPAPI, current user) into memory only; anything but a DPAPI blob is refused unread --
    $blob = (Microsoft.PowerShell.Management\Get-Content -LiteralPath $full -Raw).Trim()
    if (-not (Test-DpapiBlob $blob)) {
        throw "the key file $full is not a DPAPI blob written by set-openrouter-key.ps1; store the key again with set-openrouter-key.ps1 -Force"
    }
    $secure = Microsoft.PowerShell.Security\ConvertTo-SecureString -String $blob
    $blob = $null
    $plain = ConvertFrom-SecureToPlain $secure
    foreach ($a in $runArgs) {
        if ($plain -and $a.Contains($plain)) { throw 'an argument contains the stored key; nothing was run' }
    }

    # -- One child process with the key in its own environment block only --
    # ProcessStartInfo.EnvironmentVariables starts as a copy of this process's environment; adding the key there
    # changes the child's copy, not this session's. UseShellExecute false lets the child share this console.
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $pyCmd.Source
    $psi.Arguments = (@($RunPy) + $runArgs | ForEach-Object { ConvertTo-CommandLineArgument $_ }) -join ' '
    $psi.UseShellExecute = $false
    $psi.EnvironmentVariables[$EnvName] = $plain
    $plain = $null
    $proc = [System.Diagnostics.Process]::Start($psi)
    [void]$psi.EnvironmentVariables.Remove($EnvName)
    $proc.WaitForExit()
    $code = $proc.ExitCode
} catch {
    [Console]::Error.WriteLine("run-cloud: $($_.Exception.Message)")
    $code = 2
} finally {
    # Drop every copy this script holds, on success, failure or Ctrl+C.
    if ($psi) { [void]$psi.EnvironmentVariables.Remove($EnvName) }
    if ($secure) { $secure.Dispose() }
    $plain = $null
    $secure = $null
}
exit $code
