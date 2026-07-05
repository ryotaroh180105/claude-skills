# hermes-relay

このブランチは **Claude Code（リモート）と実機で動く Hermes Agent の間のメッセージキュー**です。
スキル本体・コードの開発はここでは行いません（`hermes-x-search` プラグイン参照）。

## 仕組み

```
Claude Code セッション                     実機（cron: 毎分）
─────────────────────                     ──────────────────────
automation/queries/pending/<id>.md  ───▶  hermes-relay-watcher.sh が検出
        （クエリを push）                    hermes -z "…" --accept-hooks 実行
                                            結果を automation/results/<id>.md へ
automation/results/<id>.md   ◀───────      クエリは queries/done/ へ移動して push
        （fetch して読む）
```

## ディレクトリ

| パス | 役割 |
|---|---|
| `automation/queries/pending/` | 未実行クエリ（1ファイル=1クエリ、内容は hermes に渡すプロンプト全文） |
| `automation/queries/done/` | 実行済みクエリ（watcher が移動） |
| `automation/results/` | 実行結果（frontmatter に status / executed_at / duration） |
| `automation/setup-local.sh` | 実機の初回セットアップ（1回だけ実行） |
| `automation/hermes-relay-watcher.sh` | cron から毎分実行される watcher |

## 実機セットアップ（1回だけ）

**Linux / macOS / WSL2:**

```bash
curl -fsSL https://raw.githubusercontent.com/ryotaroh180105/claude-skills/hermes-relay/automation/setup-local.sh | bash
```

**Windows ネイティブ（WSL不要、PowerShellで実行）:**

```powershell
git clone --branch hermes-relay --single-branch https://github.com/ryotaroh180105/claude-skills.git "$env:USERPROFILE\.hermes-relay"
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\.hermes-relay\automation\setup-local.ps1"
```

`irm ... -OutFile` 方式ではなく `git clone` を使うのは、`raw.githubusercontent.com` への名前解決がブロックされている環境（ISP/セキュリティソフトのDNSフィルタ）があるため。`git clone` は `github.com` だけを使うので回避できる。

Windows 版は cron の代わりにタスクスケジューラ（タスク名 `HermesRelayWatcher`）で毎分実行します。
停止: `schtasks /Delete /TN HermesRelayWatcher /F`

## 注意

- **このリポジトリが public の場合、クエリと結果も public になります。**
  秘密情報・未公開戦略をクエリに書かないでください。気になる場合はリポジトリを
  private にするか、`HERMES_RELAY_REPO` で別の private リポジトリを指定してください。
- 結果の反映まで通常 1〜4 分（cron 1分間隔 + x_search 実行 最大3分程度）かかります。
