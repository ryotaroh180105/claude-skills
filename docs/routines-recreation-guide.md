# Routine 再作成ガイド（2026-07-12 定期実行全滅障害の恒久対応）

## 経緯（なぜ再作成が必要か）

2026-07-12、定期実行系タスク（Routine）がことごとくエラー停止していることが判明した。

- **根本原因**: 全 Routine が MCP ツール `create_trigger`（meta_mcp）で作成されており、この経路では**リポジトリ（Sources）とモデルを紐付けられない**。発火した新規セッションは空のホームディレクトリで起動し（Obsidian 系は clone なしで即失敗）、claude-skills 系は env の git 認証で clone できても push が 403「is not in this session's authorized repository set」で拒否される。
- **裏付け**:
  - Obsidian: vault-lint 実行セッションの報告「/home/user/Obsidian が存在しません（空のホームディレクトリのみ）」
  - biz-ops-guard 実行セッション（2026-07-12 00:00）: Doer/Verifier・SKILL.md 修正・コミットまで完了後、push 403 で作業消失
  - 診断プローブ（最小の git push タスク、2026-07-12 15:50 発火）も成果物ゼロ
  - Obsidian リポジトリの最終 push は 2026-07-07 09:29（Routine 作成の5分後）＝この型の Routine は一度も成功していない
  - 対照的に、既存セッションへ発火する型（send_later / persistent_session_id）は全て成功している（例: 2026-07-11 T4 フォローアップ → PR #41）
- **公式仕様**: Routine は「プロンプト＋リポジトリ＋モデル」をセットで保存し、実行ごとにリポジトリを clone する（https://code.claude.com/docs/en/routines）。リポジトリ・モデルの紐付けは claude.ai の Routine UI でのみ設定可能。
- **対応済み**: 壊れた Routine 7本は 2026-07-12 に無効化済み（削除はしていない。本ガイドの文面確認用）。診断プローブは削除済み。

## 再作成手順（ユーザー操作）

**意図**: Routine にリポジトリとモデルを紐付けられるのは claude.ai の UI だけのため、以下7本を UI で作り直す。

**内容**: claude.ai の Claude Code → ルーチン（Routines）→ 新規作成 で、下の各表のとおり設定する。プロンプトはコードブロックをそのままコピペする。**リポジトリ指定を必ず行う**（これが今回の障害の核心）。モデルは全て **Sonnet 5** を推奨（定型ループ実行は Sonnet の領分。Fable/Opus は不要 — 分業原則）。

**確認方法**: 作成後、各 Routine を1回手動実行（Run now）し、以下を確認して初めて完了とみなす:
- claude-skills 系 → 該当ブランチ（例: `claude/biz-ops-guard-quality-loop`）が push され PR ができること
- Obsidian 系 → `ryotaroh180105/Obsidian` に commit が push されること（対象データが無い日は「何もせず終了」報告でも可）

全て確認できたら、無効化済みの旧 Routine 7本の削除を Claude に依頼する（trigger_id は本ガイド各表に記載）。

---

## 1. SNS週次 配信→反応分析→次バッチループ

| 項目 | 設定 |
|---|---|
| スケジュール | 毎週月曜 09:00 JST（UTC cron: `0 0 * * 1`） |
| リポジトリ | ryotaroh180105/claude-skills |
| モデル | Sonnet 5 |
| 旧trigger_id（無効化済み） | `trig_01RUM6ujkzYZuNkhFjMMHD8T` |

```
ryotaroh180105/claude-skills の SNS週次ループを1周実行する。手順の正は LOOPS.md の「ループ設計: SNS週次 配信→反応分析→次バッチループ」と plugins/sns-ops-team/skills/sns-ops-team/SKILL.md（「配信→反応分析ループ」「週次バッチ」節）。

1. 冒頭ゲート: リポジトリの sns/ 配下に sns-strategy.md を持つアカウントディレクトリが1つも無ければ、何も作らず「SNSアカウントの初回セットアップが未実施のためスキップした。運用を始めるには通常セッションで『Xアカウントの運用を立ち上げたい』と依頼して sns-strategy.md を作成すること」とだけ報告して終了する。
2. アカウントごとに反応分析: post-queue.md の posted 行のうち投稿から48時間以上経過かつ数値未記録のものについて、hermes-relay（CLAUDE.md の手順。x_search で投稿URLの反応を調査）で数値を取得する。取得できない行は「数値なし」と記録し、推測で数字を埋めない（Epistemia対策）。分析は SKILL.md の規定どおり（アカウント内中央値との相対比較・数値なき学び禁止・3回ルール）。学びを sns-strategy.md の振り返りログに追記する。勝ちの型が3回再現していたら x-post-quality.md への追記案を PR 本文で提案する（直接書き換えない）。
3. 週次バッチ: SKILL.md の役割設計（リサーチ→企画→執筆→レビュー→キュー化）で今週分の投稿を post-queue.md に draft で追記する。本数は戦略ファイルの投稿頻度に従う。ステータスは全行 draft のまま。approved / posted への変更は絶対にしない。
4. ブランチ claude/sns-weekly-loop をデフォルトブランチ（事前に origin のデフォルトブランチ名を確認）から作り直してコミット・push し、PR を作成する。マージはしない（Ryo が承認する）。PR 本文には「今週の draft 本数一覧 / 前週の振り返りサマリー（数値と学び）/ approved にする手順（post-queue.md の該当行のステータスを approved に変更）」を書く。
5. Stop Rules: 最大60分・レビュー再生成2周まで。収束しなければ途中結果を PR に書いて終了。数値が2週連続取得不可なら PR に「数値取得手段の相談」を明記。炎上兆候（否定的リプ急増・フォロワー急減）を検知したら新規 draft を作らず、その報告のみで終了する。
```

## 2. biz-ops-guard 週次品質改善ループ v2

| 項目 | 設定 |
|---|---|
| スケジュール | 毎週日曜 09:00 JST（UTC cron: `0 0 * * 0`） |
| リポジトリ | ryotaroh180105/claude-skills |
| モデル | Sonnet 5 |
| 旧trigger_id（無効化済み） | `trig_017W4sdQVumbiTMdGt4xFPTX` |

```
ryotaroh180105/claude-skills の biz-ops-guard スキル（v2.0.0〜）の品質改善ループを1周実行する。手順の正は LOOPS.md の「ループ設計: biz-ops-guard 品質改善ループ」と docs/skill-quality-loop.md、修正の落とし込みは plugins/repo-skill-creator の SKILL.md。

1. plugins/biz-ops-guard/skills/biz-ops-guard/test-log.md を読み、前回の「次にやるべきこと」と既出シナリオを確認する
2. 別コンテキストの Agent（Doer）に、既出と重複しない新規テストシナリオ4〜6件（正常/境界/異常/逆用の4軸）で SKILL.md を適用させる。v2.0の実シグナルゲート・ファストパス/設計先行パスの分岐・シート1枚統合が実際に機能するかを重点的に見る
3. さらに別の Agent（Verifier）にルーブリック（修正必須/推奨/不要/削除推奨/不明。不明は不明と言わせる。過剰規定はYAGNIで棄却）で採点させる。**削除推奨カテゴリを必ず使う**: 今回のSKILL.mdを読み直し、削除・簡略化できる箇所を毎周最低1件提案させる（無ければ「削除候補なし」と明記させる。無言は不可）
4. 修正必須/推奨/削除推奨のみ SKILL.md に反映し、plugin.json の version を上げる（PATCHまたはMINOR。破壊的変更が要るならその旨をPRで提案するだけに留めMAJOR bumpは自動で行わない）。0件なら version 据え置き
5. test-log.md に結果と「次にやるべきこと」を追記
6. python3 scripts/validate_skills.py を通し、ブランチ claude/biz-ops-guard-quality-loop をデフォルトブランチ（claude/ryo-skills-repo-setup-hmkghn 相当。事前に origin のデフォルトブランチ名を確認すること）から作り直して push し、PR を作成する。マージはしない（Ryo が承認する）
7. 停止条件: 修正の往復は最大3回・60分以内。収束しなければ作業を止めて PR に状況を書く。test-log.md で2周連続「修正必須/推奨/削除推奨すべて0件」になっていたら、この Routine の卒業（無効化）を PR 本文で提案する
```

## 3. MISTAKES.md 週次レビューループ

| 項目 | 設定 |
|---|---|
| スケジュール | 毎週土曜 09:00 JST（UTC cron: `0 0 * * 6`） |
| リポジトリ | ryotaroh180105/claude-skills |
| モデル | Sonnet 5 |
| 旧trigger_id（無効化済み） | `trig_01MMifpFWbbf1rRvMtUpGoMv`（2026-07-12 に月次から週次化した際に MCP で作り直したもの） |

```
MISTAKES.md の週次レビューを実施する。手順: (1) LOOPS.md の「MISTAKES.md 週次レビューループ」と docs/mistakes-db-design.md を読む (2) 冒頭ゲート: 前回レビュー以降の新規/再発 M-NNN が0件かつルール行が20行以内なら、何もコミットせず「変更なし」とだけ報告して終了する（空回り防止） (3) `python3 scripts/validate_mistakes.py` でスキーマ検証 (4) 記録ログを集計: カテゴリ別件数・再発ありの件数・active ルール行数と20行上限への余裕 (5) 判定: CLAUDE.md への昇格候補 / 同カテゴリ統合候補 / 廃止候補（3ヶ月以上再発なしで環境固有のもの等）を挙げる (6) MISTAKES.md 末尾の「## レビュー履歴」に今回の集計と判断を2行以内で追記 (7) 変更（履歴追記＋提案の反映）を claude/mistakes-weekly-review ブランチ（origin のデフォルトブランチから作り直す）にコミット・push し、PR を作成する。マージはしない（Ryo が承認する human gate）。安全上限: 最大30分・エージェントは自分1体のみ・修正の往復は3回まで。収束しない場合は途中結果を PR 本文に書いて終了する。
```

## 4. Obsidian: reading-convert (nightly)

| 項目 | 設定 |
|---|---|
| スケジュール | 毎日 05:30 JST（UTC cron: `30 20 * * *`） |
| リポジトリ | ryotaroh180105/Obsidian |
| モデル | Sonnet 5 |
| 旧trigger_id（無効化済み） | `trig_012LhMoAyiDKCo62xMt5L8RF` |

```
毎晩の自動メンテナンス。最初に /home/user/Obsidian で `git checkout main && git pull origin main` を実行して最新状態にすること（クローン直後は古いブランチにいる可能性がある）。その後、最新の CLAUDE.md の「自動実行コマンド共通の前処理・後処理」と .claude/commands/reading-convert.md の手順に従って /reading-convert を実行する。日付はJST基準。未変換ハイライトがなければ何もせず終了、変換した場合のみ commit + push。完了したら結果を短く報告する。
```

## 5. Obsidian: daily-summary

| 項目 | 設定 |
|---|---|
| スケジュール | 毎日 06:00 JST（UTC cron: `0 21 * * *`） |
| リポジトリ | ryotaroh180105/Obsidian |
| モデル | Sonnet 5 |
| 旧trigger_id（無効化済み） | `trig_01YbwDJyXdsaY6gVcz9ywdxh` |

```
毎日の自動メンテナンス。最初に /home/user/Obsidian で `git checkout main && git pull origin main` を実行して最新状態にすること（クローン直後は古いブランチにいる可能性がある）。その後、最新の CLAUDE.md の「自動実行コマンド共通の前処理・後処理」と .claude/commands/daily-summary.md の手順に従って /daily-summary を実行する。対象はJSTでの前日の Daily/ ノート。対象が存在しない、または対応する日次サマリーが既にある場合は何もせず終了。生成した場合のみ commit + push。完了したら結果を短く報告する。
```

## 6. Obsidian: weekly-review

| 項目 | 設定 |
|---|---|
| スケジュール | 毎週月曜 06:00 JST（UTC cron: `0 21 * * 0`） |
| リポジトリ | ryotaroh180105/Obsidian |
| モデル | Sonnet 5 |
| 旧trigger_id（無効化済み） | `trig_01R1P3uAxzWw5vGV1Jap6Umk` |

```
週次の自動メンテナンス。最初に /home/user/Obsidian で `git checkout main && git pull origin main` を実行して最新状態にすること（クローン直後は古いブランチにいる可能性がある）。その後、最新の CLAUDE.md の「自動実行コマンド共通の前処理・後処理」と .claude/commands/weekly-review.md の手順に従って /weekly-review を実行する。対象はJSTで前週の月曜〜日曜。該当する週次レビューが既に存在すれば何もせず終了。生成した場合のみ commit + push。完了したら結果を短く報告する。
```

## 7. Obsidian: vault-lint

| 項目 | 設定 |
|---|---|
| スケジュール | 毎週日曜 06:00 JST（UTC cron: `0 21 * * 6`） |
| リポジトリ | ryotaroh180105/Obsidian |
| モデル | Sonnet 5 |
| 旧trigger_id（無効化済み） | `trig_01AxdtgG7LV14QWEZvtUK3vy` |

```
週次の自動メンテナンス。最初に /home/user/Obsidian で `git checkout main && git pull origin main` を実行して最新状態にすること（クローン直後は古いブランチにいる可能性がある）。その後、最新の CLAUDE.md の「自動実行コマンド共通の前処理・後処理」と .claude/commands/vault-lint.md の手順に従って /vault-lint を実行する。検出は `python3 scripts/vault_lint.py` の出力を正とし、レポートを Reviews/vault-lint-<JST日付>.md に書いて commit + push する。完了したら検出内容を短く報告する。
```

---

## 今後の使い分け（再発防止）

- **新規セッション発火型の定期実行** → claude.ai の Routine UI で作成（リポジトリ＋モデル必須）。MCP `create_trigger` では作らない。
- **既存セッションへの発火**（リマインダー・フォローアップ） → MCP の `send_later` / `create_trigger`＋`persistent_session_id`（従来どおり動作する）。
- どちらの型でも、**初回発火の成果物（push/PR/レポート）を確認するまで「作成完了」とみなさない**（MISTAKES.md M-008）。
