# スキル・ルール・アプリ 分類カタログ

このリポジトリの全成果物を **種別（スキル / 常時ルール / アプリ）** と、スキル内の
**機能サブ分類** で整理した索引。新規追加時はこのカタログにも1行足す。

> 物理フォルダで分けない理由: `plugins/` 配下のディレクトリを移動すると
> `marketplace.json` の source パス・`/plugin install` 済みスキル・ローカル watcher が
> 壊れる（詳細は `docs/designs/04-repo-reorganization.md` §5.3）。よって分類はこの
> カタログ（規約）で担保し、ディレクトリはフラットのまま維持する。

---

## 種別1: スキル（`plugins/` 配下・オンデマンド発動）— 全29個

### 1-A. 品質ガード系（CLAUDE.md が常時適用 / 作業前チェック）

| スキル | 役割 |
|---|---|
| `token-saver` | 簡潔応答モード（トークン節約） |
| `yagni-guard` | 過剰設計防止（ponytail方式） |
| `biz-ops-guard` | プロダクト成立性（導入・保守・運用・マーケ・差別化） |
| `skill-design-rigor` | 設計規律（計画ゲート・自己反証・Fable-Sonnetブリッジ） |
| `model-switcher` | タスク種別別のモデル選択 |

### 1-B. 基盤・メタ系（スキル作成・仕事の進め方の土台）

| スキル | 役割 |
|---|---|
| `requirements-definition` | 要件定義（イシュー特定→MECE→ピラミッド） |
| `work-approach-playbook` | 仕事の進め方（着手前・報連相・完了報告） |
| `repo-skill-creator` | スキル作成・練度向上・導入確認 |
| `task-management` | TODO.md 一元管理 |
| `loop-engineering` | 自律ループ設計 |
| `session-start-hook` | SessionStart フック作成 |

### 1-C. SNS・発信・副業系

| スキル | 役割 |
|---|---|
| `sns-ops-team` | SNS運用マルチエージェント（企画・執筆・レビュー） |
| `sns-auto-posting` | X/Instagram/TikTok 投稿実行 |
| `article-writer` | note記事の企画・執筆・推敲 |
| `owned-media` | オウンドメディアSEO記事 |
| `lp-builder` | LP制作副業（ヒアリング→納品→修正） |

### 1-D. 情報収集基盤系

| スキル | 役割 |
|---|---|
| `hermes-agent-setup` | Hermes Agent + Grok/X Search 収集基盤 |
| `hermes-x-search` | X（Twitter）調査（x_search） |
| `agent-reach` | 各SNS横断の検索・読取 |
| `twitter-intel` | X情報収集・要約 |
| `github-trends` | GitHubトレンド取り込み |
| `pickup-automation` | 条件に合う情報の抽出・整形 |

### 1-E. インターン業務・ドキュメント系

| スキル | 役割 |
|---|---|
| `document-creation` | 議事録・提案書・週報・社外メール |
| `testcase-usecase` | テストケース・ユースケース洗い出し |
| `code-review-adr` | コードレビュー + アーキテクチャADR |
| `pr-review` | GitHub PR レビュー |
| `voicememo-pipeline` | 録音→文字起こし→議事録+フィードバック |

### 1-F. 学習系

| スキル | 役割 |
|---|---|
| `consulting-quiz` | コンサル・営業知識クイズ |
| `aws-exam-practice` | AWS試験（SAA等）模試 |

---

## 種別2: 常時ルール（`CLAUDE.md` の常時適用節・プラグインではない）

CLAUDE.md に直接書かれ、全セッションで自動適用される運用ルール。一部は上記スキルに
裏打ちされている（スキルを常時ONにするルール）。

| ルール | 実体 | 裏打ちスキル |
|---|---|---|
| 簡潔応答モード | CLAUDE.md「常時適用: token-saver」 | `token-saver` |
| 過剰設計防止 | CLAUDE.md「常時適用: yagni-guard」 | `yagni-guard` |
| プロダクト成立性の設計 | CLAUDE.md「常時適用: biz-ops-guard」 | `biz-ops-guard` |
| ミス・エラーの記録（MISTAKES.md） | CLAUDE.md「常時適用: MISTAKES.md」 | なし |
| ユーザーに操作を依頼する時の説明義務 | CLAUDE.md 該当節 | なし |
| 調査は hermes-relay で実行 | CLAUDE.md 該当節 | `hermes-x-search` |
| （設計中）Fable運用原則 | `docs/designs/07-claude-always-on-rules.md` | `skill-design-rigor` |

## 種別3: アプリ（別リポジトリ予定・現在は設計/未着手）

コード成果物として独立デプロイするもの。設計04の分類Eに従い `ryotaroh180105/<app-name>`
の別リポジトリに置く（このリポジトリには置かない）。

| アプリ | 状態 |
|---|---|
| コマtimes（KomaTimes） | 未着手 |
| テニスアプリ | 未着手（デプロイ目標） |
| Kindle AI リサーチ・要約補助ツール | 設計対象（`docs/designs/03-intel-hub.md` の一部） |
| 動画編集エージェント（FFmpeg+OpenMontage） | 未着手 |
| 社内タスク管理MTGアプリ変更 | 未着手（提案→実装） |

---

## 設計フェーズの成果物（参考）

Fable 5 で設計中の資産は `docs/designs/` に番号付きで格納:

| 番号 | 設計書 | 種別 |
|---|---|---|
| 00 | fable-sonnet-bridge（skill-design-rigor） | スキル（実装済み） |
| 01 | personal-growth-strategy-engine | スキル |
| 02 | agent-team | 常時ルール + 設定 |
| 03 | intel-hub（情報集約） | スキル + アプリ |
| 04 | repo-reorganization | スキル/規約 |
| 05 | analysis-skills（市場・競合・ボトルネック） | スキル |
| 06 | affiliate-monetization | スキル |
| 07 | claude-always-on-rules | 常時ルール |

全体像は `docs/fable5-design-assets.md` を参照。
