# hermes-relay watcher (Windows native)
#
# Runs on the user's Windows machine via Task Scheduler (every minute).
# Picks up query files queued on the hermes-relay branch by Claude Code
# sessions, executes them against the local Hermes Agent, and pushes the
# results back. Installed by setup-local.ps1. Safe to run manually.

$ErrorActionPreference = "Continue"

$RelayDir = if ($env:HERMES_RELAY_DIR) { $env:HERMES_RELAY_DIR } else { Join-Path $env:USERPROFILE ".hermes-relay" }
$Branch = "hermes-relay"
$QueryTimeout = if ($env:HERMES_QUERY_TIMEOUT) { [int]$env:HERMES_QUERY_TIMEOUT } else { 900 }

# Task Scheduler runs with a minimal environment; watcher.env.ps1 pins the
# hermes binary path captured at setup time.
$HermesBin = $null
$envFile = Join-Path $RelayDir "watcher.env.ps1"
if (Test-Path $envFile) { . $envFile }
if (-not $HermesBin) {
    $cmd = Get-Command hermes -ErrorAction SilentlyContinue
    if ($cmd) { $HermesBin = $cmd.Source }
}
if (-not $HermesBin -or -not (Test-Path $HermesBin)) {
    Write-Output "$(Get-Date -Format o) hermes binary not found (set `$HermesBin in $envFile)"
    exit 1
}

Set-Location $RelayDir

# Single-instance lock. Directory creation is atomic; x_search runs can
# exceed the 1-minute schedule, so overlapping invocations must bail out.
$LockDir = Join-Path $RelayDir ".watcher.lock.d"
try {
    New-Item -ItemType Directory -Path $LockDir -ErrorAction Stop | Out-Null
} catch {
    $existing = Get-Item $LockDir -ErrorAction SilentlyContinue
    if ($existing -and ((Get-Date) - $existing.CreationTime).TotalMinutes -gt 60) {
        Remove-Item $LockDir -Force -Recurse -ErrorAction SilentlyContinue
        try { New-Item -ItemType Directory -Path $LockDir -ErrorAction Stop | Out-Null } catch { exit 0 }
    } else {
        exit 0
    }
}

try {
    git fetch -q origin $Branch
    if ($LASTEXITCODE -ne 0) { exit 1 }
    git checkout -q $Branch 2>$null
    git reset -q --hard "origin/$Branch"

    $processed = $false
    $pending = Get-ChildItem (Join-Path $RelayDir "automation\queries\pending") -Filter *.md -ErrorAction SilentlyContinue
    foreach ($qfile in $pending) {
        $id = $qfile.BaseName
        $query = [IO.File]::ReadAllText($qfile.FullName)
        $start = Get-Date

        $job = Start-Job -ScriptBlock {
            param($bin, $q)
            & $bin -z $q --accept-hooks 2>&1 | Out-String
        } -ArgumentList $HermesBin, $query

        if (Wait-Job $job -Timeout $QueryTimeout) {
            $output = (Receive-Job $job | Out-String).Trim()
            $status = "ok"
        } else {
            Stop-Job $job
            $output = "(timed out after ${QueryTimeout}s)"
            $status = "error (timeout)"
        }
        Remove-Job $job -Force -ErrorAction SilentlyContinue

        $dur = [int]((Get-Date) - $start).TotalSeconds
        $ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        $result = "---`nid: $id`nstatus: $status`nexecuted_at: $ts`nduration_seconds: $dur`n---`n`n$output`n"
        $outPath = Join-Path $RelayDir "automation\results\$id.md"
        [IO.File]::WriteAllText($outPath, $result, (New-Object System.Text.UTF8Encoding($false)))

        Move-Item $qfile.FullName (Join-Path $RelayDir "automation\queries\done\$id.md") -Force
        git add -A
        git -c user.name=hermes-relay -c user.email=hermes-relay@local commit -q -m "hermes-relay: result for $id"
        $processed = $true
    }

    if ($processed) {
        git push -q origin $Branch
        if ($LASTEXITCODE -ne 0) {
            git pull -q --rebase origin $Branch
            git push -q origin $Branch
        }
    }
} finally {
    Remove-Item $LockDir -Force -Recurse -ErrorAction SilentlyContinue
}
