# OpenMontage 動画編集エージェント（CLI アプリ）設計書

| 項目 | 値 |
|---|---|
| ステータス | 実装完了（2026-07-10、`ryotaroh180105/openmontage` にpush済み）。単体16+E2E3=19テスト全通過。ingestのwhisper文字起こしのみ開発サンドボックスのネットワーク制約で未検証（CI環境では到達可）。同梱フォントはNoto Sans JP→IPAゴシックに変更（開発環境の制約、ライセンス互換） |
| 種別 | アプリ（CLI） |
| 優先度 | Tier F-6 |
| 実装モデル | Sonnet 5（推奨 effort: high） |
| 依存する設計書 | docs/designs/00-fable-sonnet-bridge.md（テンプレ・運用プロセス）、docs/designs/04-repo-reorganization.md §5.1 分類E（アプリは別リポジトリ） |
| 依存する既存スキル | なし（将来 sns-ops-team が出力を消費するが本アプリ側の依存ではない） |
| 外部依存 | ffmpeg / ffprobe（システムバイナリ）、faster-whisper（pip、初回に音声認識モデルを自動ダウンロード）、Anthropic API キー（compose ステップの AI 判断） |

**成果物の置き場（確定）**: 本アプリのコードは**このリポジトリに置かない**。別リポジトリ
`ryotaroh180105/openmontage` を新規作成する（04 設計書 §5.1 分類E: 1アプリ1リポジトリ、
FFmpeg 実行と動画バイナリ出力を伴うためスキルではなくアプリ）。本設計書のみ claude-skills
の `docs/designs/` に置く。実装は openmontage リポジトリで行う。

## 1. 目的・背景（Why）

長尺の横長素材（セミナー録画・自撮り解説・画面録画、数分）から、TikTok/Shorts/Reels 向けの
縦型（1080x1920）ショート動画を作る作業は、CapCut や Premiere で「無音カット → テロップ打ち →
縦型トリミング → 強調装飾」を手作業で行うと1本30〜60分かかる。この定型作業を、
**AI が編集方針を判断し、その判断を確定スキーマの中間表現（EditPlan）に落とし、コードが
FFmpeg フィルタグラフに変換して決定的にレンダリングする**ことで数分に短縮する。

設計の核は **AI 判断層とコード処理層の分離**:

- AI はテキスト（文字起こし＋無音区間）だけを見て「どの区間を残すか・テロップの割り方と
  文言・強調箇所」を**構造化 JSON（EditPlan）として1回だけ**出力する。
- FFmpeg コマンド・フィルタグラフは AI に書かせない。EditPlan を決定的コンパイラが
  filter_complex + 字幕ファイルに変換する。同じ EditPlan からは同じ動画が再現される。

これにより「AI 生成の不確実性」を EditPlan の生成という1点に閉じ込め、レンダリングは
再現可能・検証可能・バッチ可能になる。想定ユーザーは本人（SNS 運用で縦動画を量産）と、
ショート動画編集を外注している発信者。既存スキル（sns-ops-team 等）はテキスト投稿までで、
動画そのものを出力する資産はない。

### OpenMontage 思想（パイプライン分割）の適用

編集を4段に分け、各段の入出力を確定スキーマの JSON ファイルにする。各段は独立実行でき、
中間ファイルを差し替えれば途中からやり直せる:

1. **取り込み（ingest）**: probe.json + transcript.json
2. **カット候補抽出（segment）**: segments.json
3. **構成（compose・唯一の AI 判断段）**: editplan.json
4. **レンダリング（render・決定的）**: 完成 mp4

## 2. スコープ

### 2.1 やること

- Python CLI `openmontage`（サブコマンド: `ingest` / `segment` / `compose` / `render` / `run`）
- ingest: ffprobe でメタ情報取得 + faster-whisper で単語タイムスタンプ付き文字起こし
- segment: ffmpeg `silencedetect` で無音区間を検出し、発話区間の候補を切り出す
- compose: transcript.json + segments.json を Anthropic API に渡し、EditPlan JSON を1回生成
  → JSON Schema 検証（失敗時1回リトライ、なお失敗なら exit 1）
- render: EditPlan → filter_complex（trim/concat/crop/scale）+ ASS 字幕ファイルを生成 →
  ffmpeg 実行 → 1080x1920 mp4 出力（無音カット済み・テロップ焼き込み済み・強調色反映済み）
- 入力正規化: render 前に素材を固定 fps・ステレオ音声・既知ピクセルフォーマットへ変換する前処理段
- EditPlan の人手編集を前提とした設計（compose 出力を「叩き台」とし、ユーザーが JSON を
  直接直して render し直せる）
- 対象言語は日本語のみ（Noto Sans JP Bold フォントを同梱）
- ビジネス運用面シート（§下部）と README 冒頭10行を成果物に含める

### 2.2 やらないこと（明示的スコープ外）

- **ハイライトの意味的自動抽出**（「面白い所」をAIが判断して切る）— YAGNI かつ品質検証不能。
  MVP は「無音カット＋全編テロップ化」に限定。意味抽出は別 MVP（§12）
- **BGM の自動選曲・ミキシング** — 著作権リスクと選曲品質の不確実性。BGM は扱わない
- **複雑なトランジション・エフェクト・複数素材の合成** — YAGNI。カットは単純 concat のみ
- **GUI・プレビュー UI・タイムライン編集画面** — CLI のみ。編集は EditPlan JSON の直接編集で行う
- **SaaS 化・クラウドデプロイ・ジョブキュー・複数ユーザー対応** — YAGNI。ローカル CLI のみ
- **多言語対応**（英語字幕・自動翻訳）— 日本語のみ。実ユーザーの要望が出てから
- **リアルタイム/ライブ配信処理** — ファイルバッチのみ
- **顔追従の自動クロップ・話者ダイアライゼーション** — MVP は中央固定 or 手動 focus_x のみ
- **claude-skills 側への companion スキル作成** — YAGNI。Claude は CLI を直接呼べる。
  CLI が安定し手動利用が3回を超えたら薄い起動スキルを再検討（§11）
- **EditPlan スキーマのバージョン移行機構** — v1 のみ。破壊的変更が必要になってから

## 3. 完成条件（Definition of Done）

すべて openmontage リポジトリ内で検証する。`SAMPLE` は同梱テスト素材
`tests/assets/sample_1080p_30s.mp4`（横長1920x1080・30fps・日本語音声30秒・無音区間を含む）。

- [ ] `ffmpeg -version` と `ffprobe -version` が exit 0（前提バイナリの存在確認）
- [ ] `pip install -e .` が exit 0 で、`openmontage --help` が exit 0 でサブコマンド一覧を表示
- [ ] `openmontage ingest tests/assets/sample_1080p_30s.mp4 --workdir work` が exit 0 で
      `work/probe.json` と `work/transcript.json` を生成し、transcript.json の `words` 配列が
      1要素以上・各要素が `{"start","end","text"}` を持つ
- [ ] `openmontage segment tests/assets/sample_1080p_30s.mp4 --workdir work` が exit 0 で
      `work/segments.json` を生成し、`segments` 配列が1要素以上
- [ ] `python -c "import json,jsonschema; jsonschema.validate(json.load(open('work/editplan.json')), json.load(open('schema/editplan.schema.json')))"`
      が例外なく終了する（compose 出力が確定スキーマに適合）。※ compose には API キーが必要なため
      キー無し環境では `tests/assets/editplan_fixed.json` を editplan.json として使う
- [ ] `openmontage render --edit-plan tests/assets/editplan_fixed.json --input tests/assets/sample_1080p_30s.mp4 -o out.mp4`
      が exit 0 で `out.mp4` を生成
- [ ] `ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 out.mp4`
      の出力が `1080,1920`（縦型に変換されている）
- [ ] `ffprobe -v error -show_entries format=duration -of csv=p=0 out.mp4` の値が、
      editplan_fixed.json の keep=true 区間の合計尺 ±0.15 秒に収まる（無音カットが効いている）
- [ ] 同じ EditPlan で render を2回実行し、出力2本の映像ストリーム尺が一致（再現性）
- [ ] `openmontage run --input tests/assets/sample_1080p_30s.mp4 -o out2.mp4`（要 API キー）が
      exit 0 で out2.mp4 を生成。キー無し環境ではこの項目のみスキップ可（理由をログ出力）
- [ ] 音声トラックなし素材 `tests/assets/silent_1080p.mp4` に対し ingest が exit 0 で、
      transcript.json の `words` が空配列（クラッシュしない）
- [ ] README.md 冒頭10行に一文価値提案・デモ実行例・導入3ステップがある
- [ ] `docs/biz-ops.md` が本設計書のシートと同内容で存在する

## 4. 成果物の構成（ファイルレイアウト）

openmontage リポジトリの構成（このリポジトリには作らない）:

```
openmontage/
├── README.md                       # 冒頭10行=LP（価値提案・デモ・導入3ステップ）
├── pyproject.toml                  # パッケージ定義（entry point: openmontage）
├── docs/biz-ops.md                 # ビジネス運用面シート（本設計書§下部を転記）
├── CHANGELOG.md                    # v0.1.0
├── schema/
│   └── editplan.schema.json        # EditPlan の JSON Schema（§5.3）
├── assets/
│   └── NotoSansJP-Bold.ttf         # 日本語テロップ用フォント（同梱・SIL OFL）
├── src/openmontage/
│   ├── __init__.py
│   ├── __main__.py                 # `python -m openmontage` エントリ
│   ├── cli.py                      # argparse サブコマンド定義
│   ├── ingest.py                   # probe.json + transcript.json 生成
│   ├── segment.py                  # segments.json 生成（silencedetect）
│   ├── compose.py                  # Anthropic API 呼び出し→editplan.json + schema検証
│   ├── render.py                   # 入力正規化→filter_complex+ASS生成→ffmpeg実行
│   ├── filtergraph.py              # EditPlan→filter_complex 文字列コンパイラ（決定的）
│   ├── ass.py                      # EditPlan.captions→ASS字幕ファイル生成（決定的）
│   ├── schema.py                   # editplan の読込・検証ヘルパ
│   └── errors.py                   # 例外定義（前提未設定を自己説明的に出す）
└── tests/
    ├── assets/sample_1080p_30s.mp4       # 正常系テスト素材
    ├── assets/silent_1080p.mp4           # 音声なしテスト素材
    ├── assets/editplan_fixed.json        # 固定 EditPlan（API不要でrenderをテスト）
    ├── test_filtergraph.py               # コンパイラ単体（ffmpeg不要・文字列検証）
    ├── test_ass.py                       # ASS生成単体
    ├── test_schema.py                    # スキーマ検証（正例・反例）
    └── test_render_e2e.py                # render E2E（ffmpeg実行・ffprobeで実測）
```

## 5. データ構造

段間の受け渡しはすべて JSON ファイル。時間の単位は秒（float、小数第2位まで）。

### 5.1 probe.json（ingest 出力・素材メタ）

```json
{
  "path": "tests/assets/sample_1080p_30s.mp4",
  "duration": 30.00,
  "width": 1920,
  "height": 1080,
  "fps": 30.0,
  "has_audio": true
}
```

### 5.2 transcript.json（ingest 出力・単語タイムスタンプ）

```json
{
  "language": "ja",
  "words": [
    {"start": 1.20, "end": 1.55, "text": "今日"},
    {"start": 1.55, "end": 1.80, "text": "は"}
  ]
}
```

`has_audio: false` の素材では `words: []`（空配列）を出す。

### 5.2b segments.json（segment 出力・発話候補区間）

silencedetect（デフォルト: noise=-30dB, d=0.5s）で無音を検出し、無音でない区間を発話候補とする。

```json
{
  "silence_db": -30,
  "min_silence_sec": 0.5,
  "segments": [
    {"id": 0, "src_start": 1.10, "src_end": 8.40},
    {"id": 1, "src_start": 9.30, "src_end": 15.20}
  ]
}
```

### 5.3 editplan.json（compose 出力＝AI 判断層の唯一の出力・render 入力）

**これが AI 判断層とコード処理層の境界**。AI はこの JSON だけを生成し、FFmpeg には一切触れない。

```json
{
  "version": "1",
  "source": {"path": "tests/assets/sample_1080p_30s.mp4", "duration": 30.00, "width": 1920, "height": 1080, "fps": 30.0},
  "output": {"width": 1080, "height": 1920, "fps": 30.0},
  "crop": {"mode": "center", "focus_x": 0.5},
  "style": {
    "font": "assets/NotoSansJP-Bold.ttf",
    "font_size": 64,
    "primary_color": "&H00FFFFFF",
    "outline_color": "&H00000000",
    "emphasis_color": "&H0000FFFF",
    "position": "bottom",
    "margin_v": 220
  },
  "segments": [
    {"id": 0, "src_start": 1.10, "src_end": 8.40, "keep": true},
    {"id": 1, "src_start": 9.30, "src_end": 15.20, "keep": false}
  ],
  "captions": [
    {"segment_id": 0, "src_start": 1.20, "src_end": 3.00, "text": "今日はこれを紹介します", "emphasis": false},
    {"segment_id": 0, "src_start": 3.00, "src_end": 4.80, "text": "完全無料", "emphasis": true}
  ]
}
```

**確定ルール（コンパイラが依拠する不変条件。schema と render で強制）**:

- 出力タイムライン = `keep:true` の segments を editplan の配列順に連結したもの。
- caption は素材時間（src_start/src_end）で指定。コンパイラが出力時間へ変換する:
  `out_t = (直前までの keep 区間の合計尺) + (caption.src_start − 所属 segment.src_start)`。
- caption.src_start/src_end は所属 segment の [src_start, src_end] 内に収まらねばならない（schema 外・render 側検証で強制、外れたらクランプせず exit 1）。
- color は ASS の `&HAABBGGRR` 16進。emphasis:true の caption は primary_color の代わりに emphasis_color を使う。
- crop.mode は `center` のみ MVP 対応（focus_x は将来拡張のため受けるが center 以外は exit 1）。

### 5.3b editplan.schema.json（JSON Schema・要点）

`version`（const "1"）・`source`・`output`・`crop`・`style`・`segments`（各 id,src_start,src_end,keep 必須）・
`captions`（各 segment_id,src_start,src_end,text,emphasis 必須）を `required`。追加プロパティ禁止
（`additionalProperties:false`）。数値は `minimum:0`。text は `minLength:1`。フル JSON は実装時に schema/ へ置く。

### 5.4 AI 判断層への制約（compose のプロンプト設計・確定）

compose は Anthropic API（claude-code-guide で最新モデル ID を確認して選ぶ、既定 effort=通常）に
transcript.json の words と segments.json を渡し、以下を厳守させる:

1. 出力は editplan.schema.json に適合する JSON のみ（前後の散文禁止、tool 出力 or ```json ブロック）。
2. caption.text は transcript の words を連結・軽整形（句読点付与・言い淀み除去）した文字列に限る。
   **transcript に無い内容を創作しない**（render 側で全 caption text の文字が該当 segment の
   words 連結に含まれるかを緩く検証し、乖離率が高ければ warn。ハード fail はしない）。
3. 各 caption は最大18文字（超える発話は複数 caption に分割）。
4. 明らかなフィラー区間（words が無い segments、相槌のみ）は keep:false。
5. emphasis:true は動画全体の caption の20%以下。

## 6. 処理フロー

`openmontage run` は ingest→segment→compose→render を順に実行。各サブコマンドは単独実行可。

- **ingest**（入力: 素材パス → 出力: probe.json, transcript.json）
  ffprobe で probe.json 生成 → faster-whisper（既定モデル `small`、初回に自動 DL、`--model` で変更可）で
  単語タイムスタンプ付き文字起こし → transcript.json。has_audio=false なら words=[] で正常終了。
- **segment**（入力: 素材パス → 出力: segments.json）
  ffmpeg silencedetect のログをパースし無音区間を得る → 補集合を発話候補 segment とし id 付与。
- **compose**（入力: transcript.json + segments.json + `--target-sec`（既定なし=無音カットのみ）→
  出力: editplan.json）§5.4 の制約で Anthropic API を1回呼ぶ → JSON 抽出 → schema 検証 →
  失敗時プロンプトに検証エラーを添えて1回だけ再試行 → なお失敗なら exit 1。
- **render**（入力: editplan.json + 素材パス → 出力: mp4）
  1) 入力正規化: ffmpeg で固定 fps・yuv420p・44.1kHz ステレオへ変換した中間ファイルを作る
     （可変フレームレート・無音声・異ピクセルフォーマット素材を吸収）。音声なし素材は
     無音トラックを合成。
  2) filtergraph.py が editplan → filter_complex を生成（segments を trim+setpts、
     audio を atrim+asetpts、concat=n:v=1:a=1、crop で 9:16 中央切り出し、scale=1080:1920）。
  3) ass.py が captions → ASS ファイルを生成（style と emphasis 色を反映、時間は出力タイムライン）。
  4) ffmpeg を `-filter_complex ...,subtitles=work/caption.ass` で実行し mp4 出力。
     完了後、ffprobe で解像度と尺を実測し、editplan の期待尺と ±0.15s 以内かを検査（外れたら
     非0終了して警告）。

## 7. エッジケース

| ケース | 期待挙動 |
|---|---|
| ffmpeg/ffprobe が PATH にない | 起動時に検出し「ffmpeg が必要です。インストール手順は README 参照」と自己説明メッセージを出し exit 2（無言クラッシュしない） |
| Anthropic API キー未設定で compose/run 実行 | 「ANTHROPIC_API_KEY を設定してください」と出し exit 2。render 単独は API 不要で動く旨も表示 |
| 素材に音声トラックがない | ingest は words=[] で正常終了。compose は全区間 keep で caption なしの editplan を返す（テロップ無し縦型変換のみ） |
| 可変フレームレート素材 | render の入力正規化段で固定 fps に変換してから処理 |
| 素材が既に縦型（例 1080x1920） | crop=center は縦横比一致のため実質スケールのみ。クラッシュしない |
| caption.src が所属 segment 範囲外 | render 側検証で exit 1（クランプで黙って直さない。EditPlan の欠陥を顕在化） |
| compose が schema 不適合 JSON を2回返す | exit 1。work/compose_raw.txt に生応答を残し原因追跡可能にする |
| 巨大素材（30分超） | 警告を出すが処理は続行。whisper が遅い旨を表示（MVP は上限を設けない。実運用で遅ければ §12 で分割検討） |
| keep:true の segment が0件 | 「残す区間がありません。EditPlan を確認してください」と出し exit 1 |
| 日本語フォント欠損（同梱アセット削除） | render 開始前に assets/NotoSansJP-Bold.ttf の存在を確認し、無ければ exit 2 |

## 8. 失敗シナリオとレッドチーム所見

| # | 失敗シナリオ | 早期警報サイン | 設計上の対策 |
|---|---|---|---|
| 1 | AI のテロップ割り・強調・カット判断が手作業に劣り、結局手直しで時短にならない（最頻・プロダクト成立の生命線） | ドッグフーディングログで「render 後に EditPlan を手修正した割合」が高い／再生成回数が多い | 完全自動を謳わず EditPlan を**編集可能な叩き台**と位置づける（§1・§2.1）。EditPlan JSON を人が直して再 render できる設計で「AI 8割＋手修正2割でも手作業ゼロより速い」を狙う。§5.4 で AI の裁量を限定し暴走を防ぐ |
| 2 | ffmpeg・faster-whisper モデル DL・日本語フォントの導入で time-to-first-value が5分を超え、使われない | 導入手順の途中で失敗報告が出る／初回 whisper DL が数百MBで詰まる | 前提を README 先頭に表で明示（§biz-ops）。フォントは同梱、whisper 既定モデルを軽量な `small` にし DL サイズを抑える。前提未設定時は exit 2 で自己説明メッセージ（§7）。将来 Dockerfile を検討（§12） |
| 3 | 特定入力（可変fps・音声なし・異ピクセルフォーマット・縦型素材）で filtergraph が壊れ、出力が破損 or クラッシュ | render が非0終了、または ffprobe で解像度/尺が期待外 | render 冒頭に入力正規化段を必須化（§6-render-1）。§3 の完成条件で解像度・尺・音声なし素材を実測検証。§7 のエッジケース表で各異常入力の期待挙動を確定。filtergraph.py は ffmpeg 不要の文字列単体テスト（test_filtergraph.py）で網羅 |

計画ゲート回答: (1) 上表3件。(2) やらない境界は §2.2（特にハイライト意味抽出・BGM・GUI・SaaS を
明示禁止）。(3) 完成条件は全て ffprobe/exit code の実行観察形式（§3）。(4) 実装者が最初に詰まるのは
「AI に ffmpeg を直接書かせるか」→ 書かせず EditPlan→決定的コンパイルと §1・§5.3 で確定。
(5) 必要性: 既存スキル・設計書に動画出力資産なし、SNS 運用パイプラインを直接補完。

## 9. 実装手順（Sonnet 向けタスク分割）

順序依存: 1→2→3 は基盤。4（filtergraph/ass/render）と 5（ingest/segment）は 3 の後で並行可。
6（compose）は 5 と schema の後。7 は最後。

1. **リポジトリ初期化** — `ryotaroh180105/openmontage` を作成（public/private はユーザー確認・§12）。
   pyproject.toml で entry point `openmontage=openmontage.cli:main`。完了条件: `pip install -e .` と
   `openmontage --help` が exit 0。
2. **EditPlan スキーマ確定** — schema/editplan.schema.json を §5.3/§5.3b どおり作成。schema.py で
   読込・検証ヘルパ。完了条件: test_schema.py の正例通過・反例（additionalProperties 混入）で fail 検出。
3. **CLI 骨組み** — cli.py に5サブコマンドと共通 `--workdir`。前提バイナリ/キー検査と自己説明エラー
   （errors.py, §7）。完了条件: 各サブコマンドが未実装でも引数解釈し exit 2 で前提エラーを出す。
4. **決定的レンダリング** — filtergraph.py（EditPlan→filter_complex）、ass.py（captions→ASS）、
   render.py（入力正規化→ffmpeg 実行→ffprobe 検証）。テスト素材 tests/assets/ を用意。
   完了条件: §3 の render/ffprobe 解像度=1080,1920・尺 ±0.15s・再現性・音声なし素材の各項目。
5. **ingest / segment** — ingest.py（ffprobe+faster-whisper）、segment.py（silencedetect パース）。
   完了条件: §3 の probe/transcript/segments 生成項目、has_audio=false で words=[]。
6. **compose（AI 判断層）** — compose.py。§5.4 の制約プロンプトで Anthropic API 呼び出し→JSON 抽出→
   schema 検証→1回リトライ。claude-code-guide で最新モデル ID を確認。完了条件: fixed fixture で
   schema 適合 JSON を生成、不適合2回で exit 1・生応答を残す。
7. **README + biz-ops.md + CHANGELOG + 通し確認** — README 冒頭10行（§biz-ops）、docs/biz-ops.md、
   CHANGELOG v0.1.0。`openmontage run`（要キー）で通し E2E。完了条件: §3 全項目にチェック。

## 10. テスト計画

- **単体（ffmpeg/API 不要）**: test_filtergraph.py（既知 EditPlan→期待 filter_complex 文字列を
  部分一致検証）、test_ass.py（emphasis 色・出力時間変換の検証）、test_schema.py（正例/反例）。
- **E2E（ffmpeg 必要・API 不要）**: test_render_e2e.py で editplan_fixed.json を render し、
  ffprobe で解像度=1080x1920・尺 ±0.15s・2回実行の尺一致を実測（コード読解での確認は不可）。
- **API 必要部分**: compose は Anthropic レスポンスをモック（固定 JSON）した単体テストで
  「schema 検証→リトライ→exit 1」の分岐を検証。実 API を使う通し確認は §3 の run 項目で1回、
  キー無し CI ではスキップ（スキップ理由をログ出力）。
- **CI**: GitHub Actions で ffmpeg を apt インストールし単体＋E2E（API 不要分）を実行。

## 11. 実装時判断ルール

- AI に ffmpeg コマンド・filter_complex を直接生成させない。AI の出力は EditPlan JSON のみ。
  filtergraph はコード（filtergraph.py）が決定的に生成する（本設計の不変則）。
- 字幕は drawtext を多数連結せず、ASS ファイル1本を生成し `subtitles` フィルタで焼く
  （強調のインライン色指定と可読性のため）。
- faster-whisper 既定モデルは `small`（DL サイズと精度の折衷）。`--model` で上書き可だが
  設定ファイルは作らない（CLI フラグのみ）。
- 音声認識に外部 API（Groq 等）は使わない（キーを1本に抑え、転写の限界費用をゼロにする）。
  ローカル whisper で足りなければ §12 で再検討。
- Anthropic モデル ID・料金・パラメータはメモリから書かず、実装時に claude-code-guide／
  claude-api で最新を確認する。
- companion スキルは作らない。CLI が3回以上手動利用され定型化したら薄い起動スキルを別途提案。
- public/private とリポジトリ命名の最終決定はユーザーに確認（§12）。勝手に public にしない。

## 12. 未解決事項（ユーザー確認待ち）

- リポジトリ `ryotaroh180105/openmontage` の命名可否と public/private（同梱フォント SIL OFL は
  再配布可、テスト素材は本人撮影 or CC0 を使う前提）。
- MVP を「縦動画テロップ付け＋無音カット」に確定してよいか（もう一案「長尺→ハイライト自動カット」は
  意味抽出の品質検証が困難なため本設計では除外。こちらを望むなら別設計書 14 を起こす）。
- Dockerfile 提供で導入を1コマンド化するか（time-to-value 対策の候補。実ユーザーが導入で
  詰まったら着手）。
- 30分超の長尺で whisper が遅い場合の分割処理（実運用で遅延が問題化してから）。

---

## ビジネス運用面シート（biz-ops-guard full 適用）

### Go/No-Go ラダー

1. **想定ユーザー3人**: 本人（SNS 運用で縦ショートを週数本量産）／ショート編集を外注している
   発信者A（セミナー録画を切り抜き）／副業クライアントの SNS 運用担当B。→ Yes
2. **乗り換え理由（1文）**: CapCut/Premiere で無音カット＋テロップ＋縦型変換を手作業する30〜60分/本を、
   文字起こしベースの自動生成＋EditPlan 微修正で数分に短縮できる（ChatGPT に聞くだけでは動画は出ない）。→ Yes
3. **導入5分3ステップ**: ①ffmpeg インストール ②`pip install openmontage` ③`ANTHROPIC_API_KEY` 設定。
   → 概ね Yes（初回 whisper モデル DL が律速。既定 small で緩和、Dockerfile は §12）
4. **保守予算**: 週30分（ffmpeg/whisper/Anthropic SDK の破壊的変更追随）。→ Yes
5. **最初の10ユーザー到達経路**: 本人の sns-ops-team パイプラインで自用 → note でツール紹介記事
   → GitHub 公開。→ Yes

### シート

```markdown
# openmontage ビジネス運用面シート
- 一文価値提案: SNS運用者が CapCut で手作業せずに、横長素材から縦型テロップ付きショートを数分で作れる
- 想定ユーザー（3人）: 本人 / 外注中の発信者A / 副業クライアントSNS担当B
- 代替手段と乗り換え理由（1点）: 手作業(CapCut/Premiere)/auto-editor(無音カットのみ)/Descript(有料SaaS英語中心) に対し、
  「AI判断=EditPlan中間表現」で再現・微修正・バッチ可能な点が唯一の差別化
- 導入: 手順数 3 / 所要 5〜8分（初回whisper DL次第） / 前提条件: ffmpeg, Python3.10+, ANTHROPIC_API_KEY
- 保守: 予算 週30分 / 壊れる要因: ffmpegフィルタ仕様変更・faster-whisper更新・Anthropic API変更 / 廃止基準: 2ヶ月ユーザー0 or 予算2回連続超過
- 運用: 定常作業: なし(オンデマンドCLI) / 失敗通知経路: 非0終了コード＋stderr / 1利用あたりコスト: compose のClaude API1回分（transcript入力トークン）＋ローカルCPU/GPU（whisper・ffmpeg、外部課金なし）
- 配布チャネルと最初の10ユーザー（到達期限: 公開後4週）: 本人利用→note記事→GitHub
- 収益/回収: 無料。回収は自分の動画量産時短＋副業ポートフォリオ＋就活エピソード(G3)
- 記録する指標: 新規clone数 / 再利用(自分のrender実行回数) / 紹介。ドッグフーディング: render後にEditPlanを手修正した割合
- 意図的に無視すること: GUI・BGM・多言語・SaaS化・ハイライト意味抽出（MVP品質検証不能）
- 悪魔の代弁者: 実装着手前に red-team / 別Agent で3件検査し本シートに追記（marketplace追記は無いがアプリ公開前に実施）
```

注: 公開前チェックリスト（前提表・クリーン環境5分導入・README冒頭10行・悪魔の代弁者3件）は
openmontage リポジトリ側の初回リリース PR で消化する。実名は書かない（本人以外はイニシャル・属性）。
