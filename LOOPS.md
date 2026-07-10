# LOOPS.md — 再利用する自律ループ

`loop-engineering` スキルで設計したループの保存先。

## ループ設計: biz-ops-guard 品質改善ループ

- ゴール: biz-ops-guard がテストシナリオで fail 0 を維持し、曖昧箇所（Verifier の修正必須/推奨）が2周連続で0件になること（=卒業）。
- Trigger: タイマー。Claude Code Remote の Routine（週1、日曜 09:00 JST）で新規セッションを起動。手動では「biz-ops-guard を壁打ちしたい」で随時。
- Doer: docs/skill-quality-loop.md の Phase 1〜2。別コンテキストの Agent がテストシナリオ（4軸: 正常/境界/異常/逆用）を生成し SKILL.md を適用。
- Verifier: Doer とは別の Agent。ルーブリック（修正必須/推奨/不要/不明）で採点。不明は不明と言わせる。YAGNI（過剰規定の棄却）も Verifier の責務。
- Stop Rules:
  - 成功条件: 1周＝シナリオ1セットの実行→採点→反映まで。修正必須/推奨が0件なら version 据え置きで終了。
  - 安全上限: 1周につき Doer/Verifier 各1体まで・内側の修正往復は最大3回・60分以内。収束しなければ止めて Ryo に相談。
  - 卒業: 2周連続で修正0件 → Routine を無効化し、実利用時の症状ベース（skill-creator）に移行。
- Memory/State: plugins/biz-ops-guard/skills/biz-ops-guard/test-log.md（毎周、結果と「次にやるべきこと」を追記）。
- Skills/Routines: CLAUDE.md、対象 SKILL.md、docs/skill-quality-loop.md、skill-creator（修正の落とし込み）。
- Human gate: 自動実行時の反映は PR 作成まで（マージは Ryo が承認）。
- 失敗モードチェック: Blind（Verifier分離済み）/ Tangled（Doerは既存手順呼び出しのみ）/ Amnesiac（test-log.md）/ Manual（Routineで自動起動）いずれも該当なし。
- 履歴: 2026-07-05 1周目完了（v1.2.0、fail 0）。2026-07-05 2周目完了（実地適用、v1.3.0 + hermes-x-search v1.1.0、修正必須1件=実名プライバシー。卒業カウント0リセット）。

## ループ設計: MISTAKES.md 月次レビューループ

- ゴール: 再発防止ルールが「効いているか」を月1で棚卸しし、ルール行が20行上限内で高密度に保たれること（昇格・統合・廃止の判断が滞留しないこと）。
- Trigger: タイマー。Claude Code Remote の Routine（毎月1日 09:00 JST、新規セッション起動、trigger_id: `trig_015S7ZVaajbca8vmZygMFoYE`）。
- Doer: 起動されたセッションが docs/mistakes-db-design.md の UC6 手順を実行（validate_mistakes.py → 集計 → 昇格/統合/廃止の提案 → レビュー履歴追記 → PR 作成）。
  - 冒頭ゲート: 前回レビュー以降の新規/再発 M-NNN が0件かつルール行が20行以内なら、「変更なし」PR も作らずレビュー履歴1行の追記のみで即終了する（空回り防止。設計17の唯一の採択差分をここに吸収）。
- Verifier: 2層。(1) `scripts/validate_mistakes.py`（CI でも毎 push 実行）がスキーマ・20行上限・ID整合を機械判定 (2) 提案の採否は Ryo が PR レビューで判断（Doer に自己マージさせない）。
- Stop Rules:
  - 成功条件: レビュー履歴の追記と PR 作成まで（提案ゼロの月は「変更なし」PR）。
  - 安全上限: 最大30分・エージェント1体・修正往復3回。収束しなければ途中結果を PR に書いて終了。
- Memory/State: MISTAKES.md の「## レビュー履歴」セクション（毎月2行以内で追記）。
- Skills/Routines: CLAUDE.md、MISTAKES.md 運用ルール、docs/mistakes-db-design.md。
- Human gate: マージは Ryo のみ。ルールの廃止・CLAUDE.md 昇格は必ず PR 経由。
- 失敗モードチェック: Blind（validate_mistakes.py + PR レビューで分離）/ Tangled（Doer は既存手順の実行のみ）/ Amnesiac（レビュー履歴に永続化）/ Manual（Routine で自動起動）いずれも該当なし。
- 履歴: 2026-07-05 設計・Routine 作成。初回実行は 2026-08-01。

## ループ設計: SNS週次 配信→反応分析→次バッチループ

- ゴール: X運用が「作って終わり」にならず、毎週「前週の数値分析 → 学びの還流 → 今週分のdraft作成」が人手ゼロで回ること。勝ちパターンが3回再現するたびに x-post-quality.md が実データで更新され続けること。
- Trigger: タイマー。Claude Code Remote の Routine（毎週月曜 09:00 JST = cron `0 0 * * 1` UTC、新規セッション起動、trigger_id: `trig_01RUM6ujkzYZuNkhFjMMHD8T`）。
- Doer: 起動されたセッションが sns-ops-team スキルの「配信→反応分析ループ」→「週次バッチ」を順に実行する。
  - 冒頭ゲート: `sns/<アカウント>/sns-strategy.md` が1つも無ければ何も作らず「初回セットアップ未実施のためスキップ。運用を始めるには『Xアカウントの運用を立ち上げたい』と依頼」とだけ報告して終了する（空回り防止）。
  - 数値取得: ユーザー提供値が振り返りログに未反映なら最優先で反映 → 無ければ hermes-relay で posted 行の投稿URLの反応を調査 → 取得不可は「数値なし」と記録（Epistemia対策: 推測で数字を埋めない）。
  - バッチ: リサーチ→企画→執筆→レビュー→post-queue.md に draft 追記（本数は戦略ファイルの投稿頻度）。
- Verifier: 2層。(1) ④レビュー担当エージェント（炎上・法令・トーン・AIっぽさ。executor と分離） (2) draft→approved の昇格は Ryo のみ（キュー行の自動承認禁止）。数値なき「学び」は書かない・1回の結果で戦略を変えない（3回ルール）。
- Stop Rules:
  - 成功条件: 振り返りログ追記＋今週分 draft 追記＋PR 作成まで（マージしない）。
  - 安全上限: 最大60分・レビュー再生成2周まで。収束しなければ途中結果を PR に書いて終了。
  - 数値が2週連続取得不可 → バッチは作るが PR に「数値取得手段の相談」を明記。
  - 炎上兆候（否定的リプ急増・フォロワー急減）→ 新規 draft を作らず、その報告のみで終了。
- Memory/State: `sns/<アカウント>/sns-strategy.md` の振り返りログ（数値・学び）と `post-queue.md`（キュー本体）。勝ち3回再現時は x-post-quality.md への追記を PR で提案。
- Skills/Routines: sns-ops-team（手順の正）、twitter-intel / hermes-relay（数値・リサーチ）、sns-auto-posting（配信。このループの外、approved 後に実行）。
- Human gate: ①approved への変更は Ryo のみ ②ファイル変更はすべて PR 経由でマージは Ryo ③戦略・リファレンスの書き換えは PR 内で提案として明示。
- 失敗モードチェック: Blind（レビュー担当分離＋approved は人間）/ Tangled（Doer は既存スキル手順の実行のみ）/ Amnesiac（振り返りログ＋post-queue に永続化）/ Manual（Routine で自動起動）いずれも該当なし。
- 履歴: 2026-07-10 設計・Routine 作成。戦略ファイル未作成のため、初回セットアップ完了までは毎週スキップ報告のみ。
