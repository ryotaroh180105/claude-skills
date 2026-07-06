---
name: intel-hub
description: hermes-relay経由で調べた原則・知見（システムR）やSNS投稿（システムG）を intel/ 配下のMarkdown+YAML frontmatterレコードとして正規化・蓄積し、Grepベースで再検索するスキル。「intelに入れて」「intelで検索」「調べてDBに蓄積」「リサーチDB」「過去に調べたことを探して」といった依頼で使う。単に「◯◯を調べて」だけの依頼（DB蓄積の指示なし）では発動しない。X収集そのものは twitter-intel、ROADMAP候補出しは github-trends/pickup-automation の担当であり、本スキルはその結果をDB化・再検索する後段工程を担う。現状 Phase 1（収集→保存→検索）のみ実装済み。週次分析・矛盾検出（Phase 2）、ブックマーク/Kindle取り込み（Phase 3）は未実装。
---

# intel-hub（Phase 1: 収集→保存→検索）

`intel/` 配下の Markdown レコードDBへの ingest（正規化して保存）と検索を行う。
スキーマ・運用ルールの正は `intel/README.md`。処理フロー・エッジケースの正は
`docs/designs/03-intel-hub.md`（本ファイルはその実装のPhase 1部分）。

**未実装（呼ばれても案内するだけ）**: 週次SNS分析レポート、矛盾検出、ブックマーク取り込み、
Kindleリサーチ。該当の依頼が来たら「Phase 2/3 は未実装」と伝え、設計書 §3 を参照するよう案内する。

## 1. 収集（ingest）

### 1.1 入力

- ユーザーの調査依頼（例:「note の文章術の原則を調べて intel に入れて」）
- または既存の hermes-relay 結果ファイルの直接指定（例: ウォークスルーAのように
  `automation/results/<id>.md` を指定される）

### 1.2 エンジン選択（クエリ整形のみ。実行体は hermes-relay）

| 調査種別 | ヘッダ | 実行体 |
|---|---|---|
| 事実（法律・IR・公式ドキュメントの確認） | `engine: notebooklm` + `topic:` | NotebookLM Deep Research |
| トレンド・実践知（Web記事・比較） | `engine: hermes-web` | Hermes web_search/web_extract（Grok） |
| Xの投稿・反応・アカウント分析 | ヘッダなし | Hermes x_search（Grok） |

hermes-web が未稼働（docs/hermes-web-engine-design.md の受け入れテスト未完了）の場合は
上表の hermes-web 行を notebooklm に読み替える。engine 名をハードコードせず、CLAUDE.md /
本表のルーティングに従う。

クエリの整形手順（enqueue・ポーリングのコマンド含む）は `plugins/hermes-x-search/skills/hermes-x-search/SKILL.md`
の「Automated relay」節をそのまま使う（本スキルは変更・再実装しない）。日本語指定・
出力セクション指定・根拠URL必須・逐語引用・ASCIIダブルクォート禁止のチェックリストに従う。

### 1.3 正規化（結果 → レコード）

1. 結果本文（またはユーザーが直接渡した調査結果）から原則・投稿・知見を抽出する。
   1結果あたり最大10件。根拠URLの無い主張はレコード化しないか `confidence: unconfirmed` にする。
2. 1原則 = 1 principle レコード（`claim` は1行・100文字以内）。sns-post も同じ手順で
   type: sns-post として正規化する。1つの調査結果から principle と sns-post の両方が
   取れる場合は両方作り `related` で相互リンクする。
3. ファイルパス: `intel/principles/<YYYY-MM>/<id>.md` または `intel/sns/<YYYY-MM>/<id>.md`。
   `<id>` は `intel/README.md` の共通 frontmatter 仕様どおり `<UTC時刻>-<slug>`。
4. frontmatter・本文セクションは `intel/README.md` の該当 type の仕様に厳密に従う
   （本文セクションは順序固定。空でも見出しは残し「該当なし」と書く）。
5. domain / post_type / platform 等の enum に当てはまらない場合は最も近い値を選び
   tags で補足する。enum への値追加はユーザー確認を取ってから行う。

### 1.4 重複チェック（レコード作成前に必ず実行）

`source_urls` の各URLを `intel/` 全体に Grep する。ヒットしたら新規作成せず既存 id を
報告する（再取り込みの明示指示があった場合のみ新規作成し `related` に旧 id を入れる。
旧レコードは変更しない）。

### 1.5 検証・保存

`python scripts/validate_intel.py` を実行し exit 0 を確認してからコミットする。
push はユーザー指示時のみ（リレークエリの enqueue 自体は hermes-relay ブランチへの
push が必須で、これは従来どおり許可されている）。

## 2. 検索

1. 入力例:「intel で note の文章術を検索して」
2. Grep を2段で実行する（`path: intel/` 固定。`intel/README.md` と `intel/contradictions.md`
   はスキーマ説明文にヒットするノイズ源なので検索対象から除外し、レコードファイル
   （`intel/principles/`・`intel/sns/`・`intel/books/` 配下）だけを見る）。
   1. frontmatter: `claim:` `tags:` `domain:` `book_title:` を対象に Grep
   2. ヒットが薄ければ本文全文を対象に Grep
3. 出力: 表 `| id | type | claim/要点1行 | confidence | source_urls |`。
   ヒット0件なら「0件。使用パターン: <実際に使ったGrepパターン>」と報告する
   （結果を捏造しない）。

## 3. エッジケース（Phase 1範囲）

| ケース | 期待挙動 |
|---|---|
| リレー結果が `status: error` | レコード化しない。frontmatter の stderr を読み診断を報告。再enqueueは1回まで |
| リレー結果 15分タイムアウト | 「watcher停止の可能性」を報告し、hermes-x-search SKILL.mdのトラブルシュート（watcher.log / schtasks確認）を案内。レコード化しない |
| 同一 source_url のレコードが既存 | 新規作成せず既存idを報告（再取り込み明示指示時のみ新規作成） |
| 根拠URLゼロの調査結果 | principle化しない。「出典なしのためレコード化見送り」と報告（捏造禁止） |
| metricsが1つも取れないsns-post | metrics全フィールドnullで保存可 |
| validate_intel.pyが既存レコードでエラー | 新規作業を止め、壊れたレコードの修正を先に提案 |
| 巨大な生テキストをレコードに入れたくなった | 入れない。生テキストはhermes-relayのresults/が保持。レコードは`relay_result_id`で参照する |

## 4. ネガティブ確認（発動範囲）

- 「◯◯を調べて」だけでDB蓄積の指示が無い場合、勝手に `intel/` へ書き込まない。
- X収集そのものの依頼は twitter-intel / hermes-x-search の担当。本スキルはその結果を
  DB化・再検索したいときにのみ発動する。
