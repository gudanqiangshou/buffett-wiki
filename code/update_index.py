#!/usr/bin/env python3
"""
update_index.py
Regenerate wiki/index.md by scanning all wiki/ markdown files,
parsing YAML frontmatter, grouping by type/category, and generating
a table organized by category with links to each page.
"""

import argparse
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path("/Users/a1/巴菲特知识库")
WIKI_DIR = PROJECT_ROOT / "wiki"
INDEX_FILE = WIKI_DIR / "index.md"

# Display labels for each type value
TYPE_LABELS: dict[str, str] = {
    "concept": "概念",
    "company": "公司",
    "person": "人物",
    "letter": "股东信",
    "interview": "访谈",
    "insight": "洞察",
    "other": "其他",
}

# Preferred display order of categories
CATEGORY_ORDER = ["concept", "company", "person", "letter", "interview", "insight", "other"]


def parse_frontmatter(text: str) -> dict[str, str]:
    """Extract YAML frontmatter fields as a flat string dict.

    Splits on '---' delimiters. Returns empty dict if no frontmatter found.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    fm_lines: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        fm_lines.append(line)

    fields: dict[str, str] = {}
    for line in fm_lines:
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip().strip('"').strip("'")

    return fields


def collect_pages() -> list[dict[str, str]]:
    """Scan wiki/ for markdown files and return a list of page dicts."""
    pages: list[dict[str, str]] = []
    skip_names = {"index", "README", "SCHEMA", "log"}

    for md_file in sorted(WIKI_DIR.rglob("*.md")):
        if md_file.stem in skip_names:
            continue

        text = md_file.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)

        title = fm.get("title") or md_file.stem
        type_ = fm.get("type") or "other"
        page_date = fm.get("date") or ""

        # Relative path from wiki/ for wikilink-style reference
        rel_path = md_file.relative_to(WIKI_DIR)
        # Use stem for display link (Obsidian-style [[stem]])
        link_name = md_file.stem

        pages.append(
            {
                "title": title,
                "type": type_,
                "date": page_date,
                "link": link_name,
                "rel_path": str(rel_path),
            }
        )

    return pages


def group_pages(pages: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    """Group pages by their type value."""
    groups: dict[str, list[dict[str, str]]] = {}
    for page in pages:
        type_ = page["type"] if page["type"] in TYPE_LABELS else "other"
        groups.setdefault(type_, []).append(page)
    return groups


def render_index(groups: dict[str, list[dict[str, str]]]) -> str:
    today = date.today().isoformat()
    lines: list[str] = [
        "---",
        'title: "知识库索引"',
        "type: index",
        f"updated: {today}",
        "---",
        "",
        "# 巴菲特知识库 — 索引",
        "",
        f"> 自动生成于 {today}。如需手动编辑，请在重新生成前备份。",
        "",
    ]

    total = sum(len(v) for v in groups.values())
    lines.append(f"共收录 **{total}** 个条目，按类别分组如下。")
    lines.append("")

    # Table of contents
    lines.append("## 目录")
    lines.append("")
    for type_key in CATEGORY_ORDER:
        if type_key not in groups:
            continue
        label = TYPE_LABELS.get(type_key, type_key)
        count = len(groups[type_key])
        anchor = label  # GitHub/Obsidian anchor from heading text
        lines.append(f"- [{label}（{count}）](#{label})")
    lines.append("")

    # Per-category tables
    for type_key in CATEGORY_ORDER:
        if type_key not in groups:
            continue
        label = TYPE_LABELS.get(type_key, type_key)
        category_pages = sorted(groups[type_key], key=lambda p: p["date"] or "", reverse=True)

        lines.append(f"## {label}")
        lines.append("")
        lines.append("| 标题 | 类型 | 日期 |")
        lines.append("|------|------|------|")

        for page in category_pages:
            title_link = f"[[{page['link']}|{page['title']}]]"
            type_label = TYPE_LABELS.get(page["type"], page["type"])
            page_date = page["date"] or "—"
            lines.append(f"| {title_link} | {type_label} | {page_date} |")

        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regenerate wiki/index.md from all wiki/ markdown files."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the generated index to stdout without writing to disk.",
    )
    args = parser.parse_args()

    if not WIKI_DIR.exists():
        print(f"Wiki directory not found: {WIKI_DIR}", file=sys.stderr)
        sys.exit(1)

    pages = collect_pages()
    if not pages:
        print("No markdown pages found in wiki/.", file=sys.stderr)
        sys.exit(1)

    groups = group_pages(pages)
    index_content = render_index(groups)

    if args.dry_run:
        print(index_content)
        print(f"\n[DRY-RUN] Would write {len(index_content)} bytes to {INDEX_FILE}")
    else:
        INDEX_FILE.write_text(index_content, encoding="utf-8")
        total = sum(len(v) for v in groups.values())
        print(f"Written: {INDEX_FILE.relative_to(PROJECT_ROOT)} ({total} entries)")


if __name__ == "__main__":
    main()
