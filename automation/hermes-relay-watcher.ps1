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
$MaxParallel = if ($env:HERMES_MAX_PARALLEL) { [int]$env:HERMES_MAX_PARALLEL } else { 3 }

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

$LogFile = Join-Path $RelayDir "watcher.log"
function Log($msg) {
    "$((Get-Date).ToString('o')) $msg" | Add-Content -Path $LogFile -Encoding UTF8
}

# Single-instance lock. Directory creation is atomic; x_search runs can
# exceed the 1-minute schedule, so overlapping invocations must bail out.
# A lock is only broken when BOTH conditions hold: it is older than 20 min
# AND the process that created it (pid file inside the lock dir) is gone.
# Age alone is not enough: a legitimate serial batch once ran 22 minutes,
# a second watcher "broke" its live lock at the 20-minute mark, and the two
# processes then raced git operations in the same working tree -- which is
# how a stray .git\index.lock ended up wedging every subsequent run.
$LockDir = Join-Path $RelayDir ".watcher.lock.d"
$LockPidFile = Join-Path $LockDir "pid"

function Test-LockHolderAlive {
    if (-not (Test-Path $LockPidFile)) { return $false }
    $lockPid = Get-Content $LockPidFile -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $lockPid) { return $false }
    return [bool](Get-Process -Id $lockPid -ErrorAction SilentlyContinue)
}

try {
    New-Item -ItemType Directory -Path $LockDir -ErrorAction Stop | Out-Null
    Set-Content -Path $LockPidFile -Value $PID
} catch {
    $existing = Get-Item $LockDir -ErrorAction SilentlyContinue
    $isOld = $existing -and ((Get-Date) - $existing.CreationTime).TotalMinutes -gt 20
    if ($isOld -and -not (Test-LockHolderAlive)) {
        Log "breaking stale lock created at $($existing.CreationTime.ToString('o')) (holder process gone)"
        Remove-Item $LockDir -Force -Recurse -ErrorAction SilentlyContinue
        try {
            New-Item -ItemType Directory -Path $LockDir -ErrorAction Stop | Out-Null
            Set-Content -Path $LockPidFile -Value $PID
        } catch { Log "could not acquire lock after breaking stale one, skipping this run"; exit 0 }
    } else {
        exit 0
    }
}

# We hold the exclusive watcher lock, so no other watcher is mid-git-op.
# A leftover .git\index.lock can only be debris from a crashed/killed run
# (or the historical double-run race) -- clear it or every git command
# below fails and the queue wedges permanently.
Remove-Item (Join-Path $RelayDir ".git\index.lock") -Force -ErrorAction SilentlyContinue

try {
    git fetch -q origin $Branch
    if ($LASTEXITCODE -ne 0) { Log "git fetch failed (exit $LASTEXITCODE)"; exit 1 }
    git checkout -q $Branch 2>$null
    git reset -q --hard "origin/$Branch"

    $processed = $false
    $pending = Get-ChildItem (Join-Path $RelayDir "automation\queries\pending") -Filter *.md -ErrorAction SilentlyContinue
    Log "found $($pending.Count) pending quer(y/ies)"

    # Parallel execution: launch up to MaxParallel hermes jobs at once, then
    # collect them under one shared deadline (they all start together, so a
    # single QueryTimeout window covers each of them individually). Queries
    # beyond the cap stay pending and are picked up by the next run. Set
    # HERMES_MAX_PARALLEL=1 to restore serial behavior if concurrent OAuth
    # token refreshes ever start failing.
    $batch = @($pending | Select-Object -First $MaxParallel)
    $launched = @()
    foreach ($qfile in $batch) {
        $id = $qfile.BaseName
        $query = [IO.File]::ReadAllText($qfile.FullName)
        Log "starting hermes for ${id}"

        # Force UTF-8 for the child process's stdout/stderr. Hermes (a Python
        # CLI) writes UTF-8, but Start-Job spawns a fresh powershell.exe whose
        # console encoding defaults to the system's legacy codepage (e.g.
        # cp932 on Japanese Windows) unless told otherwise -- without this,
        # multi-byte Japanese text gets captured as mojibake even though
        # Hermes itself produced correct output.
        $job = Start-Job -ScriptBlock {
            param($bin, $q)
            [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
            $OutputEncoding = [System.Text.Encoding]::UTF8
            $env:PYTHONIOENCODING = "utf-8"
            # Escape embedded double quotes: PowerShell 5.1's native-command
            # argument passing breaks the argument at unescaped embedded
            # quotes, so a query containing "Fable 5" splits mid-string and
            # hermes sees the remainder as a positional command (fails in
            # ~1s with 'invalid choice'). Backslash-escaping survives the
            # MSVCRT command-line reparse.
            $q = $q -replace '"', '\"'
            & $bin -z $q --accept-hooks 2>&1 | Out-String
        } -ArgumentList $HermesBin, $query

        $launched += [pscustomobject]@{ Id = $id; File = $qfile; Job = $job; Start = Get-Date }
    }

    if ($launched.Count -gt 0) {
        $null = Wait-Job -Job ($launched | ForEach-Object { $_.Job }) -Timeout $QueryTimeout
    }

    foreach ($l in $launched) {
        if ($l.Job.State -eq "Completed") {
            $output = (Receive-Job $l.Job | Out-String).Trim()
            $status = "ok"
        } else {
            Stop-Job $l.Job -ErrorAction SilentlyContinue
            $output = "(timed out or failed after ${QueryTimeout}s; job state: $($l.Job.State))"
            $status = "error (timeout)"
        }
        Remove-Job $l.Job -Force -ErrorAction SilentlyContinue
        Log "finished $($l.Id): $status"

        $dur = [int]((Get-Date) - $l.Start).TotalSeconds
        $ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        $result = "---`nid: $($l.Id)`nstatus: $status`nexecuted_at: $ts`nduration_seconds: $dur`n---`n`n$output`n"
        $outPath = Join-Path $RelayDir "automation\results\$($l.Id).md"
        [IO.File]::WriteAllText($outPath, $result, (New-Object System.Text.UTF8Encoding($false)))

        Move-Item $l.File.FullName (Join-Path $RelayDir "automation\queries\done\$($l.Id).md") -Force
        git add -A
        git -c user.name=hermes-relay -c user.email=hermes-relay@local commit -q -m "hermes-relay: result for $($l.Id)"
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
