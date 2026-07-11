# リサーチ用AIエージェント選定と自動化設計

「調査はどのAIにやらせるか」の決定表と、NoimosAI を使った SNS 分析自動化の設計。

- 調査経路: hermes-relay（Grok web_search）、調査ID `20260707T115842Z-research-ai-comparison`
- 調査日: 2026-07-07。料金・機能は変動するため、採用直前に該当ツールのみ再調査する

## 1. 結論（どれを使うか）

| 用途 | 1位 | 理由 |
|---|---|---|
| 日常の調査（X・Web、追加コスト0） | **既存 hermes-relay**（Grok x_search / web_search） | 追加課金なし・自動化済み・このリポジトリの CLAUDE.md 標準経路。まずこれで足りるかを常に先に判定 |
| 単発の深いレポート調査 | **ChatGPT Deep Research** または **Gemini Deep Research**（$20/mo 級） | 構造化長文レポートに強い。頻度が低いなら契約は不要（hermes で代替） |
| 出典の信頼性・API自動化重視 | **Perplexity**（Sonar/Agent API, Pro $20/mo） | 引用付き回答・Agent API でスケジュール実行可 |
| 日本語特化・低価格 | **Felo**（Pro ¥2,099/mo） | 日本語 Tier 1 対応、AI Agents で自動モニタリング |
| SNS 分析＋実行まで自動化 | **NoimosAI**（§3） | 調査に留まらず X/TikTok/YouTube/Instagram の分析・生成・自動投稿・24/7 リスニングまで一体 |

**運用原則**: 有料エージェントは「hermes-relay で3回やって力不足だった用途」にだけ契約する。
最初から複数契約しない（月額の固定費化を防ぐ）。

## 2. 比較表（2026-07 時点、出典は調査結果ファイル参照）

| 名称 | 得意分野 | 料金 | 日本語 | 自動化 |
|---|---|---|---|---|
| Perplexity | 引用付き高速リサーチ | Pro $20/mo（Max $200） | ○ | Agent API + Make/n8n でスケジュール可 |
| ChatGPT Deep Research | 構造化された長文レポート | Plus $20/mo（回数制限） | ○ | API 経由で一部可 |
| Gemini Deep Research | Google エコシステム・広いDB | AI Pro $19.99/mo | ○ | Workspace 統合 |
| Claude (Research) | 長文合成・PDF 分析 | Pro $20/mo | ○ | agentic browsing で一部可 |
| Genspark | オールインワン・Super Agent | Plus $24.99/mo | ○（日本展開中） | no-code agents |
| Manus | 自律実行・Wide Research | Starter $39/mo〜 | ○ | API・ブラウザ操作・スケジュール |
| Felo | 多言語（日本語 Tier 1） | Pro ¥2,099/mo | ◎ | AI Agents で監視 |
| NoimosAI | SNS マーケ全域（分析〜投稿） | プラン制（要公式確認） | 要確認 | 自律エージェント・24/7 |

主要出典: https://www.aimagicx.com/blog/chatgpt-vs-claude-vs-perplexity-vs-gemini-april-2026 /
https://docs.perplexity.ai/docs/agent-api/quickstart / https://felo.ai/tools/research /
https://www.genspark.ai/ / https://manus.im/

## 3. NoimosAI — 正体と使いどころ

**実在確認済み**。2026年4月頃リリースのオールインワン自律型 AI マーケティングプラットフォーム。
公式: https://noimosai.com/en

できること（出典: https://noimosai.com/en / https://theresanaiforthat.com/ai/noimosai/）:
- X/Twitter 投稿分析・ソーシャルリスニング（24/7 モニタリング）
- TikTok / YouTube / Instagram 含むコンテンツ生成・自動投稿
- SEO/GEO 最適化・競合分析

→ ユーザーの想定用途「バズってる動画の分析」「X の分析」は守備範囲。
未確認: 日本語コンテンツの品質、料金詳細、分析の粒度（視聴数・感情分析等）。
**契約前に必ず無料枠/デモで日本語 X アカウント1つを分析させて品質確認する。**

### 段階導入設計（将来の自動化を見据えて）

| フェーズ | 条件 | やること |
|---|---|---|
| P0（現在） | 追加コスト0で回す | X 分析 = twitter-intel + hermes-relay、投稿 = sns-ops-team + sns-auto-posting の既存構成を継続 |
| P1（試験） | バズ動画分析の需要が週1回以上発生 | NoimosAI 無料枠/最安プランで X 分析・動画トレンド分析を2週間並走させ、hermes-relay の結果と品質比較。`ROADMAP.md` に結果を記録 |
| P2（採用） | P1 で hermes より明確に優位 | NoimosAI を「動画・マルチプラットフォーム分析」担当に採用。X テキスト調査は hermes-relay のまま（無料のため）。sns-ops-team のリサーチ工程から参照する運用に変更 |
| P3（自動化） | 分析結果を毎週使っている | NoimosAI の自動モニタリング/レポートをスケジュール設定し、結果をユーザーが週次で sns-ops-team に食わせる |

代替候補（P1 で NoimosAI が不合格の場合）: Blotato（$29/mo、9プラットフォーム自動投稿）、
n8n + AI ワークフロー（自前構築、無料枠あり）。

### P1 開始時のユーザー操作（意図・内容・確認方法）

| 操作 | 意図 | 内容 | 確認方法 |
|---|---|---|---|
| NoimosAI アカウント作成 | Claude は外部 SaaS の会員登録・支払い設定を代行できないため | https://noimosai.com/en でサインアップし、無料枠または最安プランを選択 | ダッシュボードにログインできる |
| X アカウント連携 | 自分のアカウントの実データで分析品質を検証するため | NoimosAI の設定画面から X アカウントを OAuth 連携 | ダッシュボードに自アカウントの投稿分析が表示される |
| 分析結果の共有 | Claude が品質比較（vs hermes-relay）を行うため | 生成された分析レポートをテキストでセッションに貼り付け | Claude が比較表を返す |

## 4. 既存スタックとの役割分担（重複させない）

| 調査タスク | 担当 |
|---|---|
| X の投稿・トレンド調査 | hermes-relay x_search（twitter-intel スキル経由） |
| Web 記事・ドキュメント調査 | hermes-relay web_search（CLAUDE.md 手順） |
| 同じソース群への反復 QA | NotebookLM（hermes-relay engine 指定） |
| 特定 URL の本文抽出 | 不可（ユーザーに貼り付け依頼）— CLAUDE.md 準拠 |
| バズ動画・マルチプラットフォーム分析 | P1 以降 NoimosAI（それまでは対応外と明言する） |
| 深い単発レポート（契約した場合のみ） | Perplexity / Deep Research 系 |
