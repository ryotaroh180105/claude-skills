# sidejob/pipeline-state.md — 案件台帳（唯一の進捗ファイル）

出典: `docs/designs/22-side-job-automation.md` §5.2。列・status値域はここから増減させない。

## status の値域と遷移

```
found → screened-out | proposal-drafted → applied | expired → won | lost
won → producing → qa → delivery-ready → delivered → revising | paid
revising → qa（2往復まで）
```

- `expired`: 提案文下書きが生成から24時間 G1 未消化のまま経過した状態。次回 intake が機械的に遷移させる
- `applied`（G1通過）・`won`・`delivered`（G3通過）・`paid` への遷移は**人間の操作結果の記録**であり、Claude は人間の報告なしにこれらへ変更しない
- `hours_human`: その案件に人間が使った累計時間（週次レビューで実効時給計算に使う）

## 台帳

| id | date | lane | channel | category | title | url | price | status | next | hours_human | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
