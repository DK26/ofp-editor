# DPAPI round trip of the key scripts (tools/local-qual/cloud), with dummy keys only.
#
# Called by test_free_mode_review.py (t53) with the dummy OpenRouter key in CLOUDQUAL_DUMMY_KEY and, for steps 16-22
# (Groq and Cloudflare through set-provider-key.ps1, run-cloud.ps1 --provider and remove-provider-key.ps1), a dummy Groq
# key, a dummy Cloudflare token and a dummy account id in CLOUDQUAL_DUMMY_GROQ, CLOUDQUAL_DUMMY_CF and
# CLOUDQUAL_DUMMY_ACCOUNT. The variables are removed from this session before anything runs, so a key can reach a
# child process only through a DPAPI file and run-cloud.ps1. Prints PASS/FAIL lines; exit 1 if any check failed. Never
# prints a key or the account id. ASCII only (Windows PowerShell 5.1).
param(
    [string]$Tool,
    [string]$Work,
    [string]$BaseUrl,
    [string]$Python,
    [string]$Probe
)
$ErrorActionPreference = 'Stop'
$script:failures = 0
function Report([bool]$ok, [string]$name, [string]$detail) {
    if ($ok) { Write-Output "PASS $name`: $detail" } else { Write-Output "FAIL $name`: $detail"; $script:failures++ }
}

$cloud = Join-Path $Tool 'cloud'
$set = Join-Path $cloud 'set-openrouter-key.ps1'
$run = Join-Path $cloud 'run-cloud.ps1'
$remove = Join-Path $cloud 'remove-openrouter-key.ps1'
$setP = Join-Path $cloud 'set-provider-key.ps1'
$removeP = Join-Path $cloud 'remove-provider-key.ps1'
. (Join-Path $cloud 'secret-common.ps1')

$dummy = $env:CLOUDQUAL_DUMMY_KEY
$groqDummy = $env:CLOUDQUAL_DUMMY_GROQ
$cfDummy = $env:CLOUDQUAL_DUMMY_CF
$acctDummy = $env:CLOUDQUAL_DUMMY_ACCOUNT
if (-not $dummy -or -not $groqDummy -or -not $cfDummy -or -not $acctDummy) {
    Write-Output 'FAIL setup: CLOUDQUAL_DUMMY_KEY, _GROQ, _CF or _ACCOUNT is not set'; exit 1
}
Remove-Item Env:\CLOUDQUAL_DUMMY_KEY, Env:\CLOUDQUAL_DUMMY_GROQ, Env:\CLOUDQUAL_DUMMY_CF, Env:\CLOUDQUAL_DUMMY_ACCOUNT
foreach ($v in @('OPENROUTER_API_KEY', 'GROQ_API_KEY', 'CLOUDFLARE_API_TOKEN', 'CLOUDFLARE_ACCOUNT_ID')) {
    Remove-Item "Env:\$v" -ErrorAction SilentlyContinue
}
# One character at a time: no cmdlet receives the dummy as a parameter (module logging would record it).
$secure = New-Object System.Security.SecureString
foreach ($ch in $dummy.ToCharArray()) { $secure.AppendChar($ch) }
# Every blob ConvertFrom-SecureString makes with DPAPI starts with the DPAPI version and provider GUID in hex; a blob
# made with -Key (AES) starts differently.
$dpapiHeader = '01000000d08c9ddf0115d1118c7a00c04fc297eb'
$hasher = [System.Security.Cryptography.SHA256]::Create()
$sha = ([BitConverter]::ToString($hasher.ComputeHash([Text.Encoding]::UTF8.GetBytes($dummy)))).Replace('-', '').ToLower()
New-Item -ItemType Directory -Force -Path $Work | Out-Null
$store = Join-Path $Work 'store\openrouter.key'
$marker = Join-Path $Work 'probe-ran.txt'
$probeOut = Join-Path $Work 'probe.json'
$env:PROBE_MARKER = $marker
$env:PROBE_OUT = $probeOut

function Clear-Probe { Remove-Item -LiteralPath $marker, $probeOut -ErrorAction SilentlyContinue }

# -- 1. Store: DPAPI blob, no plaintext in the file --
& $set -SecretPath $store -SecureKey $secure
$c = $LASTEXITCODE
$blob = if (Test-Path -LiteralPath $store) { Get-Content -LiteralPath $store -Raw } else { '' }
$utf16hex = -join ([Text.Encoding]::Unicode.GetBytes($dummy) | ForEach-Object { $_.ToString('x2') })
$utf8hex = -join ([Text.Encoding]::UTF8.GetBytes($dummy) | ForEach-Object { $_.ToString('x2') })
$plainIn = $blob.Contains($dummy) -or $blob.ToLower().Contains($utf16hex) -or $blob.ToLower().Contains($utf8hex)
Report ($c -eq 0 -and $blob.Length -gt 100 -and -not $plainIn) 'store' "exit $c, DPAPI blob of $($blob.Length) hex characters, plaintext (ASCII, UTF-8 hex or UTF-16 hex) in the file: $plainIn"

# -- 2. Access list: current user only, inheritance off (file and folder) --
$sid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$okAcl = $true
$details = @()
foreach ($p in @($store, (Split-Path -Parent $store))) {
    $acl = Get-Acl -LiteralPath $p
    $rules = @($acl.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier]))
    $only = ($rules.Count -eq 1) -and ($rules[0].IdentityReference.Value -eq $sid) -and $acl.AreAccessRulesProtected
    $okAcl = $okAcl -and $only
    $details += "$(Split-Path -Leaf $p): $($rules.Count) rule(s), protected $($acl.AreAccessRulesProtected)"
}
Report $okAcl 'acl' ($details -join '; ')

# -- 3. No silent overwrite; a non-key refused --
& $set -SecretPath $store -SecureKey $secure
$c1 = $LASTEXITCODE
$notKey = ConvertTo-SecureString -String 'not an openrouter key' -AsPlainText -Force
& $set -SecretPath (Join-Path $Work 'store2\openrouter.key') -SecureKey $notKey
$c2 = $LASTEXITCODE
Report ($c1 -eq 2 -and $c2 -eq 2 -and -not (Test-Path (Join-Path $Work 'store2\openrouter.key'))) 'set-refusals' "existing key without -Force: exit $c1; a value without sk-or-: exit $c2, nothing stored"

# -- 4. Round trip into the child: same value, in the environment only, arguments quoted intact --
Clear-Probe
$tricky = 'a "quoted" value\with spaces\'
& $run -SecretPath $store -Python $Python -RunPy $Probe --free-only --label $tricky --extra-body '{"a": "b c"}'
$c = $LASTEXITCODE
$p = if (Test-Path -LiteralPath $probeOut) { Get-Content -LiteralPath $probeOut -Raw | ConvertFrom-Json } else { $null }
$want = @('--free-only', '--label', $tricky, '--extra-body', '{"a": "b c"}', '--api-key-env', 'OPENROUTER_API_KEY')
$argsOk = $p -and ((@($p.argv) -join '|') -ceq ($want -join '|'))
Report ($c -eq 0 -and $p -and $p.sha256 -eq $sha -and $p.len -eq $dummy.Length -and -not $p.in_argv -and $argsOk) 'decrypt-to-child' "exit $c; the child's variable matches the stored key (SHA-256 equal: $($p.sha256 -eq $sha)); key in argv: $($p.in_argv); arguments intact: $argsOk"

# -- 5. This session never held the key --
$scopes = @('Process', 'User', 'Machine') | Where-Object { [Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY', $_) }
Report ($scopes.Count -eq 0) 'parent-env-clean' "OPENROUTER_API_KEY set in scopes: [$($scopes -join ', ')]"

# -- 6. The child's exit code comes back; still no copy in this session --
Clear-Probe
$env:PROBE_EXIT = '3'
& $run -SecretPath $store -Python $Python -RunPy $Probe --free-only
$c = $LASTEXITCODE
Remove-Item Env:\PROBE_EXIT
Report ($c -eq 3 -and -not [Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY', 'Process')) 'exit-code' "child exit 3 returned as $c; variable absent afterwards"

# -- 7. Refusals: exit 2 and the child never starts --
$fake = Join-Path $Work 'fakerepo'
New-Item -ItemType Directory -Force -Path (Join-Path $fake '.git'), (Join-Path $fake 'secrets') | Out-Null
Copy-Item -LiteralPath $store -Destination (Join-Path $fake 'secrets\openrouter.key') -Force
$wide = Join-Path $Work 'wide'
New-Item -ItemType Directory -Force -Path $wide | Out-Null
Copy-Item -LiteralPath $store -Destination (Join-Path $wide 'openrouter.key') -Force
Set-UserOnlyAcl -Path (Join-Path $wide 'openrouter.key')
# Widen it: the access list only (Set-Acl would try to rewrite the audit list, which needs a privilege).
$item = Get-Item -LiteralPath (Join-Path $wide 'openrouter.key')
$acl = $item.GetAccessControl([System.Security.AccessControl.AccessControlSections]::Access)
$everyone = New-Object System.Security.Principal.SecurityIdentifier('S-1-1-0')
$acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($everyone, 'Read', 'Allow')))
$item.SetAccessControl($acl)
# A stored key without the sk-or- prefix, to reach the check that runs after decryption.
$other = Join-Path $Work 'other\openrouter.key'
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $other) | Out-Null
$otherPlain = 'plain-dummy-' + [Guid]::NewGuid().ToString('N')
[System.IO.File]::WriteAllText($other, (ConvertFrom-SecureString -SecureString (ConvertTo-SecureString -String $otherPlain -AsPlainText -Force)))
Set-UserOnlyAcl -Path $other
$cases = @(
    @{ n = 'no --free-only'; s = $store; a = @('--suite', 'pick') },
    @{ n = 'sk-or- in an argument'; s = $store; a = @('--free-only', '--label', 'sk-or-v1-0123456789') },
    @{ n = 'the stored key in an argument'; s = $other; a = @('--free-only', '--label', "x$otherPlain") },
    @{ n = '--api-key'; s = $store; a = @('--free-only', '--api-key', 'x') },
    @{ n = 'another --api-key-env'; s = $store; a = @('--free-only', '--api-key-env', 'OTHER_VAR') },
    @{ n = 'secret inside a git working tree'; s = (Join-Path $fake 'secrets\openrouter.key'); a = @('--free-only') },
    @{ n = 'secret inside the tool folder'; s = (Join-Path $Tool 'results\openrouter.key'); a = @('--free-only') },
    @{ n = 'no stored key'; s = (Join-Path $Work 'nope\openrouter.key'); a = @('--free-only') },
    @{ n = 'key file readable by Everyone'; s = (Join-Path $wide 'openrouter.key'); a = @('--free-only') }
)
$bad = @()
foreach ($case in $cases) {
    Clear-Probe
    $a = $case.a
    & $run -SecretPath $case.s -Python $Python -RunPy $Probe @a
    $c = $LASTEXITCODE
    if ($c -ne 2 -or (Test-Path -LiteralPath $marker)) { $bad += "$($case.n): exit $c, child ran: $(Test-Path -LiteralPath $marker)" }
}
& $set -SecretPath (Join-Path $fake 'secrets2\openrouter.key') -SecureKey $secure
$c = $LASTEXITCODE
if ($c -ne 2 -or (Test-Path (Join-Path $fake 'secrets2\openrouter.key'))) { $bad += "set inside a git tree: exit $c" }
Report ($bad.Count -eq 0) 'refusals' ("$($cases.Count) launcher refusals and 1 store refusal, each exit 2 with no child started" + $(if ($bad) { '; ' + ($bad -join '; ') } else { '' }))

# -- 8. End to end: run.py --free-only against the mock, key only from the DPAPI store --
Remove-Item Env:\PROBE_OUT, Env:\PROBE_MARKER -ErrorAction SilentlyContinue
$records = Join-Path $Work 'e2e.jsonl'
& $run -SecretPath $store -Python $Python --backend openai --free-only --base-url $BaseUrl --model 'mock/free-model:free' --reasoning none --retry-base-s 0.01 --retry-cap-s 0.05 --ledger (Join-Path $Work 'e2e-ledger.jsonl') --out $records --suite pick --k 1 --limit 1
$c = $LASTEXITCODE
$text = if (Test-Path -LiteralPath $records) { Get-Content -LiteralPath $records -Raw } else { '' }
Report ($c -eq 0 -and $text.Length -gt 0 -and -not $text.Contains($dummy)) 'end-to-end' "run.py --free-only through run-cloud.ps1: exit $c, records written without the key"

# -- 10. No cmdlet or function ever receives the plaintext key as an argument --
# Module logging (event 800, when a policy turns it on) records every cmdlet parameter binding, so a key passed to
# ConvertTo-SecureString -AsPlainText would land in the event log. The plaintext lives only in $plain and $trimmed.
$leaky = @()
foreach ($f in @(Get-ChildItem -LiteralPath $cloud -Filter '*.ps1')) {
    $tokens = $null
    $parseErrors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseFile($f.FullName, [ref]$tokens, [ref]$parseErrors)
    $commands = $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] }, $true)
    foreach ($cmd in $commands) {
        $refs = $cmd.FindAll({ param($n) $n -is [System.Management.Automation.Language.VariableExpressionAst] -and
                $n.VariablePath.UserPath -in @('plain', 'trimmed') }, $true)
        if (@($refs).Count -gt 0) { $leaky += "$($f.Name):$($cmd.Extent.StartLineNumber) $($cmd.GetCommandName())" }
    }
    foreach ($t in $tokens) {
        if ($t.Kind -eq 'Parameter' -and $t.Text -eq '-AsPlainText') { $leaky += "$($f.Name):$($t.Extent.StartLineNumber) -AsPlainText" }
    }
}
Report ($leaky.Count -eq 0) 'no-plaintext-to-cmdlets' ("commands that take the plaintext: [" + ($leaky -join ', ') + ']')

# -- 11. Parameter defaults in the calling session cannot swap DPAPI for a known AES key --
$store5 = Join-Path $Work 'store5\openrouter.key'
$aes = [byte[]](1..16)
$PSDefaultParameterValues['ConvertFrom-SecureString:Key'] = $aes
$PSDefaultParameterValues['ConvertTo-SecureString:Key'] = $aes
try {
    & $set -SecretPath $store5 -SecureKey $secure | Out-Null
    $c5 = $LASTEXITCODE
    Clear-Probe
    $env:PROBE_OUT = $probeOut
    & $run -SecretPath $store5 -Python $Python -RunPy $Probe --free-only
    $c6 = $LASTEXITCODE
} finally {
    $PSDefaultParameterValues.Remove('ConvertFrom-SecureString:Key')
    $PSDefaultParameterValues.Remove('ConvertTo-SecureString:Key')
}
$blob5 = if (Test-Path -LiteralPath $store5) { (Get-Content -LiteralPath $store5 -Raw).Trim() } else { '' }
$p5 = if (Test-Path -LiteralPath $probeOut) { Get-Content -LiteralPath $probeOut -Raw | ConvertFrom-Json } else { $null }
Report ($c5 -eq 0 -and $blob5.StartsWith($dpapiHeader) -and $c6 -eq 0 -and $p5 -and $p5.sha256 -eq $sha) 'defaults-neutralised' "with -Key defaults set for both cmdlets: store exit $c5, DPAPI blob: $($blob5.StartsWith($dpapiHeader)); launch exit $c6, the child got the key: $($p5 -and $p5.sha256 -eq $sha)"

# -- 12. A key file that is not a DPAPI blob is refused before anything is decrypted or started --
$aesFile = Join-Path $Work 'aes\openrouter.key'
$plainFile = Join-Path $Work 'plainfile\openrouter.key'
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $aesFile), (Split-Path -Parent $plainFile) | Out-Null
[System.IO.File]::WriteAllText($aesFile, (ConvertFrom-SecureString -SecureString $secure -Key $aes))
$plainText = 'plain-dummy-' + [Guid]::NewGuid().ToString('N')
[System.IO.File]::WriteAllText($plainFile, $plainText)
Set-UserOnlyAcl -Path $aesFile
Set-UserOnlyAcl -Path $plainFile
$bad12 = @()
# The probe touches the marker only when PROBE_MARKER is set (step 8 removed it), so "child ran" below is a real check.
$env:PROBE_MARKER = $marker
foreach ($f in @($aesFile, $plainFile)) {
    Clear-Probe
    $errFile = Join-Path $Work 'run-err.txt'
    $proc = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', "`"$run`"", '-SecretPath', "`"$f`"", '-Python', "`"$Python`"", '-RunPy', "`"$Probe`"", '--free-only') -NoNewWindow -Wait -PassThru -RedirectStandardError $errFile
    $errText = if (Test-Path -LiteralPath $errFile) { Get-Content -LiteralPath $errFile -Raw } else { '' }
    if ($proc.ExitCode -ne 2 -or (Test-Path -LiteralPath $marker) -or ($errText -and $errText.Contains($plainText)) -or $errText -notmatch 'DPAPI') {
        $bad12 += "$(Split-Path -Leaf (Split-Path -Parent $f)): exit $($proc.ExitCode), child ran: $(Test-Path -LiteralPath $marker)"
    }
}
Remove-Item Env:\PROBE_MARKER -ErrorAction SilentlyContinue
Report ($bad12.Count -eq 0) 'non-dpapi-refused' ("an AES blob and a plaintext file: each exit 2, no child, the file's text not echoed" + $(if ($bad12) { '; ' + ($bad12 -join '; ') } else { '' }))

# -- 13. A pasted trailing space is trimmed on the way in; the child receives the exact key --
$secTrail = New-Object System.Security.SecureString
foreach ($ch in ($dummy + ' ').ToCharArray()) { $secTrail.AppendChar($ch) }
$store6 = Join-Path $Work 'store6\openrouter.key'
& $set -SecretPath $store6 -SecureKey $secTrail | Out-Null
$c7 = $LASTEXITCODE
Clear-Probe
$env:PROBE_OUT = $probeOut
& $run -SecretPath $store6 -Python $Python -RunPy $Probe --free-only
$c8 = $LASTEXITCODE
$p6 = if (Test-Path -LiteralPath $probeOut) { Get-Content -LiteralPath $probeOut -Raw | ConvertFrom-Json } else { $null }
Report ($c7 -eq 0 -and $c8 -eq 0 -and $p6 -and $p6.sha256 -eq $sha -and $p6.len -eq $dummy.Length) 'trim-round-trip' "key + trailing space: store exit $c7, launch exit $c8, the child got the trimmed key: $($p6 -and $p6.sha256 -eq $sha)"
Remove-Item Env:\PROBE_OUT -ErrorAction SilentlyContinue

# -- 14. --output passes through powershell -File, as the runbook launches the script --
# PowerShell's binder reads "--out" as an abbreviation of its common parameters -OutVariable/-OutBuffer and stops
# before the script starts, so run.py's output file is named with its alias --output on this path.
Clear-Probe
$env:PROBE_OUT = $probeOut
$outFile = Join-Path $Work 'alias out.jsonl'
$errFile = Join-Path $Work 'run-err14.txt'
$proc = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', "`"$run`"", '-SecretPath', "`"$store`"", '-Python', "`"$Python`"", '-RunPy', "`"$Probe`"", '--free-only', '--output', "`"$outFile`"") -NoNewWindow -Wait -PassThru -RedirectStandardError $errFile
$p14 = if (Test-Path -LiteralPath $probeOut) { Get-Content -LiteralPath $probeOut -Raw | ConvertFrom-Json } else { $null }
$want14 = @('--free-only', '--output', $outFile, '--api-key-env', 'OPENROUTER_API_KEY')
$args14 = $p14 -and ((@($p14.argv) -join '|') -ceq ($want14 -join '|'))
Report ($proc.ExitCode -eq 0 -and $args14 -and $p14.sha256 -eq $sha) 'output-alias-through-file' "powershell -File with --output: exit $($proc.ExitCode), run.py received --output and the path intact: $args14"
Remove-Item Env:\PROBE_OUT -ErrorAction SilentlyContinue

# -- 15. --key-status through the launcher: no --free-only needed, the key record printed, nothing secret shown --
# run.py --key-status sends one GET /key and nothing else (no model request, no ledger, no lock), so the launcher lets
# it through without --free-only; the sk-or- and --api-key refusals still apply. The child shares the launcher's
# console, so its output is captured by redirecting the whole powershell -File run into files (in the work folder,
# where the Python side's final sweep also searches them for the key and the key label).
Clear-Probe
$ksOut = Join-Path $Work 'key-status-out.txt'
$ksErr = Join-Path $Work 'key-status-err.txt'
$proc = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', "`"$run`"", '-SecretPath', "`"$store`"", '-Python', "`"$Python`"", '--key-status', '--base-url', $BaseUrl) -NoNewWindow -Wait -PassThru -RedirectStandardOutput $ksOut -RedirectStandardError $ksErr
$ksText = ''
foreach ($f in @($ksOut, $ksErr)) { if (Test-Path -LiteralPath $f) { $ksText += [string](Get-Content -LiteralPath $f -Raw) } }
$fields = @('credit limit:', 'usage:', 'free tier:', 'management key:', 'free-model requests today:', 'per-key rate limit:')
$missing15 = @($fields | Where-Object { -not $ksText.Contains($_) })
$shown15 = $ksText.Contains($dummy) -or $ksText.Contains('sk-or-')
$env:PROBE_MARKER = $marker
$bad15 = @()
foreach ($a in @(@('--key-status', '--label', 'sk-or-v1-0123456789'), @('--key-status', '--api-key', 'x'))) {
    Clear-Probe
    & $run -SecretPath $store -Python $Python -RunPy $Probe @a
    $c = $LASTEXITCODE
    if ($c -ne 2 -or (Test-Path -LiteralPath $marker)) { $bad15 += "$($a -join ' '): exit $c, child ran: $(Test-Path -LiteralPath $marker)" }
}
Remove-Item Env:\PROBE_MARKER -ErrorAction SilentlyContinue
Report ($proc.ExitCode -eq 0 -and $missing15.Count -eq 0 -and -not $shown15 -and $bad15.Count -eq 0) 'key-status' ("without --free-only: exit $($proc.ExitCode), missing fields [$($missing15 -join ', ')], key or sk-or- text shown: $shown15; sk-or- and --api-key still refused with no child: $($bad15.Count -eq 0)" + $(if ($bad15) { '; ' + ($bad15 -join '; ') } else { '' }))

# ===== Groq and Cloudflare (set-provider-key.ps1, run-cloud.ps1 --provider, remove-provider-key.ps1) =====
function New-Secure([string]$Text) {
    # A SecureString built one character at a time: no cmdlet receives the dummy as a parameter.
    $s = New-Object System.Security.SecureString
    foreach ($ch in $Text.ToCharArray()) { $s.AppendChar($ch) }
    return $s
}
function Get-Sha([string]$Text) {
    return ([BitConverter]::ToString($hasher.ComputeHash([Text.Encoding]::UTF8.GetBytes($Text)))).Replace('-', '').ToLower()
}
function Read-Probe {
    if (Test-Path -LiteralPath $probeOut) { return (Get-Content -LiteralPath $probeOut -Raw | ConvertFrom-Json) }
    return $null
}
function Test-OnlyMe([string]$Path) {
    $acl = Get-Acl -LiteralPath $Path
    $rules = @($acl.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier]))
    return ($rules.Count -eq 1) -and ($rules[0].IdentityReference.Value -eq $sid) -and $acl.AreAccessRulesProtected
}
$gsec = New-Secure $groqDummy
$csec = New-Secure $cfDummy
$groqSha = Get-Sha $groqDummy
$cfSha = Get-Sha $cfDummy
$acctSha = Get-Sha $acctDummy
$pstore = Join-Path $Work 'pstore'
$groqStore = Join-Path $pstore 'groq.key'
$cfStore = Join-Path $pstore 'cloudflare.key'
$cfAccount = Join-Path $pstore 'cloudflare-account.key'

# -- 16. Provider keys through set-provider-key.ps1 (which runs set-groq-key.ps1 and set-cloudflare-token.ps1): DPAPI
#        blobs, user-only access, and the Cloudflare account id beside the token as a DPAPI blob of its own --
& $setP -Provider groq -SecretPath $groqStore -SecureKey $gsec
$c1 = $LASTEXITCODE
& $setP -Provider cloudflare -SecretPath $cfStore -SecureKey $csec -SecureAccountId (New-Secure $acctDummy)
$c2 = $LASTEXITCODE
$gBlob = if (Test-Path -LiteralPath $groqStore) { (Get-Content -LiteralPath $groqStore -Raw).Trim() } else { '' }
$cBlob = if (Test-Path -LiteralPath $cfStore) { (Get-Content -LiteralPath $cfStore -Raw).Trim() } else { '' }
$aBlob = if (Test-Path -LiteralPath $cfAccount) { (Get-Content -LiteralPath $cfAccount -Raw).Trim() } else { '' }
$acctBack = if ($aBlob.StartsWith($dpapiHeader)) { ConvertFrom-SecureToPlain (ConvertTo-SecureString -String $aBlob) } else { '' }
$plain16 = $false
foreach ($pair in @(@($gBlob, $groqDummy), @($cBlob, $cfDummy), @($aBlob, $acctDummy))) {
    $hex16 = -join ([Text.Encoding]::Unicode.GetBytes($pair[1]) | ForEach-Object { $_.ToString('x2') })
    $plain16 = $plain16 -or $pair[0].Contains($pair[1]) -or $pair[0].ToLower().Contains($hex16)
}
$acl16 = (Test-Path -LiteralPath $cfAccount) -and (@($groqStore, $cfStore, $cfAccount, $pstore) | Where-Object { -not (Test-OnlyMe $_) }).Count -eq 0
$blobs16 = $gBlob.StartsWith($dpapiHeader) -and $cBlob.StartsWith($dpapiHeader) -and $aBlob.StartsWith($dpapiHeader)
Report ($c1 -eq 0 -and $c2 -eq 0 -and $blobs16 -and -not $plain16 -and $acctBack -ceq $acctDummy -and $acl16) 'provider-store' "groq exit $c1, cloudflare exit $c2; three DPAPI blobs: $blobs16; plaintext in a blob: $plain16; the account id decrypts back: $($acctBack -ceq $acctDummy); user-only access on the files and folder: $acl16"

# -- 17. Store refusals: wrong shapes, the Global API Key, a legacy token, a bad account id, a token pasted as the id,
#        an unknown provider, an existing key without -Force, a path inside a git working tree; nothing is stored --
$bad17 = @()
$cases17 = @(
    @{ n = 'an OpenRouter key as the Groq key'; p = 'groq'; k = $secure; a = $null; s = (Join-Path $Work 'p17a\groq.key') },
    @{ n = 'the Global API Key'; p = 'cloudflare'; k = (New-Secure ('cfk_' + ('a' * 40))); a = (New-Secure $acctDummy); s = (Join-Path $Work 'p17b\cloudflare.key') },
    @{ n = 'a legacy token'; p = 'cloudflare'; k = (New-Secure ('L' * 40)); a = (New-Secure $acctDummy); s = (Join-Path $Work 'p17c\cloudflare.key') },
    @{ n = 'a malformed account id'; p = 'cloudflare'; k = $csec; a = (New-Secure 'xyz'); s = (Join-Path $Work 'p17d\cloudflare.key') },
    @{ n = 'a token as the account id'; p = 'cloudflare'; k = $csec; a = (New-Secure ('cfat_' + ('b' * 40))); s = (Join-Path $Work 'p17e\cloudflare.key') },
    @{ n = 'an account id for Groq'; p = 'groq'; k = $gsec; a = (New-Secure $acctDummy); s = (Join-Path $Work 'p17g\groq.key') },
    @{ n = 'an unknown provider'; p = 'mistral'; k = $gsec; a = $null; s = (Join-Path $Work 'p17f\mistral.key') },
    @{ n = 'inside a git working tree'; p = 'groq'; k = $gsec; a = $null; s = (Join-Path $fake 'secrets3\groq.key') }
)
foreach ($case in $cases17) {
    if ($case.a) { & $setP -Provider $case.p -SecretPath $case.s -SecureKey $case.k -SecureAccountId $case.a }
    else { & $setP -Provider $case.p -SecretPath $case.s -SecureKey $case.k }
    $c = $LASTEXITCODE
    $leftover = (Test-Path -LiteralPath $case.s) -or (Test-Path -LiteralPath (Join-Path (Split-Path -Parent $case.s) 'cloudflare-account.key'))
    if ($c -ne 2 -or $leftover) { $bad17 += "$($case.n): exit $c, stored: $leftover" }
}
$before17 = (Get-Content -LiteralPath $groqStore -Raw)
& $setP -Provider groq -SecretPath $groqStore -SecureKey $csec
$c = $LASTEXITCODE
if ($c -ne 2 -or (Get-Content -LiteralPath $groqStore -Raw) -ne $before17) { $bad17 += "existing key without -Force: exit $c" }
Report ($bad17.Count -eq 0) 'provider-store-refusals' ("$($cases17.Count + 1) refusals, each exit 2 with nothing stored" + $(if ($bad17) { '; ' + ($bad17 -join '; ') } else { '' }))

# -- 18. Into the child: each provider's key in its own variable only, the account id in CLOUDFLARE_ACCOUNT_ID, the
#        other providers' variables taken out of the child's copy, nothing in the arguments --
$env:PROBE_OUT = $probeOut
$env:PROBE_ENV_ABSENT = 'OPENROUTER_API_KEY,CLOUDFLARE_API_TOKEN,CLOUDFLARE_ACCOUNT_ID,GROQ_API_KEY'
$env:CLOUDFLARE_API_TOKEN = 'decoy-in-the-parent-session'
Clear-Probe
$env:PROBE_ENV_NAME = 'GROQ_API_KEY'
& $run -SecretPath $groqStore -Python $Python -RunPy $Probe --provider groq --suite pick
$cg = $LASTEXITCODE
$pg = Read-Probe
Remove-Item Env:\CLOUDFLARE_API_TOKEN
$wantG = @('--provider', 'groq', '--suite', 'pick', '--api-key-env', 'GROQ_API_KEY')
$okG = $cg -eq 0 -and $pg -and $pg.sha256 -eq $groqSha -and -not $pg.in_argv -and ((@($pg.argv) -join '|') -ceq ($wantG -join '|')) -and -not $pg.present.CLOUDFLARE_API_TOKEN -and -not $pg.present.OPENROUTER_API_KEY
Clear-Probe
$env:PROBE_ENV_NAME = 'CLOUDFLARE_API_TOKEN'
$env:PROBE_ENV_EXTRA = 'CLOUDFLARE_ACCOUNT_ID'
& $run -SecretPath $cfStore -Python $Python -RunPy $Probe --provider cloudflare
$cc = $LASTEXITCODE
$pc = Read-Probe
$wantC = @('--provider', 'cloudflare', '--api-key-env', 'CLOUDFLARE_API_TOKEN')
$okC = $cc -eq 0 -and $pc -and $pc.sha256 -eq $cfSha -and -not $pc.in_argv -and $pc.extra.CLOUDFLARE_ACCOUNT_ID.sha256 -eq $acctSha -and -not $pc.extra.CLOUDFLARE_ACCOUNT_ID.in_argv -and ((@($pc.argv) -join '|') -ceq ($wantC -join '|')) -and -not $pc.present.GROQ_API_KEY
Remove-Item Env:\PROBE_ENV_NAME, Env:\PROBE_ENV_EXTRA, Env:\PROBE_ENV_ABSENT
$scopes18 = @('GROQ_API_KEY', 'CLOUDFLARE_API_TOKEN', 'CLOUDFLARE_ACCOUNT_ID') | Where-Object { [Environment]::GetEnvironmentVariable($_, 'Process') }
Report ($okG -and $okC -and $scopes18.Count -eq 0) 'provider-decrypt-to-child' "groq: exit $cg, the child's GROQ_API_KEY matches the stored key: $($pg -and $pg.sha256 -eq $groqSha), the parent's decoy CLOUDFLARE_API_TOKEN absent in the child: $($pg -and -not $pg.present.CLOUDFLARE_API_TOKEN); cloudflare: exit $cc, token and account id match: $($pc -and $pc.sha256 -eq $cfSha -and $pc.extra.CLOUDFLARE_ACCOUNT_ID.sha256 -eq $acctSha); arguments intact: $($okG -and $okC); variables left in this session: [$($scopes18 -join ', ')]"

# -- 19. Launcher refusals for the providers: exit 2 and the child never starts --
$env:PROBE_MARKER = $marker
# A folder holding the OpenRouter key and a Groq blob whose plaintext has no prefix: only the comparison with keys
# stored for other providers can catch it in an argument.
$mix = Join-Path $Work 'mix'
New-Item -ItemType Directory -Force -Path $mix | Out-Null
Copy-Item -LiteralPath $store -Destination (Join-Path $mix 'openrouter.key') -Force
Set-UserOnlyAcl -Path (Join-Path $mix 'openrouter.key')
$groqPlain = 'groq-plain-dummy-' + [Guid]::NewGuid().ToString('N')
[System.IO.File]::WriteAllText((Join-Path $mix 'groq.key'), (ConvertFrom-SecureString -SecureString (ConvertTo-SecureString -String $groqPlain -AsPlainText -Force)))
Set-UserOnlyAcl -Path (Join-Path $mix 'groq.key')
# Cloudflare tokens without an account file, with one open to Everyone, with a DPAPI blob of a malformed id, and with
# the id in plain text instead of a DPAPI blob.
foreach ($d in @('noacct', 'wideacct', 'badacct', 'plainacct')) {
    New-Item -ItemType Directory -Force -Path (Join-Path $Work $d) | Out-Null
    Copy-Item -LiteralPath $cfStore -Destination (Join-Path $Work "$d\cloudflare.key") -Force
    Set-UserOnlyAcl -Path (Join-Path $Work "$d\cloudflare.key")
}
Copy-Item -LiteralPath $cfAccount -Destination (Join-Path $Work 'wideacct\cloudflare-account.key') -Force
Set-UserOnlyAcl -Path (Join-Path $Work 'wideacct\cloudflare-account.key')
$item = Get-Item -LiteralPath (Join-Path $Work 'wideacct\cloudflare-account.key')
$acl = $item.GetAccessControl([System.Security.AccessControl.AccessControlSections]::Access)
$acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($everyone, 'Read', 'Allow')))
$item.SetAccessControl($acl)
[System.IO.File]::WriteAllText((Join-Path $Work 'badacct\cloudflare-account.key'), (ConvertFrom-SecureString -SecureString (New-Secure 'xyz')))
Set-UserOnlyAcl -Path (Join-Path $Work 'badacct\cloudflare-account.key')
[System.IO.File]::WriteAllText((Join-Path $Work 'plainacct\cloudflare-account.key'), $acctDummy)
Set-UserOnlyAcl -Path (Join-Path $Work 'plainacct\cloudflare-account.key')
New-Item -ItemType Directory -Force -Path (Join-Path $fake 'secrets4') | Out-Null
Copy-Item -LiteralPath $groqStore -Destination (Join-Path $fake 'secrets4\groq.key') -Force
$cases19 = @(
    @{ n = 'gsk_ in an argument'; s = $groqStore; a = @('--provider', 'groq', '--label', 'gsk_abcdefghij') },
    @{ n = 'cfat_ in an argument'; s = $cfStore; a = @('--provider', 'cloudflare', '--label', 'cfat_abcdefghij') },
    @{ n = 'cfk_ in an OpenRouter run'; s = $store; a = @('--free-only', '--label', 'cfk_abcdefghij') },
    @{ n = 'the account id in an argument'; s = $cfStore; a = @('--provider', 'cloudflare', '--label', "x$acctDummy") },
    @{ n = 'the account id in capitals'; s = $cfStore; a = @('--provider', 'cloudflare', '--label', "x$($acctDummy.ToUpper())") },
    @{ n = 'a key stored for another provider'; s = (Join-Path $mix 'openrouter.key'); a = @('--free-only', '--label', "x$groqPlain") },
    @{ n = '-AllowPaid with groq'; s = $groqStore; a = @('--provider', 'groq'); ap = $true },
    @{ n = 'an unknown provider'; s = $groqStore; a = @('--provider', 'mistral') },
    @{ n = 'two providers'; s = $groqStore; a = @('--provider', 'groq', '--provider', 'cloudflare') },
    @{ n = '--provider without a value'; s = $groqStore; a = @('--provider') },
    @{ n = 'another --api-key-env'; s = $groqStore; a = @('--provider', 'groq', '--api-key-env', 'OTHER_VAR') },
    @{ n = 'another --account-id-env'; s = $cfStore; a = @('--provider', 'cloudflare', '--account-id-env', 'OTHER_VAR') },
    @{ n = 'no account id file'; s = (Join-Path $Work 'noacct\cloudflare.key'); a = @('--provider', 'cloudflare') },
    @{ n = 'an account file open to Everyone'; s = (Join-Path $Work 'wideacct\cloudflare.key'); a = @('--provider', 'cloudflare') },
    @{ n = 'a malformed account id'; s = (Join-Path $Work 'badacct\cloudflare.key'); a = @('--provider', 'cloudflare') },
    @{ n = 'an account id that is not a DPAPI blob'; s = (Join-Path $Work 'plainacct\cloudflare.key'); a = @('--provider', 'cloudflare') },
    @{ n = 'a Groq key inside a git working tree'; s = (Join-Path $fake 'secrets4\groq.key'); a = @('--provider', 'groq') }
)
$bad19 = @()
foreach ($case in $cases19) {
    Clear-Probe
    $a = $case.a
    $ap = [bool]$case.ap
    & $run -SecretPath $case.s -Python $Python -RunPy $Probe -AllowPaid:$ap @a
    $c = $LASTEXITCODE
    if ($c -ne 2 -or (Test-Path -LiteralPath $marker)) { $bad19 += "$($case.n): exit $c, child ran: $(Test-Path -LiteralPath $marker)" }
}
Remove-Item Env:\PROBE_MARKER -ErrorAction SilentlyContinue
Report ($bad19.Count -eq 0) 'provider-launcher-refusals' ("$($cases19.Count) refusals, each exit 2 with no child started" + $(if ($bad19) { '; ' + ($bad19 -join '; ') } else { '' }))

# -- 20. --provider passes through powershell -File (as the runbook launches the script), with --output --
Clear-Probe
$env:PROBE_OUT = $probeOut
$env:PROBE_ENV_NAME = 'GROQ_API_KEY'
$outFile20 = Join-Path $Work 'groq out.jsonl'
$errFile = Join-Path $Work 'run-err20.txt'
$proc = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', "`"$run`"", '-SecretPath', "`"$groqStore`"", '-Python', "`"$Python`"", '-RunPy', "`"$Probe`"", '--provider', 'groq', '--output', "`"$outFile20`"") -NoNewWindow -Wait -PassThru -RedirectStandardError $errFile
$p20 = Read-Probe
$want20 = @('--provider', 'groq', '--output', $outFile20, '--api-key-env', 'GROQ_API_KEY')
$args20 = $p20 -and ((@($p20.argv) -join '|') -ceq ($want20 -join '|'))
Remove-Item Env:\PROBE_OUT, Env:\PROBE_ENV_NAME -ErrorAction SilentlyContinue
Report ($proc.ExitCode -eq 0 -and $args20 -and $p20.sha256 -eq $groqSha) 'provider-through-file' "powershell -File with --provider groq and --output: exit $($proc.ExitCode), run.py received both intact: $args20"

# -- 21. --key-status through the launcher, run.py itself against the mock: Groq's model list, Cloudflare's token
#        verify and model search; no key, no key prefix and no account id on the console --
$cfRoot = $BaseUrl -replace '/api/v1$', '/client/v4'
$bad21 = @()
foreach ($case in @(@{ n = 'groq'; s = $groqStore; a = @('--provider', 'groq', '--key-status', '--base-url', $BaseUrl); want = 'key: accepted' },
                    @{ n = 'cloudflare'; s = $cfStore; a = @('--provider', 'cloudflare', '--key-status', '--base-url', $cfRoot); want = 'token: active' })) {
    $ksOut = Join-Path $Work "ks-$($case.n)-out.txt"
    $ksErr = Join-Path $Work "ks-$($case.n)-err.txt"
    $argList = @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', "`"$run`"", '-SecretPath', "`"$($case.s)`"", '-Python', "`"$Python`"") + $case.a
    $proc = Start-Process -FilePath 'powershell.exe' -ArgumentList $argList -NoNewWindow -Wait -PassThru -RedirectStandardOutput $ksOut -RedirectStandardError $ksErr
    $text = ''
    foreach ($f in @($ksOut, $ksErr)) { if (Test-Path -LiteralPath $f) { $text += [string](Get-Content -LiteralPath $f -Raw) } }
    # Key-shaped text is a prefix and 8 or more key characters (the report names a token's kind as "(cfat_)").
    $shown = $text.Contains($groqDummy) -or $text.Contains($cfDummy) -or $text.Contains($acctDummy) -or ($text -match '(gsk_|cfat_|cfut_)[A-Za-z0-9_-]{8,}')
    if ($proc.ExitCode -ne 0 -or -not $text.Contains($case.want) -or $shown) { $bad21 += "$($case.n): exit $($proc.ExitCode), report found: $($text.Contains($case.want)), secret shown: $shown" }
}
Report ($bad21.Count -eq 0) 'provider-key-status' ("groq and cloudflare --key-status through the launcher: exit 0, report printed, no key, prefix or account id shown" + $(if ($bad21) { '; ' + ($bad21 -join '; ') } else { '' }))

# -- 22. Remove through remove-provider-key.ps1 (which runs remove-groq-key.ps1 and remove-cloudflare-token.ps1): the key
#        files and the account id file are gone; this test's other copies are removed too --
& $removeP -Provider groq -SecretPath $groqStore
$r1 = $LASTEXITCODE
& $removeP -Provider cloudflare -SecretPath $cfStore
$r2 = $LASTEXITCODE
$gone = -not (Test-Path -LiteralPath $groqStore) -and -not (Test-Path -LiteralPath $cfStore) -and -not (Test-Path -LiteralPath $cfAccount)
& $removeP -Provider mistral
$r3 = $LASTEXITCODE
foreach ($d in @('noacct', 'wideacct', 'badacct', 'plainacct')) {
    & $removeP -Provider cloudflare -SecretPath (Join-Path $Work "$d\cloudflare.key") | Out-Null
}
Report ($r1 -eq 0 -and $r2 -eq 0 -and $gone -and $r3 -eq 2) 'provider-remove' "groq exit $r1, cloudflare exit $r2; key and account files gone: $gone; an unknown provider: exit $r3"

# -- 9. Remove --
& $remove -SecretPath $store
$c = $LASTEXITCODE
Report ($c -eq 0 -and -not (Test-Path -LiteralPath $store)) 'remove' "exit $c; key file gone: $(-not (Test-Path -LiteralPath $store))"

if ($script:failures -gt 0) { exit 1 }
exit 0
