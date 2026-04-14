#!/usr/bin/env python3
"""
convert_existing.py
Batch convert raw/{concepts,companies,people}/ pages to wiki/ format.
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path("/Users/a1/巴菲特知识库")
RAW_DIR = PROJECT_ROOT / "raw"
WIKI_DIR = PROJECT_ROOT / "wiki"

CATEGORY_TYPE_MAP = {
    "concepts": "concept",
    "companies": "company",
    "people": "person",
}

CATEGORY_TAGS_MAP = {
    "concepts": ["价值投资", "核心概念"],
    "companies": ["公司", "投资标的"],
    "people": ["核心人物", "投资家"],
}


def strip_existing_header(text: str) -> str:
    """Remove all > **Source** / > **Type** lines and bare --- separator lines."""
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # Remove blockquote lines that are Source or Type metadata
        if re.match(r"^>\s*\*\*(?:Source|Type)\*\*", stripped):
            continue
        # Remove bare horizontal rule lines (--- used as separators)
        if stripped == "---":
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def insert_wikilinks(text: str, all_entities: list[str], self_name: str) -> str:
    """Replace entity names with [[entity_name]] wikilinks.

    - Entities sorted by name length descending (longest first to avoid partial matches)
    - Skips self_name
    - Skips heading lines (starting with #)
    - Skips code blocks
    - Does not track frontmatter state (input has no frontmatter)
    """
    # Build sorted entity list: longest first, exclude self
    entities = sorted(
        [e for e in all_entities if e != self_name],
        key=len,
        reverse=True,
    )

    lines = text.splitlines()
    in_code_block = False
    result = []

    for line in lines:
        # Track fenced code blocks
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            result.append(line)
            continue

        # Skip headings and code block content
        if in_code_block or line.lstrip().startswith("#"):
            result.append(line)
            continue

        # Apply wikilink replacements for this line
        for entity in entities:
            # Match entity name only when not already inside [[ ]]
            # Pattern: entity name not preceded by [[ and not followed by ]]
            pattern = r"(?<!\[\[)" + re.escape(entity) + r"(?!\]\])"
            replacement = f"[[{entity}]]"
            line = re.sub(pattern, replacement, line)

        result.append(line)

    return "\n".join(result)


def add_frontmatter(
    text: str,
    title: str,
    type_: str,
    source_path: str,
    category: str,
) -> str:
    """Prepend YAML frontmatter to text."""
    today = date.today().isoformat()
    tags = CATEGORY_TAGS_MAP.get(category, [])
    tags_yaml = "[" + ", ".join(tags) + "]"

    frontmatter = f"""---
title: "{title}"
type: {type_}
date: {today}
source: "{source_path}"
tags: {tags_yaml}
related: []
created: {today}
updated: {today}
---

"""
    return frontmatter + text


def collect_all_entities() -> list[str]:
    """Collect entity names from all raw concept/company/people files."""
    entities = []
    for category in ("concepts", "companies", "people"):
        category_dir = RAW_DIR / category
        if not category_dir.exists():
            continue
        for md_file in category_dir.glob("*.md"):
            entities.append(md_file.stem)
    # Also add from wiki dir
    for category in ("concepts", "companies", "people"):
        category_dir = WIKI_DIR / category
        if not category_dir.exists():
            continue
        for md_file in category_dir.glob("*.md"):
            name = md_file.stem
            if name not in entities:
                entities.append(name)
    return entities


def convert_file(
    src: Path,
    dest: Path,
    category: str,
    all_entities: list[str],
    dry_run: bool,
) -> None:
    raw_text = src.read_text(encoding="utf-8")
    title = src.stem
    type_ = CATEGORY_TYPE_MAP.get(category, category)
    relative_source = str(src.relative_to(PROJECT_ROOT))

    text = strip_existing_header(raw_text)

    # Remove leading/trailing blank lines
    text = text.strip()

    # Remove existing H1 title if it matches the filename stem (will be re-added via frontmatter context)
    # We keep the H1 intact for wiki format
    text = insert_wikilinks(text, all_entities, self_name=title)
    text = add_frontmatter(text, title, type_, relative_source, category)

    if dry_run:
        print(f"[DRY-RUN] Would write: {dest}")
        print(f"  Source: {src}")
        print(f"  Title:  {title}  Type: {type_}")
        return

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    print(f"Converted: {src.relative_to(PROJECT_ROOT)} -> {dest.relative_to(PROJECT_ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch convert raw/ pages to wiki/ format."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing files.",
    )
    parser.add_argument(
        "--category",
        choices=["concepts", "companies", "people"],
        help="Only process a specific category (default: all).",
    )
    args = parser.parse_args()

    categories = (
        [args.category] if args.category else ["concepts", "companies", "people"]
    )

    all_entities = collect_all_entities()

    converted = 0
    skipped = 0

    for category in categories:
        src_dir = RAW_DIR / category
        dest_dir = WIKI_DIR / category

        if not src_dir.exists():
            print(f"Source directory not found, skipping: {src_dir}", file=sys.stderr)
            continue

        for src_file in sorted(src_dir.glob("*.md")):
            dest_file = dest_dir / src_file.name

            if dest_file.exists() and not args.dry_run:
                print(f"Skipping (already exists): {dest_file.relative_to(PROJECT_ROOT)}")
                skipped += 1
                continue

            convert_file(src_file, dest_file, category, all_entities, args.dry_run)
            converted += 1

    print(f"\nDone. Converted: {converted}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
