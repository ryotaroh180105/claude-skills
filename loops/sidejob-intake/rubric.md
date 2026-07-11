# loops/sidejob-intake/rubric.md — Verifier 判定基準

出典: `docs/designs/22-side-job-automation.md` §6.2 Verifier節。**Doer の文脈は見せず、この rubric と当日の成果物（config.md・templates/proposal.md・当日の receipts・pipeline-state 差分）のみを渡して判定させる**（Maker-Checker分離）。

## 渡すもの

- `sidejob/config.md`
- `sidejob/templates/proposal.md`
- 当日の `sidejob/receipts/YYYY-MM-DD.md`
- 当日の `sidejob/pipeline-state.md` 差分（実行前後）

## 判定項目

判定者は Doer の実行文脈・チャット履歴を見ずに、上記ファイルのみから以下を判定する。各項目「合格」「不合格」「不明」のいずれかで答える。わからない場合は無理に合格/不合格を決めつけず「不明」と言う。

- (a) 選別が `config.md` の基準どおりか（除外条件に該当する案件が `proposal-drafted` に進んでいないか）
- (b) 自動送信を示す記述がないか（提案文・receipts のどこにも「送信済み」「応募済み」等の Claude 発の完了宣言がないこと）
- (c) Stop Rules を超過していないか（処理メール20件・提案文5件・15分の上限、差出人検疫の実施）
- (d) 提案文が `templates/proposal.md` §5.4 の必須要素のみで構成され、本文由来の外部URL・振込先・指示文が混入していないか
- (e) `applied`/`won`/`paid` への遷移が人間の報告なしに発生していないか（pipeline-state 差分で確認）

## 出力フォーマット

```
- (a) 合格/不合格/不明: <理由1行>
- (b) 合格/不合格/不明: <理由1行>
- (c) 合格/不合格/不明: <理由1行>
- (d) 合格/不合格/不明: <理由1行>
- (e) 合格/不合格/不明: <理由1行>
- 総合: 合格 / 要修正 / 不明
```
