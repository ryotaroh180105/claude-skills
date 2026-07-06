# claude-skills リポジトリでの作業指針

このリポジトリで作業する全セッションに、以下を最初から適用する（ユーザーの明示的なトリガーワードを待たない）。

## 常時適用: token-saver（簡潔応答モード, full）

`plugins/token-saver/skills/token-saver/SKILL.md` のルールを、ユーザーが
「stop caveman」「通常モードで」と言うまで常時適用する。

- 前置き・相槌・言い訳・埋め草語・ヘッジ表現を書かない。
- やったことの反復説明をしない。diff・ツール結果の再解説をしない。
- 箇条書き・表を文章より優先する。
- コード・エラー文字列・URL・数値・ユーザーの使用言語は一字も削らない。
- セキュリティ警告・破壊的操作の確認だけは例外的に通常の明瞭さに戻す。

## 常時適用: yagni-guard（過剰設計防止, full）

`plugins/yagni-guard/skills/yagni-guard/SKILL.md` の判断ラダーを、
コードを書く前に毎回適用する。

- 依頼にない抽象化・設定オプション・依存を追加しない。
- 重複は3箇所目が出るまで許容する。
- 意図的な簡略化には `ponytail:` コメントで上限を残す。
- 入力検証・エラー処理・セキュリティ・明示された要件は省略しない。

## 常時適用: biz-ops-guard（プロダクト成立性の設計）

他人に使ってもらう前提のアプリ・スキル・ツールを設計/実装/リリースする時は、
`plugins/biz-ops-guard/skills/biz-ops-guard/SKILL.md` を適用する。

- コードを書く前に Go/No-Go ラダー（ユーザー3人・乗り換え理由・導入5分・保守予算・配布経路）に答える。
- 導入・保守・運用・マーケティング・差別化の5観点でビジネス運用面シートを埋めてから実装する。
- No の項目は設計で解消するか「意図的に無視」とシートに明記する。暗黙に無視して実装に進まない。
- 自分専用ツールには適用しない（yagni-guard のみでよい）。

## 新しいスキルを追加する際の注意

`README.md` の「新しいスキルを追加する」節の手順に従う。加えて、コミット・push
だけでは完了とみなさず、実機インストール確認（`/plugin install` → `/plugin list`）
まで行って初めて完了とする。

## 調査は hermes-relay で実行する（リモートセッションでも）— Claude は整形のみ

**NotebookLM は使わない**（Google認証切れが常態化し不安定だったため廃止）。
Web全般の調査も含め、**すべての調査は Hermes Agent 1本**（X検索の x_search +
一般Web検索の web_search）で行う。エンジン切り替えのヘッダは不要。

調査依頼が来たとき、このリポジトリに push できるセッションなら**プラグイン
未導入でも実行できる**。ユーザーのローカルPCでタスクスケジューラ常駐の
watcher が `hermes-relay` ブランチを毎分監視し実行する:

- **X(Twitter)の調査もWeb全般の調査も同じ経路**（ヘッダなし）。Hermes Agent が
  クエリ内容から x_search（X投稿・スレッド・プロフィール）と web_search（記事・
  ドキュメント・比較記事等の一般Web）を自動選択する。日本語の自然文で
  「Xで〜を調べて」「〜についてWebで調べて」のように書けば自動で振り分けられる。
- **Claude の役割はクエリ整形と結果整形のみ**。Claude 自身の WebSearch を
  ユーザーの調査に使わない（パイプラインのデバッグ等のメタ用途のみ可）。
  ただし watcher が長時間詰まっている・エラーが続く等の障害時は、ユーザーの
  明示的な許可を得たうえで一時的に Claude 自身の WebSearch に切り替えてよい。

手順（詳細は `plugins/hermes-x-search/skills/hermes-x-search/SKILL.md` が正）:

1. `hermes-relay` ブランチを clone し、`automation/queries/pending/<UTC時刻>-<slug>.md`
   にプロンプト全文（日本語指定・出力セクション指定・根拠URL必須。ASCIIの
   ダブルクォートは使わない）を置いて push
2. 1〜4分後に `automation/results/<同名>.md` が返る（frontmatter に engine/status、
   本文はセクション化された Markdown）

「このセッションからは Hermes を使えない」と答えるのは誤り。使えないのは
`/plugin` のスキル読み込みであって、リレー経由の実行は git push さえできれば可能。

**注意**: `web_extract`（リンク先ページの全文抽出）は現状 xAI Web Search
（Grok）バックエンドが search-only のため失敗する。全文抽出が必要な依頼では
この制約をユーザーに伝え、web_search で得られる検索結果・スニペットの範囲で
回答する。
