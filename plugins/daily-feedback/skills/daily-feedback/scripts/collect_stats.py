#!/usr/bin/env python3
"""Claude Code の当日トランスクリプト（~/.claude/projects/**/*.jsonl）を集計し、
daily-feedback スキルが分析に使うコンパクトな JSON を stdout に出す。

Usage: python3 collect_stats.py [YYYY-MM-DD]   # 省略時はローカル日付の今日
生の JSONL をコンテキストに読み込まないための前処理。標準ライブラリのみ使用。
"""
import json
import sys
from datetime import datetime
from pathlib import Path

PROMPT_MAX_CHARS = 200
PROMPT_MAX_COUNT = 100

# $/1M tokens (input, output)。モデルIDの部分一致で判定（詳細は model-switcher スキル参照）
PRICES = [
    ("fable", (10.0, 50.0)),
    ("opus", (5.0, 25.0)),
    ("sonnet", (3.0, 15.0)),
    ("haiku", (1.0, 5.0)),
]


def price_for(model: str):
    for key, p in PRICES:
        if key in model:
            return p
    return (3.0, 15.0)  # 不明モデルは Sonnet 相当で概算


def text_of(content):
    """message.content から人間のテキストだけ取り出す（tool_result は除外）。"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [b.get("text", "") for b in content
                 if isinstance(b, dict) and b.get("type") == "text"]
        return "\n".join(p for p in parts if p)
    return ""


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d")
    root = Path.home() / ".claude" / "projects"
    if not root.is_dir():
        print(json.dumps({"error": f"{root} が存在しない。Claude Code を使う実機で実行すること。"},
                         ensure_ascii=False))
        return 1

    sessions = set()
    projects = {}          # project dir -> turn count
    models = {}            # model -> {turns, input, output, cache_read, cache_write}
    tools = {}             # tool name -> count
    prompts = []           # {time, project, text}
    compactions = 0
    interruptions = 0      # ユーザーによる中断（手戻りシグナル）

    for path in root.glob("*/*.jsonl"):
        # 当日更新のないファイルはパースせずスキップ
        if datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d") < target:
            continue
        project = path.parent.name
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(e, dict):
                    continue
                ts = e.get("timestamp", "")
                if not ts:
                    continue
                try:
                    local_day = datetime.fromisoformat(ts.replace("Z", "+00:00")) \
                        .astimezone().strftime("%Y-%m-%d")
                except ValueError:
                    continue
                if local_day != target:
                    continue

                etype = e.get("type")
                msg = e.get("message") or {}
                if etype == "summary" or e.get("isCompactSummary"):
                    compactions += 1
                    continue
                if etype not in ("user", "assistant"):
                    continue

                sessions.add(e.get("sessionId", path.stem))
                projects[project] = projects.get(project, 0) + 1

                if etype == "user" and not e.get("isMeta"):
                    text = text_of(msg.get("content")).strip()
                    if not text:
                        continue
                    if "[Request interrupted by user" in text:
                        interruptions += 1
                        continue
                    if text.startswith("<") or text.startswith("Caveat:"):
                        continue  # システム注入・ラッパーは除外
                    hhmm = ts[11:16]
                    prompts.append({"time": hhmm, "project": project,
                                    "text": text[:PROMPT_MAX_CHARS]})

                if etype == "assistant":
                    model = msg.get("model", "unknown")
                    u = msg.get("usage") or {}
                    m = models.setdefault(model, {"turns": 0, "input": 0, "output": 0,
                                                  "cache_read": 0, "cache_write": 0})
                    m["turns"] += 1
                    m["input"] += u.get("input_tokens", 0)
                    m["output"] += u.get("output_tokens", 0)
                    m["cache_read"] += u.get("cache_read_input_tokens", 0)
                    m["cache_write"] += u.get("cache_creation_input_tokens", 0)
                    for b in msg.get("content") or []:
                        if isinstance(b, dict) and b.get("type") == "tool_use":
                            name = b.get("name", "?")
                            tools[name] = tools.get(name, 0) + 1

    cost = 0.0
    for model, m in models.items():
        pin, pout = price_for(model)
        cost += (m["input"] * pin + m["cache_write"] * pin * 1.25
                 + m["cache_read"] * pin * 0.1 + m["output"] * pout) / 1e6
        total_in = m["input"] + m["cache_read"] + m["cache_write"]
        m["cache_hit_pct"] = round(100 * m["cache_read"] / total_in, 1) if total_in else 0.0

    dropped = max(0, len(prompts) - PROMPT_MAX_COUNT)
    out = {
        "date": target,
        "sessions": len(sessions),
        "projects": projects,
        "models": models,
        "estimated_cost_usd": round(cost, 2),
        "tools": dict(sorted(tools.items(), key=lambda x: -x[1])),
        "compactions": compactions,
        "user_interruptions": interruptions,
        "prompt_count": len(prompts),
        "prompts_dropped": dropped,
        "prompts": prompts[:PROMPT_MAX_COUNT],
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
