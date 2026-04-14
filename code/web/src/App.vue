<template>
  <div class="app-layout">
    <!-- ── Sidebar ── -->
    <aside class="sidebar">
      <!-- Logo -->
      <div class="sidebar-logo">
        <span class="logo-icon">📚</span>
        <span>Tina-巴菲特知识库</span>
      </div>

      <!-- Scrollable nav -->
      <nav class="sidebar-nav">
        <!-- 首页 -->
        <router-link
          to="/"
          class="nav-item"
          :class="{ active: $route.path === '/' }"
        >
          <span class="nav-icon">🏠</span>
          <span class="nav-text">知识库首页</span>
        </router-link>

        <!-- 索引 -->
        <div class="nav-label">索引</div>

        <router-link
          to="/category/concepts"
          class="nav-item"
          :class="{ active: $route.path === '/category/concepts' }"
        >
          <span class="nav-icon">💡</span>
          <span class="nav-text">核心概念</span>
          <span v-if="counts.concepts" class="nav-count">{{ counts.concepts }}</span>
        </router-link>

        <router-link
          to="/category/companies"
          class="nav-item"
          :class="{ active: $route.path === '/category/companies' }"
        >
          <span class="nav-icon">🏢</span>
          <span class="nav-text">投资公司</span>
          <span v-if="counts.companies" class="nav-count">{{ counts.companies }}</span>
        </router-link>

        <router-link
          to="/category/people"
          class="nav-item"
          :class="{ active: $route.path === '/category/people' }"
        >
          <span class="nav-icon">👤</span>
          <span class="nav-text">关键人物</span>
          <span v-if="counts.people" class="nav-count">{{ counts.people }}</span>
        </router-link>

        <!-- 来源 -->
        <div class="nav-label">来源</div>

        <router-link
          to="/category/interviews"
          class="nav-item"
          :class="{ active: $route.path === '/category/interviews' }"
        >
          <span class="nav-icon">🎤</span>
          <span class="nav-text">访谈与演讲</span>
          <span v-if="counts.interviews" class="nav-count">{{ counts.interviews }}</span>
        </router-link>

        <router-link
          to="/category/letters"
          class="nav-item"
          :class="{ active: $route.path === '/category/letters' }"
        >
          <span class="nav-icon">✉️</span>
          <span class="nav-text">股东信</span>
          <span v-if="counts.letters" class="nav-count">{{ counts.letters }}</span>
        </router-link>

        <!-- 工具 -->
        <div class="nav-label">工具</div>

        <router-link
          to="/graph"
          class="nav-item"
          :class="{ active: $route.path === '/graph' }"
        >
          <span class="nav-icon">🕸️</span>
          <span class="nav-text">知识图谱</span>
        </router-link>
      </nav>

      <!-- Bottom: AI chat button -->
      <div class="sidebar-bottom">
        <router-link to="/chat" class="ai-chat-btn">
          <span class="btn-icon">🧑‍💼</span>
          <span class="btn-text">AI 巴菲特</span>
          <span class="badge-new">NEW</span>
        </router-link>
      </div>
    </aside>

    <!-- ── Main Content ── -->
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const counts = ref({
  concepts: null,
  companies: null,
  people: null,
  interviews: null,
  letters: null
})

onMounted(async () => {
  try {
    const res = await fetch(`${import.meta.env.BASE_URL}data/wiki-index.json`)
    if (!res.ok) return
    const data = await res.json()

    // Support both flat {concepts: 42} and nested {categories: {concepts: 42}}
    const cats = data.categories ?? data
    counts.value = {
      concepts:   cats.concepts   ?? null,
      companies:  cats.companies  ?? null,
      people:     cats.people     ?? null,
      interviews: cats.interviews ?? null,
      letters:    cats.letters    ?? null
    }
  } catch {
    // Index not yet built — counts remain hidden
  }
})
</script>
