# 収益ライン接続設計書（レビュー19 B1/B2/B3 の確定実装仕様）

| 項目 | 値 |
|---|---|
| ステータス | 実装完了（B1/B2/B3全て前倒し実装。B3-bはsns-ops-team既存観点(2)の強化に統合） |
| 種別 | 既存スキル3本への追記（新規スキルなし） |
| 実装モデル | Sonnet 5（推奨 effort: medium — 挿入文は本書で確定済みの転記作業） |
| 依存する設計書 | docs/designs/19-redteam-review-2026-07-07.md（B1/B2/B3の根拠）、06/10 設計書 |
| 外部依存 | なし |

## 1. 目的・背景（Why）

レビュー19で確定した3つの断線を塞ぐ: (B1) oss-explainer→article-writer の委譲契約が片側のみで、article-writer の既存ルール（切り口3案提示・実体験なしテーマは解説記事非推奨）と衝突する。(B2) oss-explainer の記事が link-registry（アフィリエイト台帳）に接続されず収益ラインに乗らない。(B3) PR表記チェックが affiliate-monetization 発動時にしか働かず、article-writer / sns-ops-team 直呼びで素通りする。

本書は挿入文を確定値で持つ。実装者は転記と version bump のみ行う。

## 2. スコープ

### 2.1 やること

- B1: `plugins/article-writer/skills/article-writer/SKILL.md` に「explainer-brief 入力時の分岐」1節を追加
- B2: `plugins/oss-explainer/skills/oss-explainer/SKILL.md` の Step 5 定型プロンプトに link-registry 確認1行を追加
- B3: `plugins/article-writer` の工程5（推敲チェックリスト）と `plugins/sns-ops-team` のレビュー観点に、アフィリンク検出→PR表記確認の1項目を追加
- 3プラグインの plugin.json version を1段上げる

### 2.2 やらないこと

- affiliate-monetization / sns-auto-posting 本体の変更（B3は「検出したら affiliate-monetization に回す」участまで。表記ルール本体は affiliate-monetization が正のまま）
- explainer-brief スキーマの変更（10設計書 §5 が正）
- 新しいチェックリスト体系の導入（既存の節に1項目/1分岐を足すだけ。yagni）

## 3. 完成条件（Definition of Done）

- [ ] `grep -c "explainer-brief" plugins/article-writer/skills/article-writer/SKILL.md` が 2 以上（分岐節の見出しと本文）
- [ ] `grep -n "link-registry" plugins/oss-explainer/skills/oss-explainer/SKILL.md` が Step 5 の定型プロンプト内でヒット
- [ ] `grep -c "PR表記\|アフィリエイトリンク" plugins/article-writer/skills/article-writer/SKILL.md` が 1 以上、同 `plugins/sns-ops-team/skills/sns-ops-team/SKILL.md` が 1 以上
- [ ] 3つの plugin.json の version が上がっている
- [ ] `python scripts/validate_skills.py` exit 0
- [ ] ネガティブ確認: explainer-brief を渡さない通常の note 依頼で、article-writer が従来どおり切り口3案から始める（分岐が誤発動しない）

## 4. 成果物の構成（ファイルレイアウト）

```
plugins/article-writer/skills/article-writer/SKILL.md   # B1 + B3(工程5)
plugins/article-writer/.claude-plugin/plugin.json        # version bump
plugins/oss-explainer/skills/oss-explainer/SKILL.md     # B2
plugins/oss-explainer/.claude-plugin/plugin.json         # version bump
plugins/sns-ops-team/skills/sns-ops-team/SKILL.md       # B3(レビュー観点)
plugins/sns-ops-team/.claude-plugin/plugin.json          # version bump
docs/designs/21-content-pipeline-connections.md          # 本書
```

## 5. データ構造（挿入文の確定値）

### 5.1 B1: article-writer への追加節

挿入位置: 「## 最初にやること: 文体メモの確認（必須の分岐）」節の**直後**（工程1の前）。

```markdown
## explainer-brief 入力時の分岐（oss-explainer からの委譲）

依頼に oss-explainer 産の explainer-brief（4軸骨子 + 事実台帳）が添付されている場合は、
以下を通常フローに優先する:

- **工程1（切り口設計）をスキップする**。切り口は brief の4軸（何が新しいか/なぜバズったか/
  どう動くか/仕事にどう活かすか)で確定済み。3案の再提示・再設計をしない。
- **「実体験がないテーマは解説記事非推奨」のエッジケースを適用しない**。OSS解説は
  実体験ではなく事実台帳（裏取り済み）を根拠とする記事型であり、体験談型への
  切り替え提案をしない。
- 執筆時、事実台帳で「未確認」の主張は本文でも断定しない（「〜とされる」を使う）。
  brief に無い技術的主張を本文で新たに追加しない。
- 工程2（タイトル）以降は通常どおり進める。文体メモの分岐も通常どおり。
```

### 5.2 B2: oss-explainer Step 5 定型プロンプトへの追加行

挿入位置: Step 5 の article-writer 呼び出し定型プロンプト内の末尾（「（工程6）は article-writer の標準手順どおりに進めてください。」の直後の行）。

```markdown
> 公開設定の前に affiliate-monetization の link-registry を確認し、この記事のテーマに
> 合致する登録済みリンク（link_id）があれば PR 表記付きで挿入を検討してください。
> 台帳が空・未整備なら挿入せずそのまま公開してよい（リンクなし公開を止めない）。
```

### 5.3 B3-a: article-writer 工程5（推敲チェックリスト）への追加1項目

挿入位置: 「## 工程5: 推敲チェックリスト」の既存チェック項目の末尾。

```markdown
- [ ] 本文にアフィリエイトリンク（ASP ドメイン・計測パラメータ付きURL）が含まれる場合、
      affiliate-monetization スキルの PR 表記ルールに従った表記が冒頭にあるか。
      表記が無ければ公開前に必ず追加する（景表法ステマ規制対応。リンクの有無自体の判断は
      affiliate-monetization が正）
```

### 5.4 B3-b: sns-ops-team レビュー観点への追加

挿入位置: 「**④ レビュー**」のエージェント指示例にある観点列挙 `(1) 炎上リスク…` の並びに観点を1つ追加。

```markdown
> (追加観点) アフィリエイトリンク・案件性の告知漏れ: 投稿にアフィリンクや案件性が
> あるのに #PR 等の表記が無いものは「要修正」。表記ルールは affiliate-monetization
> スキルの funnel-config が正。
```

## 6. 処理フロー

該当なし（静的なSKILL.md追記。実行時フローは各スキル本体に従う）。

## 7. エッジケース

| ケース | 期待挙動 |
|---|---|
| explainer-brief 抜きの通常 note 依頼 | 分岐が発動せず従来フロー（DoD のネガティブ確認） |
| brief はあるが事実台帳が空 | 執筆は進めるが技術的主張は全て非断定表現。article-writer から oss-explainer への差し戻しはしない |
| link-registry が存在しない/空 | リンク挿入せず公開を止めない（§5.2 の文言どおり） |
| 短縮URLでASPドメインが判定不能 | 「リンク先不明のURLがある」として PR 表記確認をユーザーに促す（素通りさせない） |

## 8. 失敗シナリオとレッドチーム所見

| # | 失敗シナリオ | 早期警報サイン | 設計上の対策 |
|---|---|---|---|
| 1 | 分岐追記で article-writer が肥大し、通常依頼でも brief 分岐を誤発動する | brief の無い依頼で「工程1をスキップ」と言い出す | 分岐条件を「brief が添付されている場合」に限定し、DoD にネガティブ確認を含めた |
| 2 | PR 表記チェックが形骸化する（チェック項目はあるが素通り） | PR 表記なしのアフィリンク記事が公開される | 出口2箇所（article-writer 工程5 + sns-ops-team レビュー）の二重化。すり抜けが実測されたら sns-auto-posting（投稿直前）にも第三の検出を追加（今回はyagniで見送り） |
| 3 | 3ファイル同時変更で version bump 漏れ・validate 落ち | CI fail / plugin list で旧 version | DoD に version・validate を明記。1コミットで3プラグイン+本書ステータス更新を完結させる |

## 9. 実装手順（Sonnet 向けタスク分割）

1コミットで完結（分割不要の小変更）:

1. §5.1〜5.4 の4挿入を各アンカー位置に転記 → 3つの plugin.json を patch version bump → `python scripts/validate_skills.py` → DoD 全項目検証 → 本書ステータスを「実装完了」に更新してコミット。

## 10. テスト計画

- DoD の grep 4件 + validate_skills.py（機械検証）
- ウォークスルー2件: ①explainer-brief 添付の依頼文を模擬し、工程1スキップ・体験談切替非適用で進むこと ②brief 無しの通常依頼で従来フローになること（ネガティブ）

## 11. 実装時判断ルール

- 挿入文の文言は §5 の確定値を使う。トーン調整のための軽微な言い換えは可、条件・参照先（affiliate-monetization が正、リンクなし公開を止めない）の変更は不可
- 既存節の文面は1文字も変更しない（追記のみ）
- アンカー見出しが改版で変わっていた場合は、同じ意味の節（文体メモ分岐の直後/工程5末尾/レビュー観点列挙）を探して挿入し、その旨を最終報告に書く

## 12. 未解決事項（ユーザー確認待ち）

- B2・B3 の実装トリガーである「ASP審査・アフィリエイト Phase 1 開始」の時期（06設計書 §12 と同一の待ち）。B1 のみ先行実装してよい（oss-explainer を使い始めるならその前に）
