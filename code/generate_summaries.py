#!/usr/bin/env python3
"""
Generate wiki summary pages for all raw letters and interviews.
Reads raw/*.md files, extracts entities/quotes/key points,
and writes structured wiki pages to wiki/letters/ and wiki/interviews/.
"""

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "raw"
WIKI_DIR = ROOT / "wiki"
TODAY = "2026-04-13"

# All entity names from wiki/concepts/, wiki/companies/, wiki/people/
CONCEPTS = sorted([
    "买入价格", "企业文化", "低估", "保险业", "保险浮存金", "债券",
    "公司治理", "内在价值", "分散投资", "品牌", "商业模式", "商誉",
    "回购", "复利", "套利", "安全边际", "市场先生", "市场预测",
    "市盈率", "护城河", "收购", "承保纪律", "有效市场", "杠杆",
    "特许经营权", "留存收益", "税收效率", "竞争优势", "管理层",
    "纺织业务", "股东导向", "股息", "能力圈", "能源", "航空业",
    "衍生品", "账面价值", "资本配置", "透视盈余", "通货膨胀",
    "长期持有", "集中投资", "科技与互联网", "零售与消费", "银行业",
    "铁路运输", "媒体与出版", "可转换证券",
], key=lambda x: -len(x))

COMPANIES = sorted([
    "BNSF铁路", "IBM", "三井物产", "三菱商事", "世界图书百科全书",
    "中国石油", "中美能源", "伊斯卡", "伊藤忠商事", "伯克希尔哈撒韦",
    "伯克希尔哈撒韦能源", "克莱顿房屋", "内布拉斯加家具店", "冰雪皇后",
    "利捷航空", "华盛顿邮报", "卡夫亨氏", "可口可乐", "吉列",
    "喜诗糖果", "国民保险公司", "大都会通信", "威利家居", "威瑞森通讯",
    "富国银行", "州立农业保险", "布法罗新闻报", "康菲石油",
    "德克斯特鞋业", "房地美", "所罗门", "斯科特费泽", "比亚迪",
    "波仙珠宝", "精密铸件", "约翰斯曼维尔", "穆迪", "科比吸尘器",
    "纽约梅隆银行", "美国合众银行", "美国家庭服务", "美国运通",
    "美国银行", "苹果", "蓝筹印花", "西方石油", "费希海默制服",
    "路博润", "通用再保险", "通用汽车", "通用电气", "雪佛龙",
    "韦斯科", "飞安公司", "马蒙集团", "高盛", "鲜果布衣", "麦克莱恩",
    "特许通讯", "森林河公司",
], key=lambda x: -len(x))

PEOPLE = sorted([
    "B夫人", "托德·库姆斯", "格雷厄姆", "格雷格·阿贝尔",
    "泰德·韦施勒", "芒格", "阿吉特·贾恩",
], key=lambda x: -len(x))

ALL_ENTITIES = CONCEPTS + COMPANIES + PEOPLE


def read_raw(path: Path) -> str:
    """Read a raw markdown file."""
    return path.read_text(encoding="utf-8")


def strip_header(text: str) -> str:
    """Remove the # title, > Source, > Type, and --- header lines."""
    lines = text.split("\n")
    body_lines = []
    in_header = True
    for line in lines:
        if in_header:
            stripped = line.strip()
            if stripped.startswith("# "):
                continue
            if stripped.startswith("> **Source"):
                continue
            if stripped.startswith("> **Type"):
                continue
            if stripped == "---":
                in_header = False
                continue
            if stripped == "":
                continue
            # First non-header content line
            in_header = False
            body_lines.append(line)
        else:
            body_lines.append(line)
    return "\n".join(body_lines).strip()


def find_entities(text: str, entity_list: list) -> list:
    """Find which entities from the list appear in the text."""
    found = []
    for name in entity_list:
        if name in text:
            found.append(name)
    return found


def extract_quotes(text: str, max_quotes: int = 8) -> list:
    """Extract notable quotes from the text."""
    quotes = []
    lines = text.split("\n")

    # Look for lines that are clearly quotable wisdom
    wisdom_keywords = [
        "护城河", "安全边际", "能力圈", "复利", "内在价值", "长期",
        "恐惧", "贪婪", "市场先生", "竞争优势", "品牌", "管理层",
        "投资", "企业", "价值", "回报", "资本", "股东", "诚信",
        "错误", "风险", "永久性", "持久", "简单", "理性",
        "时间是", "最重要的", "关键是", "本质", "根本", "原则",
    ]

    for line in lines:
        line = line.strip()
        if not line or len(line) < 20 or len(line) > 300:
            continue
        # Skip headings and metadata
        if line.startswith("#") or line.startswith(">") or line.startswith("-"):
            continue
        if line.startswith("|") or line.startswith("---"):
            continue

        # Score the line for "quotability"
        score = 0
        for kw in wisdom_keywords:
            if kw in line:
                score += 1
        if score >= 2:
            quotes.append(line)

    # Deduplicate and limit
    seen = set()
    unique = []
    for q in quotes:
        if q not in seen:
            seen.add(q)
            unique.append(q)

    return unique[:max_quotes]


def extract_key_points(text: str, max_points: int = 6) -> list:
    """Extract key points by finding section headings and their first sentences."""
    points = []
    lines = text.split("\n")

    # Find section-like headings (short lines preceded by blank, or lines ending with specific patterns)
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Skip empty lines
        if not stripped:
            continue

        # Detect section headings: short lines (< 30 chars) that look like titles
        is_heading = False
        if len(stripped) <= 40 and not stripped.endswith("。") and not stripped.endswith("："):
            if i > 0 and lines[i-1].strip() == "":
                is_heading = True
        if stripped.startswith("## "):
            is_heading = True
            stripped = stripped[3:]

        if is_heading and len(stripped) > 2:
            # Get the first meaningful sentence after this heading
            for j in range(i+1, min(i+5, len(lines))):
                next_line = lines[j].strip()
                if next_line and len(next_line) > 15 and not next_line.startswith("#"):
                    # Extract first sentence
                    sentence = next_line
                    # Cut at first period if long
                    for sep in ["。", "——", "；"]:
                        idx = sentence.find(sep)
                        if idx > 10:
                            sentence = sentence[:idx + len(sep)]
                            break
                    if len(sentence) > 200:
                        sentence = sentence[:200] + "……"
                    points.append(f"**{stripped}**：{sentence}")
                    break

    if not points:
        # Fallback: extract first sentences of long paragraphs
        for line in lines:
            stripped = line.strip()
            if len(stripped) > 50 and not stripped.startswith("#") and not stripped.startswith(">"):
                sentence = stripped
                for sep in ["。", "；"]:
                    idx = sentence.find(sep)
                    if idx > 10:
                        sentence = sentence[:idx + len(sep)]
                        break
                if len(sentence) > 200:
                    sentence = sentence[:200] + "……"
                points.append(sentence)
                if len(points) >= max_points:
                    break

    return points[:max_points]


def generate_summary(text: str, max_chars: int = 3000) -> str:
    """Generate a condensed summary by taking key paragraphs."""
    lines = text.split("\n")
    paragraphs = []
    current = []

    for line in lines:
        if line.strip() == "":
            if current:
                para = "\n".join(current).strip()
                if len(para) > 30:
                    paragraphs.append(para)
                current = []
        else:
            # Skip tables and raw data
            if line.strip().startswith("|") or line.strip().startswith("---:"):
                continue
            current.append(line)
    if current:
        para = "\n".join(current).strip()
        if len(para) > 30:
            paragraphs.append(para)

    # Take first N paragraphs that fit within max_chars
    summary_parts = []
    total = 0
    for para in paragraphs:
        # Skip headings-only paragraphs
        if len(para) < 20:
            continue
        if para.startswith("#"):
            # Keep heading but continue
            summary_parts.append(para)
            total += len(para)
            continue

        # For long paragraphs, take first 2 sentences
        if len(para) > 400:
            sentences = []
            remaining = para
            for _ in range(3):
                idx = remaining.find("。")
                if idx > 0:
                    sentences.append(remaining[:idx+1])
                    remaining = remaining[idx+1:]
                else:
                    break
            if sentences:
                para = "".join(sentences)
            else:
                para = para[:400] + "……"

        summary_parts.append(para)
        total += len(para)
        if total >= max_chars:
            break

    return "\n\n".join(summary_parts)


def insert_wikilinks(text: str, entities: list, self_title: str = "") -> str:
    """Insert [[wikilinks]] for entity mentions in text."""
    # Sort by length descending to avoid partial matches
    sorted_entities = sorted(entities, key=lambda x: -len(x))

    # Track already-linked positions
    for entity in sorted_entities:
        if entity == self_title:
            continue
        # Only link first occurrence in each paragraph
        # Simple approach: replace first occurrence not already in [[ ]]
        if entity in text and f"[[{entity}]]" not in text:
            # Replace first occurrence only
            text = text.replace(entity, f"[[{entity}]]", 1)

    return text


def parse_filename(path: Path) -> tuple:
    """Extract year and title from filename."""
    name = path.stem  # e.g., "1977 巴菲特致股东信"
    # Try to extract year
    match = re.match(r"(\d{4})", name)
    year = match.group(1) if match else "unknown"
    return year, name


def determine_letter_type(path: Path) -> str:
    """Determine if partnership, berkshire, or special letter."""
    parts = str(path).split(os.sep)
    if "partnership" in parts:
        return "合伙人信"
    elif "special" in parts:
        return "特别信件"
    else:
        return "股东信"


def generate_tags(letter_type: str, year: str, mentioned_concepts: list) -> list:
    """Generate tags for the page."""
    tags = ["价值投资"]
    if letter_type == "合伙人信":
        tags.append("合伙人信")
    elif letter_type == "股东信":
        tags.append("股东信")
    elif letter_type == "特别信件":
        tags.append("特别信件")

    # Add era tag
    y = int(year) if year.isdigit() else 0
    if y < 1970:
        tags.append("合伙人时期")
    elif y < 1990:
        tags.append("早期伯克希尔")
    elif y < 2010:
        tags.append("成熟期")
    else:
        tags.append("近期")

    return tags


def build_letter_page(raw_path: Path, relative_source: str) -> str:
    """Build a wiki summary page for a letter."""
    year, title = parse_filename(raw_path)
    letter_type = determine_letter_type(raw_path)
    raw_text = read_raw(raw_path)
    body = strip_header(raw_text)

    # Find entities
    found_concepts = find_entities(body, CONCEPTS)
    found_companies = find_entities(body, COMPANIES)
    found_people = find_entities(body, PEOPLE)
    all_found = found_concepts + found_companies + found_people

    # Extract content
    key_points = extract_key_points(body)
    summary = generate_summary(body)
    quotes = extract_quotes(body)

    # Insert wikilinks in summary
    summary_linked = insert_wikilinks(summary, all_found, self_title=title)

    # Generate tags
    tags = generate_tags(letter_type, year, found_concepts)
    tags_str = ", ".join(tags)

    # Build page
    page = f"""---
title: "{title}"
type: letter-summary
date: {year}-01-01
source: "{relative_source}"
tags: [{tags_str}]
related: []
created: {TODAY}
updated: {TODAY}
---

# {title}

"""

    # 核心要点
    page += "## 核心要点\n\n"
    if key_points:
        for point in key_points:
            point_linked = insert_wikilinks(point, all_found, self_title=title)
            page += f"- {point_linked}\n"
    else:
        page += f"- 本信为{year}年{letter_type}\n"
    page += "\n"

    # 详细摘要
    page += "## 详细摘要\n\n"
    page += summary_linked + "\n\n"

    # 提到的概念
    page += "## 提到的概念\n\n"
    if found_concepts:
        for c in found_concepts:
            page += f"- [[{c}]]\n"
    else:
        page += "- （本信未涉及已收录的核心概念）\n"
    page += "\n"

    # 提到的公司
    page += "## 提到的公司\n\n"
    if found_companies:
        for c in found_companies:
            page += f"- [[{c}]]\n"
    else:
        page += "- （本信未提及已收录的公司）\n"
    page += "\n"

    # 提到的人物
    page += "## 提到的人物\n\n"
    if found_people:
        for p in found_people:
            page += f"- [[{p}]]\n"
    else:
        page += "- （本信未提及已收录的人物）\n"
    page += "\n"

    # 原文金句
    page += "## 原文金句\n\n"
    if quotes:
        for q in quotes:
            q_linked = insert_wikilinks(q, all_found, self_title=title)
            page += f"> {q_linked}\n\n"
    else:
        page += "> （待补充）\n\n"

    return page


def build_interview_page(raw_path: Path, relative_source: str) -> str:
    """Build a wiki summary page for an interview."""
    year, title = parse_filename(raw_path)
    raw_text = read_raw(raw_path)
    body = strip_header(raw_text)

    # Find entities
    found_concepts = find_entities(body, CONCEPTS)
    found_companies = find_entities(body, COMPANIES)
    found_people = find_entities(body, PEOPLE)
    all_found = found_concepts + found_companies + found_people

    # Extract content
    key_points = extract_key_points(body)
    summary = generate_summary(body)
    quotes = extract_quotes(body)

    # Insert wikilinks
    summary_linked = insert_wikilinks(summary, all_found, self_title=title)

    # Determine tags
    tags = ["价值投资"]
    # Detect interview vs speech
    name_lower = title.lower()
    if "演讲" in title or "发言" in title:
        tags.append("演讲")
    elif "股东大会" in title:
        tags.append("股东大会")
    elif "采访" in title or "专访" in title or "访谈" in title or "CNBC" in title:
        tags.append("访谈")
    else:
        tags.append("对话")

    y = int(year) if year.isdigit() else 0
    if y < 1990:
        tags.append("早期")
    elif y < 2010:
        tags.append("成熟期")
    else:
        tags.append("近期")

    tags_str = ", ".join(tags)

    # Build page
    page = f"""---
title: "{title}"
type: interview-summary
date: {year}-01-01
source: "{relative_source}"
tags: [{tags_str}]
related: []
created: {TODAY}
updated: {TODAY}
---

# {title}

"""

    # 核心要点
    page += "## 核心要点\n\n"
    if key_points:
        for point in key_points:
            point_linked = insert_wikilinks(point, all_found, self_title=title)
            page += f"- {point_linked}\n"
    else:
        page += f"- 本访谈/演讲记录于{year}年\n"
    page += "\n"

    # 详细摘要
    page += "## 详细摘要\n\n"
    page += summary_linked + "\n\n"

    # 提到的概念
    page += "## 提到的概念\n\n"
    if found_concepts:
        for c in found_concepts:
            page += f"- [[{c}]]\n"
    else:
        page += "- （本访谈未涉及已收录的核心概念）\n"
    page += "\n"

    # 提到的公司
    page += "## 提到的公司\n\n"
    if found_companies:
        for c in found_companies:
            page += f"- [[{c}]]\n"
    else:
        page += "- （本访谈未提及已收录的公司）\n"
    page += "\n"

    # 提到的人物
    page += "## 提到的人物\n\n"
    if found_people:
        for p in found_people:
            page += f"- [[{p}]]\n"
    else:
        page += "- （本访谈未提及已收录的人物）\n"
    page += "\n"

    # 原文金句
    page += "## 原文金句\n\n"
    if quotes:
        for q in quotes:
            q_linked = insert_wikilinks(q, all_found, self_title=title)
            page += f"> {q_linked}\n\n"
    else:
        page += "> （待补充）\n\n"

    return page


def process_letters():
    """Process all letter files."""
    letters_dir = WIKI_DIR / "letters"
    letters_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for subdir in ["partnership", "berkshire", "special"]:
        raw_subdir = RAW_DIR / "letters" / subdir
        if not raw_subdir.exists():
            continue
        for f in sorted(raw_subdir.glob("*.md")):
            relative_source = f"raw/letters/{subdir}/{f.name}"
            page_content = build_letter_page(f, relative_source)
            out_path = letters_dir / f.name
            out_path.write_text(page_content, encoding="utf-8")
            count += 1
            print(f"  [letter] {f.name}")

    return count


def process_interviews():
    """Process all interview files."""
    interviews_dir = WIKI_DIR / "interviews"
    interviews_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    raw_interviews = RAW_DIR / "interviews"
    if not raw_interviews.exists():
        return 0

    for f in sorted(raw_interviews.glob("*.md")):
        relative_source = f"raw/interviews/{f.name}"
        page_content = build_interview_page(f, relative_source)
        out_path = interviews_dir / f.name
        out_path.write_text(page_content, encoding="utf-8")
        count += 1
        print(f"  [interview] {f.name}")

    return count


if __name__ == "__main__":
    print("=== Generating Wiki Summary Pages ===\n")

    print("Processing letters...")
    letter_count = process_letters()
    print(f"\n  → {letter_count} letter summaries generated\n")

    print("Processing interviews...")
    interview_count = process_interviews()
    print(f"\n  → {interview_count} interview summaries generated\n")

    print(f"=== Done: {letter_count + interview_count} total pages generated ===")
