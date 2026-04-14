#!/usr/bin/env python3
"""
fix_paragraphs.py
Fix long paragraphs missing line breaks in wiki/ markdown files.

For lines > 150 characters, split at Chinese period (。) followed by more text,
and insert a blank line between each resulting segment.
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path("/Users/a1/巴菲特知识库")
WIKI_DIR = PROJECT_ROOT / "wiki"

MAX_LINE_LEN = 150


def split_long_line(line: str) -> list[str]:
    """Split a long line at 。boundaries. Returns list of segments."""
    segments = []
    remaining = line
    while len(remaining) > MAX_LINE_LEN:
        # Find the last 。 before position MAX_LINE_LEN
        # so that the first segment is not longer than MAX_LINE_LEN
        cut = -1
        # Search for 。 within the string up to a reasonable point
        idx = 0
        while idx < len(remaining):
            pos = remaining.find("。", idx)
            if pos == -1:
                break
            # The split point is right after 。 (include the period in the segment)
            split_after = pos + 1
            if split_after < len(remaining):
                # There is more text after the period — good split candidate
                cut = split_after
                if split_after > MAX_LINE_LEN:
                    # We've gone past the limit; use the last found cut
                    break
            idx = pos + 1

        if cut == -1 or cut == 0:
            # No useful split point found — keep as-is
            break

        segment = remaining[:cut].rstrip()
        segments.append(segment)
        remaining = remaining[cut:].lstrip()

    if remaining:
        segments.append(remaining)

    return segments if len(segments) > 1 else [line]


def fix_paragraphs_in_text(text: str) -> tuple[str, int]:
    """Return (fixed_text, change_count)."""
    lines = text.splitlines()
    result: list[str] = []
    changes = 0
    in_frontmatter = False
    in_code_block = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Frontmatter
        if i == 0 and stripped == "---":
            in_frontmatter = True
            result.append(line)
            continue
        if in_frontmatter:
            if stripped == "---":
                in_frontmatter = False
            result.append(line)
            continue

        # Code block
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            result.append(line)
            continue
        if in_code_block:
            result.append(line)
            continue

        # Skip headings, blockquotes, list items, table rows
        if (
            stripped.startswith("#")
            or stripped.startswith(">")
            or stripped.startswith("-")
            or stripped.startswith("*")
            or stripped.startswith("|")
        ):
            result.append(line)
            continue

        # Only process lines longer than the threshold
        if len(line) <= MAX_LINE_LEN:
            result.append(line)
            continue

        # Check if the line contains 。 followed by more content
        if "。" not in line:
            result.append(line)
            continue

        segments = split_long_line(line)
        if len(segments) == 1:
            result.append(line)
            continue

        # Insert blank line between segments
        for j, seg in enumerate(segments):
            result.append(seg)
            if j < len(segments) - 1:
                result.append("")
        changes += 1

    return "\n".join(result), changes


def process_file(path: Path, dry_run: bool) -> int:
    text = path.read_text(encoding="utf-8")
    fixed, changes = fix_paragraphs_in_text(text)
    if changes == 0:
        return 0
    if dry_run:
        print(
            f"[DRY-RUN] {path.relative_to(PROJECT_ROOT)}: "
            f"{changes} paragraph(s) would be split"
        )
    else:
        path.write_text(fixed, encoding="utf-8")
        print(f"Split {changes} paragraph(s) in: {path.relative_to(PROJECT_ROOT)}")
    return changes


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fix long paragraphs missing line breaks in wiki/ files."
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

    print(f"\nDone. {total_changes} paragraph(s) split across {total_files} file(s).")


if __name__ == "__main__":
    main()
