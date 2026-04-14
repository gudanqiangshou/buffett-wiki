# Wiki 结构规则（SCHEMA）

## 基本规则

1. 所有页面必须用 Markdown 格式
2. 必须包含 YAML frontmatter
3. 必须使用 `[[双向链接]]` 关联实体
4. 每个实体必须有独立页面

## Frontmatter 模板

```yaml
---
title: "页面标题"
type: letter-summary | interview-summary | concept | company | person | insight | index
date: YYYY-MM-DD
source: "原始文件路径（信件和访谈必填）"
tags: [标签1, 标签2]
related: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

## 6 种页面类型

| 类型 | 说明 | 目录 |
|------|------|------|
| letter-summary | 股东信/合伙人信摘要 | wiki/letters/ |
| interview-summary | 访谈/演讲摘要 | wiki/interviews/ |
| concept | 投资概念 | wiki/concepts/ |
| company | 公司 | wiki/companies/ |
| person | 人物 | wiki/people/ |
| insight | 交叉分析 | wiki/insights/ |

## 摘要页结构

```markdown
# 标题

## 核心要点
- 要点1
- 要点2

## 详细摘要
正文内容...

## 提到的概念
- [[概念1]]
- [[概念2]]

## 提到的公司
- [[公司1]]

## 提到的人物
- [[人物1]]

## 原文金句
> "引用1"
> "引用2"
```

## 链接规则

- 使用 `[[实体名]]` 格式
- 避免自链接
- 跳过标题行和代码块中的链接
- 按名称长度降序匹配（避免短名称误匹配）
