---
name: academic-research
description: 学術研究の「文献調査→論文執筆→査読→改稿→仕上げ」を通しでこなす Academic Research Skills（Imbad0202/academic-research-skills）の導入・実行ガイド。「論文を書きたい」「文献レビューをして」「体系的レビューを回したい」「この論文を査読観点でレビューして」「研究レポートをDOCX/LaTeX/PDFで出したい」といった学術・研究文脈の依頼で発動する。note記事は article-writer、SEO記事は owned-media の管轄で、こちらは学術文書専用。実体は本家マーケットプレイスからインストールする Wrapper で、このリポジトリにコードは同梱しない。英語キーワード: academic writing, literature review, systematic review, peer review simulation, research pipeline, thesis, paper drafting.
---

# Academic Research — 学術研究・論文執筆パイプライン

`Imbad0202/academic-research-skills` は、研究→執筆→査読→修正→完成を4スキル・
マルチエージェント構成で通しでこなす Claude Code 向けスキル集である。

| 本家スキル | 構成 | 役割 |
|---|---|---|
| Deep Research | 13エージェント | 文献調査・ファクトチェック。全モード/迅速/体系的レビュー/ソクラティック等8モード |
| Academic Paper | 12エージェント | 執筆パイプライン。11モード、Markdown→DOCX/LaTeX/PDF 変換、引用確認 |
| Academic Paper Reviewer | 7エージェント | 編集者＋査読者3名＋Devil's Advocate による0-100点ルーブリック査読 |
| Academic Pipeline | 10段階 | 上記3つを研究→執筆→査読→修正→完成まで統合するオーケストレータ |

## このリポジトリでの位置づけ（Wrapper）

このスキルは本家のコードを複製しない。理由:

- 本家は4スキル＋10個の `/ars-*` コマンド＋エージェント定義＋Python検証スクリプトを含む
  大規模スイートで、高頻度に更新されている（確認時点で Pipeline v3.15.0）。部分コピーは
  追従不能。
- 本家は自己完結した Claude Code マーケットプレイスとして配布されており、直接
  インストールするのが最も安全で最新版を保てる。
- **ライセンスが CC-BY-NC 4.0（表示必須・非営利限定）**。コードをこのリポジトリに
  同梱すると NC 条件の管理が複雑になるため、参照に留める。

## ⚠️ ライセンス上の利用制限（先に必ず伝える）

本家は **CC-BY-NC 4.0**。利用を案内する前に次を確認する:

- **商用利用は不可**。受託の記事作成・有償納品物・営利目的の成果物にこのスキル群を
  使ってはいけない。副業案件には使わない。
- 大学のレポート・卒論・修論・投稿論文・個人の学習・非営利の研究利用は問題ない。
- 成果物にクレジット表示を推奨:
  `Based on Academic Research Skills by Cheng-I Wu — https://github.com/Imbad0202/academic-research-skills`
- 商用で同種の機能が必要な場合は、article-writer / owned-media＋WebSearchで代替する
  （このリポジトリのスキルは自作のため制限なし）。

## 前提セットアップ

| 種別 | 名前 | 用途 | 未設定時の挙動 |
|---|---|---|---|
| プラグイン | 本家マーケットプレイス | スキル本体 | 下記の導入手順を案内する |
| 任意 | pandoc / LaTeX 環境 | DOCX/LaTeX/PDF 変換（Academic Paper の形式変換） | 未導入なら Markdown 出力までで運用し、変換時に本家 `docs/SETUP.md` を案内 |

## 導入手順

```
/plugin marketplace add Imbad0202/academic-research-skills
/plugin install academic-research-skills
```

導入確認: `/plugin list` で enabled を確認し、`/ars-plan` で論文構成のソクラティック対話が
起動すれば成功。従来方式（`git clone` ＋ `~/.claude/skills/` へのシンボリックリンク）も
本家 `docs/SETUP.md` に記載があるが、マーケットプレイス方式を既定とする。

## 使い方（代表パターン）

- **研究計画から始める**: `/ars-plan` — ソクラティック対話でリサーチクエスチョンと
  論文構成を固める。
- **文献調査だけ**: Deep Research を「体系的レビュー」または「迅速」モードで呼ぶ。
- **執筆〜形式変換**: Academic Paper で草稿→引用確認→DOCX/LaTeX/PDF。
- **提出前の模擬査読**: Academic Paper Reviewer に通し、0-100点のルーブリックと
  Devil's Advocate の反論を受けてから改稿する。
- **全部通しで**: Academic Pipeline に任せ、10段階（研究→執筆→査読→修正→完成）を
  オーケストレーションさせる。

コマンドの全一覧・各モードの詳細は本家 `commands/` と `docs/ARCHITECTURE.md` を参照する
（このリポジトリには複製しない）。

## このリポジトリの他スキルとの境界

| 依頼 | 使うスキル |
|---|---|
| note の発信記事 | article-writer |
| SEO・アフィリエイト記事（商用） | owned-media |
| 学術論文・文献レビュー・卒論修論（非商用） | このスキル（本家スイート） |
| 商用の調査レポート | requirements-definition ＋ WebSearch（本家スイートは NC のため使わない） |

## エッジケース

- **商用案件で使いたいと言われた**: NC 制限を伝えて断り、上の表の代替を提案する。
- **本家が未インストールのまま学術依頼が来た**: 導入手順を案内し、導入の意思がなければ
  article-writer の体験談型とは別物である旨を断った上で、素の Claude＋WebSearch での
  簡易文献調査に縮退する（「体系的レビュー」を名乗らない）。
- **引用・参考文献の正確性**: 本家の引用確認機能があっても、実在しない文献の混入
  （ハルシネーション）はゼロにならない。最終的な文献実在チェックはユーザーが行う
  （CLAUDE.md「AI出力の検収原則」参照）。

---
出典: https://github.com/Imbad0202/academic-research-skills（CC-BY-NC 4.0, by Cheng-I Wu）。
本リポジトリにはコードを同梱せず、導入・利用条件の案内のみを行う。
