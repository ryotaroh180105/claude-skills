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

## 新しいスキルを追加する際の注意

`README.md` の「新しいスキルを追加する」節の手順に従う。加えて、コミット・push
だけでは完了とみなさず、実機インストール確認（`/plugin install` → `/plugin list`）
まで行って初めて完了とする。

## 調査は hermes-relay で実行する（リモートセッションでも）— Claude は整形のみ

調査依頼が来たとき、このリポジトリに push できるセッションなら**プラグイン
未導入でも実行できる**。ユーザーのローカルPCでタスクスケジューラ常駐の
watcher が `hermes-relay` ブランチを毎分監視し、エンジンに振り分ける:

- **X(Twitter)の調査** → ヘッダなし（デフォルト）= Hermes Agent の x_search
- **Web全般の調査**（記事・ドキュメント・比較など）→ クエリ先頭に
  `engine: notebooklm` + `topic: <短い調査トピック>` を付ける = NotebookLM の
  Deep Research + 出典付き回答
- **Claude の役割はクエリ整形と結果整形のみ**。Claude 自身の WebSearch を
  ユーザーの調査に使わない（パイプラインのデバッグ等のメタ用途のみ可）

手順（詳細は `plugins/hermes-x-search/skills/hermes-x-search/SKILL.md` が正）:

1. `hermes-relay` ブランチを clone し、`automation/queries/pending/<UTC時刻>-<slug>.md`
   にプロンプト全文（日本語指定・出力セクション指定・根拠URL必須。ASCIIの
   ダブルクォートは使わない）を置いて push
2. 1〜4分後に `automation/results/<同名>.md` が返る（frontmatter に engine/status、
   本文はセクション化された Markdown）

「このセッションからは Hermes/NotebookLM を使えない」と答えるのは誤り。使えない
のは `/plugin` のスキル読み込みであって、リレー経由の実行は git push さえできれば可能。
