---
name: asset-research
description: 自分専用の資産運用分析エンジン。無料の一次データ（FRED・e-Stat・EDINET・SEC EDGAR）に基づくマクロダッシュボード・分析メモ・意思決定ジャーナルで投資判断の規律を構造化する。「資産運用の分析をして」「IPSを作りたい」「マクロの状況を教えて」「〜を分析メモにして」「ジャーナルをレビューして」「投資判断を記録したい」といった依頼で使用する。詳細設計は docs/designs/23-asset-research-engine.md が正。英語キーワード: asset research, investment journal, IPS, macro dashboard, DCF, equity analysis, decision journal.
---

# asset-research — 自分専用の資産運用分析エンジン

**本スキルは投資助言を行わない。** 分析メモ・ジャーナルは判断材料の整理であり、
妥当性の評価と最終判断はユーザー自身が行う。価格予測・売買シグナル生成・自動売買は
スコープ外（`docs/designs/23-asset-research-engine.md` §2.2）。

## 前提セットアップ

| 種別 | 名前 | 用途 | 未設定時の挙動 |
|---|---|---|---|
| 環境変数 | `FRED_API_KEY` | 米マクロ指標取得 | 発行URL(https://fred.stlouisfed.org/docs/api/api_key.html)を提示して当該指標のみ`FETCH_FAILED` |
| 環境変数 | `ESTAT_APP_ID` | 日本統計取得 | 発行URL(https://www.e-stat.go.jp/api/)を提示して当該指標のみ`FETCH_FAILED` |
| 環境変数 | `EDINET_SUBSCRIPTION_KEY` | 日本企業開示取得 | 発行URL(https://api.edinet-fsa.go.jp/)を提示して停止 |
| private リポジトリ | `<GitHub owner>/invest-journal` | IPS・ジャーナル・分析メモの保存先 | セットアップ手順を提示して停止（§1参照） |
| プラグイン（任意・Phase 1.5） | `anthropics/financial-services` の `model-builder` | DCF/Comps/3-statementのExcelモデル | 未導入でも動作する（E2が簡易記述に留める） |

キーは `~/.asset-research/.env`（ローカル）または本セッションの環境変数に設定する。
**このリポジトリにも invest-journal にもキーを書かない。**

## 0. 初回セットアップ（invest-journal が無い場合）

1. ユーザーに private リポジトリ `invest-journal` の新規作成を依頼する（GitHub上で作成）。
2. 作成後、`add_repo` でセッションに追加してもらう。
3. `journal/`, `memos/`, `reviews/` ディレクトリと空の `README.md` を作成する。

## 1. IPS（投資方針書）作成

初回、または `ips.md` が存在しない場合に対話で作成する。埋める項目は
`docs/designs/23-asset-research-engine.md §5.5` の全項目（運用目的・期間、月次拠出可否、
リスク許容度、資産クラス配分レンジ、1銘柄上限、コア/サテライト比率、NISA枠、
リバランス条件、変更ルール）。リスク許容度は「30%下落したら金額でいくら減るか」を
提示して体感確認する。作成後:

```bash
python plugins/asset-research/skills/asset-research/scripts/ips_schema.py --validate <invest-journal>/ips.md
```

`NG` の場合、指摘された不足項目を埋め直すまで先に進まない。

## 2. マクロダッシュボード

```bash
python plugins/asset-research/skills/asset-research/scripts/fetch_macro.py --dashboard
```

出力は中立記述のみ。百分位を根拠にした配分変更提案はしない（§6.2）。

## 3. 分析（analyze フロー、E2→E3→E4）

1. `asset-research-analyst`（E2）エージェントにテーマ・銘柄を渡し、8セクション形式の
   ドラフトを作らせる（`references/memo-template.md` 参照）。
2. ドラフトを一時ファイルに保存し、**別コンテキストの** `asset-research-verifier`（E3）に
   検証させる。FAIL ならメモを差し戻す。
3. E3合格後、**別コンテキストの** `asset-research-risk`（E4）にゲート判定させる
   （買い/売り登録の場合のみ。ウォッチ目的の分析はE4を省略可）。
4. E4が「差し戻し」を返したら、E2に理由を伝えて再ドラフト（最大2往復）。
5. 承認されたメモを `invest-journal/memos/YYYY-MM-DD-<slug>.md` に保存する。

保存前に必ずスキーマ検証を通す:

```bash
python plugins/asset-research/skills/asset-research/scripts/memo_schema.py --validate <path>
```

## 4. ジャーナル登録（買い/売り/リバランス/ウォッチ）

E4承認後、`docs/designs/23-asset-research-engine.md §5.4` のスキーマで
`invest-journal/journal/J-NNN-<slug>.md` を作成する。IDは以下で採番:

```bash
python plugins/asset-research/skills/asset-research/scripts/journal.py --journal-dir <invest-journal>/journal
```

クーリングオフ起点の `first_seen_at` は、対象テーマの最初の分析メモの frontmatter `date`
（日付のみの場合は当日00:00Z）とする。メモが無い場合はゲートを実行できない（先にメモを書く）。

## 5. 月次レビュー（30分に収める）

```bash
python plugins/asset-research/skills/asset-research/scripts/journal.py --list-due \
  --journal-dir <invest-journal>/journal
```

該当ジャーナルの答え合わせ、IPSレンジ逸脱確認、override回数・所要時間の記録を行い、
`invest-journal/reviews/YYYY-MM.md` に保存する。**縮退基準**（§6.4）: レビュー所要60分超が
2ヶ月連続、または fetcher 修繕が月3件超 → Phase を1段階縮退する提案をユーザーに出す。

## 6. 暴落時モード

ユーザーが「下がってる」「売りたい」と言った時は新規分析をせず、まず該当ジャーナルの
`falsifier` と `ips.md` を確認し、反証条件に該当しているかだけを判定する
（§6.6）。該当なしなら「IPS上は何もしない日」と返す。

## やらないこと（明示的スコープ外）

- 価格予測・売買シグナル生成・自動売買（原理的に不可能、または執行リスクを負わないため）
- 他人向けの助言・レポート販売（`docs/designs/22-agent-monetization-designs.md` 案③bへ委譲）
- Bloomberg/FactSet等の有償データ接続（`anthropics/financial-services` の `partner-built/` 配下、本スキールでは使わない）

## 参照

- 詳細設計・データ層・品質10要素・失敗シナリオ: `docs/designs/23-asset-research-engine.md`
- 分析メモ8セクションのテンプレート: `references/memo-template.md`
- IPSのテンプレート: `references/ips-template.md`
