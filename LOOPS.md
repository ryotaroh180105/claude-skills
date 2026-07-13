# LOOPS.md — 再利用する自律ループ

`loop-engineering` スキルで設計したループの保存先。

> **2026-07-12 障害対応**: MCP（create_trigger）製の新規セッション発火型 Routine は Sources 未紐付けで全滅していたことが判明（MISTAKES.md M-008）。本ファイル記載の trigger_id は全て**無効化済み**。claude.ai の Routine UI での再作成手順とプロンプト全文は `docs/routines-recreation-guide.md` を参照。再作成後に本ファイルの trigger_id を更新すること。

## ループ設計: biz-ops-guard 品質改善ループ（v2、trigger_id: `trig_017W4sdQVumbiTMdGt4xFPTX`）

- ゴール: biz-ops-guard がテストシナリオで fail 0 を維持し、Verifier の判定（修正必須/推奨/削除推奨）が2周連続で0件になること（=卒業）。
- Trigger: タイマー。Claude Code Remote の Routine（週1、日曜 09:00 JST）で新規セッションを起動。手動では「biz-ops-guard を壁打ちしたい」で随時。
- Doer: docs/skill-quality-loop.md の Phase 1〜2。別コンテキストの Agent がテストシナリオ（4軸: 正常/境界/異常/逆用）を生成し SKILL.md を適用。v2.0からは実シグナルゲート・ファストパス分岐・シート1枚統合の実効性も見る。
- Verifier: Doer とは別の Agent。ルーブリック（修正必須/推奨/不要/**削除推奨**/不明）で採点。不明は不明と言わせる。YAGNI（過剰規定の棄却）も Verifier の責務。**削除推奨カテゴリを毎周最低1件使う**（無ければ「削除候補なし」と明記させる。無言は不可。旧v1で6版通じて削除ゼロだったラチェット構造の解消策）。
- Stop Rules:
  - 成功条件: 1周＝シナリオ1セットの実行→採点→反映まで。修正必須/推奨/削除推奨が0件なら version 据え置きで終了。
  - 安全上限: 1周につき Doer/Verifier 各1体まで・内側の修正往復は最大3回・60分以内。収束しなければ止めて Ryo に相談。
  - 卒業: 2周連続で修正0件 → Routine を無効化し、実利用時の症状ベース（repo-skill-creator）に移行。
- Memory/State: plugins/biz-ops-guard/skills/biz-ops-guard/test-log.md（毎周、結果と「次にやるべきこと」を追記）。
- Skills/Routines: CLAUDE.md、対象 SKILL.md、docs/skill-quality-loop.md、repo-skill-creator（修正の落とし込み）。
- Human gate: 自動実行時の反映は PR 作成まで（マージは Ryo が承認）。
- 失敗モードチェック: Blind（Verifier分離済み）/ Tangled（Doerは既存手順呼び出しのみ）/ Amnesiac（test-log.md）/ Manual（Routineで自動起動）いずれも該当なし。
- 履歴: 2026-07-05 1周目完了（v1.2.0、fail 0）。2026-07-05 2周目完了（実地適用、v1.3.0 + hermes-x-search v1.1.0、修正必須1件=実名プライバシー。卒業カウント0リセット）。2026-07-10 Fable監査によりv2.0.0へ破壊的変更（実シグナルゲート導入・ラダー廃止・シート1枚統合・5→3観点）。旧Routine（`trig_01PfvJPPnoZd4GzXqg24FepM`）は削除し、削除提案義務化を組み込んだ本Routineに再作成。

## ループ設計: MISTAKES.md 週次レビューループ

- ゴール: 再発防止ルールが「効いているか」を週1で棚卸しし、ルール行が20行上限内で高密度に保たれること（昇格・統合・廃止の判断が滞留しないこと）。
- Trigger: タイマー。Claude Code Remote の Routine（毎週土曜 09:00 JST = cron `0 0 * * 6` UTC、新規セッション起動、trigger_id: `trig_01MMifpFWbbf1rRvMtUpGoMv`）。
- Doer: 起動されたセッションが docs/mistakes-db-design.md の UC6 手順を実行（validate_mistakes.py → 集計 → 昇格/統合/廃止の提案 → レビュー履歴追記 → PR 作成）。
  - 冒頭ゲート: 前回レビュー以降の新規/再発 M-NNN が0件かつルール行が20行以内なら、何もコミットせず「変更なし」とだけ報告して即終了する（空回り防止。週次化に伴い「変更なし PR」も廃止）。
- Verifier: 2層。(1) `scripts/validate_mistakes.py`（CI でも毎 push 実行）がスキーマ・20行上限・ID整合を機械判定 (2) 提案の採否は Ryo が PR レビューで判断（Doer に自己マージさせない）。
- Stop Rules:
  - 成功条件: レビュー履歴の追記と PR 作成まで（新規/再発0件の週はゲートで即終了、PR なし）。
  - 安全上限: 最大30分・エージェント1体・修正往復3回。収束しなければ途中結果を PR に書いて終了。
- Memory/State: MISTAKES.md の「## レビュー履歴」セクション（レビュー実施週のみ2行以内で追記）。
- Skills/Routines: CLAUDE.md、MISTAKES.md 運用ルール、docs/mistakes-db-design.md。
- Human gate: マージは Ryo のみ。ルールの廃止・CLAUDE.md 昇格は必ず PR 経由。
- 失敗モードチェック: Blind（validate_mistakes.py + PR レビューで分離）/ Tangled（Doer は既存手順の実行のみ）/ Amnesiac（レビュー履歴に永続化）/ Manual（Routine で自動起動）いずれも該当なし。
- 履歴: 2026-07-05 設計・月次 Routine 作成（`trig_015S7ZVaajbca8vmZygMFoYE`、実行前に廃止）。2026-07-12 ユーザー指示により週次へ変更、Routine を作り直し（旧月次 Routine は削除）。初回実行は 2026-07-18（土）。

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

## ループ設計: affiliate-monetization 週次バッチ自動実行ループ

- ゴール: SKILL.mdの週次バッチ（note誘導ポスト企画→note記事制作(画像込み)→リンク更新→数値反映）が、ユーザーが毎週依頼しなくてもRoutineで起動し、post-queue.mdのdraft追記とnote原稿（画像ファイル込み）の生成まで自動完了すること。データ契約（funnel-config.md/link-registry.md/kpi-log.md）・役割分担は一切変更しない。
- Trigger: タイマー。Claude Code Remote の Routine（週1、曜日・時刻はユーザー指定）。
- Doer: affiliate-monetization `references/automation.md` §1。SKILL.md週次バッチの4工程をそのまま実行。note記事制作時の画像はarticle-writer `references/note-quality.md` 4-1節（OpenAI画像生成MCP既定/Gemini代替/Adobe Express手動フォールバック）でこの場で生成。
- Verifier: Doerと別Agent（model: haiku）がPR表記文言・link_id整合・誇大表現の不在を検証。不合格ならdraft/要修正のまま残す（不明を合格にしない）。
- Stop Rules: 60分・Doer/Verifier各1体・修正往復3回。funnel-config.md未作成（Step 0未実施）ならDoerを起動せず報告のみで終了（空回り防止）。post-queue.mdのdraft→approved昇格は自動化しない（ユーザーのみ）。
- Memory/State: funnel-config.md / link-registry.md / kpi-log.md（既存3ファイル）。
- Skills/Routines: affiliate-monetization、sns-ops-team、article-writer（画像生成含む）、sns-auto-posting（承認後）。
- Human gate: draft→approved昇格、note公開ボタン＋画像アップロード、週次数値の転記。
- 失敗モードチェック: Blind（Verifier分離、承認は人間）/ Tangled（既存スキル手順呼び出しのみ）/ Amnesiac（既存3ファイルに永続化）/ Manual（Routineで自動起動）いずれも該当なし。
- 履歴: 2026-07-12 設計。Routine登録待ち。

## ループ設計: affiliate-monetization KPI転記・判断ループ

- ゴール: kpi-log.mdの最新行にSKILL.mdのKPI判断表を適用し、継続/調整/縮小/撤退検討/撤退/保留の判断が毎週自動で1行追記されること。撤退系の判断は人間確認を経ること。
- Trigger: タイマー。Routine（週1、週次バッチRoutineの半日〜1日後を推奨）。
- Doer: affiliate-monetization `references/automation.md` §2。kpi-log.mdの数値にKPI判断表を上から順に適用。
- Verifier: 別Agentが「数値→条件→適用した判断」の対応を検算。不一致なら適用を保留し両論併記。
- Stop Rules: 20分・1体。撤退検討・撤退の適用は自動実行禁止（ユーザー確認ゲート）。
- Memory/State: kpi-log.md（判断列への追記）。
- Skills/Routines: affiliate-monetization のみ。
- Human gate: 撤退検討・撤退の最終判断、数値未転記継続時の運用継続確認。
- 失敗モードチェック: Blind（検算Agent分離）/ Tangled（既存ファイル読み書きのみ）/ Amnesiac（kpi-log.mdに永続化）/ Manual（Routineで自動起動）いずれも該当なし。
- 履歴: 2026-07-12 設計。Routine登録待ち。
