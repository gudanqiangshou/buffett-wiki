#!/usr/bin/env python3
"""
build-data.py — Generate frontend JSON data from wiki/ pages.

Outputs:
  public/data/wiki-index.json   — page metadata index
  public/data/graph.json        — knowledge graph nodes & edges
  public/data/search-index.json — search index
  public/data/pages/            — copies of wiki markdown files
  public/data/raw/              — copies of raw source files
"""

import json
import os
import re
import shutil
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
WEB_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = WEB_DIR.parent.parent
WIKI_DIR = PROJECT_ROOT / "wiki"
RAW_DIR = PROJECT_ROOT / "raw"
DATA_DIR = WEB_DIR / "public" / "data"
PAGES_DIR = DATA_DIR / "pages"
RAW_OUT_DIR = DATA_DIR / "raw"

CATEGORIES = ["concepts", "companies", "people", "interviews", "letters", "insights"]


def parse_frontmatter(text):
    """Parse YAML frontmatter from markdown text (no gray-matter dependency)."""
    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    yaml_text = parts[1].strip()
    body = parts[2].strip()
    meta = {}

    for line in yaml_text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()

        # Strip quotes
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1]

        # Parse arrays: [item1, item2]
        if value.startswith("[") and value.endswith("]"):
            items = value[1:-1].split(",")
            value = [item.strip().strip('"').strip("'") for item in items if item.strip()]

        meta[key] = value

    return meta, body


def extract_wikilinks(text):
    """Extract all [[wikilinks]] from text."""
    return re.findall(r"\[\[(.+?)\]\]", text)


def strip_markdown(text, max_len=200):
    """Strip markdown formatting and truncate."""
    text = re.sub(r"#{1,6}\s+", "", text)       # headings
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text) # bold
    text = re.sub(r"\*(.+?)\*", r"\1", text)     # italic
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)  # links
    text = re.sub(r"\[\[(.+?)\]\]", r"\1", text) # wikilinks
    text = re.sub(r"> .+", "", text)              # blockquotes
    text = re.sub(r"- ", "", text)                # list markers
    text = re.sub(r"\n{2,}", "\n", text)          # collapse newlines
    text = text.strip()
    if len(text) > max_len:
        text = text[:max_len] + "..."
    return text


def scan_wiki():
    """Scan all wiki pages and parse metadata."""
    pages = []

    for category in CATEGORIES:
        cat_dir = WIKI_DIR / category
        if not cat_dir.exists():
            continue

        for md_file in sorted(cat_dir.glob("*.md")):
            text = md_file.read_text(encoding="utf-8")
            meta, body = parse_frontmatter(text)

            if not meta.get("title"):
                continue

            slug = md_file.stem
            links = extract_wikilinks(body)
            summary = strip_markdown(body)

            pages.append({
                "title": meta.get("title", slug),
                "type": meta.get("type", ""),
                "date": meta.get("date", ""),
                "path": f"{category}/{slug}",
                "category": category,
                "summary": summary,
                "links": links,
                "tags": meta.get("tags", []),
                "source": meta.get("source", ""),
            })

    return pages


def build_graph(pages):
    """Build knowledge graph from pages and their wikilinks."""
    # Collect all node names
    node_set = {}  # name -> {id, name, type, category}

    # Add all pages as nodes
    for p in pages:
        name = p["title"]
        node_set[name] = {
            "id": name,
            "name": name,
            "type": p["type"],
            "category": p["category"],
        }

    # Add link targets that don't have their own pages
    for p in pages:
        for link in p["links"]:
            if link not in node_set:
                node_set[link] = {
                    "id": link,
                    "name": link,
                    "type": "unknown",
                    "category": "unknown",
                }

    # Build edges
    edges = []
    seen_edges = set()
    for p in pages:
        source = p["title"]
        for target in p["links"]:
            edge_key = f"{source}->{target}"
            if edge_key not in seen_edges and source != target:
                edges.append({"source": source, "target": target})
                seen_edges.add(edge_key)

    nodes = list(node_set.values())
    return {"nodes": nodes, "edges": edges}


def build_search_index(pages):
    """Build search index with content snippets."""
    index = []
    for p in pages:
        # Read full body for search
        md_path = WIKI_DIR / p["category"] / f"{p['path'].split('/')[-1]}.md"
        if md_path.exists():
            text = md_path.read_text(encoding="utf-8")
            _, body = parse_frontmatter(text)
            snippet = strip_markdown(body, max_len=500)
        else:
            snippet = p["summary"]

        index.append({
            "title": p["title"],
            "path": p["path"],
            "category": p["category"],
            "content_snippet": snippet,
        })
    return index


def copy_wiki_pages():
    """Copy wiki markdown files to public/data/pages/."""
    for category in CATEGORIES:
        src_dir = WIKI_DIR / category
        dst_dir = PAGES_DIR / category
        dst_dir.mkdir(parents=True, exist_ok=True)

        if not src_dir.exists():
            continue

        for md_file in src_dir.glob("*.md"):
            shutil.copy2(md_file, dst_dir / md_file.name)


def copy_raw_sources():
    """Copy raw source files to public/data/raw/."""
    for subdir in ["letters/partnership", "letters/berkshire", "letters/special", "interviews"]:
        src_dir = RAW_DIR / subdir
        dst_dir = RAW_OUT_DIR / subdir
        dst_dir.mkdir(parents=True, exist_ok=True)

        if not src_dir.exists():
            continue

        for md_file in src_dir.glob("*.md"):
            shutil.copy2(md_file, dst_dir / md_file.name)


def main():
    print("=== build-data.py ===")
    print(f"Wiki dir: {WIKI_DIR}")
    print(f"Output dir: {DATA_DIR}")

    # Ensure output dirs
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    RAW_OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Scan wiki
    pages = scan_wiki()
    print(f"\nFound {len(pages)} wiki pages:")
    for cat in CATEGORIES:
        count = sum(1 for p in pages if p["category"] == cat)
        if count:
            print(f"  {cat}: {count}")

    # Generate wiki-index.json
    index_path = DATA_DIR / "wiki-index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(pages, f, ensure_ascii=False, indent=2)
    print(f"\nGenerated: {index_path.relative_to(WEB_DIR)}")

    # Generate graph.json
    graph = build_graph(pages)
    graph_path = DATA_DIR / "graph.json"
    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
    print(f"Generated: {graph_path.relative_to(WEB_DIR)} ({len(graph['nodes'])} nodes, {len(graph['edges'])} edges)")

    # Generate search-index.json
    search_index = build_search_index(pages)
    search_path = DATA_DIR / "search-index.json"
    with open(search_path, "w", encoding="utf-8") as f:
        json.dump(search_index, f, ensure_ascii=False, indent=2)
    print(f"Generated: {search_path.relative_to(WEB_DIR)}")

    # Copy files
    copy_wiki_pages()
    print(f"Copied wiki pages to: {PAGES_DIR.relative_to(WEB_DIR)}/")

    copy_raw_sources()
    print(f"Copied raw sources to: {RAW_OUT_DIR.relative_to(WEB_DIR)}/")

    print("\n=== Done ===")


if __name__ == "__main__":
    main()
