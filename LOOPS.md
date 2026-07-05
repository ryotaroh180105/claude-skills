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
