---
name: loop-engineering
description: 定型作業・監視・繰り返しタスク（週次のSNS投稿、日次のピックアップ、週次のトレンド収集、学習の反復演習など）を、Trigger/Doer/Verifier/Stop Rules/Memory/Skillsの6要素からなる自律ループとして設計するスキル。「これを自動化したい」「定期的に回したい」「ループを組みたい」「毎日/毎週チェックさせたい」「/loopで回したい」「暴走しないループにしたい」といった依頼で使う。既存スキル（sns-ops-team, pickup-automation, github-trends, consulting-quiz等）に自動化を組み込む前の設計フェーズを担当し、各スキル自体のSKILL.mdは変更しない。
---

# loop-engineering — 自律ループ設計スキル

## 目的

「毎回手動でプロンプトを書く」から「一度ループを設計すれば繰り返し回る」への移行を、
安全に行うための設計スキル。対象は Claude Code の自律実行ループ（`/loop`、Routine、
cronウォッチャー等の実行基盤の上で回るもの）。**このスキルはループの設計図を作る**。
実行基盤そのもの（`/loop`コマンド、`create_trigger`等）や、ループに乗せる個別業務
（SNS投稿、レビュー等）は既存スキルに任せ、重複させない。

## 発動条件

- 「〇〇を自動化したい」「毎週/毎日回したい」「ループにしたい」
- 既存スキル（`sns-ops-team`の週次投稿、`pickup-automation`の日次抽出、
  `github-trends`の週次収集、`consulting-quiz`/`aws-exam-practice`の反復演習など）を
  定期実行に乗せたいとき
- 「暴走しそうで怖い」「コストが心配」など安全設計の相談

似て非なるもの: 既存スキル1個をどう改善するかは `repo-skill-creator`、テストケースを
使った品質改善サイクルは
[docs/skill-quality-loop.md](../../../../docs/skill-quality-loop.md) が担当する。
loop-engineeringはそれらより広く、「何かを繰り返し自動で回す」設計全般を扱う。

## 前提セットアップ

| 用途 | 必要なもの | 無い場合 |
|---|---|---|
| 設計・レビューのみ | なし | そのまま使える |
| 定期実行（時刻トリガー） | Claude Code Remoteの `create_trigger` / `/loop` スキル | 手動起動のループとして設計し、後で自動化 |
| コスト上限の実強制 | Agent SDKの `max_turns` / `max_budget_usd` 相当のパラメータ、または `model-switcher` でのモデル使い分け | 上限をチェックリスト化し、人間が毎回確認する運用に留める |

## ループの6要素

強いループは以下6要素で構成される（Claude Code公式 `/goal` 機能や
複数の実践事例に共通するパターン）。設計時は全て埋める。

| 要素 | 役割 | 埋まっていないと起きる失敗 |
|---|---|---|
| **Trigger** | いつ始まるか（タイマー/イベント/自己発見） | 誰も起動しない「幽霊ループ」 |
| **Doer** | 実行層。既存スキルの手順を呼ぶ | — |
| **Verifier** | Doerとは別の主体が完了条件を判定（Maker-Checker） | 自己採点の「Blind Loop」 |
| **Stop Rules** | 成功条件＋安全上限の二重 | 無限ループ、予算爆発 |
| **Memory/State** | 進捗をファイルに永続化 | セッションが切れると迷子になる「Amnesiac Loop」 |
| **Skills/Routines** | 毎回ロードする知識・手順 | 判断がその場しのぎになる |

## ワークフロー

### 1. ゴール定義

何を達成すれば成功か、できれば機械判定可能な形に落とす
（例:「`validate_skills.py` が通る」「投稿キューのapproved行が0件になる」）。
曖昧なら曖昧なままにせず、`requirements-definition` スキルで先にイシューを
特定してから戻ってくる。

### 2. Trigger を選ぶ

- **タイマー**: 毎日/毎週など時刻ベース。Claude Code Remoteの `create_trigger`
  （cron式）や `/loop` スキルを使う。
- **イベント**: PRコメント、CI失敗、ファイル変更など。
- **自己発見**: ログや状態ファイルをスキャンして「やるべきことがあれば」起動。

### 3. Doer を設計する

実行層。多くの場合、このリポジトリの既存スキル（`sns-ops-team`,
`pickup-automation`, `github-trends` 等）の手順をそのまま呼び出すだけでよい。
Doer自体を新しく作り込まない（既存スキルを再利用する）。

### 4. Verifier を分離する（Maker-Checker）

**Doerと同じ文脈・同じ主体に自己採点させない。** これが最も破られやすい原則。

- 実装方法: Agent tool で別セッションのAgentを1体立て、ゴールと出力だけを渡して
  判定させる（`/code-review` のファインダー→検証者分離と同じ発想）。
- 判定はルーブリック化し、**わからない場合は「不明」と言わせる**
  （無理に合格/不合格を決めつけさせない）。
- コスト最適化: Verifierは `model-switcher` の基準で軽量モデルに委譲してよい。
  判断者と実行者は違うモデルでよいが、違う「文脈」であることの方が重要。

### 5. Stop Rules を二重で決める

1. **成功条件**: 何をもってこのループを終える/一時停止するか。
2. **安全上限**: 最大ターン数・所要時間・コストの上限。目安は既存事例で
   `max-turns 25` 前後、1ループ30〜60分。3周しても収束しなければ止めて
   人間に相談する（`docs/skill-quality-loop.md` と同じ考え方）。

**上限は指示文（プロンプトに書くだけ）では守られない。** タスク達成に動機づけ
られたエージェントはプロンプト上の「予算を守れ」を無視しがちなので、
**実際にループを打ち切る行動**（ターン数を数えて機械的に止める、
Verifierが上限超過を検知したら強制終了する）で担保する。

### 6. Memory / State を永続化する

コンテキストウィンドウに頼らず、ファイルに進捗を書く。

- **汎用の自動化ループ**（このスキルで新しく設計したもの）は `LOOPS.md` に
  保存し、次回セッションで再利用できるようにする。
- **既存スキルの品質改善ループ**は `plugins/<skill>/skills/<skill>/test-log.md`
  （`docs/skill-quality-loop.md` の管轄）を使う。両者を混同しない。
- ループ実行のたびに「次にやるべきこと」を1〜2行、状態ファイルの末尾に書き足す。

### 7. Skills/Routines を明示する

そのループが毎回参照すべき知識（CLAUDE.md、対象スキルのSKILL.md）を明記する。
新しくSkillを作る必要がある場合は `repo-skill-creator` に委譲する。

### 8. 失敗モードチェック

設計を終える前に、以下4つの失敗パターンに当てはまっていないか確認する。

| 失敗モード | 症状 | 対策 |
|---|---|---|
| Blind Loop | 検証なしで進む | Verifierを必ず分離する（手順4） |
| Tangled Loop | 依存関係が複雑すぎて誰も追えない | Doerを既存スキル呼び出しだけに絞る |
| Amnesiac Loop | 記憶がなく毎回ゼロから | Memory/Stateファイルを必ず用意する |
| Manual Loop | 結局人間が毎回全部やっている「自動化ごっこ」 | Triggerが実際に自動起動するか確認する |

## 出力フォーマット（ループ設計書）

```markdown
## ループ設計: <名前>

- ゴール: <何をもって成功か>
- Trigger: <タイマー/イベント/自己発見の別と具体的な条件>
- Doer: <呼び出すスキル・手順>
- Verifier: <誰が/どのモデルが/何を基準に判定するか>
- Stop Rules:
  - 成功条件: <...>
  - 安全上限: <最大ターン数/時間/コスト>
- Memory/State: <保存先ファイルパス>
- Skills/Routines: <毎回参照する知識>
- 失敗モードチェック: Blind/Tangled/Amnesiac/Manual いずれも該当なしを確認済み
```

## 注意点

- **完全自動化が常に正解ではない。** 高判断が必要な工程（投稿の最終承認、
  金銭・対外的な発信を伴う判断）は human gate として人間の確認を残す。
  `sns-ops-team` の投稿承認フロー（draft→approved はRyoのみ）が好例。
- 既存スキルに自動化を組み込む場合、**そのスキルのSKILL.md自体は変更しない**。
  loop-engineeringは「どう回すか」の設計に徹し、対象スキルの中身には踏み込まない。
- 参考実装（設計の型を借りる場合の出典）:
  - Claude Code公式 `/goal`（別モデルによる完了判定の実装例）
  - [cobusgreyling/loop-engineering](https://github.com/cobusgreyling/loop-engineering)（loop-init/audit CLI）
  - [Forward-Future/loopy](https://github.com/Forward-Future/loopy)（`npx skills add Forward-Future/loopy --skill loopy --agent claude-code -g -y` でインストールし、セッションを観察して繰り返しパターンからループを自動生成する）
  - `loops.elorm.xyz`（コピー可能なループテンプレート集）
- コスト実例（未検証・一般論として参考程度に扱う。日付: 2026年7月時点のX上の報告）:
  検証なしのretry loopで $300/日規模、年$30,000超の暴走事例が報告されている一方、
  高額モデルは計画のみ・実行は安価モデルという hybrid 運用で $50/月に抑える例もある。
  数値は鵜呑みにせず、自分のループでは Stop Rules（手順5）で上限を必ず設ける。
