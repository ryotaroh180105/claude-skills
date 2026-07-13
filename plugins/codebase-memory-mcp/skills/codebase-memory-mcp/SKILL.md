---
name: codebase-memory-mcp
description: 大規模リポジトリを高速インデックス化し、構造検索・呼び出しチェーン追跡・影響範囲分析・デッドコード検出などをtree-sitterベースの知識グラフで行いたいときに使う導入・実行ガイド。「このリポジトリをインデックスして」「codebase-memory-mcpを使いたい」「関数の呼び出し元を全部追って」「この変更の影響範囲を調べて」といった依頼で発動。実体は本家 DeusData/codebase-memory-mcp のMCPサーバーをインストールする案内スキルで、このリポジトリにバイナリ・コードは同梱しない。LLM推論によるコードレビュー・可読性評価は code-review-adr、処理フローの図解は code-flow-visualizer が担当し、本スキルは構造検索エンジンとして両者と併用できる（役割が異なるため競合しない）。英語キーワード: code intelligence, knowledge graph, tree-sitter, MCP server, call chain trace, impact analysis, dead code detection.
---

# codebase-memory-mcp — コード知識グラフMCPサーバー

`codebase-memory-mcp`（`github.com/DeusData/codebase-memory-mcp`、MITライセンス）は、
tree-sitter AST解析（158言語）＋ Hybrid LSP型解決により、関数・クラス・呼び出しチェーン・
HTTPルート・サービス間リンクの知識グラフを構築するMCPサーバー。単一静的バイナリで
依存関係ゼロ。Linuxカーネル規模（2800万行）を3分でフルインデックス可能。

## このリポジトリでの位置づけ（Installer/Wrapper）

コードはこのリポジトリに複製しない。理由:

- 本体は Go/C製のバイナリ配布ツールで、`install.sh`/`install.ps1` がプラットフォーム判定・
  ダウンロード・エージェント設定ファイル書き換え（Claude Code含む11エージェント対応）まで
  自動化している。部分コピーは意味を持たない。
- リリースバイナリは署名・チェックサム・70+アンチウイルスエンジンでスキャン済み
  （本家 README のSecurity節参照）。

## 前提セットアップ

| 種別 | 名前 | 用途 | 未設定時の挙動 |
|---|---|---|---|
| バイナリ | codebase-memory-mcp本体 | インデックス作成・グラフクエリ | 未インストールならMCPツールが見えない |
| MCP登録 | `.mcp.json`（プロジェクト）または `~/.claude/.mcp.json`（グローバル） | Claude Codeへの接続 | install スクリプトが自動登録。手動設定も可 |

APIキー・環境変数は不要（全処理がローカル完結）。

## 導入手順

`install.sh` はエージェント設定ファイル（`.mcp.json`等）を自動書き換えする。`curl | bash` の
直接実行はスクリプト内容を確認しないまま実行することになるため、まず保存してから中身を
確認し、実行することを推奨する:

```bash
curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh -o install.sh
less install.sh   # 内容を確認してから実行する
bash install.sh
```

グラフ可視化UI（`localhost:9749`）も使う場合:

```bash
curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh | bash -s -- --ui
```

手動でMCP登録する場合は `.mcp.json` に以下を追記する:

```json
{
  "mcpServers": {
    "codebase-memory-mcp": {
      "command": "/path/to/codebase-memory-mcp",
      "args": []
    }
  }
}
```

Claude Codeを再起動し、`/mcp` で `codebase-memory-mcp`（14ツール）が見えることを確認する。

## 使い方

インストール後、対象リポジトリで「このプロジェクトをインデックスして」と言うだけで
`index_repository` が実行される。以降は以下のようなMCPツールが使える:

- `search_graph` — 構造検索（関数名・クラス名パターンマッチ）
- `trace_path` — 呼び出しチェーン追跡
- `impact_analysis` — 変更の影響範囲分析
- Cypherクエリによる自由なグラフ探索、デッドコード検出、ADR管理 等

Claude Code向けには `PreToolUse` フック（Grep/Glob呼び出し時にグラフ検索結果を
`additionalContext` として自動注入、`Read`はゲートしない）も自動設定される。

## 既存スキルとの役割境界

- `code-review-adr`: LLMによる観点別レビュー・ADR作成が対象。
- `code-flow-visualizer`: LLMによる静的読解からのMermaid図生成が対象。
- 本スキルはどちらでもなく、grep/read連打を代替する高速構造検索エンジンで、
  上記2スキルの調査フェーズを補強する形で併用する。

## 注意点

- コードは一切ここに同梱していない。実行は必ず本家インストールスクリプト経由。
- トラブル時は `/mcp` にサーバーが出ない→`.mcp.json`の絶対パスを確認、
  `index_repository`失敗→絶対パス指定、で本家READMEのTroubleshooting表を参照。
- 個人利用専用の導入ガイド。本家リポジトリの信頼性・継続性はこのリポジトリでは保証しない。
- 発動時、まず `~/.claude/.mcp.json` 等に `codebase-memory-mcp` が既に登録済みかを確認し、
  未導入なら先に導入手順を案内してから使い方の説明に進む。

---
出典: https://github.com/DeusData/codebase-memory-mcp（MITライセンス）
