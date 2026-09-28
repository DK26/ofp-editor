# Starts llama.cpp's llama-server hidden for one GGUF, waits for /health and emits one object:
# ready, pid, port, load_s, gpu_mib_before, gpu_mib_after, out_log, err_log.
# Called by drive_pilot.py; usable by hand:
#   .\start-server.ps1 -Gguf <model.gguf> -LogDir <folder> [-Ctx 24576] [-Name label] [-LlamaServer <exe>]
# Nothing machine-specific lives here: the server binary is -LlamaServer, else the RWM_LLAMA_SERVER
# environment variable, else llama-server on PATH (the pilot used release b11146). -StopOllama unloads
# whatever an Ollama install holds in GPU memory first (it never deletes models). GPU memory is read with
# nvidia-smi when it exists and left empty otherwise. Messages go to the host, so the pipeline carries
# only the result object (the driver reads it as the last JSON line).
param(
  [Parameter(Mandatory = $true)][string]$Gguf,
  [Parameter(Mandatory = $true)][string]$LogDir,
  [int]$Ctx = 8192,
  [string]$Name = 'server',
  [int]$WaitSec = 240,
  [string]$LlamaServer = $(if ($env:RWM_LLAMA_SERVER) { $env:RWM_LLAMA_SERVER } else { 'llama-server' }),
  # Extra llama-server arguments, for example '-np','1','--cache-ram','4096'.
  [string[]]$ExtraArgs = @(),
  [switch]$StopOllama
)
$ErrorActionPreference = 'Stop'
$bin = (Get-Command $LlamaServer -CommandType Application | Select-Object -First 1).Source
New-Item -ItemType Directory -Force $LogDir | Out-Null

if ($StopOllama) {
  $ollama = Get-Command ollama -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($ollama) {
    $loaded = & $ollama.Source ps 2>$null | Select-Object -Skip 1 | Where-Object { $_.Trim() }
    foreach ($line in $loaded) {
      $model = ($line -split '\s+')[0]
      if ($model) { & $ollama.Source stop $model | Out-Null; Write-Host "stopped ollama model $model" }
    }
  }
}

# Refuse to start a second server: the pilot runs one model at a time on one GPU.
$old = Get-Process llama-server -ErrorAction SilentlyContinue
if ($old) { throw "llama-server already running (pid $($old.Id -join ','))" }

function Get-GpuMiB {
  $smi = Get-Command nvidia-smi -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $smi) { return $null }
  try { return ((& $smi.Source --query-gpu=memory.used --format=csv,noheader,nounits) | Select-Object -First 1).Trim() }
  catch { return $null }
}

$before = Get-GpuMiB
# A free loopback port: bind port 0, read the port the OS picked, release it.
$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
$listener.Start()
$port = $listener.LocalEndpoint.Port
$listener.Stop()

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$out = Join-Path $LogDir "$Name-$stamp.out.log"
$err = Join-Path $LogDir "$Name-$stamp.err.log"
$srvArgs = @('-m', "`"$Gguf`"", '--jinja', '-ngl', '99', '-c', "$Ctx", '--host', '127.0.0.1', '--port', "$port") + $ExtraArgs
$t0 = Get-Date
$p = Start-Process -FilePath $bin -ArgumentList $srvArgs -WindowStyle Hidden -RedirectStandardOutput $out -RedirectStandardError $err -PassThru
$ok = $false
while (((Get-Date) - $t0).TotalSeconds -lt $WaitSec) {
  if ($p.HasExited) { break }
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$port/health" -TimeoutSec 3
    if ($r.StatusCode -eq 200) { $ok = $true; break }
  } catch { }
  Start-Sleep -Milliseconds 500
}
$load = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
$after = Get-GpuMiB
if (-not $ok) { Get-Content $err -Tail 40 | Write-Host }
[pscustomobject]@{ ready = $ok; pid = $p.Id; port = $port; load_s = $load; gpu_mib_before = $before; gpu_mib_after = $after; out_log = $out; err_log = $err }
