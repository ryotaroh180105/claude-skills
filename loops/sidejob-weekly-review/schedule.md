# loops/sidejob-weekly-review/schedule.md — Trigger 定義と登録記録

出典: `docs/designs/22-side-job-automation.md` §6.5, §9。

## 定義

- cron式: `0 0 * * 0`（UTC） = JST 日曜朝9時
- 対象: 本セッション（`create_trigger` のデフォルトモード。同一セッションへ再開）

## 登録状態

**未登録**。設計書§12-4「Routine 登録の承認」に対するユーザー回答を得てから、リーダーセッションが `create_trigger` を実行し、以下に trigger_id を記録する。

```
trigger_id: (未登録)
登録日: (未登録)
```

## 手動起動

登録前でも、ユーザーが「週次レビューを実行して」と依頼すれば、本CONTRACT.mdの手順を手動で1回実行できる。
