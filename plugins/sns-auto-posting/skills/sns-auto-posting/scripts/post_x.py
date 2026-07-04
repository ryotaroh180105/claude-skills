#!/usr/bin/env python3
"""X (Twitter) API v2 への投稿スクリプト（標準ライブラリのみ）。

POST /2/tweets を OAuth 1.0a User Context（HMAC-SHA1 署名を自前実装）で呼ぶ。

必要な環境変数:
    X_API_KEY             (Consumer Key)
    X_API_SECRET          (Consumer Secret)
    X_ACCESS_TOKEN        (Access Token)
    X_ACCESS_TOKEN_SECRET (Access Token Secret)

使い方:
    python3 post_x.py --text "本文"                # 投稿
    python3 post_x.py --file body.txt              # ファイルから本文を読む
    python3 post_x.py --text "本文" --dry-run       # API を呼ばずリクエスト内容を表示
    python3 post_x.py --text "返信" --reply-to <tweet_id>

終了コード:
    0 = 成功（dry-run 含む）
    2 = 入力エラー（本文なし / 文字数超過など）
    3 = 環境変数（API キー）未設定
    4 = 認証エラー (401/403)
    5 = レート制限 (429)
    1 = その他のエラー
"""

import argparse
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API_URL = "https://api.x.com/2/tweets"

ENV_KEYS = ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET"]

MAX_WEIGHTED_LENGTH = 280  # 半角280 / 全角(日本語)140 相当
URL_WEIGHT = 23            # URL は長さに関わらず t.co 短縮で23字換算
URL_RE = re.compile(r"https?://[^\s]+")

# X の weightedLength 仕様: 以下のコードポイント範囲は重み1、それ以外(日本語・絵文字等)は重み2
WEIGHT1_RANGES = (
    (0x0000, 0x10FF),   # Latin, かな漢字以外の基本文字域
    (0x2000, 0x200D),   # 一般句読点の一部
    (0x2010, 0x201F),   # ハイフン・引用符
    (0x2032, 0x2037),   # プライム記号
)


def weighted_length(text: str) -> int:
    """X の文字数カウント。ASCII等=1、日本語・絵文字=2、URL=23字換算。"""
    total = 0
    pos = 0
    for m in URL_RE.finditer(text):
        total += _segment_weight(text[pos:m.start()])
        total += URL_WEIGHT
        pos = m.end()
    total += _segment_weight(text[pos:])
    return total


def _segment_weight(segment: str) -> int:
    weight = 0
    for ch in segment:
        cp = ord(ch)
        if any(lo <= cp <= hi for lo, hi in WEIGHT1_RANGES):
            weight += 1
        else:
            weight += 2
    return weight


def _pct(value: str) -> str:
    """RFC 3986 percent-encode（OAuth 1.0a 用）。"""
    return urllib.parse.quote(value, safe="")


def build_oauth_header(method: str, url: str, creds: dict) -> str:
    """OAuth 1.0a Authorization ヘッダを生成（HMAC-SHA1 署名）。

    JSON ボディの POST では、署名対象は oauth パラメータのみ（ボディは含めない）。
    """
    oauth_params = {
        "oauth_consumer_key": creds["X_API_KEY"],
        "oauth_nonce": secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": creds["X_ACCESS_TOKEN"],
        "oauth_version": "1.0",
    }
    param_string = "&".join(
        f"{_pct(k)}={_pct(v)}" for k, v in sorted(oauth_params.items())
    )
    base_string = "&".join([method.upper(), _pct(url), _pct(param_string)])
    signing_key = f"{_pct(creds['X_API_SECRET'])}&{_pct(creds['X_ACCESS_TOKEN_SECRET'])}"
    digest = hmac.new(
        signing_key.encode("utf-8"), base_string.encode("utf-8"), hashlib.sha1
    ).digest()
    oauth_params["oauth_signature"] = base64.b64encode(digest).decode("ascii")
    header = "OAuth " + ", ".join(
        f'{_pct(k)}="{_pct(v)}"' for k, v in sorted(oauth_params.items())
    )
    return header


def load_text(args) -> str:
    if args.text is not None:
        return args.text
    try:
        with open(args.file, encoding="utf-8") as f:
            return f.read().rstrip("\n")
    except OSError as e:
        print(f"エラー: ファイルを読めません: {e}", file=sys.stderr)
        sys.exit(2)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="X (Twitter) API v2 に投稿する。--text か --file のどちらかで本文を渡す。",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", help="投稿本文")
    group.add_argument("--file", help="投稿本文を書いた UTF-8 テキストファイル")
    parser.add_argument("--reply-to", metavar="TWEET_ID",
                        help="このツイートIDへの返信として投稿する")
    parser.add_argument("--dry-run", action="store_true",
                        help="API を呼ばず、送信予定のリクエスト内容を表示して終了")
    args = parser.parse_args()

    text = load_text(args)
    if not text.strip():
        print("エラー: 本文が空です。", file=sys.stderr)
        return 2

    length = weighted_length(text)
    if length > MAX_WEIGHTED_LENGTH:
        print(
            f"エラー: 文字数超過です（加重カウント {length}/{MAX_WEIGHTED_LENGTH}）。\n"
            "  日本語・絵文字は2字、半角英数は1字、URLは23字として数えます。\n"
            "  本文を短くしてから再実行してください。",
            file=sys.stderr,
        )
        return 2

    payload = {"text": text}
    if args.reply_to:
        payload["reply"] = {"in_reply_to_tweet_id": args.reply_to}

    creds = {k: os.environ.get(k, "") for k in ENV_KEYS}
    missing = [k for k in ENV_KEYS if not creds[k]]

    if args.dry_run:
        print("=== DRY RUN（APIは呼びません） ===")
        print(f"POST {API_URL}")
        print(f"文字数（加重カウント）: {length}/{MAX_WEIGHTED_LENGTH}")
        print("ペイロード:")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        if missing:
            print(f"注意: 未設定の環境変数: {', '.join(missing)}"
                  "（本投稿にはすべて必要です）")
        else:
            print("環境変数: 4キーすべて設定済み")
        return 0

    if missing:
        print(
            "エラー: X API のキーが未設定です。以下の環境変数を設定してください:\n"
            + "".join(f"  - {k}\n" for k in missing)
            + "取得手順: developer.x.com でアプリ作成 → App permissions を "
            "Read and Write に変更 → Keys and tokens でキーを(再)発行。\n"
            "キーなしで内容確認だけしたい場合は --dry-run を使ってください。",
            file=sys.stderr,
        )
        return 3

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(API_URL, data=body, method="POST")
    req.add_header("Authorization", build_oauth_header("POST", API_URL, creds))
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        if e.code == 401:
            print(
                "エラー(401): 認証に失敗しました。\n"
                "  - 4つのキーの値が正しいか（コピペミス・前後の空白）\n"
                "  - アプリの権限が Read and Write か（Read のみだと投稿不可。\n"
                "    権限変更後は Access Token の再発行が必要）\n"
                f"  レスポンス: {detail}",
                file=sys.stderr,
            )
            return 4
        if e.code == 403:
            print(
                "エラー(403): 投稿が拒否されました。よくある原因:\n"
                "  - 直近の投稿と本文が完全に同一（重複投稿）\n"
                "  - アプリの権限不足、またはアカウントの制限\n"
                f"  レスポンス: {detail}",
                file=sys.stderr,
            )
            return 4
        if e.code == 429:
            reset = e.headers.get("x-rate-limit-reset", "")
            when = ""
            if reset.isdigit():
                when = time.strftime(
                    " %H:%M:%S 頃に解除見込み", time.localtime(int(reset))
                )
            print(
                f"エラー(429): レート制限に達しました。{when}\n"
                "  しばらく待ってから再実行してください。残りの投稿は中断を推奨します。\n"
                f"  レスポンス: {detail}",
                file=sys.stderr,
            )
            return 5
        print(f"エラー({e.code}): {detail}", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"エラー: 接続に失敗しました: {e.reason}", file=sys.stderr)
        return 1

    tweet_id = data.get("data", {}).get("id", "")
    print("投稿に成功しました。")
    print(f"tweet_id: {tweet_id}")
    print(f"URL: https://x.com/i/web/status/{tweet_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
