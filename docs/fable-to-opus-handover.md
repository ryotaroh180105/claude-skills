# Fable 5 → Opus 4.8 引き継ぎ資料（品質維持の仕組み）

Fable 5 が使えなくなった後、Opus 4.8 で Fable 相当のアウトプット品質を出すための
運用ルール集。**Opus セッションでこの資料を有効化する方法は §1。**

- 作成日: 2026-07-07（Fable 週次利用枠 50% 込み期間の最終日。以降は usage credits 消費）
- 調査経路: hermes-relay（Grok web_search）、調査ID `20260707T115842Z-fable-vs-opus`
- **`docs/designs/16-post-fable-model-operations.md` との役割分担**: 16番は「タスク種別ごとに
  どのモデルを使うか」（設計=Opus、実装=Sonnet 等の配分）の確定運用が正。本書は
  「同じタスクをOpusで受けた時に、Fableと同等のアウトプット品質をどう出すか」（品質の
  補償テクニック）を扱う。両者は独立して併用する——16番でOpusを選んだ後、本書§3のルールで
  そのOpusセッションの品質を上げる、という順で読む。

## 1. 使い方（有効化の手順）

| 手段 | 手順 |
|---|---|
| 都度（推奨・確実） | Opus セッション冒頭で §5 のセッション開始テンプレートを貼る |
| 常時（このリポジトリ内） | CLAUDE.md に「Opus で作業する時は `docs/fable-to-opus-handover.md` の運用ルールを適用する」の1行を追加（ユーザー承認後） |

## 2. Fable と Opus の差分

### 2-1. 公式・外部情報による差分（出典付き）

| 項目 | Fable 5 | Opus 4.8 | 出典 |
|---|---|---|---|
| 位置づけ | Mythos-class（Opus の上位階級）。一般公開の最先端モデル | 複雑な agentic coding / enterprise work 向け最強の常用モデル | https://www.anthropic.com/news/claude-fable-5-mythos-5 / https://docs.anthropic.com/en/docs/about-claude/models/overview |
| SWE-Bench Pro | 80.3% | 69.2%（差 +11.1pt） | https://www.truefoundry.com/fr/blog/claude-fable-5-vs-opus-4-8-benchmarks-pricing-when-to-use-each |
| FrontierCode (Cognition) | 29.3% | 13.4%（差 +15.9pt） | 同上 |
| 傾向 | **長く複雑なタスクほど差が開く**。長文推論・指示追従・agentic 継続で優位 | 短〜中タスクでは差が小さい | 同上 / https://www.finout.io/blog/claude-fable-5-mythos-5-pricing-benchmarks |
| 速度/コスト | MineBench 平均 18m04s だがトークン使用多 | 24m48s、トークン少 | https://www.rdworldonline.com/how-claude-fable-5-stacks-up-against-opus-4-8-and-gpt-5-5/ |
| 価格 | $10 / $50 per 1M tok | $5 / $25 per 1M tok（半額） | https://www.anthropic.com/news/claude-fable-5-mythos-5 |
| 提供 | 2026-06-09 GA。輸出規制で一時停止→07-01 復旧。Pro/Max等の週次枠込みは 07-07 まで、以降 usage credits | 常用可 | https://www.anthropic.com/news/redeploying-fable-5 / https://www.anthropic.com/news/fable-mythos-access |

未確認: 無料/プレビュー終了日はソース間で 6/22 と 7/7 の記述揺れあり（本リポジトリでは
model-switcher の 2026-07-07 を正とする）。網羅的ベンチ比較は公式 System Card 以外未確認。

### 2-2. このリポジトリでの観測に基づく差分（**仮説**。断定しない）

| 観点 | 仮説 |
|---|---|
| 曖昧な依頼の意図汲み取り | Fable は少ない手がかりから正しいスコープを推定しやすい。Opus は要件化を挟まないと的を外すことがある |
| 長時間の自律継続 | Fable は多工程を一括で完走しやすい。Opus は途中で品質が均されやすく、工程分割が必要 |
| 自己検証の粘り | Fable は「動くはず」で止まらず自分で検証まで回りやすい。Opus は明示的に検証を指示した方が安定 |
| 設計の一貫性 | 長い成果物（設計書・スキル）で、Fable は前半の決定を後半まで保持しやすい |

## 3. Opus で Fable 相当の品質を出す運用ルール

補償原理: **モデル地力の差は ①タスク分解の細分化 ②明示的な自己検証ループ
③コンテキストの事前整備 で埋める**（ベンチ差が「長く複雑なタスク」で開く以上、
タスクを短く単純にして渡せば差は縮む）。

| # | 場面 | Fable なら | Opus では追加でこうする |
|---|---|---|---|
| 1 | 曖昧な依頼 | そのまま着手可 | requirements-definition スキルで要件化してから着手。不明点は着手前に列挙 |
| 2 | 大きい設計 | 一括で設計→実装 | Plan mode 必須。設計書を docs/ に書き出し、**実装は別セッション**（計画と実装のコンテキスト分離） |
| 3 | 複数成果物の依頼 | 並列で自律走行 | TODO リスト化（TaskCreate）し、1 タスクずつ「完了条件を満たしたか」を確認してから次へ |
| 4 | 実装後 | 自発的にセルフレビュー | /code-review 相当のセルフレビューを必ず1回。挙動に触れる変更は verify スキルまで回す |
| 5 | 難デバッグで2回失敗 | 粘って原因到達 | 3回目に入らない。/clear し、判明事実の要約だけ持ち込んで再開（失敗コンテキストを引きずらせない） |
| 6 | プロンプト | 短い依頼でも成立 | 成果物・制約・完了条件・検証方法の4点を毎回明示（基準は plugins/daily-feedback/.../references/ideal-usage.md） |
| 7 | 長い成果物（設計書等） | 一気に書いて一貫 | 章ごとに書かせ、章の冒頭で「前章までの決定事項」を3行で復唱させる |
| 8 | スキル作成・高難度作業 | — | token-saver + yagni-guard を必ず併用（CLAUDE.md 既定）。effort は高難度時のみ high に上げ、定型時は上げない |
| 9 | 調査を含むタスク | 自分で調査設計 | 調査は hermes-relay（CLAUDE.md 手順）に固定。Opus に調査経路を選ばせない |
| 10 | 最難関で Opus が行き詰まる | — | その1タスクだけ Fable（usage credits）に上げる。恒常利用はしない（model-switcher 準拠） |

### 品質ゲート チェックリスト（成果物を出す前に Opus に自己確認させる）

1. 依頼の完了条件を1文で言えるか。成果物はそれを満たすか
2. 依頼にない抽象化・オプション・依存を足していないか（yagni-guard）
3. 動くと主張する箇所を実際に実行/検証したか。していないなら「未検証」と明記したか
4. 数値・URL・コード・エラー文字列を一字も改変していないか
5. 長い成果物の前半の決定と後半が矛盾していないか（章間の整合を1周読み直す）
6. エッジケース・エラー処理・セキュリティ要件を省略していないか
7. ユーザーに操作を依頼する箇所は「意図・内容・確認方法」の3点セットか
8. 同じ問題で2回失敗したまま3回目に突っ込んでいないか
9. このタスクは Opus 適正か（過剰/過小スペックなら model-switcher で切替提案）

## 4. セッション開始テンプレート（Opus セッション冒頭に貼る）

```
このセッションは Opus 4.8 で、Fable 5 相当の品質を出す運用で進めてください。
docs/fable-to-opus-handover.md を読み、§3 の運用ルール10項目と品質ゲート
チェックリストを有効化してください。特に:
- 曖昧な依頼は要件化してから着手（勝手に着手しない）
- 大きい作業は TODO 分割し、1タスクずつ完了確認
- 実装後はセルフレビュー1回＋検証、成果物提出前に品質ゲートを自己適用
- 同じ問題で2回失敗したら /clear を提案
token-saver（full）と yagni-guard（full）も併用してください。
```

## 5. 移行チェックリスト（ユーザーが一度だけやること）

| # | 操作 | 意図 | 内容 | 確認方法 |
|---|---|---|---|---|
| 1 | デフォルトモデルを Opus に変更 | Fable は週次枠終了後 usage credits 消費になるため、既定を常用上限の Opus に切り替える（model-switcher の確定運用では既定はSonnet、設計等の難所だけOpus。プロジェクトの実態に合わせる） | Claude Code で `/model claude-opus-4-8` を実行（恒久化する場合は `~/.claude/settings.json` の `model` を `claude-opus-4-8` に） | `/model` 実行時の表示が Opus 4.8 になっている |
| 2 | CLAUDE.md への1行追加（任意） | Opus セッションで本資料を自動適用するため | このリポジトリの CLAUDE.md に「Opus で作業する時は docs/fable-to-opus-handover.md の運用ルールを適用する」を追記して commit | 新セッションで Opus がルール適用を宣言する |
| 3 | daily-feedback で移行後1週間を観察 | Opus 移行で品質低下が起きていないかを日次で検出するため | 毎日 `/daily-feedback` を実行し、④コンテキストエンジニアリング軸と手戻り回数を確認 | レポートの訂正回数・手戻り指摘が Fable 期と同水準 |

## 6. この資料の更新ルール

- Opus 運用で「Fable ならこうだったのに」という差分を観測したら、§2-2 の仮説表に
  追記し、対応ルールを §3 に足す（MISTAKES.md と同じく同セッション内で commit）。
- Anthropic 公式が Fable/Opus の比較情報を更新したら §2-1 を hermes-relay で再調査する。
