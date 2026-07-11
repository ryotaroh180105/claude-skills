# loops/sidejob-weekly-review/rubric.md — Verifier 判定基準

出典: `docs/designs/22-side-job-automation.md` §6.5 Verifier節。**Doer の文脈は見せず、この rubric と pipeline-state.md・算出結果のみを渡して判定させる**。model: haiku 可（集計値の再計算チェックのみのため）。

## 渡すもの

- `sidejob/pipeline-state.md`（全体）
- Doer が算出したKPI表（応募数・受注率・売上・実効時給・G1消化率・運用コスト対売上・判定4値）

## 判定項目

- (a) 各KPIの計算式が正しいか（pipeline-state.md の値から独立に再計算し、Doer の算出値と一致するか）
- (b) 撤退基準の適用が正しいか（開始8週未満のレーンに撤退提案を誤って出していないか等）
- (c) status 列や pipeline-state.md 本体が本ループによって書き換えられていないか（notes 列以外は不変であること）

## 出力フォーマット

```
- (a) 合格/不合格/不明: <再計算した値と差異があれば明記>
- (b) 合格/不合格/不明: <理由1行>
- (c) 合格/不合格/不明: <理由1行>
- 総合: 合格 / 要修正 / 不明
```
