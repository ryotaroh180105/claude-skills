#!/usr/bin/env python3
"""Validate that every skill referenced by the marketplace has a well-formed SKILL.md."""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_plugin_entries():
    marketplace_path = REPO_ROOT / ".claude-plugin" / "marketplace.json"
    marketplace = json.loads(marketplace_path.read_text())
    return marketplace.get("plugins", [])


def validate_skill_md(skill_dir: Path, label: str, errors: list):
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        errors.append(f"{label}: SKILL.md not found at {skill_md}")
        return

    text = skill_md.read_text()
    if not text.startswith("---"):
        errors.append(f"{label}: SKILL.md must start with a '---' frontmatter block")
        return

    end = text.find("---", 3)
    if end == -1:
        errors.append(f"{label}: SKILL.md frontmatter is not closed with '---'")
        return

    frontmatter = text[3:end]
    if "name:" not in frontmatter:
        errors.append(f"{label}: frontmatter missing 'name'")
    if "description:" not in frontmatter:
        errors.append(f"{label}: frontmatter missing 'description'")


def main():
    errors = []
    plugins = load_plugin_entries()

    if not plugins:
        print("No plugins declared in marketplace.json")
        return 0

    for plugin in plugins:
        plugin_id = plugin.get("name", "<unnamed>")
        source = plugin.get("source", "")
        plugin_dir = REPO_ROOT / source.lstrip("./")

        if not plugin_dir.exists():
            errors.append(f"{plugin_id}: plugin source directory not found: {plugin_dir}")
            continue

        skills_dir = plugin_dir / "skills"
        if skills_dir.exists():
            for skill_dir in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
                validate_skill_md(skill_dir, f"{plugin_id}/{skill_dir.name}", errors)
        else:
            validate_skill_md(plugin_dir, plugin_id, errors)

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        print(f"\n{len(errors)} error(s) found")
        return 1

    print("All skills valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
