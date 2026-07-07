---
name: repo-skill-creator
description: claude-skills リポジトリ（ryotaroh180105/claude-skills）で新しいスキル/プラグインを作成・改善・導入確認するときに使うメタスキル。Anthropic公式の skill-creator（汎用スキル作成ツール）とは別物で、こちらはこのリポジトリ固有の構成（plugins以下の各スキルディレクトリ、marketplace.json、ROADMAP.md）に特化する。「新しいスキルを作って」「スキルを追加したい」「SKILL.md を書いて/改善して」「スキルが発動しなかったので直したい」「ROADMAP のステータスを更新して」といった依頼で発動する。英語キーワード: create skill, new skill, add plugin, write SKILL.md, improve skill, skill not triggering, update roadmap, marketplace.json.
---

# repo-skill-creator — このリポジトリ専用のスキル作成・練度向上メタスキル

このリポジトリで新しいスキルを作成し、**実際に Claude Code / claude.ai に導入されるまで**を
完遂するためのスキル。README の手順を体系化・強化したもの。外部サービス依存はない。

**完了定義は「作った」ではなく「導入されている」。** commit / push / validate 通過だけでは
未完了。`/plugin install` または `.skill` アップロードの確認まで行って初めて完了。

## リポジトリ構成（前提知識）

```
claude-skills/
├── .claude-plugin/marketplace.json   # Marketplace 定義（plugins 配列に全スキルを登録）
├── plugins/<name>/
│   ├── .claude-plugin/plugin.json    # プラグインメタデータ
│   └── skills/<name>/SKILL.md        # スキル本体
├── scripts/
│   ├── validate_skills.py            # 整合性チェック（CI でも実行される）
│   ├── package_skill.py              # 1スキルを .skill (zip) 化
│   └── sync_to_claude_ai.sh          # 全スキルを dist/*.skill に一括生成
└── ROADMAP.md                        # スキル一覧とステータス管理
```

## 作る前に判断する: Skill か、SubAgent 主体のオーケストレーションか

このリポジトリのスキルには2種類ある。新規作成の前にどちらを作るか決める。

- **Skill = 手順**: 毎回同じ手順で進み、成果物の形式が決まっていて、1人（1回のセッション）で
  完結する作業。例: `article-writer`（企画→タイトル→構成→執筆→推敲の固定手順）。
- **SubAgent 主体のオーケストレーション = 役割**: 複数の専門視点・役割を分けて並列/連携させる
  必要がある作業。例: `sns-ops-team`（リサーチ/企画/執筆/レビュー/スケジュール管理を役割分担）。

判断チェックリスト（すべて「はい」なら Skill、複数視点が要るなら SubAgent 設計を検討）:

1. 毎回同じ手順か
2. 成果物の形式・品質基準が決まっているか
3. 1つの担当（1回のセッション）で完結できるか
4. 異なる専門性・立場からの検討や判断が不要か

初心者・新規スキルはまず Skill から作る。SubAgent 設計は「実装とレビューを分ける」
「調査と戦略を分ける」「安全確認を別役割にする」のように役割そのものを分離したい時だけ使う。
迷ったら Skill として小さく作り、後から役割分割が要ると分かった時点で SubAgent 化を検討する。

## 新規作成ワークフロー

### ① 目的とトリガー条件を1文で定義する

書き始める前に「このスキルは **誰が・どんな依頼をしたとき** に発動し、**何を達成する** のか」を
1文で書く。これがそのまま SKILL.md の `description` の骨格になる。
1文で書けないスキルはスコープが広すぎるので分割を検討する。

### ② ディレクトリとファイルを作成する

```bash
mkdir -p plugins/<name>/.claude-plugin plugins/<name>/skills/<name>
```

`plugins/<name>/.claude-plugin/plugin.json`:

```json
{
  "name": "<name>",
  "description": "スキルの日本語説明",
  "version": "1.0.0",
  "author": { "name": "ryotaroh180105" }
}
```

- plugin 名・ディレクトリ名・skills 配下のディレクトリ名はすべて `<name>` で一致させる。
- 名前は kebab-case（小文字とハイフン）。

### ③ SKILL.md を書く

`plugins/<name>/skills/<name>/SKILL.md` を作成する。書き方は後述の
「良い SKILL.md の書き方」に従う。frontmatter の `name` / `description` は必須
（validate_skills.py がチェックする）。

### ④ marketplace.json に登録する

`.claude-plugin/marketplace.json` の `plugins` 配列に追記する:

```json
{
  "name": "<name>",
  "source": "./plugins/<name>",
  "description": "スキルの日本語説明"
}
```

※ ROADMAP のバッチ並列作成では、この手順は統合役（メインセッション）が行う。
サブエージェントとして動いている場合は `plugins/<name>/` 配下だけを作成し、
marketplace.json / README / ROADMAP には触れない（コンフリクト防止）。

### ⑤ 検証する

```bash
python3 scripts/validate_skills.py
```

marketplace.json の登録と各 SKILL.md の frontmatter の整合性をチェックする。
CI（`.github/workflows/validate-skills.yml`）でも push / PR ごとに走るが、
push 前にローカルで通しておく。

### ⑥ commit / push する

```bash
git add plugins/<name> .claude-plugin/marketplace.json
git commit -m "Add: <name>"
git push
```

### ⑦ 導入確認する（ここまでやって完了）

いずれかを実施し、結果を確認する:

- **Claude Code CLI**:
  ```
  /plugin marketplace add ryotaroh180105/claude-skills   # 初回のみ
  /plugin marketplace update claude-skills               # 2回目以降
  /plugin install <name>@claude-skills
  ```
  `/plugin list` でインストール済み・enabled になっていることを確認する。
- **claude.ai（web）**: `./scripts/sync_to_claude_ai.sh` で `dist/<name>.skill` を生成し、
  Settings > Capabilities > Skills からアップロードして一覧に表示されることを確認する。

導入確認まで済んだら ROADMAP.md のステータスを 🎉 に更新する（後述）。

### ⑧ 通知する（新規作成・version up の両方で毎回行う）

スキルが新規作成された、または既存スキルの version が上がった（練度向上
ワークフロー適用時）たびに、以下2点をセットで行う。ユーザーが Claude Code
の画面を見ていない間に完了した作業に気づけるようにするため。

1. **PushNotification** で1行の完了通知を送る。例:
   `"新スキル: requirements-definition を作成しました"` /
   `"task-management を v1.1.0 に更新しました"`。200字厳守、装飾なし。
2. **SendUserFile** で対象スキルを `.skill`（zip）にパッケージして送る:
   ```bash
   python3 scripts/package_skill.py plugins/<name>/skills/<name> -o dist
   ```
   `dist/<name>.skill` を `SendUserFile` で送付する（`status: proactive`）。
   zip 化しているのは claude.ai へそのままアップロードできる形にするためで、
   中身は SKILL.md を含むフォルダそのもの。

複数スキルを1バッチで作った場合はスキルごとに送らず、バッチ完了時に
まとめて1回の通知＋複数ファイル送付でよい。

## 良い SKILL.md の書き方

### description にトリガー条件を書く

`description` は Claude が「今このスキルを読み込むべきか」を判断する唯一の材料。
スキルの機能説明だけでなく、**どんな依頼が来たら発動すべきか**を書く。

- 悪い例: `description: タスク管理のスキル`
- 良い例: `description: タスクの洗い出し・優先順位付け・進捗管理を頼まれたときに使う。「今日やることを整理して」「タスクを分解して」などで発動。英語キーワード: task management, prioritize, todo, breakdown.`

日本語ベースで書き、マッチ率を上げるため英語キーワードも併記する。

### 外部サービス依存は「前提セットアップ」節に明記する

MCP サーバー・API キー・環境変数に依存するスキルは、本文冒頭に「前提セットアップ」節を
置き、必要なものを表で明記する:

```markdown
## 前提セットアップ

| 種別 | 名前 | 用途 | 未設定時の挙動 |
|---|---|---|---|
| MCP | Slack MCP | メッセージ送信 | ユーザーに接続を依頼して停止 |
| 環境変数 | OPENWEATHER_API_KEY | 天気取得 | ユーザーにキーを確認 |
```

さらに「未設定ならスキル自身がユーザーに確認してから進む」という指示を本文に書く。
黙って失敗する・勝手に代替手段に走る設計にしない。

### ワークフローは具体的なステップで書く

「適切に対応する」のような抽象論ではなく、実行可能なコマンド・判断基準・出力形式まで
落とし込む。Claude が本文を読んだだけで迷わず実行できるかを基準にする。

### 水増ししない

行数を稼ぐための一般論・重複・冗長な注意書きは入れない。スキルはコンテキストに
読み込まれるので、長いほどコストがかかる。目安は 100〜250 行。
それを超えるなら、詳細を `references/` 等の別ファイルに分けて本文から参照する。

## 練度向上ワークフロー（既存スキルの改善）

**多様なユースケースでテストしてから改善サイクルを回したい場合**は、先に
[docs/skill-quality-loop.md](../../../../docs/skill-quality-loop.md) の
テストケース生成→採点→診断のフェーズを回し、そこで特定した症状をここに渡す。
ここでは「症状が既に分かっている」前提の最短修正フローを扱う。

スキルを実際に使ったときのフィードバックを SKILL.md に反映するサイクル:

1. **症状を特定する**。典型パターン:
   - 発動しなかった → `description` のトリガー条件が依頼の言い回しをカバーしていない。
     実際に使われた言い回し（日本語・英語）を description に追記する。
   - 手順が曖昧で迷った → 該当ステップに具体的なコマンド・判断基準を追記する。
   - 出力が期待と違った → 期待する出力形式・例を本文に明記する。
   - 誤発動した → description のスコープを絞る（「〜のときは使わない」を書く）。
2. **SKILL.md を修正する**。修正は症状に対応する最小限にとどめ、水増ししない。
3. **version を上げる**。`plugin.json` の `version` をインクリメントする
   （トリガー条件や手順の修正はパッチ +0.0.1、節の追加など内容拡張はマイナー +0.1.0）。
4. **検証 → commit / push → 再導入 → 通知**。新規作成の⑤〜⑧と同じ。Claude Code は
   `/plugin marketplace update claude-skills` で更新を取り込み、claude.ai は
   `.skill` を再生成して再アップロードする。⑧の通知・ファイル送付も忘れずに行う。

## ROADMAP.md のステータス更新

`ROADMAP.md` のスキル一覧テーブルのステータス管理もこのスキルの管轄:

| 記号 | 意味 | 更新タイミング |
|---|---|---|
| ⬜ | 未着手 | 初期状態 |
| 🚧 | 作成中 | 作業に着手したとき |
| ✅ | 実装済み（要インストール確認） | validate 通過 + commit / push まで完了 |
| 🎉 | 導入確認済み | ⑦の導入確認まで完了 |

- スキルの着手・完了のたびに該当行の Status を書き換える。
- ✅ で止まっているスキルは未完了扱い。導入確認を促す。
- 新しいスキル候補が生まれたら ROADMAP の「候補リスト」に追記し、実装に進むかは
  ユーザーの採択判断を待つ（勝手に実装まで進めない）。
