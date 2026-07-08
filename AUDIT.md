# AUDIT.md — Claude環境監査 2026-07-08

## 対象

- リモートセッション（本環境）。`~/.claude/projects` は本セッション分のみ可視のため、
  セッション分析はこの1セッション（575行のJSONL）に限定。複数日・複数セッションの
  傾向は見えていない点に注意。
- 含めたパス: `plugins/*/skills/*/SKILL.md`（40件）、`CLAUDE.md`、`.claude/settings.json`

## 資産棚卸し

- スキル数: 40（`plugins/` と `~/.claude/skills/` で一致、ズレなし）
- `CLAUDE.md`: 131行（常時適用ルール8節）。肥大化なし
- `.claude/settings.json`: SessionStart hook（`session-start.sh`）のみ。他キーなし

主要カテゴリ内訳（目視分類）:

| カテゴリ | スキル数 | 例 |
|---|---|---|
| SNS/記事執筆 | 6 | article-writer, owned-media, sns-ops-team, sns-auto-posting, twitter-intel, academic-research |
| 情報収集基盤 | 5 | agent-reach, hermes-x-search, hermes-agent-setup, last30days, github-trends |
| メタ/運用 | 8 | repo-skill-creator, token-saver, yagni-guard, biz-ops-guard, model-switcher, context-handoff, structured-task-execution, claude-env-audit |
| その他業務・学習 | 21 | 上記以外（インターン業務・副業・学習系ほか） |

## 検出事項

| # | 観点 | 対象 | 内容 | 提案 | 根拠 |
|---|---|---|---|---|---|
| 1 | 重複 | `hermes-x-search` / `hermes-agent-setup` | 両方とも「Hermes Agent + xAI Grok による X/Web検索基盤のセットアップ」が主目的。hermes-x-search は英語・x_search単体・コスト実態の解説に強い、hermes-agent-setup は日本語・MCP込み・ROADMAP候補リスト連携まで踏み込んだ運用版。発動条件（description）がほぼ同じ意図の依頼にマッチする | 統合（hermes-agent-setup に一本化し、hermes-x-search のコスト実態・tier不整合の節を移植。CLAUDE.md の「調査は hermes-relay で実行する」節との整合も合わせて確認） | 2スキルの description・本文冒頭を直接比較。同一ツール・同一設定対象 |
| 2 | 肥大化 | `plugins/hermes-x-search/skills/hermes-x-search/SKILL.md` | 421行。目安100〜250行を大幅超過 | 統合（#1）で解消、または詳細節を `references/` に分離 | `wc -l` 実測 |
| 3 | 肥大化 | `plugins/repo-skill-creator/skills/repo-skill-creator/SKILL.md` | 298行。目安をやや超過 | 修正（練度向上ワークフロー節などを `references/` に分離し本体を200行程度に圧縮） | `wc -l` 実測 |
| 4 | 矛盾 | なし | 今回チェックした範囲（description・冒頭節の比較）では、明確な指示の食い違いは検出されなかった | 何もしない | 全SKILL.mdの全文相互比較までは実施していないため「矛盾なし」の確証度は中程度 |
| 5 | 死文 | なし | 明確な死文（実態と合わなくなったルール）は今回の棚卸し範囲では未検出 | 何もしない | 同上。CLAUDE.md 8節・主要スキルの前提セットアップ表は現状と整合していることを目視確認 |
| 6 | 機密混入 | なし | `plugins/`・`CLAUDE.md`・`.claude/settings.json` に対し API key/secret/token/password パターンで grep したが該当なし | 何もしない | `grep -rE` 実行結果ゼロ件 |

## セッション分析（本セッションのみ・複数日傾向は未反映）

- 頻出操作: Bash(42) > Read(40) > Edit(21) > Agent(9) > Write(6) > WebFetch(4) ≈ ToolSearch(4)。
  Agent tool による並列サブエージェント委譲が多用されており、model-switcher の
  「設計はメイン・実装はサブエージェント」パターンと整合。
- 今セッションで呼ばれたスキル: `claude-env-audit`（1回、このタスク自体）のみ。
  他39スキルの使用有無はこのJSONLだけでは判定不可（1セッションのサンプルサイズが
  小さすぎるため「未使用スキル」の断定はしない）。
- **精度に関する注記**: 複数セッション・複数日にまたがる利用傾向を見たい場合は、
  ローカル実機の `~/.claude/projects/**/*.jsonl`（全期間分）に対して再実行することを推奨する。

## 整備モードでの変更ログ

（未実施。診断モードのみで完了。整備の実行はユーザーの明示指示待ち）

## before → after

（整備未実施のため該当なし）

## 残課題

- **#1 の統合作業**: hermes-x-search と hermes-agent-setup、どちらを主に残すか
  ユーザー判断が必要（英語ドキュメント資産としての hermes-x-search を残す/コスト実態の節だけ
  移植して廃止、の2択）。
- **#2・#3 の肥大化解消**: `references/` への分離作業。#1 の統合と同時にやると手戻りが少ない。
- ローカル実機での複数セッション分析は未実施（上記「精度に関する注記」参照）。
