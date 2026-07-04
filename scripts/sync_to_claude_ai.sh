#!/bin/bash
# Package every skill under skills/ into a .skill zip for upload to claude.ai
# (Settings > Capabilities > Skills). Claude Code itself does not need this step.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"
OUTPUT_DIR="$REPO_ROOT/dist"

mkdir -p "$OUTPUT_DIR"

for skill in "$SKILLS_DIR"/*/; do
    skill_name="$(basename "$skill")"
    echo "Packaging $skill_name..."
    python3 "$REPO_ROOT/scripts/package_skill.py" "$skill" -o "$OUTPUT_DIR"
done

echo "All skills packaged to $OUTPUT_DIR/"
echo "Upload these .skill files at claude.ai under Settings > Capabilities > Skills"
