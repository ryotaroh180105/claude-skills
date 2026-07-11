# loops/sidejob-expansion-review/rubric.md — Verifier 判定基準

出典: `docs/designs/22-side-job-automation.md` §13.5。**Doer の文脈は見せず、この rubric と `sidejob/pipeline-state.md`・`sidejob/config.md`・生成された候補リストのみを渡して判定させる**。

## 渡すもの

- `sidejob/pipeline-state.md`（全体）
- `sidejob/config.md`（現行カテゴリ表・除外条件）
- Doer が生成した候補リスト（`sidejob/expansion-candidates.md` の当該追記分）

## 判定項目

- (a) 実データを実際に引用しているか（pipeline-state.md に存在しない数値を候補リストが引用していないか。Epistemia対策。実データ無し期は「実データなし」と明記されているかを確認）
- (b) `sidejob/config.md` の除外条件・設計書§2.2 のスコープ除外カテゴリ（動画編集・データ入力・翻訳・AI生成イラスト主体の出品）を無断で推奨していないか
- (c) 直近の weekly-review 実行が4回未満（4週未満）の状態で、「推奨度」等の確定的なラベルを付けた拡張提案を出していないか（既存レーンの検証期間を優先する原則。実データ無し期でも候補の観察・記録自体は可だが、推奨度ラベルの付与は不可 — CONTRACT.md「実データ無し期の特例」参照）
- (d) `config.md`・`pipeline-state.md` 本体が本ループによって書き換えられていないか（追記対象は expansion-candidates.md のみであること）

## 出力フォーマット

```
- (a) 合格/不合格/不明: <理由1行>
- (b) 合格/不合格/不明: <理由1行>
- (c) 合格/不合格/不明: <理由1行>
- (d) 合格/不合格/不明: <理由1行>
- 総合: 合格 / 要修正 / 不明
```
