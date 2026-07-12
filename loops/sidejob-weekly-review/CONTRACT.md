# loops/sidejob-weekly-review/CONTRACT.md — ゴール・境界・Stop Rules・human gate

出典: `docs/designs/22-side-job-automation.md` §6.5。

## ゴール

`sidejob/pipeline-state.md` を週次で集計し、レーン×カテゴリ別のKPIと撤退/継続判定を人間に提案する。

## Trigger

- Routine（cron `0 0 * * 0` UTC = JST 日曜朝9時）。**登録は §12 承認後**。現状は「未登録」（`schedule.md` 参照）。
- 手動起動も可。

## 境界（Doerが呼ぶ既存スキル・入力）

- 呼び出すスキル: affiliate-monetization（週次判定の4値ロジックを流用）
- 参照する設定: `pipeline-state.md`, `receipts/`（**実データのため private リポジトリ `ryotaroh180105/sidejob-ledger` で管理**。intake の CONTRACT.md「データの読み書き手順」と同じ手順でアクセスする）
- 更新するファイル: `pipeline-state.md` の notes 列（判定記録のみ。status は更新しない。`sidejob-ledger` リポジトリ側で更新・コミット）

## 手順（§6.5 の確定フロー）

1. `pipeline-state.md` をレーン×カテゴリ別に集計:
   - 応募数（`applied` 以降の件数）
   - 受注率（`won` 以降 ÷ `applied` 以降）
   - 売上（`paid` の price 合計）
   - 実効時給（売上 ÷ `hours_human` 合計）
   - **G1消化率**（`applied` ÷ `proposal-drafted` 以降の総数）
   - **累計運用コスト対売上**（receipts の概算トークン費合計 vs `paid` 合計）
2. 撤退基準（確定値）で4値（継続/調整/縮小/撤退）を提案:
   - Lane B のカテゴリで「応募20件以上かつ受注0」→縮小提案
   - Lane A/C で「出品後8週売上0」→テコ入れ（出品文改稿）1回→さらに4週で0なら撤退提案
   - 実効時給が2週連続で1,500円未満→そのカテゴリの単価下限を引き上げ提案
   - **開始8週未満のレーンには撤退提案を出さない**（早すぎる撤退が最頻の挫折要因）
3. KPI表と判定を提示。**採択は全てユーザー**（notes列への記録もユーザー承認後）

## Stop Rules

- **成功条件**: レーン別KPI表と判定4値の提示
- **安全上限**: 1実行=1回の集計・提示のみ（反復・自動再実行しない）

## 人間ゲート

- 撤退・縮小・調整・単価変更の**採択判断は全てユーザー**。本ループは提案のみ行う。

## 失敗モードチェック（loop-engineering §8）

- Blind Loop 回避: Verifier が集計値の再計算をチェック（rubric.md）
- Tangled Loop 回避: 集計ロジックのみ、既存Doerを呼ばない
- Amnesiac Loop 回避: pipeline-state.md の notes 列に判定記録
- Manual Loop 回避: Routine で自動起動（登録後）
