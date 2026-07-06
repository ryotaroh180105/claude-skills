# intel/ — 情報集約リサーチDB

設計書: `docs/designs/03-intel-hub.md`。実装済みは **Phase 1（収集→保存→検索）のみ**。
Phase 2（週次分析・矛盾検出）/ Phase 3（ブックマーク・Kindle）はスキーマ・ディレクトリのみ
用意されており、処理は未実装。

DB の実体はこのリポジトリの `intel/` 配下の Markdown + YAML frontmatter。SQLite 等は
使わない（数千レコード規模なら Grep で足りる。理由は設計書 §4）。

## ディレクトリ

```
intel/
├── README.md                       # 本ファイル
├── contradictions.md               # 矛盾台帳（Phase 2、現状は空）
├── inbox/                          # コネクタ投入口（Phase 3、現状未使用）
│   └── done/                       # 取り込み済み inbox ファイルの移動先（Phase 3）
├── principles/<YYYY-MM>/<id>.md    # システムR レコード（原則）
├── sns/<YYYY-MM>/<id>.md           # システムG レコード（SNS投稿）
├── sns/reports/<account>-<YYYY-Www>.md  # 週次分析レポート（Phase 2、現状未使用）
└── books/<YYYY-MM>/<id>.md         # Kindle/書籍レコード（Phase 3、現状未使用）
```

## 共通 frontmatter（全レコード必須）

```yaml
---
id: 20260706T090000Z-note-hook-writing   # UTC時刻+slug。ファイル名（拡張子除く）と完全一致
type: principle | sns-post | book-note | bookmark
collected_at: 2026-07-06                  # 取り込み日（UTC、YYYY-MM-DD）
source_engine: hermes | hermes-web | notebooklm | manual | inbox
relay_result_id: 20260705T164640Z-x-viral-post-analysis  # リレー結果ファイル名。リレー経由でなければ null
source_urls:
  - https://x.com/...                     # 1件以上必須（source_engine: manual のみ空リスト可）
tags: [note, 文章術]                       # 自由語彙、小文字、1〜5個
confidence: confirmed | unconfirmed | superseded
related: []                               # 関連レコード id のリスト
contradicts: []                           # 矛盾レコード id のリスト（Phase 2 で運用開始）
---
```

- slug 規則: 小文字 ASCII とハイフンのみ、40文字以内。
- `superseded` は矛盾解決でユーザーが「負け」と判定したレコードに付ける（削除しない）。

## type: principle（システムR）追加フィールド

```yaml
domain: 資料作成 | 文章術 | SEO | SNS運用 | 技術 | 法務IR | 書籍知見   # enum 固定
claim: 結論を最初の3行に置くと読了率が上がる                            # 原則1行・100文字以内。矛盾検出の突合対象
```

本文セクション（この順・全部必須。空なら「該当なし」と書く）:

```markdown
## 根拠（逐語引用）
> 「…」 — https://...（出典URL、引用ごとに1つ）
## 適用条件・例外
## 未確認・断定できない点
```

## type: sns-post（システムG）追加フィールド

```yaml
platform: x | note | instagram            # enum 固定
account: "@handle または note ユーザー名"
post_url: https://x.com/.../status/...
posted_at: 2026-07-05T21:00:00+09:00      # 不明なら null
post_type: 体験談 | ノウハウ | 意見主張 | 実績報告 | 質問投げかけ | まとめリスト | 引用コメント | 告知   # enum 固定・8種
own_account: true | false                  # 自アカウントの投稿か
metrics:
  impressions: 12400                       # 取得不能なら null
  likes: 230
  reposts: 41
  replies: 12
  bookmarks: 88
metrics_as_of: 2026-07-06                  # metrics 取得日。全 null なら null
```

本文セクション: `## 投稿本文（逐語）` `## 伸びた/伸びない要因の仮説` `## 未確認・断定できない点`。

## type: book-note 追加フィールド（Phase 3、現状未使用）

```yaml
book_title: "…"
book_author: "…"                           # 不明なら null
kindle_location: "位置No.1234" | null
question: "読書中に出た疑問の原文" | null   # 疑問起点でない（ハイライト取込）なら null
```

本文セクション: `## 回答/要約` `## 引用（逐語）` `## 未確認・断定できない点`。

## type: bookmark 追加フィールド（Phase 3、現状未使用）

```yaml
bookmarked_at: 2026-07-14                  # 不明なら collected_at と同値
original_platform: x | web                 # enum 固定
```

本文セクション: `## 要点` `## 引用（逐語）` `## 未確認・断定できない点`。

## inbox ファイル（Phase 3、現状未使用）

`intel/inbox/<YYYY-MM-DD>-<slug>.md`。URL 1行1件（最大10件/ファイル）。
URL 行の直後に `> メモ` 行を置いてよい。

## 運用ルール（Phase 1 で有効なもの）

- レコード作成前に `source_urls` の各URLを `intel/` 全体に Grep し、既存ヒットがあれば
  新規作成せず既存 id を報告する（再取り込みの明示指示があった場合のみ新規作成し、
  `related` に旧 id を入れる。旧レコードは変更しない）。
- 根拠URLの無い主張は principle 化しない（`confidence: unconfirmed` にするか見送る）。
- 巨大な生テキストをレコードに入れない。生テキストは hermes-relay の `automation/results/`
  が保持し、レコードは `relay_result_id` で参照するだけにする。
- domain / post_type / platform / source_engine 等の enum に当てはまらない値が出た場合、
  最も近い値を選び `tags` で補足する。enum への値追加はユーザー確認を取ってから行う
  （勝手に増やすと過去レコードとの集計互換が壊れる）。
- tags の新規追加前に同義タグ（表記ゆれ）を Grep で確認し、既存があればそちらに合わせる。
- レコード追加は git commit まで。push はユーザー指示時のみ。
- `python scripts/validate_intel.py` が exit 0 になることを確認してからコミットする。
- 移行トリガー（`find intel -name '*.md' | wc -l` が 2000 超、またはリポジトリを public に
  する決定）に到達した場合、実装者は移行を実行せずユーザーに報告して指示を待つ。

詳細な処理フロー・エッジケースは `plugins/intel-hub/skills/intel-hub/SKILL.md` と
`docs/designs/03-intel-hub.md` を参照。
