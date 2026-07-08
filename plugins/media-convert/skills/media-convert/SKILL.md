---
name: media-convert
description: 動画ファイル・動画URLを mp3/wav/m4a 等の音声ファイルに変換する小型ユーティリティ。「これをmp3にして」「動画から音声を抜いて」「voicememo用に変換して」「音声だけ抽出したい」といった依頼で使う。voicememo-pipeline の前処理（会議録画などmp4で届いた素材を音声化してから文字起こしに渡す）としても呼ばれる。英語キーワード: convert video to audio, extract audio, ffmpeg, mp3 extraction.
---

# media-convert

ffmpeg 1本で動画→音声変換だけを行う小型スキル。バッチ変換・動画編集・字幕処理などは
スコープ外（yagni-guard 準拠。必要になったら別スキルとして検討する）。

## 前提セットアップ

| 種別 | 名前 | 用途 | 未設定時の挙動 |
|---|---|---|---|
| CLI | ffmpeg | 変換処理本体 | **必須**。`ffmpeg -version` で確認し、無ければ以下を提示してユーザーに導入を依頼し、導入完了までは変換を実行しない |
| CLI | yt-dlp | URL入力からの動画取得 | 入力がURLのときのみ必須。無ければ以下を提示して導入を依頼し、それまで停止 |

未導入時の案内（OS別）:

```bash
# macOS (Homebrew)
brew install ffmpeg
brew install yt-dlp

# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y ffmpeg
sudo apt-get install -y yt-dlp   # 無ければ: pip install yt-dlp

# Windows (winget)
winget install ffmpeg
winget install yt-dlp
```

## 事前確認: DRM・権利

依頼された動画/URLが以下に該当する場合は変換を断り、理由を伝える:

- DRM保護がかかっている配信（サブスク動画サービス等）
- 著作権侵害が明らかな違法アップロード・海賊版

社内MTG録画・自分で権利を持つ素材・YouTube上の自分のチャンネル動画などは対象外（変換してよい）。判断に迷う場合はユーザーに確認する。

## ワークフロー

### ① 入力の確認

- **ローカルファイル**: パスの存在を確認し、そのまま②へ。
- **URL**: 上記「事前確認」を通ったら yt-dlp でダウンロードする。

```bash
yt-dlp -f "bestaudio/best" -o "./%(title)s.%(ext)s" "<URL>"
```

  ダウンロードした動画ファイルを②の入力にする。

ユーザーに出力形式（mp3/wav/m4a、未指定ならmp3）とビットレート（未指定なら標準品質）を軽く確認する。

### ② 変換（基本形）

```bash
ffmpeg -i in.mp4 -vn -acodec libmp3lame -q:a 2 out.mp3
```

- `-vn`: 映像を破棄し音声のみ抽出。
- `-q:a 2`: mp3のVBR品質（0=最高〜9=最低、2は高音質の標準値）。

形式別の対応:

| 出力形式 | コマンド例 |
|---|---|
| mp3（標準） | `ffmpeg -i in.mp4 -vn -acodec libmp3lame -q:a 2 out.mp3` |
| mp3（ビットレート指定） | `ffmpeg -i in.mp4 -vn -acodec libmp3lame -b:a 128k out.mp3` |
| wav | `ffmpeg -i in.mp4 -vn -acodec pcm_s16le out.wav` |
| m4a | `ffmpeg -i in.mp4 -vn -acodec aac -b:a 128k out.m4a` |

ビットレートを指定された場合は `-q:a` ではなく `-b:a <値>`（例: `192k`）を使う。

### ③ 出力の報告

- 出力ファイルの絶対パス、形式、サイズ（`ls -lh`）を報告する。
- voicememo-pipeline に渡す用途なら、そのまま `scripts/transcribe.py` の入力パスとして使える旨を添える。

## エッジケース

| 状況 | 挙動 |
|---|---|
| ffmpeg / yt-dlp 未導入 | 上記インストールコマンドを提示し、導入確認が取れるまで変換を実行しない |
| DRM保護・違法アップロードの疑い | 変換を断り、理由を伝える |
| 入力ファイルが存在しない・破損 | ffmpeg のエラー出力をそのまま見せ、パスの再確認を依頼する |
| 音声トラックが無い動画 | ffmpeg が失敗するのでその旨を伝え、映像のみの素材である可能性を案内する |
| 出力形式が mp3/wav/m4a 以外を要求された | ffmpeg 自体は他形式にも対応できるが、本スキルはこの3形式に限定する。他形式が必要な場合はコーデック名を確認してから個別対応する |
