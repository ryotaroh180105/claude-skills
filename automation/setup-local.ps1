# hermes-x-search: one-time local setup (Windows native, no WSL required)
#
# Run in PowerShell:
#
#   git clone --branch hermes-relay --single-branch https://github.com/ryotaroh180105/claude-skills.git "$env:USERPROFILE\.hermes-relay"
#   powershell -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\.hermes-relay\automation\setup-local.ps1"
#
# What it does:
#   1. Installs Hermes Agent if missing (native Windows installer)
#   2. Runs X/Grok OAuth login (the ONLY interactive step; skipped if done)
#   3. Clones the hermes-relay branch to %USERPROFILE%\.hermes-relay
#   4. Registers a Task Scheduler job running the relay watcher every minute
#
# NOTE: this file is plain ASCII on purpose. Windows PowerShell 5.1 reads
# .ps1 files using the system's legacy codepage unless the file has a UTF-8
# BOM, so non-ASCII text here reliably breaks string parsing on Japanese
# Windows installs. Keep all Write-Host text ASCII-only.

$ErrorActionPreference = "Stop"

$RepoUrl = if ($env:HERMES_RELAY_REPO) { $env:HERMES_RELAY_REPO } else { "https://github.com/ryotaroh180105/claude-skills.git" }
$RelayDir = if ($env:HERMES_RELAY_DIR) { $env:HERMES_RELAY_DIR } else { Join-Path $env:USERPROFILE ".hermes-relay" }
$Branch = "hermes-relay"

Write-Host "== hermes-x-search local relay setup (Windows native) =="

function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "Machine")
}

# 1. Hermes Agent
if (-not (Get-Command hermes -ErrorAction SilentlyContinue)) {
    Write-Host "-- hermes not found, installing Hermes Agent"
    Invoke-Expression (Invoke-RestMethod https://hermes-agent.nousresearch.com/install.ps1)
    Refresh-Path
}
if (-not (Get-Command hermes -ErrorAction SilentlyContinue)) {
    Write-Host "!! hermes is not on PATH. Open a new PowerShell window and re-run this script" -ForegroundColor Red
    exit 1
}
$HermesPath = (Get-Command hermes).Source
Write-Host "-- hermes: $HermesPath"

# 2. git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "!! git not found. Run 'winget install Git.Git', open a new PowerShell, then re-run this script" -ForegroundColor Red
    exit 1
}

# 3. X/Grok OAuth (the only manual step; skipped if already authenticated)
if (-not (Test-Path (Join-Path $env:USERPROFILE ".hermes\auth.json"))) {
    Write-Host "-- Starting X/Grok OAuth login (a browser window will open; log in with your X account)"
    hermes auth add xai-oauth
} else {
    Write-Host "-- OAuth already configured - skipping"
}

# 4. Relay clone (hermes-relay branch only)
if (-not (Test-Path (Join-Path $RelayDir ".git"))) {
    Write-Host "-- Creating relay clone at $RelayDir"
    git clone --branch $Branch --single-branch $RepoUrl $RelayDir
    if ($LASTEXITCODE -ne 0) { Write-Host "!! clone failed" -ForegroundColor Red; exit 1 }
} else {
    Write-Host "-- Relay clone already exists - skipping"
}
git -C $RelayDir push --dry-run origin $Branch 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "!! Cannot push to the relay repo yet. A GitHub auth prompt (browser) is expected on first push. If it still fails, run 'git -C $RelayDir push origin $Branch' manually to see the error" -ForegroundColor Yellow
}

# 5. Watcher env file (Task Scheduler runs with a minimal PATH, so pin the hermes binary path)
"`$HermesBin = `"$HermesPath`"" | Set-Content (Join-Path $RelayDir "watcher.env.ps1") -Encoding UTF8

# 6. Task Scheduler registration (every minute; overlapping runs are prevented by the watcher's own lock)
$WatcherPath = Join-Path $RelayDir "automation\hermes-relay-watcher.ps1"
$TaskAction = "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$WatcherPath`""
schtasks /Create /F /TN "HermesRelayWatcher" /SC MINUTE /MO 1 /TR $TaskAction | Out-Null
Write-Host "-- Task Scheduler job registered (runs every minute, task name: HermesRelayWatcher)"

# 7. Run once immediately (does nothing if the pending queue is empty)
Write-Host "-- Running the watcher once now to verify..."
& powershell -NoProfile -ExecutionPolicy Bypass -File $WatcherPath

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "   From now on, queries Claude Code pushes to the hermes-relay branch run"
Write-Host "   automatically every minute and results are pushed back. No action needed from you."
Write-Host "   To stop: schtasks /Delete /TN HermesRelayWatcher /F"
