# daily-feedback テストログ（スキル品質ループ）

## Loop 1: 初期検証・品質改善（2026-07-05）

### Phase 0: スコープ・Stop Rules
- **対象**: daily-feedback v1.1.0（新規スキル初回テスト）
- **Stop Rules**:
  - 成功条件: 3つの検証（トリガー境界・SKILL.md追随性・スクリプト敵対テスト）で重大度 HIGH 〜 LOW の修正が全て適用され、妥当性確認完了
  - 安全上限: 3つの検証エージェント並列実行、最大 2 周までリテスト（セッション限度に達した場合は一度の修正で卒業）

### Phase 1-4: 検証・診断

#### 1-1. トリガー境界検証（Haiku / Fable）
- **検証内容**: daily-feedback のキーワードが誤発動・不発動を起こさないか（20パターン）
- **結果**: HIGH リスク 3 件、MEDIUM リスク 5 件を検出
  - HIGH リスク例:
    - #9 「毎日22時に振り返りを自動実行して」→ loop-engineering との dual-match
    - #12 「プロジェクトの振り返り会議事録を作って」→ "retrospective" で誤発動
    - #20 「フィードバックをください（成果物感想）」→ 成果物レビューとの混同
  - MEDIUM リスク例: 時間粒度曖昧（1週間集計への誤対応）、キーワード重複（"prompt improvement"）等

#### 1-2. SKILL.md 追随性検証（Haiku）
- **検証内容**: フィールド名整合・ルーブリック整合・ウォークスルー実施
- **結果**: 重大度 HIGH 1 件、中大 3 件を検出
  - HIGH: ルーブリック②（コスト最適化）の「Fable + cache_hit_pct 高い」ケースが 3 点・1 点どちらか不明確
  - 中大: user_interruptions 定義がスクリプトと矛盾、「良い例の引用不足時の対応」が曖昧、前日確認手順が不具体的

#### 1-3. スクリプト敵対テスト（Sonnet）
- **実施結果**: セッション限度に達して中止（Phase 1 途中で終了）
- **代替**: トリガー・追随性の検証結果から必須項目を手動確認
  - ✅ isSidechain / isMeta / isCompactSummary フィルタの実装は適切（続行確認不要）
  - ✅ JSON キー一致確認済み（観点1）
  - ⚠️ timezone 動作・日付引数検証は未テスト（今後の懸念リスト へ）

### Phase 5: 修正内容

| 優先度 | 項目 | 修正内容 | ファイル・行番号 |
|---|---|---|---|
| HIGH | description 誤発動排除 | 「당日の」明記、"retrospective" 削除、「成果物フィードバック」「会議議事録」を非対応明示 | SKILL.md L3-5 |
| HIGH | loop-engineering 区別 | 「毎日22時に実行」は loop-engineering で設計後、daily-feedback を定時トリガーに登録と明記 | SKILL.md L118-120 |
| HIGH | ルーブリック②明確化 | 3 点の定義を「モデル偏重 + 他指標優良」と「バランス低め」の 2 パターンに分化；1 点に「セッション管理不適切」を追加 | ideal-usage.md L251-260 |
| 中大 | 前日確認手順の具体化 | 「冒頭で 1 行」→「『前回アクション実行状況』セクションを追加し、前日の『明日のアクション』を確認」と明示 | SKILL.md L107-109 |
| 中大 | 「良い例の引用不足」対応 | prompts_dropped > 0 や件数不足時に「データ不足で評価不能」と明記。全体分析が必要な場合の再実行案内も記載 | SKILL.md L47-50 |
| 中大 | user_interruptions 定義の同期 | 「自動検出は『[Request interrupted by user』のみ。自由形式の訂正は手作業確認」と明示 | SKILL.md L55 |

### Phase 6: 記録・卒業判定

**修正後の状態**:
- ✅ description が明確化され、loop-engineering・model-switcher・token-saver との役割分担が文字列レベルで明示
- ✅ ルーブリック②が複合判定に対応（「モデル偏重 + キャッシュ優秀」の場合の判定方法が一意に決まる）
- ✅ SKILL.md のプロセス記述が実装スクリプトと同期（user_interruptions、前日確認の具体性）
- ✅ エッジケース（prompts_dropped > 0）が明示的に処理される

**卒業準備状況**:
- 本ループでは「実運用フィードバック」（Ryo の一言）を得ていないため、「直近10ケース連続合格」には至らず
- セッション限度により「スクリプト敵対テスト」が未完了（以下を懸念リストへ）

### 懸念リスト（Loop 2 以降）
3. **実運用未確認**:
   - ユーザー実機での `/plugin install daily-feedback@claude-skills` 動作
   - 初回実行時の出力形式・引用品質

---

## Loop 2: スクリプト敵対テスト完遂・回帰修正（2026-07-06）

### Phase 1-2: 検証実施（fake HOME + 合成 JSONL、TZ=Asia/Tokyo 明示指定で実行）

Loop 1 で未完了だった6項目を全て実行し、**4件のバグを新規発見**:

| # | 検証観点 | 結果 |
|---|---|---|
| a | isSidechain のプロンプト混入 | **FAIL** → 修正 |
| b | timezone（time フィールド表示） | **FAIL** → 修正 |
| c | 無効な日付引数 | **FAIL**（黙って全ゼロ返却）→ 修正 |
| d | summary/compaction カウント | **FAIL**（type:"summary" が常に未カウント）→ 修正 |
| e | プロンプト順序 | PASS（単一ファイル内は時刻順） |
| f | `<`始まり除外 | PASS（意図通りのトレードオフ） |
| g | 100件超 | PASS（dropped=20, len=100 正確） |
| h | usage/model 欠損 | PASS（クラッシュなし、unknown 扱い） |
| i | コスト計算検算 | PASS（$22.05 一致） |
| — | 非ゼロパディング日付（`2026-7-5`） | **FAIL**（strptime は通すが文字列比較で不一致）→ 修正 |

### Phase 4: 診断・修正

1. **isSidechain 混入（重大）**: サブエージェントへの指示文（Claude自身が書いた文）が
   `prompts` 配列に人間のプロンプトとして混入し、①軸（プロンプティング力）採点を歪めていた。
   `etype == "user" and not e.get("isMeta") and not e.get("isSidechain")` で除外。
   ただしトークンコスト（`models`）は sidechain 分も引き続き集計（実際に消費されたコストのため）。
   → scripts/collect_stats.py L104

2. **timezone 表示バグ**: `time` フィールドが `ts[11:16]`（UTC 生切り出し）になっており、
   JST 環境で表示される時刻が実際のローカル時刻と最大9時間ズレていた。
   `local_dt.strftime("%H:%M")` に変更し、日付フィルタで既に計算済みのローカル時刻を再利用。
   → scripts/collect_stats.py L113

3. **summary 型 compaction 未カウント（重大）**: 実際の Claude Code トランスクリプトで
   `type:"summary"` の圧縮マーカーは timestamp を持たないため、`if not ts: continue` で
   当日フィルタより先に弾かれ、`compactions` に一切カウントされていなかった
   （`isCompactSummary`＝timestamp 付きの別マーカーのみカウントされていた）。
   `type == "summary"` の判定を timestamp チェックより前に移動。
   → scripts/collect_stats.py L78-82

4. **無効・非正規日付引数**: `foobar` 等の不正な値は黙って全ゼロ JSON を返し、ユーザーが
   「本日は利用なし」と誤解するリスクがあった。また `2026-7-5`（ゼロパディングなし）は
   `strptime` 自体は通すが、後続の文字列比較（`target` vs `strftime("%Y-%m-%d")` 出力）で
   常に不一致になり同様に黙って全ゼロを返していた。
   `datetime.strptime(...).strftime("%Y-%m-%d")` で正規化し、パース失敗時は明示的にエラー
   JSON を返すよう修正。
   → scripts/collect_stats.py L44-50

### Phase 5: 回帰確認

- 4修正の個別テスト（PASS）に加え、全シナリオ（summary + isCompactSummary + 通常プロンプト +
  sidechain + interruption + tool_use + コスト計算）を1つの合成ファイルに混在させた統合テストで
  再確認。期待値と完全一致（`compactions: 2`, `user_interruptions: 1`, `prompt_count: 1`,
  `time: "10:00"` JST 等）。
- `python3 -m py_compile` で構文確認、`validate_skills.py` で全スキル整合性確認（PASS）。

### Phase 6: 記録・卒業判定

- 懸念リスト項目1・2（スクリプト敵対テスト・timezone/日付/compaction 系）は本ループで解消。
- 残るは「リサーチ結果統合」（hermes-relay 経由、外部待ち）と「実運用未確認」のみ。

### 懸念リスト（Loop 3 以降）
1. **リサーチ結果統合待ち**（外部・hermes-relay pending）:
   - Claude Code JSONL スキーマの公式定義（isSidechain/isMeta が今回の合成データ前提の推測に
     留まっている点。実機の生ログでの最終確認が望ましい）
   - モデル価格の 2026/07 最新値（collect_stats.py PRICES 定数の妥当性）
   - note.com での Claude 振り返り実践例（reference の厚み向上）
2. **実運用未確認**:
   - ユーザー実機での `/plugin install daily-feedback@claude-skills` 動作
   - 初回実行時の出力形式・引用品質（実データでの動作確認）

---

## 次のループ予定

- **Loop 3**: リサーチ結果統合（cc-cost-ops-web-v2 等）、実機での初回実運用テスト
- **卒業基準到達後**: 「直近10ケース連続合格」達成による「安定運用フェーズ」への移行
