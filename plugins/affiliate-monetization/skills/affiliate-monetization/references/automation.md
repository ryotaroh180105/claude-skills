# automation — 自動運転オプション（既定はオフ。ユーザーがcron登録して初めて動く）

SKILL.md の「週次バッチ」は本来ユーザーの依頼で都度実行するが、`loop-engineering` の
6要素に従い**定時実行に乗せることもできる**。データ契約（funnel-config.md /
link-registry.md / kpi-log.md）・役割分担（§既存スキルとの役割分担）は一切変更しない。
本書はその上に「いつ・誰が実行するか」だけを足す。

## 0. 人間に残る作業（自動運転にしても変わらない）

| 頻度 | 作業 | 自動化できない理由 |
|---|---|---|
| 一度だけ | Step 0ヒアリング5問・ASP登録・Xキー設定・cron登録（§4） | 本人の意思決定・本人名義の会員登録・本人の鍵 |
| 週1 | Xアナリティクス/noteダッシュボード/ASP管理画面の数値をkpi-log.mdへ転記 | 個人向け取得APIが無い（研究済み事実。SKILL.mdの前提どおり） |
| 週2 | note記事の公開ボタン（本文・画像とも自動生成済み。コピペ＋生成済み画像ファイルのアップロードのみ） | noteに公式投稿APIがなく、非公式手段はアカウント停止リスクがあるため不採用（article-writer SKILL.md記載の調査結果と同一根拠） |
| 随時 | post-queue.mdのdraft→approved昇格 | SKILL.mdの契約どおり、承認はユーザーのみ（自動承認は導入しない＝Blind Loop回避） |

## 1. 週次バッチの自動実行ループ

| 要素 | 内容 |
|---|---|
| Trigger | Claude Code Remote の Routine（cron、週1。曜日・時刻はユーザー指定。§4） |
| Doer | SKILL.md「週次バッチ」の4工程をそのまま実行（変更しない）。工程2の note記事制作で
article-writerに委譲する際、画像生成は article-writer `references/note-quality.md` 4-1節の
手順（OpenAI画像生成MCP優先、Gemini代替、両方未設定ならAdobe Express手動フォールバック）で
**この場で画像ファイルまで生成**する |
| Verifier | Doerとは別のAgent（model: haiku）が(a) PR表記文言の有無 (b) link-registryのlink_id指定の整合
(c) 誇大・断定効能表現の不在 を検証。1つでも不合格ならpost-queue.mdはdraftのまま・note原稿も
「要修正」として提示する（Blind Loop回避。合否不明のときは合格にしない） |
| Stop Rules | 成功条件: post-queue.mdへのdraft追記＋note原稿（画像込み）の生成＋PR作成まで。安全上限: 60分・
Doer/Verifier各1体・修正往復3回。**Step 0未実施（funnel-config.mdが無い）ならDoerを起動せず
「初回セットアップ未実施」とだけ報告して終了**（空回り防止） |
| Memory | funnel-config.md / link-registry.md / kpi-log.md（既存3ファイル、フォーマット変更なし） |
| Skills | affiliate-monetization、sns-ops-team、article-writer（画像生成含む）、sns-auto-posting（投稿実行はapproved化後、ユーザー承認を経てから） |
| Human gate | draft→approved昇格・note公開ボタン・週次数値の転記はすべて人間（§0） |

## 2. KPI転記・判断ループ（週1、上記の後 or 別日）

| 要素 | 内容 |
|---|---|
| Trigger | Routine（cron、週1。ユーザーが数値転記を終えた後に起動するのが望ましいため、上記より半日〜1日後を推奨） |
| Doer | kpi-log.mdの最新行を読み、SKILL.mdのKPI判断表を上から順に適用して判断（継続/調整/縮小/撤退検討/撤退/保留）を1行追記。該当したら次週ブリーフに反映する提案をPRに書く |
| Verifier | 別Agentが「数値→判断表の条件→適用した判断」の対応を検算。不一致なら適用を保留しPRに両論併記 |
| Stop Rules | 成功条件: kpi-log.mdへの判断追記＋PR作成。安全上限: 20分・1体。**撤退検討・撤退の適用は自動実行禁止**（ユーザー確認ゲート。SKILL.mdの撤退基準どおり、惰性で進めない） |
| Memory | kpi-log.md |
| Skills | affiliate-monetization のみ |
| Human gate | 撤退検討・撤退の最終判断、数値未転記が続く場合の運用継続確認 |

## 3. セットアップ（一度だけ・ユーザー操作）

| # | 操作 | 意図 | 内容 | 確認方法 |
|---|---|---|---|---|
| 1 | （推奨）画像生成MCPの追加 | note記事のアイキャッチ・挿入画像を週次バッチで完全自動生成するため。未設定でも動くが人間作業がAdobe Express手動生成分だけ増える | `plugins/article-writer/skills/article-writer/references/note-quality.md` 4-1節の手順で OpenAI画像生成MCP（既定）を追加。無料枠で回したい場合のみ Gemini画像生成MCP も追加 | `/mcp` で `gpt-image-mcp` が connected と表示される |
| 2 | 定時実行の登録 | 人が毎週依頼しなくてもループが回るようにする（これが無いと「自動化ごっこ」になる） | `create_trigger`（Claude Code Remote）で週次バッチ用と判断ループ用の2つのRoutineを作成 | 翌週、post-queue.mdにdraft・kpi-log.mdに判断行が自動生成されている |

```
Routine例（プロンプトの骨子。実際の作成は create_trigger で行う）:
1. 週次バッチ: 「affiliate-monetizationの週次バッチを実行して。references/automation.md の
   自動実行ループに従い、Step 0未実施なら何もせず報告して終了して」
2. KPI判断: 「kpi-log.mdの最新行にKPI判断表を適用し、references/automation.md のKPI転記・
   判断ループに従って1行追記して。撤退検討/撤退の場合は自動反映せず私に確認して」
```

## 4. 失敗モードチェック（loop-engineering §8）

| 失敗モード | 対策 |
|---|---|
| Blind Loop | Verifierを Doer と別Agentに分離（§1・§2）。post-queue.mdの承認自体はユーザーのみで自動化しない |
| Tangled Loop | Doerは既存スキル（sns-ops-team / article-writer / sns-auto-posting）の手順呼び出しのみ。データ契約は変更しない |
| Amnesiac Loop | funnel-config.md / link-registry.md / kpi-log.md に毎回永続化 |
| Manual Loop | Routineで自動起動。人間作業は§0の表に列挙されたものだけ |

## 5. 画像生成MCP（2026-07-11 追加調査。既定=OpenAI）

- OpenAI/Google公式のMCPサーバーは確認されず、全てコミュニティ製OSS。
- OpenAI（既定）: [labeveryday/gpt-image-mcp](https://github.com/labeveryday/gpt-image-mcp)。
  課金設定込みのAPIキー必須。1枚あたり目安 Low $0.011 / Medium $0.042 / High $0.167。
- Gemini（無料枠・代替）: [shinpr/mcp-image](https://github.com/shinpr/mcp-image)。
  Google AI Studio の無料枠APIキー。
- 導入手順の正は `plugins/article-writer/skills/article-writer/references/note-quality.md`
  4-1節（重複記載しない）。
- 調査ID: `20260711T191257Z-openai-image-mcp` / `20260711T191257Z-gemini-image-mcp`
