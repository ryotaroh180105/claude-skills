# hermes-x-search: one-time local setup (Windows native, no WSL required)
#
# Run in PowerShell:
#
#   irm https://raw.githubusercontent.com/ryotaroh180105/claude-skills/hermes-relay/automation/setup-local.ps1 -OutFile "$env:TEMP\setup-local.ps1"
#   powershell -NoProfile -ExecutionPolicy Bypass -File "$env:TEMP\setup-local.ps1"
#
# What it does:
#   1. Installs Hermes Agent if missing (native Windows installer)
#   2. Runs X/Grok OAuth login (the ONLY interactive step; skipped if done)
#   3. Clones the hermes-relay branch to %USERPROFILE%\.hermes-relay
#   4. Registers a Task Scheduler job running the relay watcher every minute

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
    Write-Host "-- Hermes Agent が見つからないためインストールします"
    Invoke-Expression (Invoke-RestMethod https://hermes-agent.nousresearch.com/install.ps1)
    Refresh-Path
}
if (-not (Get-Command hermes -ErrorAction SilentlyContinue)) {
    Write-Host "!! hermes が PATH にありません。新しい PowerShell を開いてこのスクリプトを再実行してください" -ForegroundColor Red
    exit 1
}
$HermesPath = (Get-Command hermes).Source
Write-Host "-- hermes: $HermesPath"

# 2. git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "!! git が見つかりません。'winget install Git.Git' を実行し、新しい PowerShell でこのスクリプトを再実行してください" -ForegroundColor Red
    exit 1
}

# 3. X/Grok OAuth (唯一の手動ステップ。認証済みならスキップ)
if (-not (Test-Path (Join-Path $env:USERPROFILE ".hermes\auth.json"))) {
    Write-Host "-- X/Grok OAuth ログインを開始します（ブラウザが開きます。X Premium のアカウントでログイン）"
    hermes auth add xai-oauth
} else {
    Write-Host "-- OAuth 認証済み — スキップ"
}

# 4. リレー用クローン（hermes-relay ブランチのみ）
if (-not (Test-Path (Join-Path $RelayDir ".git"))) {
    Write-Host "-- $RelayDir にリレー用クローンを作成"
    git clone --branch $Branch --single-branch $RepoUrl $RelayDir
    if ($LASTEXITCODE -ne 0) { Write-Host "!! clone に失敗しました" -ForegroundColor Red; exit 1 }
} else {
    Write-Host "-- リレー用クローンあり — スキップ"
}
git -C $RelayDir push --dry-run origin $Branch 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "!! push できません。初回はブラウザで GitHub 認証が出るはずです。認証しても失敗する場合は 'git -C $RelayDir push origin $Branch' を手で実行してエラーを確認してください" -ForegroundColor Yellow
}

# 5. watcher 環境ファイル（Task Scheduler は PATH が最小限のため hermes の実体パスを固定）
"`$HermesBin = `"$HermesPath`"" | Set-Content (Join-Path $RelayDir "watcher.env.ps1") -Encoding UTF8

# 6. Task Scheduler 登録（毎分。多重起動は watcher 側のロックで防止）
$WatcherPath = Join-Path $RelayDir "automation\hermes-relay-watcher.ps1"
$TaskAction = "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$WatcherPath`""
schtasks /Create /F /TN "HermesRelayWatcher" /SC MINUTE /MO 1 /TR $TaskAction | Out-Null
Write-Host "-- タスクスケジューラ登録完了（毎分実行、タスク名: HermesRelayWatcher）"

# 7. 一度だけ即時実行（pending が空なら何もしません）
Write-Host "-- watcher を一度実行して動作確認します..."
& powershell -NoProfile -ExecutionPolicy Bypass -File $WatcherPath

Write-Host ""
Write-Host "✅ セットアップ完了" -ForegroundColor Green
Write-Host "   以後、Claude Code が hermes-relay ブランチに置いたクエリは毎分自動実行され、"
Write-Host "   結果が自動で push されます。ユーザー操作は不要です。"
Write-Host "   停止するには: schtasks /Delete /TN HermesRelayWatcher /F"
