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
# Per-engine caps, not one shared number: Hermes calls are independent CLI
# processes hitting a remote API, so concurrency mainly costs OAuth-refresh
# risk (3 concurrent ran clean in testing) -- default a bit higher. NotebookLM
# drives a single persistent Playwright/Chrome profile (~/.notebooklm/profiles),
# which is not documented as safe for concurrent access and browser profiles
# generally lock against a second process -- default to serial (1) until
# proven otherwise. Override per engine if you've verified your machine
# tolerates more: HERMES_MAX_PARALLEL_HERMES, HERMES_MAX_PARALLEL_NOTEBOOKLM.
$MaxParallelHermes = if ($env:HERMES_MAX_PARALLEL_HERMES) { [int]$env:HERMES_MAX_PARALLEL_HERMES } else { 5 }
$MaxParallelNotebookLm = if ($env:HERMES_MAX_PARALLEL_NOTEBOOKLM) { [int]$env:HERMES_MAX_PARALLEL_NOTEBOOKLM } else { 1 }
# How many same-topic notebooklm queries share a single research crawl (see
# below). Bounded so one job can't hold the lock for too long.
$MaxNotebookLmQueriesPerJob = if ($env:HERMES_MAX_NOTEBOOKLM_PER_JOB) { [int]$env:HERMES_MAX_NOTEBOOKLM_PER_JOB } else { 4 }

# Task Scheduler runs with a minimal environment; watcher.env.ps1 pins the
# hermes / notebooklm binary paths captured at setup time, and optionally
# $McUrl / $McApiKey for the Mission Control task queue integration below.
$HermesBin = $null
$NotebookLmBin = $null
$McUrl = $null
$McApiKey = $null
$envFile = Join-Path $RelayDir "watcher.env.ps1"
if (Test-Path $envFile) { . $envFile }
if (-not $HermesBin) {
    $cmd = Get-Command hermes -ErrorAction SilentlyContinue
    if ($cmd) { $HermesBin = $cmd.Source }
}
if (-not $NotebookLmBin) {
    $cmd = Get-Command notebooklm -ErrorAction SilentlyContinue
    if ($cmd) { $NotebookLmBin = $cmd.Source }
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

    # Parse engine/topic header for every pending file up front so batching
    # can cap each engine independently in the same run.
    $parsed = foreach ($qfile in $pending) {
        $raw = [IO.File]::ReadAllText($qfile.FullName)
        $engine = "hermes"
        $topic = $null
        $query = $raw
        $lines = $raw -split "`r?`n"
        if ($lines.Count -gt 0 -and $lines[0] -match '^engine:\s*(\S+)') {
            $engine = $Matches[1].ToLower()
            $rest = @($lines | Select-Object -Skip 1)
            if ($rest.Count -gt 0 -and $rest[0] -match '^topic:\s*(.+)$') {
                $topic = $Matches[1].Trim()
                $rest = @($rest | Select-Object -Skip 1)
            }
            $query = ($rest -join "`n").Trim()
        }
        [pscustomobject]@{ File = $qfile; Engine = $engine; Topic = $topic; Query = $query }
    }

    # Parallel execution: launch up to each engine's own cap at once (see caps
    # above), then collect everything under one shared deadline (all jobs
    # start together, so a single QueryTimeout window covers each of them
    # individually). Queries beyond a cap stay pending for the next run.
    # Anything other than "notebooklm" falls through to the hermes execution
    # branch below (an unrecognized engine value is treated as hermes, not
    # silently dropped) -- classify the same way here so such a query still
    # gets picked up rather than sitting in neither batch forever.
    $hermesBatch = @($parsed | Where-Object { $_.Engine -ne "notebooklm" } | Select-Object -First $MaxParallelHermes)

    # NotebookLM: `source add-research` (the web-crawl pass) is the expensive
    # step, not `ask`. Concurrency stays capped at MaxParallelNotebookLm (1)
    # for browser-profile safety, but multiple pending queries that share the
    # exact same `topic:` line get bundled into ONE job -- one research crawl,
    # then one `ask` per question -- instead of re-crawling the same topic
    # once per question. This is the fix for research being the bottleneck:
    # queue depth was growing because every notebooklm query paid the full
    # crawl cost even when several questions were about the same topic.
    $notebooklmPending = @($parsed | Where-Object { $_.Engine -eq "notebooklm" })
    $notebooklmGroup = @()
    if ($notebooklmPending.Count -gt 0) {
        $firstTopic = $notebooklmPending[0].Topic
        $notebooklmGroup = @($notebooklmPending | Where-Object { $_.Topic -eq $firstTopic } | Select-Object -First $MaxNotebookLmQueriesPerJob)
    }
    $batch = @($hermesBatch)
    Log "launching $($hermesBatch.Count) hermes + $($notebooklmGroup.Count) notebooklm-in-1-job (topic-grouped) (caps: hermes=$MaxParallelHermes, notebooklm-concurrency=$MaxParallelNotebookLm, notebooklm-per-job=$MaxNotebookLmQueriesPerJob)"

    $launched = @()
    foreach ($item in $batch) {
        $qfile = $item.File
        $id = $qfile.BaseName
        $query = $item.Query
        Log "starting hermes for ${id}"

        # Force UTF-8 for the child process's stdout/stderr: hermes writes
        # UTF-8, but Start-Job spawns a fresh powershell.exe whose console
        # encoding defaults to the system's legacy codepage (e.g. cp932 on
        # Japanese Windows) unless told otherwise -- without this, multi-byte
        # Japanese text gets captured as mojibake even though hermes itself
        # produced correct output. Also escape embedded double quotes:
        # PowerShell 5.1's native-command argument passing breaks the
        # argument at unescaped embedded quotes (a query containing "Fable 5"
        # split mid-string and hermes read the remainder as a positional
        # command, failing in ~1s).
        $job = Start-Job -ScriptBlock {
            param($bin, $q)
            [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
            $OutputEncoding = [System.Text.Encoding]::UTF8
            $env:PYTHONIOENCODING = "utf-8"
            $q = $q -replace '"', '\"'
            & $bin -z $q --accept-hooks 2>&1 | Out-String
        } -ArgumentList $HermesBin, $query

        $launched += [pscustomobject]@{ Id = $id; File = $qfile; Job = $job; Start = Get-Date; Engine = "hermes" }
    }

    # NotebookLM: one job handles the whole topic-group -- a single research
    # crawl followed by one `ask` per question -- so Wait-Job's shared
    # deadline below still applies, but the expensive crawl only happens once
    # per topic instead of once per question.
    $nbJob = $null
    $nbStart = $null
    if ($notebooklmGroup.Count -gt 0) {
        Log "starting notebooklm for $($notebooklmGroup.Count) quer(y/ies) sharing topic '$($notebooklmGroup[0].Topic)'"
        $nbStart = Get-Date
        if (-not $NotebookLmBin -or -not (Test-Path $NotebookLmBin)) {
            $nbJob = Start-Job -ScriptBlock {
                param($items)
                $items | ForEach-Object {
                    [pscustomobject]@{ Id = $_.Id; Output = "notebooklm CLI not found on this machine. Install it (pip install notebooklm-py), run 'notebooklm login', create/use a notebook, then re-run setup-local.ps1 so watcher.env.ps1 pins NotebookLmBin." }
                }
            } -ArgumentList @($notebooklmGroup | ForEach-Object { [pscustomobject]@{ Id = $_.File.BaseName } })
        } else {
            $nbJob = Start-Job -ScriptBlock {
                param($bin, $topic, $items)
                [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
                $OutputEncoding = [System.Text.Encoding]::UTF8
                $env:PYTHONIOENCODING = "utf-8"
                $researchLog = ""
                if ($topic) {
                    $t = $topic -replace '"', '\"'
                    $researchLog = "### research pass (source add-research, shared across $($items.Count) question(s))`n"
                    $researchLog += (& $bin source add-research $t --import-all 2>&1 | Out-String)
                    $researchLog += "`n"
                }
                $items | ForEach-Object {
                    $q = $_.Query -replace '"', '\"'
                    $answer = (& $bin ask $q 2>&1 | Out-String)
                    [pscustomobject]@{ Id = $_.Id; Output = "$researchLog### grounded answer (ask)`n$answer" }
                }
            } -ArgumentList $NotebookLmBin, $notebooklmGroup[0].Topic, @($notebooklmGroup | ForEach-Object { [pscustomobject]@{ Id = $_.File.BaseName; Query = $_.Query } })
        }
    }

    $waitTargets = @($launched | ForEach-Object { $_.Job })
    if ($nbJob) { $waitTargets += $nbJob }
    if ($waitTargets.Count -gt 0) {
        $null = Wait-Job -Job $waitTargets -Timeout $QueryTimeout
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
        Log "finished $($l.Id) [$($l.Engine)]: $status"

        $dur = [int]((Get-Date) - $l.Start).TotalSeconds
        $ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        $result = "---`nid: $($l.Id)`nengine: $($l.Engine)`nstatus: $status`nexecuted_at: $ts`nduration_seconds: $dur`n---`n`n$output`n"
        $outPath = Join-Path $RelayDir "automation\results\$($l.Id).md"
        [IO.File]::WriteAllText($outPath, $result, (New-Object System.Text.UTF8Encoding($false)))

        Move-Item $l.File.FullName (Join-Path $RelayDir "automation\queries\done\$($l.Id).md") -Force
        git add -A
        git -c user.name=hermes-relay -c user.email=hermes-relay@local commit -q -m "hermes-relay: result for $($l.Id)"
        $processed = $true
    }

    if ($nbJob) {
        $nbDur = [int]((Get-Date) - $nbStart).TotalSeconds
        $ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        if ($nbJob.State -eq "Completed") {
            $results = @(Receive-Job $nbJob)
            foreach ($item in $notebooklmGroup) {
                $id = $item.File.BaseName
                $r = $results | Where-Object { $_.Id -eq $id } | Select-Object -First 1
                $output = if ($r) { $r.Output } else { "(no output returned for this id -- job may have partially failed)" }
                $status = "ok"
                Log "finished $id [notebooklm, grouped]: $status"
                $result = "---`nid: $id`nengine: notebooklm`nstatus: $status`nexecuted_at: $ts`nduration_seconds: $nbDur`n---`n`n$output`n"
                [IO.File]::WriteAllText((Join-Path $RelayDir "automation\results\$id.md"), $result, (New-Object System.Text.UTF8Encoding($false)))
                Move-Item $item.File.FullName (Join-Path $RelayDir "automation\queries\done\$id.md") -Force
                git add -A
                git -c user.name=hermes-relay -c user.email=hermes-relay@local commit -q -m "hermes-relay: result for $id"
                $processed = $true
            }
        } else {
            Stop-Job $nbJob -ErrorAction SilentlyContinue
            foreach ($item in $notebooklmGroup) {
                $id = $item.File.BaseName
                Log "finished $id [notebooklm, grouped]: error (timeout)"
                $output = "(timed out or failed after ${QueryTimeout}s; job state: $($nbJob.State); shared research pass may not have completed)"
                $result = "---`nid: $id`nengine: notebooklm`nstatus: error (timeout)`nexecuted_at: $ts`nduration_seconds: $nbDur`n---`n`n$output`n"
                [IO.File]::WriteAllText((Join-Path $RelayDir "automation\results\$id.md"), $result, (New-Object System.Text.UTF8Encoding($false)))
                Move-Item $item.File.FullName (Join-Path $RelayDir "automation\queries\done\$id.md") -Force
                git add -A
                git -c user.name=hermes-relay -c user.email=hermes-relay@local commit -q -m "hermes-relay: result for $id"
                $processed = $true
            }
        }
        Remove-Job $nbJob -Force -ErrorAction SilentlyContinue
    }

    if ($processed) {
        git push -q origin $Branch
        if ($LASTEXITCODE -ne 0) {
            git pull -q --rebase origin $Branch
            git push -q origin $Branch
        }
    }

    # Mission Control task queue (optional, best-effort). Independent of the
    # git-based query/result flow above -- no commit/push involved, just a
    # REST poll-execute-report loop against a locally running dashboard.
    # Claims and processes at most one task per watcher run; Hermes is
    # search-focused, so tasks routed here should be research/search asks.
    if ($McUrl -and $McApiKey) {
        try {
            # X-Agent-Name attributes comments/activity to "Hermes" on the
            # dashboard instead of the API key's generic "API Access" identity.
            $mcHeaders = @{ "X-API-Key" = $McApiKey; "X-Agent-Name" = "Hermes" }
            $queueResp = Invoke-RestMethod -Uri "$McUrl/api/tasks/queue?agent=Hermes" -Headers $mcHeaders -Method Get -TimeoutSec 15
            # "continue_current" covers a task left in_progress by a previous
            # run that crashed/timed out before reporting back (or was claimed
            # out-of-band, e.g. a manual queue poll) -- without it, that task
            # is claimed forever but never actually processed.
            # Presence: refresh last_seen every tick so the dashboard's
            # Agent Squad / Office panels show Hermes online, and flip
            # busy/idle around actual task execution below.
            $presenceIdle = [System.Text.Encoding]::UTF8.GetBytes((@{ name = "Hermes"; status = "idle" } | ConvertTo-Json -Compress))
            Invoke-RestMethod -Uri "$McUrl/api/agents" -Headers $mcHeaders -Method Put -Body $presenceIdle -ContentType "application/json; charset=utf-8" -TimeoutSec 15 | Out-Null
            if (($queueResp.reason -eq "assigned" -or $queueResp.reason -eq "continue_current") -and $queueResp.task) {
                $mcTask = $queueResp.task
                Log "mission-control: claimed task $($mcTask.id) ($($mcTask.title)) [$($queueResp.reason)]"
                $presenceBusy = [System.Text.Encoding]::UTF8.GetBytes((@{ name = "Hermes"; status = "busy"; last_activity = "Searching: $($mcTask.title)" } | ConvertTo-Json -Compress))
                Invoke-RestMethod -Uri "$McUrl/api/agents" -Headers $mcHeaders -Method Put -Body $presenceBusy -ContentType "application/json; charset=utf-8" -TimeoutSec 15 | Out-Null
                $mcQuery = if ($mcTask.description) { $mcTask.description } else { $mcTask.title }
                $mcQuery = $mcQuery -replace '"', '\"'
                # Run hermes in a child job, same as the pending-query batch
                # above -- setting [Console]::OutputEncoding in THIS process
                # does not reliably apply when it was launched non-interactively
                # (e.g. by Task Scheduler), which is what caused mojibake here.
                $mcJob = Start-Job -ScriptBlock {
                    param($bin, $q)
                    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
                    $OutputEncoding = [System.Text.Encoding]::UTF8
                    $env:PYTHONIOENCODING = "utf-8"
                    & $bin -z $q --accept-hooks 2>&1 | Out-String
                } -ArgumentList $HermesBin, $mcQuery
                $null = Wait-Job -Job $mcJob -Timeout $QueryTimeout
                if ($mcJob.State -eq "Completed") {
                    $mcOutput = (Receive-Job $mcJob | Out-String).Trim()
                } else {
                    Stop-Job $mcJob -ErrorAction SilentlyContinue
                    $mcOutput = "(timed out or failed after ${QueryTimeout}s; job state: $($mcJob.State))"
                }
                Remove-Job $mcJob -Force -ErrorAction SilentlyContinue

                # Windows PowerShell 5.1's Invoke-RestMethod -Body <string>
                # re-encodes through the process's default codepage (e.g.
                # CP932 on Japanese Windows) before sending, mangling any
                # character that codepage can't represent. Encode to UTF-8
                # bytes ourselves so the JSON on the wire is exact.
                # The dashboard UI has no rendering path for the `resolution`
                # field (only comments are shown), so report results as a
                # comment instead -- same channel Claude Code's task
                # dispatch already uses successfully.
                $commentJson = @{ content = $mcOutput } | ConvertTo-Json -Compress
                $commentBytes = [System.Text.Encoding]::UTF8.GetBytes($commentJson)
                Invoke-RestMethod -Uri "$McUrl/api/tasks/$($mcTask.id)/comments" -Headers $mcHeaders -Method Post -Body $commentBytes -ContentType "application/json; charset=utf-8" -TimeoutSec 15 | Out-Null
                $statusJson = @{ status = "review" } | ConvertTo-Json -Compress
                $statusBytes = [System.Text.Encoding]::UTF8.GetBytes($statusJson)
                Invoke-RestMethod -Uri "$McUrl/api/tasks/$($mcTask.id)" -Headers $mcHeaders -Method Put -Body $statusBytes -ContentType "application/json; charset=utf-8" -TimeoutSec 15 | Out-Null
                Invoke-RestMethod -Uri "$McUrl/api/agents" -Headers $mcHeaders -Method Put -Body $presenceIdle -ContentType "application/json; charset=utf-8" -TimeoutSec 15 | Out-Null
                Log "mission-control: completed task $($mcTask.id), moved to review"
            }
        } catch {
            Log "mission-control: poll/execute failed: $($_.Exception.Message)"
        }
    }
} finally {
    Remove-Item $LockDir -Force -Recurse -ErrorAction SilentlyContinue
}
