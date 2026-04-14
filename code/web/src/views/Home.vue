<template>
  <div class="home">

    <!-- ═══════════════════════════════════════════
         1. HERO SECTION
    ════════════════════════════════════════════ -->
    <section class="hero">
      <div class="hero-left">
        <h1 class="hero-title">巴菲特投资思想知识图谱</h1>
        <p class="hero-subtitle">
          基于 LLM Wiki 模式，结构化呈现 Warren Buffett 的投资智慧
        </p>
        <div class="hero-btns">
          <router-link to="/chat" class="btn btn-gold">🧑‍💼 问 AI 巴菲特</router-link>
          <router-link to="/graph" class="btn btn-ghost">🕸️ 探索知识图谱</router-link>
        </div>
      </div>
      <div class="hero-right">
        <svg ref="miniGraphSvg" class="mini-graph" width="240" height="150"></svg>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════
         2. STAT CARDS
    ════════════════════════════════════════════ -->
    <section class="stat-grid">
      <div
        class="stat-card"
        style="--card-accent: #C2604A"
        @click="router.push('/category/letters')"
      >
        <div class="stat-top">
          <span class="stat-icon">📊</span>
          <span class="stat-number">{{ stats.letters }}</span>
        </div>
        <div class="stat-label">信件</div>
      </div>
      <div
        class="stat-card"
        style="--card-accent: #3B7DD8"
        @click="router.push('/category/concepts')"
      >
        <div class="stat-top">
          <span class="stat-icon">💡</span>
          <span class="stat-number">{{ stats.concepts }}</span>
        </div>
        <div class="stat-label">概念</div>
      </div>
      <div
        class="stat-card"
        style="--card-accent: #47956A"
        @click="router.push('/category/companies')"
      >
        <div class="stat-top">
          <span class="stat-icon">🏢</span>
          <span class="stat-number">{{ stats.companies }}</span>
        </div>
        <div class="stat-label">公司</div>
      </div>
      <div
        class="stat-card"
        style="--card-accent: #7E5FAD"
        @click="router.push('/category/interviews')"
      >
        <div class="stat-top">
          <span class="stat-icon">🎤</span>
          <span class="stat-number">{{ stats.interviews }}</span>
        </div>
        <div class="stat-label">访谈</div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════
         3. SEARCH BOX
    ════════════════════════════════════════════ -->
    <section class="search-card">
      <div class="search-wrap">
        <span class="search-icon">🔍</span>
        <input
          ref="searchInput"
          v-model="searchQuery"
          class="search-input"
          placeholder="搜索知识库…"
          @keydown.escape="clearSearch"
          @blur="onSearchBlur"
          @focus="searchFocused = true"
          autocomplete="off"
        />
      </div>
      <div
        v-if="searchFocused && searchResults.length"
        class="search-dropdown"
        @mousedown.prevent
      >
        <div
          v-for="item in searchResults"
          :key="item.path"
          class="search-result-item"
          @click="navigateToPage(item)"
        >
          <span class="result-title">{{ item.title }}</span>
          <span class="result-badge" :style="{ background: categoryColor(item.category) }">
            {{ categoryLabel(item.category) }}
          </span>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════
         4. TOP 15 核心投资概念
    ════════════════════════════════════════════ -->
    <section class="chip-section" style="background: #F7F3EC;">
      <div class="section-header">
        <h2 class="section-title" style="color: #8B6914;">核心投资概念</h2>
        <span class="section-sub">TOP 15</span>
      </div>
      <div class="chip-list">
        <div
          v-for="item in topConcepts"
          :key="item.id"
          class="chip"
          @click="navigateToNode(item)"
        >
          <span class="chip-name">{{ item.name }}</span>
          <span class="chip-badge" style="background: #B8922A;">{{ item.count }}</span>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════
         5. TOP 15 重要公司
    ════════════════════════════════════════════ -->
    <section class="chip-section" style="background: #F0F4EF;">
      <div class="section-header">
        <h2 class="section-title" style="color: #3D7A52;">重要公司</h2>
        <span class="section-sub">TOP 15</span>
      </div>
      <div class="chip-list">
        <div
          v-for="item in topCompanies"
          :key="item.id"
          class="chip"
          @click="navigateToNode(item)"
        >
          <span class="chip-name">{{ item.name }}</span>
          <span class="chip-badge" style="background: #47956A;">{{ item.count }}</span>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════
         6. 关键人物
    ════════════════════════════════════════════ -->
    <section class="white-card">
      <div class="section-header">
        <h2 class="section-title">关键人物</h2>
      </div>
      <div class="people-grid">
        <div
          v-for="person in people"
          :key="person.path"
          class="person-card"
          @click="navigateToPage(person)"
        >
          <div class="person-avatar" :style="{ background: avatarColor(person.title) }">
            {{ person.title[0] }}
          </div>
          <div class="person-name">{{ person.title }}</div>
          <div class="person-refs">{{ person.refCount }} 引用</div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════
         7. TIMELINE 1956-2025
    ════════════════════════════════════════════ -->
    <section class="white-card">
      <div class="section-header">
        <h2 class="section-title">时间线 1956–2025</h2>
      </div>
      <div class="timeline-container">
        <div class="timeline-track">
          <div
            v-for="(item, i) in timelineItems"
            :key="i"
            class="timeline-dot"
            :style="{
              left: item.x + '%',
              background: timelineColor(item.type),
            }"
            :title="item.title"
          >
            <div class="timeline-tooltip">{{ item.title }} ({{ item.year }})</div>
          </div>
        </div>
        <div class="timeline-axis">
          <span v-for="y in timelineYearMarks" :key="y" class="axis-label" :style="{ left: yearToX(y) + '%' }">
            {{ y }}
          </span>
        </div>
      </div>
      <div class="timeline-legend">
        <span class="legend-item">
          <span class="legend-dot" style="background:#3B7DD8"></span>合伙人时期
        </span>
        <span class="legend-item">
          <span class="legend-dot" style="background:#47956A"></span>伯克希尔时期
        </span>
        <span class="legend-item">
          <span class="legend-dot" style="background:#7E5FAD"></span>访谈演讲
        </span>
        <span class="legend-item">
          <span class="legend-dot" style="background:#E07B39"></span>特别事件
        </span>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════
         8. QUICK NAVIGATION
    ════════════════════════════════════════════ -->
    <section class="white-card">
      <div class="section-header">
        <h2 class="section-title">快速导航</h2>
      </div>
      <div class="nav-grid">
        <button class="nav-btn" @click="router.push('/category/concepts')">
          <span class="nav-icon">💡</span>核心概念
        </button>
        <button class="nav-btn" @click="router.push('/category/companies')">
          <span class="nav-icon">🏢</span>投资公司
        </button>
        <button class="nav-btn" @click="router.push('/category/people')">
          <span class="nav-icon">👤</span>关键人物
        </button>
        <button class="nav-btn" @click="router.push('/category/interviews')">
          <span class="nav-icon">🎤</span>访谈与演讲
        </button>
        <button class="nav-btn" @click="router.push('/category/letters')">
          <span class="nav-icon">📊</span>股东信
        </button>
        <button class="nav-btn" @click="router.push('/graph')">
          <span class="nav-icon">🕸️</span>知识图谱
        </button>
      </div>
    </section>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as d3 from 'd3'

const router = useRouter()

// ─── Data ────────────────────────────────────────────────────────────────────
const wikiIndex = ref([])
const graphData = ref({ nodes: [], edges: [] })

// ─── Mini graph ref ───────────────────────────────────────────────────────────
const miniGraphSvg = ref(null)
let simulation = null

// ─── Search state ─────────────────────────────────────────────────────────────
const searchQuery = ref('')
const searchFocused = ref(false)
const searchInput = ref(null)

// ─── Stats ────────────────────────────────────────────────────────────────────
const stats = computed(() => {
  const idx = wikiIndex.value
  return {
    letters: idx.filter(i => i.category === 'letters').length,
    concepts: idx.filter(i => i.category === 'concepts').length,
    companies: idx.filter(i => i.category === 'companies').length,
    interviews: idx.filter(i => i.category === 'interviews').length,
  }
})

// ─── Search results ───────────────────────────────────────────────────────────
const searchResults = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return []
  return wikiIndex.value
    .filter(i => i.title && i.title.toLowerCase().includes(q))
    .slice(0, 8)
})

// ─── Top concepts & companies (by edge count) ─────────────────────────────────
function computeTopByCategory(category, limit = 15) {
  const { nodes, edges } = graphData.value
  const relevant = nodes.filter(n => n.category === category)
  const counts = {}
  for (const n of relevant) counts[n.id] = 0
  for (const e of edges) {
    if (e.source in counts) counts[e.source]++
    if (e.target in counts) counts[e.target]++
  }
  return relevant
    .map(n => ({ ...n, count: counts[n.id] ?? 0 }))
    .sort((a, b) => b.count - a.count)
    .slice(0, limit)
}

const topConcepts = computed(() => computeTopByCategory('concepts'))
const topCompanies = computed(() => computeTopByCategory('companies'))

// ─── People ───────────────────────────────────────────────────────────────────
const people = computed(() => {
  const { edges } = graphData.value
  return wikiIndex.value
    .filter(i => i.category === 'people')
    .map(person => {
      const refCount = edges.filter(
        e => e.source === person.title || e.target === person.title
      ).length
      return { ...person, refCount }
    })
    .sort((a, b) => b.refCount - a.refCount)
})

// ─── Timeline ─────────────────────────────────────────────────────────────────
const YEAR_START = 1956
const YEAR_END = 2025

function yearToX(year) {
  return ((year - YEAR_START) / (YEAR_END - YEAR_START)) * 100
}

function getTimelineType(item) {
  if (item.category === 'interviews') return 'interview'
  if (item.category === 'letters') {
    const year = new Date(item.date).getFullYear()
    return year < 1970 ? 'partnership' : 'berkshire'
  }
  return 'special'
}

function timelineColor(type) {
  const map = {
    partnership: '#3B7DD8',
    berkshire: '#47956A',
    interview: '#7E5FAD',
    special: '#E07B39',
  }
  return map[type] ?? '#999'
}

const timelineItems = computed(() => {
  return wikiIndex.value
    .filter(i => i.category === 'letters' || i.category === 'interviews')
    .filter(i => i.date)
    .map(i => {
      const year = new Date(i.date).getFullYear()
      return {
        title: i.title,
        year,
        type: getTimelineType(i),
        x: yearToX(year),
      }
    })
    .filter(i => i.year >= YEAR_START && i.year <= YEAR_END)
})

const timelineYearMarks = [1956, 1970, 1985, 2000, 2010, 2025]

// ─── Helpers ──────────────────────────────────────────────────────────────────
function categoryColor(cat) {
  const map = {
    concepts: '#3B7DD8',
    companies: '#47956A',
    people: '#C5961B',
    interviews: '#7E5FAD',
    letters: '#C2604A',
  }
  return map[cat] ?? '#888'
}

function categoryLabel(cat) {
  const map = {
    concepts: '概念',
    companies: '公司',
    people: '人物',
    interviews: '访谈',
    letters: '信件',
  }
  return map[cat] ?? cat
}

function avatarColor(name) {
  let hash = 0
  for (let i = 0; i < name.length; i++) hash = (hash << 5) - hash + name.charCodeAt(i)
  const hue = Math.abs(hash) % 360
  return `hsl(${hue}, 55%, 48%)`
}

// ─── Navigation ───────────────────────────────────────────────────────────────
function navigateToPage(item) {
  searchFocused.value = false
  searchQuery.value = ''
  if (item.path) {
    router.push(`/page/${item.path}`)
  }
}

function navigateToNode(node) {
  // node from graph — build path from category + id
  const cat = node.category
  const id = node.id
  const wikiItem = wikiIndex.value.find(i => i.title === id)
  if (wikiItem?.path) {
    router.push(`/page/${wikiItem.path}`)
  } else {
    router.push(`/category/${cat}`)
  }
}

function clearSearch() {
  searchQuery.value = ''
  searchFocused.value = false
}

function onSearchBlur() {
  // delay so click on result fires first
  setTimeout(() => { searchFocused.value = false }, 150)
}

// ─── D3 Mini Graph ────────────────────────────────────────────────────────────
const NODE_COLOR = {
  concepts: '#3B7DD8',
  companies: '#47956A',
  people: '#C5961B',
  interviews: '#7E5FAD',
  letters: '#C2604A',
}

function initMiniGraph() {
  const svg = d3.select(miniGraphSvg.value)
  svg.selectAll('*').remove()

  const W = 240, H = 150
  const { nodes: rawNodes, edges: rawEdges } = graphData.value
  if (!rawNodes.length) return

  const nodes = rawNodes.map(d => ({ ...d }))
  const links = rawEdges
    .map(e => ({
      source: typeof e.source === 'object' ? e.source.id : e.source,
      target: typeof e.target === 'object' ? e.target.id : e.target,
    }))
    .filter(e => {
      const ids = new Set(nodes.map(n => n.id))
      return ids.has(e.source) && ids.has(e.target)
    })

  svg.attr('viewBox', `0 0 ${W} ${H}`)

  const linkSel = svg.append('g')
    .selectAll('line')
    .data(links)
    .join('line')
    .attr('stroke', 'rgba(255,255,255,0.15)')
    .attr('stroke-width', 1)

  const nodeSel = svg.append('g')
    .selectAll('circle')
    .data(nodes)
    .join('circle')
    .attr('r', d => (d.category && d.category !== 'unknown') ? 4 : 2.5)
    .attr('fill', d => NODE_COLOR[d.category] ?? '#aaa')
    .attr('opacity', 0.9)

  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).distance(30).strength(0.4))
    .force('charge', d3.forceManyBody().strength(-60))
    .force('center', d3.forceCenter(W / 2, H / 2))
    .force('collision', d3.forceCollide(6))
    .on('tick', () => {
      linkSel
        .attr('x1', d => clamp(d.source.x, 4, W - 4))
        .attr('y1', d => clamp(d.source.y, 4, H - 4))
        .attr('x2', d => clamp(d.target.x, 4, W - 4))
        .attr('y2', d => clamp(d.target.y, 4, H - 4))
      nodeSel
        .attr('cx', d => { d.x = clamp(d.x, 4, W - 4); return d.x })
        .attr('cy', d => { d.y = clamp(d.y, 4, H - 4); return d.y })
    })

  setTimeout(() => { if (simulation) simulation.stop() }, 4000)
}

function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v))
}

// ─── Lifecycle ────────────────────────────────────────────────────────────────
onMounted(async () => {
  try {
    const [idxRes, graphRes] = await Promise.all([
      fetch('/data/wiki-index.json'),
      fetch('/data/graph.json'),
    ])
    wikiIndex.value = await idxRes.json()
    graphData.value = await graphRes.json()
    // init mini graph after data loads
    initMiniGraph()
  } catch (e) {
    console.error('Failed to load data:', e)
  }
})

onBeforeUnmount(() => {
  if (simulation) {
    simulation.stop()
    simulation = null
  }
})
</script>

<style scoped>
/* ── Layout ───────────────────────────────────────────────────────────────── */
.home {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px 20px 48px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* ── Hero ─────────────────────────────────────────────────────────────────── */
.hero {
  background: linear-gradient(135deg, #191D2B 0%, #252D45 100%);
  border-radius: 16px;
  padding: 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 32px;
}

.hero-left {
  flex: 1;
  min-width: 0;
}

.hero-title {
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 10px;
  line-height: 1.3;
}

.hero-subtitle {
  font-size: 13px;
  color: #8E9FC0;
  margin: 0 0 28px;
  line-height: 1.6;
}

.hero-btns {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border-radius: 22px;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  border: none;
  transition: opacity 0.2s, transform 0.2s;
  white-space: nowrap;
}

.btn:hover {
  opacity: 0.88;
  transform: translateY(-1px);
}

.btn-gold {
  background: #C5961B;
  color: #1A1200;
}

.btn-ghost {
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
  border: 1.5px solid rgba(255, 255, 255, 0.4);
}

.hero-right {
  flex-shrink: 0;
}

.mini-graph {
  display: block;
  background: transparent;
  border-radius: 8px;
}

/* ── Stat Cards ───────────────────────────────────────────────────────────── */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.07);
  border-top: 3px solid var(--card-accent, #999);
  padding: 18px 20px 16px;
  cursor: pointer;
  transition: transform 0.18s, box-shadow 0.18s;
  user-select: none;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.12);
}

.stat-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.stat-icon {
  font-size: 22px;
  line-height: 1;
}

.stat-number {
  font-size: 30px;
  font-weight: 700;
  color: #1A2340;
  line-height: 1;
}

.stat-label {
  font-size: 13px;
  color: #7A849A;
  font-weight: 500;
}

/* ── Search ───────────────────────────────────────────────────────────────── */
.search-card {
  position: relative;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.07);
  padding: 14px 18px;
}

.search-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #F2F2F4;
  border-radius: 8px;
  padding: 8px 14px;
}

.search-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-size: 14px;
  color: #1A2340;
  caret-color: #3B7DD8;
}

.search-input::placeholder {
  color: #AAACB5;
}

.search-wrap:focus-within {
  outline: 2px solid #3B7DD8;
  outline-offset: -2px;
}

.search-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.14);
  z-index: 100;
  overflow: hidden;
}

.search-result-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 18px;
  cursor: pointer;
  transition: background 0.12s;
}

.search-result-item:hover {
  background: #F4F6FF;
}

.result-title {
  font-size: 14px;
  color: #1A2340;
  font-weight: 500;
}

.result-badge {
  font-size: 11px;
  color: #fff;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
  flex-shrink: 0;
}

/* ── Chip Sections ────────────────────────────────────────────────────────── */
.chip-section {
  border-radius: 16px;
  padding: 28px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.section-title {
  font-size: 22px;
  font-weight: 700;
  margin: 0;
  color: #1A2340;
}

.section-sub {
  font-size: 12px;
  color: #999;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #fff;
  border: 1.5px solid #E0DCD5;
  border-radius: 22px;
  padding: 8px 16px;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
  user-select: none;
}

.chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.chip-name {
  font-size: 14px;
  font-weight: 500;
  color: #1A2340;
}

.chip-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  border-radius: 11px;
  height: 22px;
  min-width: 22px;
  padding: 0 5px;
}

/* ── White card ───────────────────────────────────────────────────────────── */
.white-card {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.07);
  padding: 28px;
}

/* ── People grid ──────────────────────────────────────────────────────────── */
.people-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 16px;
}

.person-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 18px 12px;
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.18s, background 0.18s;
}

.person-card:hover {
  transform: translateY(-3px);
  background: #EEF4FF;
}

.person-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 20px;
  font-weight: 700;
  flex-shrink: 0;
}

.person-name {
  font-size: 14px;
  font-weight: 600;
  color: #1A2340;
  text-align: center;
  line-height: 1.3;
}

.person-refs {
  font-size: 11px;
  color: #999;
}

/* ── Timeline ─────────────────────────────────────────────────────────────── */
.timeline-container {
  position: relative;
  width: 100%;
  height: 80px;
  margin-bottom: 28px;
}

.timeline-track {
  position: relative;
  width: 100%;
  height: 40px;
  background: #F5F6FA;
  border-radius: 4px;
  overflow: visible;
}

.timeline-track::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 2px;
  background: #DDE2EC;
  transform: translateY(-50%);
}

.timeline-dot {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 8px;
  height: 8px;
  border-radius: 50%;
  cursor: pointer;
  transition: transform 0.15s;
}

.timeline-dot:hover {
  transform: translate(-50%, -50%) scale(2);
  z-index: 10;
}

.timeline-dot:hover .timeline-tooltip {
  display: block;
}

.timeline-tooltip {
  display: none;
  position: absolute;
  bottom: 14px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(20, 25, 45, 0.9);
  color: #fff;
  font-size: 11px;
  white-space: nowrap;
  padding: 4px 8px;
  border-radius: 6px;
  pointer-events: none;
  z-index: 20;
}

.timeline-axis {
  position: relative;
  width: 100%;
  height: 20px;
  margin-top: 6px;
}

.axis-label {
  position: absolute;
  transform: translateX(-50%);
  font-size: 11px;
  color: #AAB0BF;
  user-select: none;
}

.timeline-legend {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #666;
}

.legend-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* ── Quick Navigation ─────────────────────────────────────────────────────── */
.nav-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.nav-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  background: #F5F6FA;
  border: 1.5px solid transparent;
  border-radius: 10px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  color: #1A2340;
  transition: border-color 0.18s, transform 0.18s, background 0.18s;
  text-align: left;
}

.nav-btn:hover {
  border-color: #3B7DD8;
  transform: translateY(-2px);
  background: #EEF4FF;
}

.nav-icon {
  font-size: 20px;
  flex-shrink: 0;
}

/* ── Responsive ───────────────────────────────────────────────────────────── */
@media (max-width: 720px) {
  .hero {
    flex-direction: column;
    padding: 32px 24px;
  }

  .hero-right {
    width: 100%;
    text-align: center;
  }

  .mini-graph {
    width: 100%;
    max-width: 300px;
  }

  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .nav-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .nav-grid {
    grid-template-columns: 1fr 1fr;
  }

  .hero-title {
    font-size: 20px;
  }
}
</style>
