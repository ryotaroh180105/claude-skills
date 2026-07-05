#!/usr/bin/env bash
# hermes-agent-setup スモークテスト
# 使い方: bash scripts/smoke_test.sh
# 事前に: source ~/.hermes-intel.env（XAI_API_KEY を設定しておく）
set -u

pass=0
fail=0

step() { printf '\n== %s ==\n' "$1"; }
ok()   { echo "OK: $1"; pass=$((pass+1)); }
ng()   { echo "NG: $1"; fail=$((fail+1)); }

step "1/3 環境変数チェック"
if [ -n "${XAI_API_KEY:-}" ]; then
  ok "XAI_API_KEY is set"
else
  ng "XAI_API_KEY が未設定。templates/env.example を差し替えて source してください"
  echo "以降のテストをスキップします"
  exit 1
fi

step "2/3 認証チェック (GET /v1/models)"
code=$(curl -sS -o /tmp/xai_models.json -w '%{http_code}' \
  https://api.x.ai/v1/models \
  -H "Authorization: Bearer $XAI_API_KEY")
if [ "$code" = "200" ]; then
  ok "認証成功 (HTTP 200)。利用可能モデル:"
  if command -v python3 >/dev/null 2>&1; then
    python3 -c 'import json; d = json.load(open("/tmp/xai_models.json")); print("\n".join(m.get("id", "?") for m in d.get("data", [])[:10]))'
  else
    # python3 が無い環境向けフォールバック（コロン後の空白の有無どちらにも対応）
    grep -oE '"id"[[:space:]]*:[[:space:]]*"[^"]*"' /tmp/xai_models.json | head -10
  fi
else
  ng "HTTP $code — 401/403 ならキーが無効。console.x.ai で再発行してください"
  exit 1
fi

step "3/3 X 検索の最小実行 (POST /v1/responses)"
# リクエスト body はテンプレートを唯一の正とし、クエリだけ差し替える（モデル名の二重管理を避ける）
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
TEMPLATE="$SCRIPT_DIR/../templates/x_search_request.json"
if [ ! -f "$TEMPLATE" ]; then
  ng "テンプレートが見つかりません: $TEMPLATE"
  printf '\n結果: pass=%d fail=%d\n' "$pass" "$fail"
  exit 1
fi
sed 's/REPLACE_ME_QUERY/直近24時間で Claude Code について最も反響のあった X 投稿を1件、URL付きで教えて/' \
  "$TEMPLATE" > /tmp/xai_smoke_request.json
code=$(curl -sS -o /tmp/xai_smoke.json -w '%{http_code}' \
  https://api.x.ai/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d @/tmp/xai_smoke_request.json)
if [ "$code" = "200" ]; then
  ok "x_search 実行成功。レスポンス冒頭:"
  head -c 500 /tmp/xai_smoke.json; echo
elif [ "$code" = "404" ]; then
  ng "HTTP 404 — モデル名が古い可能性。上記モデル一覧の id に差し替えて再実行してください"
elif [ "$code" = "429" ] || [ "$code" = "402" ]; then
  ng "HTTP $code — レート制限または残高不足。60秒待って再試行してください"
else
  ng "HTTP $code — レスポンス: $(head -c 300 /tmp/xai_smoke.json)"
fi

printf '\n結果: pass=%d fail=%d\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
