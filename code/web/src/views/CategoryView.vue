<template>
  <div class="category-view">
    <!-- Breadcrumb -->
    <nav class="breadcrumb">
      <router-link to="/">首页</router-link>
      <span class="sep">›</span>
      <span class="current">{{ categoryName }}</span>
    </nav>

    <!-- Header -->
    <header class="category-header">
      <h1 class="category-title">{{ categoryName }}</h1>
      <p class="category-count" v-if="!loading">共 {{ filteredItems.length }} 篇</p>
    </header>

    <!-- Search Box -->
    <div class="search-box">
      <span class="search-icon">🔍</span>
      <input
        v-model="query"
        type="text"
        class="search-input"
        placeholder="搜索标题或摘要…"
        autocomplete="off"
      />
    </div>

    <!-- Loading / Error -->
    <div v-if="loading" class="state-msg">加载中…</div>
    <div v-else-if="error" class="state-msg error">{{ error }}</div>

    <!-- Page List -->
    <template v-else>
      <div v-if="filteredItems.length === 0" class="state-msg">
        没有找到匹配的页面
      </div>

      <ul v-else class="page-list">
        <li
          v-for="item in filteredItems"
          :key="item.path"
          class="page-item"
        >
          <router-link
            :to="`/page/${item.category}/${encodeURIComponent(itemSlug(item))}`"
            class="page-link"
          >
            <span class="page-title">{{ item.title }}</span>
            <span class="page-date">{{ item.date || '' }}</span>
          </router-link>
        </li>
      </ul>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

// ── State ─────────────────────────────────────────────────────────────────────
const loading = ref(true)
const error = ref(null)
const allItems = ref([])
const query = ref('')

// ── Category helpers ──────────────────────────────────────────────────────────
const CATEGORY_NAMES = {
  concepts:   '核心概念',
  companies:  '投资公司',
  people:     '关键人物',
  interviews: '访谈与演讲',
  letters:    '股东信',
}

const categoryName = computed(
  () => CATEGORY_NAMES[route.params.type] || route.params.type
)

// ── Derive slug from item path ────────────────────────────────────────────────
function itemSlug(item) {
  if (item.path) {
    const parts = item.path.split('/')
    return parts.slice(1).join('/') || item.title
  }
  return item.title
}

// ── Filtered + sorted items ───────────────────────────────────────────────────
const categoryItems = computed(() =>
  allItems.value.filter(item => item.category === route.params.type)
)

const sortedItems = computed(() =>
  [...categoryItems.value].sort((a, b) => {
    const da = a.date || ''
    const db = b.date || ''
    return db.localeCompare(da)
  })
)

const filteredItems = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return sortedItems.value
  return sortedItems.value.filter(item => {
    const inTitle   = (item.title   || '').toLowerCase().includes(q)
    const inSummary = (item.summary || '').toLowerCase().includes(q)
    return inTitle || inSummary
  })
})

// ── Data loading ──────────────────────────────────────────────────────────────
async function loadCategory() {
  loading.value = true
  error.value = null
  query.value = ''

  try {
    const res = await fetch('/data/wiki-index.json')
    if (!res.ok) throw new Error('无法加载 wiki-index.json')
    allItems.value = await res.json()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(loadCategory)
watch(() => route.params.type, loadCategory)
</script>

<style scoped>
/* ── Layout ─────────────────────────────────────────────────────────────────── */
.category-view {
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
}
.breadcrumb a {
  color: #5b8dd9;
  text-decoration: none;
}
.breadcrumb a:hover { text-decoration: underline; }
.breadcrumb .sep { color: #bbb; }
.breadcrumb .current { color: #555; }

/* ── Category header ─────────────────────────────────────────────────────────── */
.category-header {
  margin-bottom: 24px;
}

.category-title {
  font-size: 28px;
  font-weight: 700;
  color: #1a2540;
  margin: 0 0 4px;
}

.category-count {
  font-size: 13px;
  color: #9ca3af;
  margin: 0;
}

/* ── Search box ─────────────────────────────────────────────────────────────── */
.search-box {
  display: flex;
  align-items: center;
  background: #f3f4f6;
  border-radius: 10px;
  padding: 10px 14px;
  gap: 8px;
  margin-bottom: 20px;
  border: 1px solid transparent;
  transition: border-color 0.15s, background 0.15s;
}
.search-box:focus-within {
  background: #fff;
  border-color: #93c5fd;
}

.search-icon {
  font-size: 15px;
  flex-shrink: 0;
  user-select: none;
}

.search-input {
  border: none;
  background: transparent;
  outline: none;
  font-size: 14px;
  color: #374151;
  width: 100%;
}
.search-input::placeholder { color: #9ca3af; }

/* ── State messages ──────────────────────────────────────────────────────────── */
.state-msg {
  text-align: center;
  padding: 60px 20px;
  color: #888;
  font-size: 15px;
}
.state-msg.error { color: #c0392b; }

/* ── Page list ───────────────────────────────────────────────────────────────── */
.page-list {
  list-style: none;
  margin: 0;
  padding: 0;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.page-item {
  border-bottom: 1px solid #f0f2f7;
}
.page-item:last-child { border-bottom: none; }

.page-link {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  text-decoration: none;
  color: inherit;
  transition: background 0.15s, transform 0.15s;
  gap: 16px;
}
.page-link:hover {
  background: #F0F7FF;
  transform: translateX(4px);
}

.page-title {
  font-size: 15px;
  font-weight: 500;
  color: #1a2540;
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.page-link:hover .page-title { color: #2563eb; }

.page-date {
  font-size: 12px;
  color: #9ca3af;
  flex-shrink: 0;
  white-space: nowrap;
}
</style>
