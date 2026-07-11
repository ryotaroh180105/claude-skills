# loops/sidejob-expansion-review/schedule.md — Trigger 定義と登録記録

出典: `docs/designs/22-side-job-automation.md` §13.6。

## 定義

- cron式: `0 0 1 * *`（UTC） = 毎月1日
- 対象: 本セッション（`create_trigger` のデフォルトモード。同一セッションへ再開）

## 登録状態

**未登録**。設計書§12「Routine 登録の承認」と同じくユーザー回答を得てから、リーダーセッションが `create_trigger` を実行し、以下に trigger_id を記録する。

```
trigger_id: (未登録)
登録日: (未登録)
```

## 手動起動

登録前でも、ユーザーが「拡張候補レビューを実行して」と依頼すれば、本CONTRACT.mdの手順を手動で1回実行できる。2026-07-11 に実データ無し期の初回分析を1回実行済み（`sidejob/expansion-candidates.md` 参照）。
