# loops/sidejob-expansion-review/CONTRACT.md — ゴール・境界・Stop Rules・human gate

出典: `docs/designs/22-side-job-automation.md` §13。weekly-review（既存カテゴリの継続/調整/縮小/撤退）とは別の問い「次に何を追加すべきか」を扱う月次ループ。

## ゴール

`sidejob/pipeline-state.md` の実データ蓄積後、既存カテゴリの実績傾向と本設計書§0の静的市場知識を突き合わせ、拡張候補（新カテゴリ・新レーン）を提案する。

## Trigger

- Routine（cron `0 0 1 * *` UTC = 毎月1日）。**登録は §12 承認後**。現状は「未登録」（`schedule.md` 参照）。
- 手動起動も可。

## 境界

- 参照するファイル: `pipeline-state.md`（実データ。**private リポジトリ `ryotaroh180105/sidejob-ledger` で管理**。intake の CONTRACT.md「データの読み書き手順」と同じ手順でアクセス）, `sidejob/config.md`（現行カテゴリ表。構造のみで `claude-skills` リポジトリ管理）, `docs/designs/22-side-job-automation.md` §0.2/§0.4（静的市場知識）
- 更新するファイル: `expansion-candidates.md`（追記のみ。**実データ・分析結果を含むため `sidejob-ledger` private リポジトリで管理**）
- **書き換えないファイル**: `sidejob/config.md`（新カテゴリの採用はユーザー判断。本ループは提案のみ）、`pipeline-state.md` 本体

## 手順

1. `pipeline-state.md` をレーン×カテゴリ別に集計（weekly-review と同じロジック）: 受注率・実効時給・G1消化率
2. `config.md` の現行カテゴリ表と、設計書§0.2（自動化適性・単価圧力）・§0.4（X実例）の静的知識を突き合わせる
3. 現行カテゴリの実データ傾向（高実効時給/低実効時給）から、隣接カテゴリへの拡張可否を推論する
4. 候補を `sidejob/expansion-candidates.md` に日付見出しで追記する。各候補に「推奨度（高/中/低/非推奨）」「根拠（実データ or 市場調査のどちらに基づくか明記）」「必要な新規スキルの有無」を書く

## 実データ無し期の特例

Phase 0（アカウント未開設）中は、静的市場知識のみで候補を**観察・記録するのみ**とし、「推奨度」等の確定的なラベルは付けない（実データが無い段階での推奨度表示は、設計書§0.4で確認済みの挫折要因「早すぎる方向転換」を誘発しかねない）。エントリには「実データなし・市場調査ベースの観察記録（優先順位は未定）」と明記する。実データが weekly-review 4回分（4週）以上蓄積して初めて、推奨度付きの拡張提案に切り替える。

## Stop Rules

- **成功条件**: 候補リストの提示（expansion-candidates.md への追記）
- **安全上限**: 月1回・読み取り専用実行（config.md/pipeline-state.md への書き込みは一切行わない）

## 人間ゲート

- 候補の採択（config.md への実際の追加）は**全てユーザー判断**。本ループは提案のみで完結する。

## 失敗モードチェック（loop-engineering §8）

- Blind Loop 回避: Verifier が実データ引用・スコープ除外・実行頻度を分離チェック（rubric.md）
- Tangled Loop 回避: 集計は weekly-review と同ロジックを流用するのみ
- Amnesiac Loop 回避: expansion-candidates.md に追記専用で蓄積
- Manual Loop 回避: Routine で自動起動（登録後）
