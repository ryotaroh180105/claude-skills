# Skill Roadmap（〜2026/07/07）

このリポジトリで **7/7 までにできるだけ多くの業務直結スキルを実装する** ためのロードマップ。
スキルの追加・完了のたびにこのファイルのステータスを更新する。

## スキルを作る目的

1. **インターンでの仕事の効率と質を上げる** — 上司に「仕事ができる」と認識され、早くコンサル側にアサインされる
2. **個人開発・副業で稼ぐ** — SNS運用 + ウェブ系
3. **就活で話せるエピソード・実績を作る** — 上記2つの取り組みと成果そのものがネタになる

各スキルの要件定義は [docs/skill-requirements.md](docs/skill-requirements.md) に記録する（どの目的に効くかを G1/G2/G3 でタグ付け）。

## 優先順位の考え方

Fable（高性能モデル）が無料で使えるうちに、難しいものから作る：

1. **Tier1: 基盤スキル** — 他の作業・スキル作成の土台になるもの。最優先
2. **Tier2: 高難易度スキル** — 構築難易度が高く、Fable でないと作りにくいもの。無料期間（〜7/7）中に必ず作る
3. **Tier3: 目的直結スキル** — 目的に直結するが、構造が比較的シンプルなもの

## ゴールと完了定義

- ゴールは「作った」ではなく **「ユーザーが MCP / API キー等の必要情報を入力すれば即動く状態」** になっていること。
- 外部サービスに依存するスキルは、SKILL.md 冒頭の「前提セットアップ」節に必要な MCP サーバー / API キー / 環境変数を明記し、未設定ならスキル自身がユーザーに確認するよう設計する。
- 最終確認は README の完了定義に従う（`/plugin install` で導入確認、または `.skill` 化して claude.ai にアップロード）。

## 運用方針

- **4個ずつ並列で作成**する。バックグラウンドのサブエージェントに1スキル1エージェントで割り当て、完了したら次のバッチへ。
- 各エージェントは `plugins/<skill-name>/` 配下のみを作成し、`marketplace.json` / README / 本ファイルの更新は統合役（メインセッション）が行う（コンフリクト防止）。
- バッチごとに `scripts/validate_skills.py` を通してから commit / push する。

### 品質基準（全スキル共通）

- 執筆前に代表ユースケースを5個以上列挙する（誰が・どんな状況で・何を入力し・何が出れば成功か）。
- 執筆後、最低3つのユースケースで「SKILL.md だけを読んだ Claude が正しく動けるか」をウォークスルーし、曖昧な手順を修正してから納品する。
- スクリプトを含むスキルは実際に実行してテストする（API キーが必要な部分は dry-run / モックで、引数・エラーメッセージまで確認）。
- エッジケース（入力なし・キー未設定・巨大ファイル等）の挙動を SKILL.md に明記する。

### 作成後の壁打ち→ブラッシュアップ運用（重要）

v1.0.0 は叩き台。作って終わりではなく、以下のループで練度を上げる：

1. スキルを実際に使ってみる（Ryo が本物のタスクで使う）
2. **壁打ちセッション**: 使用感を Claude と議論する — 発動しなかった／手順が曖昧だった／出力が期待と違った／もっとこうしたい
3. フィードバックを SKILL.md に反映し、plugin.json の version を上げる（`skill-creator` スキルの練度向上ワークフローを使う）
4. 1 に戻る

外部サービス依存のスキルは「**Ryo が MCP / API キー等の必要情報を入力すれば即動く**」状態で納品し、壁打ちの最初の回でセットアップを一緒に済ませる。

多様なユースケースでのテスト生成・採点・回帰確認・記録まで含めた具体的なループ定義は
[docs/skill-quality-loop.md](docs/skill-quality-loop.md) を参照。

## スキル一覧と優先順位

ステータス: ⬜ 未着手 / 🚧 作成中 / ✅ 実装済み（要インストール確認）/ 🎉 導入確認済み

### Tier1: 基盤スキル

| Status | Skill | 説明 |
|---|---|---|
| 🎉 | `requirements-definition` | 要件定義整理スキル（イシュー特定→MECE分解→ピラミッド構造） |
| 🎉 | `work-approach-playbook` | 仕事の進め方スキル（作業前チェックリスト） |
| 🎉 | `skill-creator` | スキル作成・練度向上スキル |
| 🎉 | `task-management` | タスク管理スキル |
| ✅ | `loop-engineering` | 自律ループ設計スキル（Trigger/Doer/Verifier/Stop Rules/Memory/Skills） |

### Tier2: 高難易度スキル（7/7までに実装）

| Status | Skill | 説明 |
|---|---|---|
| 🎉 | `hermes-agent-setup` | Hermes Agent + MCP + Grok/X Search 情報収集連携 |
| 🎉 | `voicememo-pipeline` | 録音→文字起こし→議事録+フィードバック→Drive/Slack 自動送信 |
| 🎉 | `sns-ops-team` | SNS運用チーム（マルチエージェント） |
| 🎉 | `model-switcher` | タスク種別別のモデル自動切り替え |
| 🎉 | `github-trends` | GitHubトレンド定期取り込み（ユーザー採択判断） |
| 🎉 | `code-review-adr` | コードレビュー + アーキテクチャADR |
| 🎉 | `pr-review` | PRレビュースキル |

### Tier3: 目的直結スキル

個人開発・副業:

| Status | Skill | 説明 |
|---|---|---|
| 🎉 | `lp-builder` | LP作成副業スキル |
| 🎉 | `article-writer` | note記事作成スキル |
| 🎉 | `owned-media` | オウンドメディア記事作成スキル |
| 🎉 | `sns-auto-posting` | Twitter/Instagram/TikTok 自動運用 |
| 🎉 | `twitter-intel` | Twitter情報収集スキル |

インターン業務:

| Status | Skill | 説明 |
|---|---|---|
| 🎉 | `testcase-usecase` | テストケース + ユースケース洗い出し |
| 🎉 | `document-creation` | 書類作成スキル |
| 🎉 | `pickup-automation` | ピックアップ自動化スキル |

学習・知識:

| Status | Skill | 説明 |
|---|---|---|
| 🎉 | `consulting-quiz` | コンサル・営業知識クイズ |
| 🎉 | `aws-exam-practice` | AWS模試スキル |

## バッチ計画

1. **Batch 1（Tier1）**: requirements-definition / work-approach-playbook / skill-creator / task-management
2. **Batch 2（Tier2 前半）**: hermes-agent-setup / voicememo-pipeline / sns-ops-team / model-switcher
3. **Batch 3（Tier2 後半 + 副業）**: github-trends / code-review-adr / pr-review / lp-builder
4. **Batch 4（副業）**: article-writer / owned-media / sns-auto-posting / twitter-intel
5. **Batch 5（インターン + 学習）**: testcase-usecase / document-creation / pickup-automation / consulting-quiz
6. **Batch 6（残り）**: aws-exam-practice

## 継続プロセス：スキルネタの収集→実装パイプライン

7/7 以降も含めた運用サイクル：

1. **収集**: X（Twitter）・GitHub トレンド等から「仕事に活かせそうなスキル/エージェント活用事例」を定期的に収集する。
   - `twitter-intel` / `github-trends` スキル自体がこの収集の実行部品になる（自分のためのスキルを自分で使う）。
2. **候補化**: 収集した情報をこの ROADMAP の「候補リスト」（下記）に追記する。
3. **採択判断**: ユーザー（Ryo）が候補を見て採択/見送りを判断する。勝手に実装まで進めない。
4. **実装**: 採択されたものを `skill-creator` スキルの手順で 4個ずつ並列実装する。
5. **導入確認**: `/plugin install` または `.skill` アップロードまで確認して 🎉 にする。

### 候補リスト（収集したスキルネタ置き場）

| 追加日 | 候補 | ソース | 状態 |
|---|---|---|---|
| - | （まだなし） | - | - |
