#!/usr/bin/env python3
"""
fix_headings2.py
Known-headings exact-match fixer for wiki/ markdown files.

For each known heading found as a bare standalone line (without ## prefix),
add ## prefix and ensure there is a blank line before and after it.
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path("/Users/a1/巴菲特知识库")
WIKI_DIR = PROJECT_ROOT / "wiki"

KNOWN_HEADINGS = {
    "概念解析",
    "定义与起源",
    "核心要义",
    "实践应用",
    "公司简介",
    "投资故事",
    "巴菲特评价精选",
    "人物简介",
    "核心要点",
    "详细摘要",
    "提到的概念",
    "提到的公司",
    "提到的人物",
    "原文金句",
    "核心投资理念",
    "重要投资决策",
    "核心思想",
    "生平与成就",
}


def fix_known_headings(text: str) -> tuple[str, int]:
    """Return (fixed_text, change_count)."""
    lines = text.splitlines()
    changes = 0
    in_frontmatter = False
    in_code_block = False

    # Pass 1: upgrade bare known-heading lines to ## headings
    upgraded: list[str] = []
    for i, line in enumerate(lines):
        stripped = line.strip()

        # Frontmatter detection
        if i == 0 and stripped == "---":
            in_frontmatter = True
            upgraded.append(line)
            continue
        if in_frontmatter:
            if stripped == "---":
                in_frontmatter = False
            upgraded.append(line)
            continue

        # Code block detection
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            upgraded.append(line)
            continue
        if in_code_block:
            upgraded.append(line)
            continue

        # Already a heading — leave alone even if it matches
        if stripped.startswith("#"):
            upgraded.append(line)
            continue

        # Exact match against known headings
        if stripped in KNOWN_HEADINGS:
            upgraded.append("## " + stripped)
            changes += 1
        else:
            upgraded.append(line)

    # Pass 2: ensure blank line before and after ## heading lines
    result: list[str] = []
    for i, line in enumerate(upgraded):
        stripped = line.strip()
        is_heading = stripped.startswith("## ")

        if is_heading:
            # Ensure blank line before (not at start of file / not already blank)
            if result and result[-1].strip() != "":
                result.append("")
            result.append(line)
            # Ensure blank line after (peek ahead)
            if i + 1 < len(upgraded) and upgraded[i + 1].strip() != "":
                result.append("")
        else:
            result.append(line)

    # Trim trailing extra blank lines introduced
    while result and result[-1].strip() == "" and len(result) > 1 and result[-2].strip() == "":
        result.pop()

    return "\n".join(result), changes


def process_file(path: Path, dry_run: bool) -> int:
    text = path.read_text(encoding="utf-8")
    fixed, changes = fix_known_headings(text)
    if changes == 0:
        return 0
    if dry_run:
        print(
            f"[DRY-RUN] {path.relative_to(PROJECT_ROOT)}: "
            f"{changes} known heading(s) would be fixed"
        )
    else:
        path.write_text(fixed, encoding="utf-8")
        print(f"Fixed {changes} known heading(s) in: {path.relative_to(PROJECT_ROOT)}")
    return changes


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fix known headings missing ## prefix in wiki/ files."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing files.",
    )
    args = parser.parse_args()

    if not WIKI_DIR.exists():
        print(f"Wiki directory not found: {WIKI_DIR}", file=sys.stderr)
        sys.exit(1)

    total_files = 0
    total_changes = 0

    for md_file in sorted(WIKI_DIR.rglob("*.md")):
        n = process_file(md_file, args.dry_run)
        if n > 0:
            total_files += 1
            total_changes += n

    print(f"\nDone. {total_changes} heading(s) fixed across {total_files} file(s).")


if __name__ == "__main__":
    main()
