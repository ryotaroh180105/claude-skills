# loops/sidejob-intake/schedule.md — Trigger 定義と登録記録

出典: `docs/designs/22-side-job-automation.md` §6.2, §9。

## 定義

- cron式: `0 22 * * *`（UTC） = JST 朝7時
- 対象: 本セッション（`create_trigger` のデフォルトモード。同一セッションへ再開）

## 登録状態

**登録済み**。設計書§12-4はユーザーの「君がトリガーで察知してよ」（2026-07-12）を承認として登録した。

```
trigger_id: trig_015WYXio1H7CWFirVMa7UrzA
登録日: 2026-07-12
モード: 自己バインド（同一セッションへ resume。create_new_session_on_fire なし）
次回実行: 2026-07-12T22:06:15Z（JST 翌7:06頃）以降、毎日
```

報告ルール（プロンプトに埋め込み済み）: 基準内の案件が1件以上あった時、または「検索ヒットあり・案件抽出0件」が3回連続した時のみユーザーに報告する。通常の0件は receipts に記録するだけで毎回報告しない（ユーザー要望に基づく）。

## 手動起動

登録前でも、ユーザーが「intakeループを実行して」と依頼すれば、本CONTRACT.mdの手順を手動で1回実行できる。
