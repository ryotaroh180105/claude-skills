#!/usr/bin/env python3
"""voicememo-pipeline: OpenAI Whisper API (whisper-1) で音声ファイルを文字起こしする。

標準ライブラリのみで動作する（multipart/form-data を urllib で自前構築）。

使い方:
    export OPENAI_API_KEY=sk-...
    python3 transcribe.py meeting.m4a --language ja --out transcript.txt

終了コード:
    0 = 成功 / 1 = 引数・ファイルエラー / 2 = OPENAI_API_KEY 未設定 / 3 = API エラー
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

API_URL = "https://api.openai.com/v1/audio/transcriptions"
MAX_BYTES = 25 * 1024 * 1024  # Whisper API の上限 25MB

SUPPORTED_EXTS = {
    ".flac": "audio/flac",
    ".m4a": "audio/mp4",
    ".mp3": "audio/mpeg",
    ".mp4": "audio/mp4",
    ".mpeg": "audio/mpeg",
    ".mpga": "audio/mpeg",
    ".oga": "audio/ogg",
    ".ogg": "audio/ogg",
    ".wav": "audio/wav",
    ".webm": "audio/webm",
}

FFMPEG_SPLIT_GUIDE = """\
対処方法: ffmpeg で 10 分ごとに分割してから、各ファイルを個別に文字起こししてください。

  # 10 分(600 秒)ごとに分割（再エンコードなし・高速）
  ffmpeg -i "{path}" -f segment -segment_time 600 -c copy "{stem}_part%03d{ext}"

  # それでも 1 ファイルが 25MB を超える場合は 64kbps mp3 に圧縮して分割
  ffmpeg -i "{path}" -f segment -segment_time 600 -ac 1 -b:a 64k "{stem}_part%03d.mp3"

分割後、各 part ファイルをこのスクリプトに順番に渡し、結果を連結してください。"""


def fail(message: str, code: int) -> None:
    print(f"エラー: {message}", file=sys.stderr)
    sys.exit(code)


def validate_audio(path: Path) -> str:
    """ファイルの存在・形式・サイズを検証し、MIME タイプを返す。"""
    if not path.exists():
        fail(
            f"音声ファイルが見つかりません: {path}\n"
            "対処方法: パスが正しいか確認してください。Google Drive 上のファイルの場合は"
            "先にローカルへダウンロードしてから渡してください。",
            1,
        )
    if not path.is_file():
        fail(f"ファイルではありません（ディレクトリ？）: {path}", 1)

    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTS:
        fail(
            f"対応していないフォーマットです: '{ext or '(拡張子なし)'}'\n"
            f"対応形式: {', '.join(sorted(SUPPORTED_EXTS))}\n"
            "対処方法: ffmpeg で変換してください。例:\n"
            f'  ffmpeg -i "{path}" "{path.with_suffix(".mp3")}"',
            1,
        )

    size = path.stat().st_size
    if size == 0:
        fail(f"ファイルが空です (0 バイト): {path}", 1)
    if size > MAX_BYTES:
        guide = FFMPEG_SPLIT_GUIDE.format(path=path, stem=path.with_suffix(""), ext=ext)
        fail(
            f"ファイルサイズが Whisper API の上限 25MB を超えています: "
            f"{size / (1024 * 1024):.1f}MB ({path})\n{guide}",
            1,
        )
    return SUPPORTED_EXTS[ext]


def build_multipart(fields: dict, file_field: str, path: Path, mime: str):
    """multipart/form-data のボディを標準ライブラリだけで構築する。"""
    boundary = f"----voicememo-{uuid.uuid4().hex}"
    parts = []
    for name, value in fields.items():
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n".encode("utf-8")
        )
    # ヘッダ内で引用符・改行は multipart を壊すため無害な文字に置換する
    safe_name = "".join("_" if c in '"\r\n\\' else c for c in path.name)
    parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{file_field}"; filename="{safe_name}"\r\n'
        f"Content-Type: {mime}\r\n\r\n".encode("utf-8")
    )
    parts.append(path.read_bytes())
    parts.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="OpenAI Whisper API (whisper-1) で音声ファイルを文字起こしする。",
        epilog="例: python3 transcribe.py meeting.m4a --language ja --out transcript.txt",
    )
    parser.add_argument("audio", help="音声ファイルのパス (mp3/m4a/wav/webm など)")
    parser.add_argument(
        "--out",
        help="文字起こし結果の出力先パス (省略時: <音声ファイル名>_transcript.txt)",
    )
    parser.add_argument("--language", default="ja", help="音声の言語コード (既定: ja)")
    parser.add_argument("--model", default="whisper-1", help="モデル名 (既定: whisper-1)")
    parser.add_argument(
        "--prompt",
        default="",
        help="固有名詞のヒント (例: 参加者名・会社名をカンマ区切りで渡すと精度が上がる)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="API を呼ばず、送信予定のリクエスト内容だけ表示して終了する",
    )
    args = parser.parse_args()

    path = Path(args.audio).expanduser()
    mime = validate_audio(path)
    size_mb = path.stat().st_size / (1024 * 1024)
    out_path = Path(args.out).expanduser() if args.out else path.with_name(path.stem + "_transcript.txt")
    if out_path.is_dir():
        out_path = out_path / (path.stem + "_transcript.txt")

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()

    if args.dry_run:
        print("[dry-run] API は呼び出しません。送信予定の内容:")
        print(f"  エンドポイント : POST {API_URL}")
        print(f"  model          : {args.model}")
        print(f"  language       : {args.language}")
        print(f"  prompt         : {args.prompt or '(なし)'}")
        print(f"  file           : {path} ({size_mb:.2f}MB, {mime})")
        print(f"  出力先         : {out_path}")
        print(f"  OPENAI_API_KEY : {'設定済み' if api_key else '未設定 (本実行前に設定が必要)'}")
        print("[dry-run] 検証 OK。本実行するには --dry-run を外してください。")
        return

    if not api_key:
        fail(
            "環境変数 OPENAI_API_KEY が設定されていません。文字起こしには OpenAI の API キーが必要です。\n"
            "対処方法:\n"
            "  1. https://platform.openai.com/api-keys でキーを発行 (sk- で始まる文字列)\n"
            "  2. 実行前に設定: export OPENAI_API_KEY=sk-...\n"
            "  3. このスクリプトを再実行\n"
            "先にリクエスト内容だけ確認したい場合は --dry-run を付けてください (キー不要)。",
            2,
        )

    # 課金される API 呼び出しの前に出力先へ書き込めることを確認しておく
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        fail(f"出力先ディレクトリを作成できません: {out_path.parent} ({e})\n対処方法: --out で書き込み可能なパスを指定してください。", 1)
    if not os.access(out_path.parent, os.W_OK):
        fail(f"出力先に書き込み権限がありません: {out_path.parent}\n対処方法: --out で書き込み可能なパスを指定してください。", 1)

    fields = {"model": args.model, "response_format": "text"}
    if args.language:
        fields["language"] = args.language
    if args.prompt:
        fields["prompt"] = args.prompt

    body, content_type = build_multipart(fields, "file", path, mime)
    request = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": content_type,
        },
    )

    print(f"文字起こし中... ({path.name}, {size_mb:.2f}MB, model={args.model})", file=sys.stderr)
    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            transcript = response.read().decode("utf-8").strip()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(detail)["error"]["message"]
        except (ValueError, KeyError, TypeError):
            pass
        hint = ""
        if e.code == 401:
            hint = "\n対処方法: OPENAI_API_KEY の値が正しいか確認してください (期限切れ・タイポの可能性)。"
        elif e.code == 429:
            hint = "\n対処方法: レート制限または残高不足です。OpenAI の Usage/Billing を確認してください。"
        fail(f"OpenAI API エラー (HTTP {e.code}): {detail}{hint}", 3)
    except urllib.error.URLError as e:
        fail(f"ネットワークエラー: {e.reason}\n対処方法: インターネット接続とプロキシ設定を確認してください。", 3)
    except OSError as e:
        # 応答の受信途中のタイムアウト・切断（TimeoutError 含む）
        fail(f"ネットワークエラー（応答の受信中に失敗）: {e}\n対処方法: 回線が不安定な可能性があります。再実行してください。", 3)

    try:
        out_path.write_text(transcript + "\n", encoding="utf-8")
    except OSError as e:
        # 課金済みの結果を失わないよう、保存に失敗したら標準出力に全文を出す
        print(transcript)
        fail(f"出力先への書き込みに失敗しました: {out_path} ({e})\n文字起こし結果は上に全文出力済みです（API の再実行は不要）。", 1)
    print(f"完了: 文字起こし結果を保存しました -> {out_path}")
    print(f"文字数: {len(transcript)}")


if __name__ == "__main__":
    main()
