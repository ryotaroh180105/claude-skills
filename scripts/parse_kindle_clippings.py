#!/usr/bin/env python3
"""Parse a Kindle "My Clippings.txt" export into intel-hub Kindle-highlights
inbox files (kind: kindle-highlights).

Format reference: docs/designs/14-app-kindle-summarizer.md §5.1 (input) and
§5.2 (output). This script only converts My Clippings.txt into
intel/inbox/kindle-<book-slug>.md files; it does not talk to intel-hub,
hermes-relay, or write book-note records (that is intel-hub's job, per
14 §1.3 role boundary).

Usage:
    python3 scripts/parse_kindle_clippings.py <path/to/My Clippings.txt> [--out DIR]

Exit codes:
    0  success, prints "OK <B> books <C> clippings"
    1  no clippings parsed (empty file / separators only), or a decode error
"""
import argparse
import re
import sys
from pathlib import Path

SEPARATOR = "=========="

HIGHLIGHT_WORDS = ("Your Highlight", "ハイライト")
NOTE_WORDS = ("Your Note", "メモ")
BOOKMARK_WORDS = ("Your Bookmark", "ブックマーク")

# Line 2 structure per 14 §5.1: "- <type> on <location/page info> | Added on <date>"
META_RE = re.compile(r"^-\s*(?P<type>.+?)\s+on\s+(?P<loc>.+?)\s*\|\s*Added on\s*.+$")
LOCATION_RE = re.compile(r"(?:Location|位置No\.?)\s*(\d+(?:-\d+)?)")
PAGE_RE = re.compile(r"page\s*(\d+)", re.IGNORECASE)
TITLE_RE = re.compile(r"^(?P<title>.+?)\s*\((?P<author>[^()]*)\)\s*$")


def classify(type_str: str) -> str:
    if any(w in type_str for w in HIGHLIGHT_WORDS):
        return "highlight"
    if any(w in type_str for w in NOTE_WORDS):
        return "note"
    if any(w in type_str for w in BOOKMARK_WORDS):
        return "bookmark"
    # Unknown language/type: treat as highlight (14 §11 判断ルール).
    return "highlight"


def extract_location(loc_str: str) -> str:
    m = LOCATION_RE.search(loc_str)
    if m:
        return f"位置No.{m.group(1)}"
    m = PAGE_RE.search(loc_str)
    if m:
        return f"page {m.group(1)}"
    return "位置No.不明"


def slugify(title: str, used: dict):
    """Return (slug, is_fallback). Fallback slugs are plain numeric sequences
    (e.g. "001") used as kindle-001.md, per 14 §7 (ASCII化不能 -> kindle-<連番>)."""
    ascii_slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    ascii_slug = re.sub(r"-{2,}", "-", ascii_slug)
    base = ascii_slug[:40].strip("-")
    if not base or not re.search(r"[a-z0-9]", base):
        used["_fallback_seq"] = used.get("_fallback_seq", 0) + 1
        return f"{used['_fallback_seq']:03d}", True
    slug = base
    n = 2
    while slug in used:
        slug = f"{base}-{n}"
        n += 1
    used[slug] = True
    return slug, False


def parse_entries(text: str):
    """Split raw clippings text into (title, author, type, location, body) tuples."""
    raw_entries = [e.strip("\n") for e in text.split(SEPARATOR)]
    parsed = []
    for raw in raw_entries:
        lines = [ln for ln in raw.splitlines()]
        # Drop leading/trailing blank lines but keep internal structure.
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        if len(lines) < 2:
            continue
        title_line = lines[0].strip()
        meta_line = lines[1].strip()
        m_title = TITLE_RE.match(title_line)
        if m_title:
            title = m_title.group("title").strip()
            author = m_title.group("author").strip() or None
        else:
            title = title_line.strip()
            author = None
        m_meta = META_RE.match(meta_line)
        if not m_meta:
            continue
        entry_type = classify(m_meta.group("type"))
        location = extract_location(m_meta.group("loc"))
        body_lines = lines[2:]
        body = "\n".join(body_lines).strip()
        parsed.append({
            "title": title,
            "author": author,
            "type": entry_type,
            "location": location,
            "body": body,
        })
    return parsed


def build_output(book_title, book_author, clips, slug):
    lines = ["---"]
    lines.append("kind: kindle-highlights")
    lines.append(f'book_title: "{book_title}"')
    if book_author:
        lines.append(f'book_author: "{book_author}"')
    else:
        lines.append("book_author: null")
    lines.append("source: my-clippings")
    lines.append(f"clip_count: {len(clips)}")
    lines.append("---")
    for clip in clips:
        prefix = "> " if clip["type"] == "note" else ""
        location_tag = clip["location"]
        if location_tag == "位置No.不明":
            location_tag = "位置No.不明"
        lines.append(f"[{location_tag}] {prefix}{clip['body']}")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="Convert a Kindle My Clippings.txt export into intel-hub "
                     "kindle-highlights inbox files (docs/designs/14 §5.2)."
    )
    parser.add_argument("clippings_path", help="Path to My Clippings.txt")
    parser.add_argument(
        "--out", default="intel/inbox/",
        help="Output directory for kindle-<book-slug>.md files (default: intel/inbox/)",
    )
    args = parser.parse_args()

    path = Path(args.clippings_path)
    try:
        raw_bytes = path.read_bytes()
    except OSError as exc:
        print(f"error reading file: {exc}", file=sys.stderr)
        return 1

    try:
        text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        print(f"encoding error: {exc}", file=sys.stderr)
        return 1

    entries = parse_entries(text)
    # Bookmarks have no body and carry no summarization value (14 §7).
    clippings = [e for e in entries if e["type"] in ("highlight", "note") and e["body"]]

    if not clippings:
        print("no clippings parsed", file=sys.stderr)
        return 1

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    books = {}
    for clip in clippings:
        key = (clip["title"], clip["author"])
        books.setdefault(key, []).append(clip)

    used_slugs = {}
    fallback_map = []
    for (title, author), clips in books.items():
        slug, is_fallback = slugify(title, used_slugs)
        if is_fallback:
            fallback_map.append(f"kindle-{slug}.md -> {title}")
        out_path = out_dir / f"kindle-{slug}.md"
        out_path.write_text(build_output(title, author, clips, slug), encoding="utf-8")

    if fallback_map:
        print("slug fallback mapping:")
        for line in fallback_map:
            print(f"  {line}")

    print(f"OK {len(books)} books {len(clippings)} clippings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
