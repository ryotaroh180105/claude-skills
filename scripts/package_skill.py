#!/usr/bin/env python3
"""Package a skill directory into a .skill zip for manual upload to claude.ai (Settings > Capabilities > Skills)."""
import sys
import zipfile
from pathlib import Path


def package_skill(skill_dir: Path, output_dir: Path) -> Path:
    if not (skill_dir / "SKILL.md").exists():
        raise FileNotFoundError(f"{skill_dir} does not contain a SKILL.md")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{skill_dir.name}.skill"

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in skill_dir.rglob("*"):
            if not file_path.is_file():
                continue
            if "__pycache__" in file_path.parts or file_path.suffix == ".pyc":
                continue
            zf.write(file_path, file_path.relative_to(skill_dir))

    return output_path


def main():
    if len(sys.argv) < 2:
        print("Usage: package_skill.py <skill_dir> [-o output_dir]")
        return 1

    skill_dir = Path(sys.argv[1]).resolve()
    output_dir = Path("dist")
    if "-o" in sys.argv:
        output_dir = Path(sys.argv[sys.argv.index("-o") + 1])

    output_path = package_skill(skill_dir, output_dir)
    print(f"Packaged {skill_dir.name} -> {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
