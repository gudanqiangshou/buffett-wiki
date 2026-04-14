<template>
  <!-- PASSWORD GATE -->
  <div v-if="!authenticated" class="gate-wrapper">
    <div class="gate-card">
      <div class="gate-icon">🔐</div>
      <h2 class="gate-title">访问密码</h2>
      <p class="gate-subtitle">请输入密码以访问 AI 巴菲特</p>
      <input
        v-model="passwordInput"
        type="password"
        class="gate-input"
        placeholder="请输入密码"
        @keydown.enter="submitPassword"
      />
      <p v-if="authError" class="gate-error">{{ authError }}</p>
      <button class="gate-btn" @click="submitPassword" :disabled="authLoading">
        {{ authLoading ? '验证中...' : '确认进入' }}
      </button>
    </div>
  </div>

  <!-- CHAT INTERFACE -->
  <div v-else class="chat-page">
    <!-- Hero -->
    <div class="hero">
      <h1 class="hero-title">🎩 AI 巴菲特</h1>
      <p class="hero-subtitle">基于巴菲特知识库的智能对话</p>
    </div>

    <!-- Messages Area -->
    <div class="messages-area" ref="messagesArea">
      <!-- Empty State -->
      <div v-if="messages.length === 0" class="empty-state">
        <div class="empty-icon">🎩</div>
        <p class="empty-text">我是 AI 巴菲特，基于巴菲特的信件、访谈和投资理念为您解答</p>
        <div class="sample-chips">
          <button
            v-for="q in sampleQuestions"
            :key="q"
            class="chip"
            @click="sendMessage(q)"
          >{{ q }}</button>
        </div>
      </div>

      <!-- Messages List -->
      <div
        v-for="(msg, idx) in messages"
        :key="idx"
        class="message-row"
        :class="msg.role === 'user' ? 'message-row--user' : 'message-row--ai'"
      >
        <!-- AI message -->
        <template v-if="msg.role === 'assistant'">
          <div class="avatar avatar--ai">🎩</div>
          <div class="bubble bubble--ai">
            <span v-if="msg.loading" class="thinking">思考中...</span>
            <div v-else class="md-content" v-html="renderMarkdown(msg.content)"></div>
            <!-- Sources -->
            <div v-if="!msg.loading && msg.sources && msg.sources.length > 0" class="sources">
              <span class="sources-label">📚 参考来源:</span>
              <a
                v-for="(src, si) in msg.sources"
                :key="si"
                :href="src.url || '#'"
                class="source-link"
                target="_blank"
                rel="noopener noreferrer"
              >{{ src.title || src.page || src }}</a>
            </div>
          </div>
        </template>

        <!-- User message -->
        <template v-else>
          <div class="bubble bubble--user">{{ msg.content }}</div>
          <div class="avatar avatar--user">👤</div>
        </template>
      </div>
    </div>

    <!-- Input Area -->
    <div class="input-area">
      <input
        v-model="inputText"
        type="text"
        class="chat-input"
        placeholder="向 AI 巴菲特 提问..."
        :disabled="streaming"
        @keydown.enter.exact="handleEnter"
      />
      <button
        class="send-btn"
        :disabled="streaming || !inputText.trim()"
        @click="handleSend"
      >发送</button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import MarkdownIt from 'markdown-it'

const router = useRouter()
const md = new MarkdownIt({ linkify: true, breaks: true })

// ── Auth state ──────────────────────────────────────────────
const authenticated = ref(false)
const passwordInput = ref('')
const authError = ref('')
const authLoading = ref(false)

onMounted(() => {
  if (sessionStorage.getItem('chat-auth') === 'true') {
    authenticated.value = true
  }
})

async function submitPassword() {
  if (!passwordInput.value.trim()) return
  authLoading.value = true
  authError.value = ''
  try {
    const res = await fetch('/api/verify-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: passwordInput.value })
    })
    const data = await res.json()
    if (data.valid === true) {
      sessionStorage.setItem('chat-auth', 'true')
      sessionStorage.setItem('chat-password', passwordInput.value)
      authenticated.value = true
    } else {
      authError.value = '密码错误，请重试'
    }
  } catch {
    // Backend not running (e.g. GitHub Pages) — show hint
    authError.value = 'AI 聊天需要在本地运行后端服务（node server.js），公网版暂不支持此功能'
  } finally {
    authLoading.value = false
  }
}

// ── Chat state ───────────────────────────────────────────────
const messages = ref([])
const inputText = ref('')
const streaming = ref(false)
const messagesArea = ref(null)

const sampleQuestions = [
  '什么是安全边际？',
  '巴菲特为什么投资可口可乐？',
  '如何评估企业的护城河？',
  '查理·芒格的投资哲学是什么？'
]

function renderMarkdown(text) {
  return md.render(text || '')
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesArea.value) {
      messagesArea.value.scrollTop = messagesArea.value.scrollHeight
    }
  })
}

function handleEnter(e) {
  if (!streaming.value && inputText.value.trim()) {
    handleSend()
  }
}

function handleSend() {
  const text = inputText.value.trim()
  if (!text || streaming.value) return
  inputText.value = ''
  sendMessage(text)
}

async function sendMessage(text) {
  streaming.value = true

  // Add user message
  messages.value.push({ role: 'user', content: text })

  // Add placeholder AI message
  const aiIdx = messages.value.length
  messages.value.push({ role: 'assistant', content: '', sources: [], loading: true })

  scrollToBottom()

  // Build conversation history (last 10 messages before the placeholder)
  const history = messages.value.slice(0, -1).slice(-10).map(m => ({
    role: m.role,
    content: m.content
  }))

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Password': sessionStorage.getItem('chat-password') || ''
      },
      body: JSON.stringify({ message: text, history })
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() // keep incomplete line

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        let data
        try {
          data = JSON.parse(line.slice(6))
        } catch {
          continue
        }

        if (data.done) {
          // Final message with sources
          messages.value[aiIdx] = {
            ...messages.value[aiIdx],
            sources: data.sources || [],
            loading: false
          }
        } else if (data.text) {
          // Streaming text chunk
          messages.value[aiIdx] = {
            ...messages.value[aiIdx],
            content: messages.value[aiIdx].content + data.text,
            loading: false
          }
        }
        scrollToBottom()
      }
    }
  } catch (err) {
    messages.value[aiIdx] = {
      ...messages.value[aiIdx],
      content: `请求失败：${err.message}`,
      sources: [],
      loading: false
    }
  } finally {
    streaming.value = false
    scrollToBottom()
  }
}
</script>

<style scoped>
/* ── Password Gate ──────────────────────────────────────── */
.gate-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary, #f5f5f0);
}

.gate-card {
  background: #fff;
  border-radius: 20px;
  padding: 48px;
  max-width: 400px;
  width: 100%;
  margin: auto;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.gate-icon {
  font-size: 48px;
  line-height: 1;
}

.gate-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary, #1a1a1a);
  margin: 0;
  text-align: center;
}

.gate-subtitle {
  font-size: 14px;
  color: #888;
  margin: 0;
  text-align: center;
}

.gate-input {
  width: 100%;
  box-sizing: border-box;
  background: #f2f2f0;
  border: none;
  border-radius: 12px;
  padding: 14px;
  font-size: 16px;
  text-align: center;
  letter-spacing: 2px;
  outline: none;
  margin-top: 8px;
  transition: box-shadow 0.2s;
}

.gate-input:focus {
  box-shadow: 0 0 0 2px var(--accent, #3B7DD8);
}

.gate-error {
  color: #C2604A;
  font-size: 13px;
  margin: 0;
}

.gate-btn {
  width: 100%;
  background: var(--accent, #3B7DD8);
  color: #fff;
  border: none;
  border-radius: 12px;
  padding: 14px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 4px;
  transition: opacity 0.2s;
}

.gate-btn:hover:not(:disabled) {
  opacity: 0.88;
}

.gate-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

/* ── Chat Page Layout ────────────────────────────────────── */
.chat-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--bg-primary, #f5f5f0);
}

/* ── Hero ────────────────────────────────────────────────── */
.hero {
  background: linear-gradient(135deg, #1a2a4a 0%, #2c4a7a 100%);
  padding: 32px 24px 28px;
  text-align: center;
}

.hero-title {
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 6px;
}

.hero-subtitle {
  font-size: 13px;
  color: #9ab4d8;
  margin: 0;
}

/* ── Messages Area ───────────────────────────────────────── */
.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: calc(100vh - 350px);
}

/* ── Empty State ─────────────────────────────────────────── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80px 24px;
  gap: 16px;
}

.empty-icon {
  font-size: 64px;
  line-height: 1;
}

.empty-text {
  font-size: 15px;
  color: #888;
  text-align: center;
  max-width: 480px;
  margin: 0;
}

.sample-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  margin-top: 8px;
}

.chip {
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 20px;
  padding: 8px 18px;
  font-size: 14px;
  color: var(--text-primary, #1a1a1a);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.chip:hover {
  background: var(--accent, #3B7DD8);
  border-color: var(--accent, #3B7DD8);
  color: #fff;
}

/* ── Message Rows ────────────────────────────────────────── */
.message-row {
  display: flex;
  align-items: flex-end;
  gap: 10px;
}

.message-row--user {
  flex-direction: row-reverse;
}

.message-row--ai {
  flex-direction: row;
}

/* ── Avatars ─────────────────────────────────────────────── */
.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.avatar--ai {
  background: #e8edf5;
}

.avatar--user {
  background: #d0e0f5;
}

/* ── Bubbles ─────────────────────────────────────────────── */
.bubble {
  max-width: 75%;
  padding: 12px 18px;
  font-size: 15px;
  line-height: 1.6;
  word-break: break-word;
}

.bubble--user {
  background: var(--accent, #3B7DD8);
  color: #fff;
  border-radius: 18px 18px 6px 18px;
}

.bubble--ai {
  background: var(--bg-secondary, #ececea);
  color: var(--text-primary, #1a1a1a);
  border-radius: 18px 18px 18px 6px;
}

/* ── Thinking animation ──────────────────────────────────── */
.thinking {
  color: #999;
  font-style: italic;
  animation: pulse 1.4s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.35; }
}

/* ── Markdown content ────────────────────────────────────── */
.md-content :deep(p) {
  margin: 0 0 8px;
}
.md-content :deep(p:last-child) {
  margin-bottom: 0;
}
.md-content :deep(ul),
.md-content :deep(ol) {
  margin: 6px 0 8px 20px;
  padding: 0;
}
.md-content :deep(li) {
  margin-bottom: 4px;
}
.md-content :deep(strong) {
  font-weight: 700;
}
.md-content :deep(code) {
  background: rgba(0,0,0,0.07);
  border-radius: 4px;
  padding: 2px 5px;
  font-size: 13px;
  font-family: monospace;
}
.md-content :deep(pre) {
  background: rgba(0,0,0,0.07);
  border-radius: 8px;
  padding: 12px;
  overflow-x: auto;
  margin: 8px 0;
}
.md-content :deep(pre code) {
  background: none;
  padding: 0;
}
.md-content :deep(blockquote) {
  border-left: 3px solid #aaa;
  margin: 8px 0;
  padding-left: 12px;
  color: #666;
}

/* ── Sources ─────────────────────────────────────────────── */
.sources {
  margin-top: 10px;
  font-size: 12px;
  color: #888;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.sources-label {
  color: #888;
}

.source-link {
  color: var(--accent, #3B7DD8);
  text-decoration: none;
  background: rgba(59, 125, 216, 0.08);
  border-radius: 6px;
  padding: 2px 8px;
  font-size: 12px;
  transition: background 0.15s;
}

.source-link:hover {
  background: rgba(59, 125, 216, 0.18);
}

/* ── Input Area ──────────────────────────────────────────── */
.input-area {
  display: flex;
  gap: 10px;
  padding: 16px 24px 24px;
  background: var(--bg-primary, #f5f5f0);
  border-top: 1px solid rgba(0,0,0,0.06);
  position: sticky;
  bottom: 0;
}

.chat-input {
  flex: 1;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 22px;
  padding: 12px 20px;
  font-size: 15px;
  outline: none;
  transition: border-color 0.2s;
}

.chat-input:focus {
  border-color: var(--accent, #3B7DD8);
}

.chat-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.send-btn {
  background: var(--accent, #3B7DD8);
  color: #fff;
  border: none;
  border-radius: 22px;
  padding: 12px 24px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  flex-shrink: 0;
  transition: opacity 0.2s;
}

.send-btn:hover:not(:disabled) {
  opacity: 0.88;
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
