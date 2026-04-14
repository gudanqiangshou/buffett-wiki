<template>
  <div class="page-view">
    <!-- Breadcrumb -->
    <nav class="breadcrumb">
      <router-link to="/">首页</router-link>
      <span class="sep">›</span>
      <router-link :to="`/category/${route.params.category}`">{{ categoryName }}</router-link>
      <span class="sep">›</span>
      <span class="current">{{ frontmatter.title || route.params.slug }}</span>
    </nav>

    <!-- Loading / Error -->
    <div v-if="loading" class="state-msg">加载中…</div>
    <div v-else-if="error" class="state-msg error">{{ error }}</div>

    <template v-else>
      <!-- Page Header -->
      <header class="page-header">
        <span class="category-badge" :class="badgeClass">{{ categoryLabel }}</span>
        <h1 class="page-title">{{ frontmatter.title }}</h1>
        <p v-if="frontmatter.date" class="page-date">{{ frontmatter.date }}</p>
      </header>

      <!-- Content Body -->
      <div class="content-card">
        <div class="markdown-body" v-html="renderedBody"></div>
      </div>

      <!-- Raw Source Viewer -->
      <div
        v-if="showRawSource"
        class="raw-source-section"
      >
        <button class="raw-toggle-btn" @click="rawExpanded = !rawExpanded">
          {{ rawExpanded ? '▼' : '▶' }} 📄 原文全文 —
          {{ rawExpanded ? '收起' : '展开阅读完整原文' }}
        </button>

        <div class="raw-content-wrapper" :class="{ expanded: rawExpanded }">
          <div class="raw-content" v-html="renderedRaw"></div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import MarkdownIt from 'markdown-it'

const route = useRoute()
const md = new MarkdownIt({ html: false, linkify: true, typographer: true })

// ── State ────────────────────────────────────────────────────────────────────
const loading = ref(true)
const error = ref(null)
const frontmatter = ref({})
const bodyMarkdown = ref('')
const wikiIndex = ref([])   // full array from wiki-index.json
const rawMarkdown = ref('')
const rawExpanded = ref(false)

// ── Category helpers ──────────────────────────────────────────────────────────
const CATEGORY_NAMES = {
  concepts:   '核心概念',
  companies:  '投资公司',
  people:     '关键人物',
  interviews: '访谈与演讲',
  letters:    '股东信',
}

const TYPE_BADGE = {
  concept:           'badge-concept',
  company:           'badge-company',
  person:            'badge-person',
  'interview-summary': 'badge-interview',
  'letter-summary':    'badge-letter',
}

const TYPE_LABEL = {
  concept:           '核心概念',
  company:           '投资公司',
  person:            '关键人物',
  'interview-summary': '访谈与演讲',
  'letter-summary':    '股东信',
}

const categoryName = computed(
  () => CATEGORY_NAMES[route.params.category] || route.params.category
)

const badgeClass = computed(
  () => TYPE_BADGE[frontmatter.value.type] || 'badge-concept'
)

const categoryLabel = computed(
  () => TYPE_LABEL[frontmatter.value.type] || categoryName.value
)

// ── Wiki-link lookup map  title → { category, slug } ─────────────────────────
const linkMap = computed(() => {
  const map = {}
  for (const item of wikiIndex.value) {
    // path is like "concepts/复利"
    const parts = item.path ? item.path.split('/') : []
    const category = parts[0] || item.category
    const slug = parts.slice(1).join('/') || item.title
    map[item.title] = { category, slug }
  }
  return map
})

// ── Render body markdown with [[wikilink]] replacement ────────────────────────
const renderedBody = computed(() => {
  if (!bodyMarkdown.value) return ''
  // First render markdown to HTML
  let html = md.render(bodyMarkdown.value)
  // Then replace [[text]] patterns with router-link anchors
  html = html.replace(/\[\[([^\]]+)\]\]/g, (_, text) => {
    const entry = linkMap.value[text]
    if (entry) {
      return `<a href="/page/${entry.category}/${encodeURIComponent(entry.slug)}" class="wikilink">${text}</a>`
    }
    return `<span class="wikilink-missing">${text}</span>`
  })
  return html
})

// ── Raw source viewer ─────────────────────────────────────────────────────────
const showRawSource = computed(() => {
  const type = frontmatter.value.type
  return (
    (type === 'letter-summary' || type === 'interview-summary') &&
    frontmatter.value.source &&
    frontmatter.value.source.trim() !== ''
  )
})

const renderedRaw = computed(() => {
  if (!rawMarkdown.value) return ''
  const filtered = rawMarkdown.value
    .split('\n')
    .filter(line => {
      const t = line.trim()
      return (
        !t.startsWith('> **Source**') &&
        !t.startsWith('> **Type**') &&
        t !== '---'
      )
    })
    .join('\n')
  return md.render(filtered)
})

// ── Source path → fetch URL mapping ──────────────────────────────────────────
function sourceToUrl(sourcePath) {
  // e.g. "raw/interviews/xxx.md" → "/data/raw/interviews/xxx.md"
  return `${import.meta.env.BASE_URL}data/${sourcePath}`
}

// ── Frontmatter parser ────────────────────────────────────────────────────────
function parseFrontmatter(text) {
  const result = { title: '', type: '', date: '', source: '', tags: [] }
  if (!text.startsWith('---')) return { fm: result, body: text }

  const end = text.indexOf('---', 3)
  if (end === -1) return { fm: result, body: text }

  const fmBlock = text.slice(3, end).trim()
  const body = text.slice(end + 3).trim()

  for (const line of fmBlock.split('\n')) {
    const colon = line.indexOf(':')
    if (colon === -1) continue
    const key = line.slice(0, colon).trim()
    const val = line.slice(colon + 1).trim().replace(/^["']|["']$/g, '')
    if (key === 'tags') {
      // e.g. [价值投资, 核心概念]
      result.tags = val.replace(/[\[\]]/g, '').split(',').map(t => t.trim()).filter(Boolean)
    } else {
      result[key] = val
    }
  }
  return { fm: result, body }
}

// ── Data loading ──────────────────────────────────────────────────────────────
async function loadPage() {
  loading.value = true
  error.value = null
  rawMarkdown.value = ''
  rawExpanded.value = false

  const { category, slug } = route.params

  try {
    // Load wiki index (for wikilink resolution)
    const idxRes = await fetch(`${import.meta.env.BASE_URL}data/wiki-index.json`)
    if (!idxRes.ok) throw new Error('无法加载 wiki-index.json')
    wikiIndex.value = await idxRes.json()

    // Load page markdown
    const pageUrl = `${import.meta.env.BASE_URL}data/pages/${category}/${decodeURIComponent(slug)}.md`
    const pageRes = await fetch(pageUrl)
    if (!pageRes.ok) throw new Error(`页面未找到：${pageUrl}`)
    const raw = await pageRes.text()

    const { fm, body } = parseFrontmatter(raw)
    frontmatter.value = fm
    bodyMarkdown.value = body

    // Load raw source if applicable
    if (
      (fm.type === 'letter-summary' || fm.type === 'interview-summary') &&
      fm.source && fm.source.trim()
    ) {
      const rawUrl = sourceToUrl(fm.source.trim())
      const rawRes = await fetch(rawUrl)
      if (rawRes.ok) {
        rawMarkdown.value = await rawRes.text()
      }
    }
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(loadPage)
watch(() => route.params, loadPage, { deep: true })
</script>

<style scoped>
/* ── Layout ─────────────────────────────────────────────────────────────────── */
.page-view {
  max-width: 860px;
  margin: 0 auto;
  padding: 24px 20px 60px;
}

/* ── Breadcrumb ─────────────────────────────────────────────────────────────── */
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #888;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.breadcrumb a {
  color: #5b8dd9;
  text-decoration: none;
}
.breadcrumb a:hover { text-decoration: underline; }
.breadcrumb .sep { color: #bbb; }
.breadcrumb .current { color: #555; }

/* ── State messages ──────────────────────────────────────────────────────────── */
.state-msg {
  text-align: center;
  padding: 60px 20px;
  color: #888;
  font-size: 15px;
}
.state-msg.error { color: #c0392b; }

/* ── Page Header ─────────────────────────────────────────────────────────────── */
.page-header {
  background: linear-gradient(135deg, #191D2B 0%, #252D45 100%);
  padding: 32px;
  border-radius: 0 0 16px 16px;
  margin-bottom: 24px;
}

.page-title {
  color: #fff;
  font-size: 28px;
  font-weight: 700;
  margin: 12px 0 0;
  line-height: 1.3;
}

.page-date {
  color: #9aa8c7;
  font-size: 13px;
  margin: 8px 0 0;
}

/* ── Category badges ─────────────────────────────────────────────────────────── */
.category-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.5px;
}
.badge-concept   { background: #2563eb22; color: #60a5fa; border: 1px solid #2563eb55; }
.badge-company   { background: #16a34a22; color: #4ade80; border: 1px solid #16a34a55; }
.badge-person    { background: #d9770622; color: #fbbf24; border: 1px solid #d9770655; }
.badge-interview { background: #7c3aed22; color: #c084fc; border: 1px solid #7c3aed55; }
.badge-letter    { background: #b91c1c22; color: #f87171; border: 1px solid #b91c1c55; }

/* ── Content card ────────────────────────────────────────────────────────────── */
.content-card {
  background: #fff;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.08);
  margin-bottom: 24px;
}

/* ── Markdown body ───────────────────────────────────────────────────────────── */
.markdown-body {
  font-size: 15px;
  color: #2c3e50;
  line-height: 1.8;
}

.markdown-body :deep(h1) {
  font-size: 22px;
  font-weight: 700;
  color: #1a2540;
  margin: 0 0 20px;
}

.markdown-body :deep(h2) {
  font-size: 18px;
  font-weight: 700;
  color: #1a2540;
  border-bottom: 1px solid var(--border-light, #e8ecf3);
  padding-bottom: 8px;
  margin-top: 32px;
  margin-bottom: 16px;
}

.markdown-body :deep(h3) {
  font-size: 16px;
  font-weight: 600;
  color: #253050;
  margin-top: 24px;
  margin-bottom: 12px;
}

.markdown-body :deep(p) { margin: 0 0 14px; }

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 24px;
  margin: 0 0 14px;
}

.markdown-body :deep(li) { margin-bottom: 6px; }

.markdown-body :deep(strong) { color: #1a2540; font-weight: 600; }

.markdown-body :deep(blockquote) {
  border-left: 4px solid #d4a017;
  background: #fdf8ec;
  margin: 20px 0;
  padding: 12px 20px;
  border-radius: 0 8px 8px 0;
  color: #5a4a1a;
  font-style: italic;
}

.markdown-body :deep(blockquote p) { margin: 0; }

.markdown-body :deep(code) {
  background: #f4f6fb;
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 13px;
  color: #d63031;
}

.markdown-body :deep(pre) {
  background: #f4f6fb;
  border-radius: 8px;
  padding: 16px;
  overflow-x: auto;
  margin: 0 0 16px;
}

.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
  color: #2d3436;
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid #e8ecf3;
  margin: 24px 0;
}

/* ── Wiki-links ──────────────────────────────────────────────────────────────── */
.markdown-body :deep(.wikilink) {
  color: #2563eb;
  text-decoration: none;
  border-bottom: 1px dashed #93c5fd;
  transition: color 0.15s, border-color 0.15s;
}
.markdown-body :deep(.wikilink:hover) {
  color: #1d4ed8;
  border-bottom-color: #2563eb;
}
.markdown-body :deep(.wikilink-missing) {
  color: #9ca3af;
  border-bottom: 1px dashed #d1d5db;
  cursor: default;
}

/* ── Raw source section ──────────────────────────────────────────────────────── */
.raw-source-section {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.raw-toggle-btn {
  width: 100%;
  text-align: left;
  padding: 16px 24px;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  background: #f9fafb;
  border: none;
  cursor: pointer;
  border-bottom: 1px solid #e8ecf3;
  transition: background 0.15s;
}
.raw-toggle-btn:hover { background: #f0f4ff; }

.raw-content-wrapper {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.35s ease;
}
.raw-content-wrapper.expanded {
  max-height: 80vh;
  overflow-y: auto;
}

.raw-content {
  padding: 24px 32px;
  font-size: 14px;
  color: #374151;
  line-height: 1.8;
}

.raw-content :deep(p)  { margin: 0 0 12px; }
.raw-content :deep(strong) { color: #1a2540; }
.raw-content :deep(blockquote) {
  border-left: 3px solid #d1d5db;
  background: #f9fafb;
  margin: 12px 0;
  padding: 8px 16px;
  border-radius: 0 6px 6px 0;
  color: #6b7280;
  font-style: italic;
}
.raw-content :deep(blockquote p) { margin: 0; }
</style>
