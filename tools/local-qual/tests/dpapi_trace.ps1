# Set-PSDebug tracing test for the OpenRouter key scripts (tools/local-qual/cloud), with a dummy key only.
#
# Called by test_free_mode_review.py (t58) with the dummy in PROBE_DUMMY. It turns on trace level 2 in this session and runs
# one key script in-process, as a user would with `& .\run-cloud.ps1`. Trace output is written to the console host,
# not to a redirectable stream, so the caller captures this whole process's console and searches it for pieces of
# the key. -Which set: store a key that ends in a space (set-openrouter-key.ps1's trim path). -Which run: store it,
# then launch a stand-in child through run-cloud.ps1. Nothing is printed on purpose; ASCII only (PowerShell 5.1).
param([string]$Tool, [string]$Work, [string]$Python, [string]$Which)
$ErrorActionPreference = 'Stop'
$cloud = Join-Path $Tool 'cloud'
$dummy = $env:PROBE_DUMMY
Remove-Item Env:\PROBE_DUMMY
New-Item -ItemType Directory -Force -Path $Work | Out-Null
# Build the SecureString one character at a time: no cmdlet ever receives the dummy as a parameter.
$sec = New-Object System.Security.SecureString
$suffix = if ($Which -eq 'set') { ' ' } else { '' }
foreach ($ch in ($dummy + $suffix).ToCharArray()) { $sec.AppendChar($ch) }
$dummy = $null
$probe = Join-Path $Work 'trace_child.py'
Set-Content -LiteralPath $probe -Value 'import sys; sys.exit(0)' -Encoding ascii
$store = Join-Path $Work "trace-$Which\openrouter.key"
Remove-Item -LiteralPath (Split-Path -Parent $store) -Recurse -Force -ErrorAction SilentlyContinue
$code = 1
if ($Which -eq 'run') {
    & (Join-Path $cloud 'set-openrouter-key.ps1') -SecretPath $store -SecureKey $sec | Out-Null
    Set-PSDebug -Trace 2
    & (Join-Path $cloud 'run-cloud.ps1') -SecretPath $store -Python $Python -RunPy $probe --free-only
    $code = $LASTEXITCODE
    Set-PSDebug -Off
} else {
    Set-PSDebug -Trace 2
    & (Join-Path $cloud 'set-openrouter-key.ps1') -SecretPath $store -SecureKey $sec
    $code = $LASTEXITCODE
    Set-PSDebug -Off
}
Remove-Item -LiteralPath (Split-Path -Parent $store) -Recurse -Force -ErrorAction SilentlyContinue
exit $code
