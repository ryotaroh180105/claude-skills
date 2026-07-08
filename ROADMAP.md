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
3. フィードバックを SKILL.md に反映し、plugin.json の version を上げる（`repo-skill-creator` スキルの練度向上ワークフローを使う）
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
| 🎉 | `repo-skill-creator` | スキル作成・練度向上スキル（公式skill-creatorと別物） |
| 🎉 | `task-management` | タスク管理スキル |
| ✅ | `loop-engineering` | 自律ループ設計スキル（Trigger/Doer/Verifier/Stop Rules/Memory/Skills） |
| 🎉 | `context-handoff` | 会話成果物の回収→L1-L4整合性チェック→引き継ぎ書化（モデル切替・セッション区切り用） |
| 🎉 | `structured-task-execution` | 完了条件固定→観測ベース→リスク先行のPhase 0-3実行メソッド |

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
| ✅ | `daily-feedback` | Claude/Claude Code利用の3軸デイリーフィードバック |

## バッチ計画

1. **Batch 1（Tier1）**: requirements-definition / work-approach-playbook / repo-skill-creator / task-management
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
4. **実装**: 採択されたものを `repo-skill-creator` スキルの手順で 4個ずつ並列実装する。
5. **導入確認**: `/plugin install` または `.skill` アップロードまで確認して 🎉 にする。

### パターン観測ログ（繰り返し手作業の検出 → 3回で候補化）

既存スキルでカバーされていない複数ステップの手順を完了するたびに記録する。
同一パターンは回数を +1。3回に達したら候補リストへ転記する（運用ルールは
`repo-skill-creator` スキルの「パターン観測 → スキル候補化」節が正）。

| 初回日 | パターン（1行） | 回数 | 直近日 | 状態 |
|---|---|---|---|---|
| 2026-07-07 | X投稿の保存ファイル（docx等）から本文抽出→投稿単位で構造化→実装候補の仕分け | 1 | 2026-07-07 | 観測中 |

### 候補リスト（収集したスキルネタ置き場）

| 追加日 | 候補 | ソース | 状態 |
|---|---|---|---|
| 2026-07-07 | Xブックマーク一括取り込み（詳細は docs/x-posts-inventory.md） | Ryo提供のX投稿群 | 採択済み・Batch 7 で実装 |
| 2026-07-07 | taste-skill（AI生成UIの"安っぽさ"防止。`npx skills add Leonxlnx/taste-skill --skill design-taste-frontend`） | https://github.com/leonxlnx/taste-skill | 採択済み・導入結果の確認待ち（Ryoの端末でnpx実行、出力未確認） |
| 2026-07-07 | claude-video（実体は「Claudeに動画を見せる」ツール。プラグインIDは`watch`。要ffmpeg/yt-dlp） | https://github.com/bradautomates/claude-video | 🎉 導入済み（`watch@claude-video`、2026-07-08確認。ffmpeg/yt-dlpの導入は継続中） |
| 2026-07-07 | agmsg（実体は複数CLIエージェント間のローカルSQLiteメッセージング基盤。Win/Linuxはbest-effort対応） | https://github.com/fujibee/agmsg | 採択済み・導入中（Ryoの端末はWindows ARM64のためbest-effort領域） |

## Batch 7（Xブックマーク由来・2026-07-07〜08 実装）

採択判断: Ryo（「全部実装したい」の明示指示）。設計: Fable 5（docs/new-skills-design.md）、
実装: Sonnet 5 サブエージェント（10-80-10 采配の実践）。
全9本 2026-07-08 に実機インストール確認済み（/plugin install → /reload-plugins で 39 plugins 反映）。

| Status | スキル | 内容 |
|---|---|---|
| 🎉 | `fable-distill` | Fable 5 の思考様式（タスク分解・自己検証・次の一手）の蒸留プレイブック |
| 🎉 | `last30days` | mvanhorn/last30days-skill（MIT）の Wrapper 導入ガイド |
| 🎉 | `claude-design-review` | Trystan-SA/claude-design-system-prompt（MIT）を4観点チェックリストに再構成 |
| 🎉 | `humanize-text` | AI臭除去の推敲専用スキル（症状診断→該当変換のみ適用） |
| 🎉 | `media-convert` | 動画→音声変換の ffmpeg ラッパー |
| 🎉 | `claude-env-audit` | .claude 資産の5観点監査＋AUDIT.md 出力（診断/整備2モード） |
| 🎉 | `screenshot-to-app` | スクショ→動く単一HTML再現（自己採点・推測箇所申告つき） |
| 🎉 | `ios-hig-prototype` | Apple HIG 準拠 iPhone プロトタイプ生成（プロンプト原文は references/） |
| 🎉 | `academic-research` | Imbad0202/academic-research-skills（CC-BY-NC 4.0）の Wrapper。非商用限定 |

既存スキル拡張（同バッチ）: token-saver / model-switcher / repo-skill-creator /
article-writer / sns-ops-team / owned-media を v1.1.0〜1.2.0 に更新、CLAUDE.md に
「完成の定義」「Epistemia対策」を追加。見送り: compliance-checker の独立化（owned-media と
sns-ops-team に組込済みのため）、RuView / CloakBrowser / openhuman / ViMax / bun
（理由は docs/x-posts-inventory.md §1 参照）。
