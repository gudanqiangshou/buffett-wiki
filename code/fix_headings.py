#!/usr/bin/env python3
"""
fix_headings.py
Fix missing ## marks on standalone short lines in wiki/ markdown files.

Detection criteria for a "heading candidate":
- Line length <= 25 characters
- Preceded by a blank line (or is the first non-blank line)
- Does NOT end with a period (。 or .)
- Does NOT start with - or * (not a list item)
- Does NOT start with # (not already a heading)
- Does NOT start with > (not a blockquote)
- Does NOT start with | (not a table row)
- Is NOT purely numeric or punctuation
- Is NOT empty
- Is NOT part of a YAML frontmatter block
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path("/Users/a1/巴菲特知识库")
WIKI_DIR = PROJECT_ROOT / "wiki"


def is_heading_candidate(line: str, prev_line: str) -> bool:
    stripped = line.rstrip()
    if not stripped:
        return False
    if len(stripped) > 25:
        return False
    # Already a heading
    if stripped.startswith("#"):
        return False
    # List item
    if stripped.startswith(("-", "*", "+")):
        return False
    # Blockquote
    if stripped.startswith(">"):
        return False
    # Table row
    if stripped.startswith("|"):
        return False
    # Ends with sentence-ending punctuation → likely normal text
    if stripped.endswith((".", "。", ",", "，", ":", "：", "!", "！", "?", "？")):
        return False
    # Starts with a digit followed by . → ordered list
    if len(stripped) > 1 and stripped[0].isdigit() and stripped[1] == ".":
        return False
    # Contains wikilink or markdown link → likely inline text
    if "[[" in stripped or "http" in stripped:
        return False
    # Must be preceded by a blank line (the previous line, after rstrip, is empty)
    if prev_line.strip() != "":
        return False
    return True


def fix_headings_in_text(text: str) -> tuple[str, int]:
    """Return (fixed_text, change_count)."""
    lines = text.splitlines()
    result = []
    changes = 0
    in_frontmatter = False
    frontmatter_done = False
    in_code_block = False

    for i, line in enumerate(lines):
        # Track YAML frontmatter (between first pair of ---)
        if i == 0 and line.strip() == "---":
            in_frontmatter = True
            result.append(line)
            continue
        if in_frontmatter and line.strip() == "---":
            in_frontmatter = False
            frontmatter_done = True
            result.append(line)
            continue
        if in_frontmatter:
            result.append(line)
            continue

        # Track fenced code blocks
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            result.append(line)
            continue
        if in_code_block:
            result.append(line)
            continue

        prev_line = lines[i - 1] if i > 0 else ""
        if is_heading_candidate(line, prev_line):
            result.append("## " + line)
            changes += 1
        else:
            result.append(line)

    return "\n".join(result), changes


def process_file(path: Path, dry_run: bool) -> int:
    text = path.read_text(encoding="utf-8")
    fixed, changes = fix_headings_in_text(text)
    if changes == 0:
        return 0
    if dry_run:
        print(f"[DRY-RUN] {path.relative_to(PROJECT_ROOT)}: {changes} heading(s) would be fixed")
    else:
        path.write_text(fixed, encoding="utf-8")
        print(f"Fixed {changes} heading(s) in: {path.relative_to(PROJECT_ROOT)}")
    return changes


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fix missing ## marks on standalone short lines in wiki/ files."
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
