import express from 'express'
import cors from 'cors'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import { spawn } from 'child_process'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// ── Startup Data Preload ─────────────────────────────────────────────────────

const wikiIndex = JSON.parse(fs.readFileSync('public/data/wiki-index.json', 'utf-8'))
const graphData = JSON.parse(fs.readFileSync('public/data/graph.json', 'utf-8'))

// Map: title → page object
const indexByTitle = new Map()
for (const page of wikiIndex) {
  indexByTitle.set(page.title, page)
}

// Map: node name → Set of neighbor names (bidirectional)
const neighbors = new Map()
for (const edge of graphData.edges) {
  const { source, target } = edge
  if (!neighbors.has(source)) neighbors.set(source, new Set())
  if (!neighbors.has(target)) neighbors.set(target, new Set())
  neighbors.get(source).add(target)
  neighbors.get(target).add(source)
}

// ── Claude CLI path ─────────────────────────────────────────────────────────

const CLAUDE_BIN = process.env.CLAUDE_BIN || 'claude'

// ── Retrieval Helpers ────────────────────────────────────────────────────────

function generateNgrams(text, minN = 2, maxN = 4) {
  const ngrams = new Set()
  // Chinese character sliding window
  for (let n = minN; n <= maxN; n++) {
    for (let i = 0; i <= text.length - n; i++) {
      ngrams.add(text.slice(i, i + n))
    }
  }
  // Keep space-separated complete words (for English)
  text.split(/\s+/).forEach(word => {
    if (word.length >= 2) ngrams.add(word.toLowerCase())
  })
  return ngrams
}

function scorePages(question, pages) {
  const ngrams = generateNgrams(question)
  const scores = []

  for (const page of pages) {
    let score = 0
    const title = page.title
    const summary = page.summary || ''
    const links = page.links || []

    // Title fully contained in question → +50
    if (question.includes(title)) score += 50

    // Question contained in title → +40
    if (title.includes(question)) score += 40

    // Ngram hits
    for (const ng of ngrams) {
      if (title.includes(ng)) score += 8
      if (summary.includes(ng)) score += 3
    }

    // Links keyword hits question → +6
    for (const link of links) {
      if (question.includes(link)) score += 6
    }

    if (score > 0) scores.push({ page, score })
  }

  return scores.sort((a, b) => b.score - a.score)
}

function retrievePages(question) {
  // Phase 1: Direct matching
  const directHits = scorePages(question, wikiIndex)
  const top4 = directHits.slice(0, 4)

  // Phase 2: Graph expansion
  const includedTitles = new Set(top4.map(h => h.page.title))
  const candidateNeighbors = []

  for (const hit of top4) {
    const neighborSet = neighbors.get(hit.page.title) || new Set()
    for (const neighborName of neighborSet) {
      if (includedTitles.has(neighborName)) continue
      const neighborPage = indexByTitle.get(neighborName)
      if (!neighborPage) continue
      candidateNeighbors.push(neighborPage)
    }
  }

  // Score neighbors against the question, only keep those with score > 0
  const neighborScores = scorePages(question, candidateNeighbors)
    .filter(h => h.score > 0)
    .slice(0, 2)

  for (const hit of neighborScores) {
    if (!includedTitles.has(hit.page.title)) {
      top4.push(hit)
      includedTitles.add(hit.page.title)
    }
  }

  return top4.map(h => h.page)
}

function buildContext(matchedPages) {
  const parts = []
  for (const page of matchedPages) {
    const mdPath = path.join(__dirname, 'public', 'data', 'pages', `${page.category}`, `${path.basename(page.path)}.md`)
    let content = ''
    try {
      const raw = fs.readFileSync(mdPath, 'utf-8')
      content = raw.slice(0, 3000)
    } catch {
      // Fall back to summary if file is missing
      content = page.summary || ''
    }
    parts.push(`## ${page.title}\n\n${content}`)
  }
  return parts.join('\n\n---\n\n')
}

// ── Express App ──────────────────────────────────────────────────────────────

const app = express()

app.use(cors())
app.use(express.json())
app.use(express.static(path.join(__dirname, 'public')))

// ── POST /api/verify-password ────────────────────────────────────────────────

app.post('/api/verify-password', (req, res) => {
  const { password } = req.body
  const valid = password === process.env.ACCESS_PASSWORD
  res.json({ valid })
})

// ── POST /api/chat (SSE Streaming) ───────────────────────────────────────────

app.post('/api/chat', async (req, res) => {
  // Password check
  const providedPassword = req.headers['x-password']
  if (providedPassword !== process.env.ACCESS_PASSWORD) {
    return res.status(401).json({ error: 'Unauthorized' })
  }

  const { message, history = [] } = req.body
  if (!message) {
    return res.status(400).json({ error: 'Missing message' })
  }

  // Retrieval
  const matchedPages = retrievePages(message)
  const context = buildContext(matchedPages)

  const systemPrompt = `你是"AI 巴菲特"，一个基于沃伦·巴菲特投资思想知识库的智能助手。

你的知识来源于巴菲特的股东信、合伙人信、访谈和演讲的结构化摘要。请基于以下知识库内容回答用户的问题。

回答要求：
1. 以巴菲特的视角和风格回答，引用他的原话和理念
2. 引用具体的信件、访谈或概念来支持你的回答
3. 使用通俗易懂的语言，就像巴菲特在股东大会上解释问题一样
4. 如果知识库中没有直接相关的内容，坦诚说明，不要编造
5. 回答要有深度但不冗长，重点突出

以下是与问题相关的知识库内容：

${context}
`

  // Build full prompt: system + history + user question
  let fullPrompt = systemPrompt + '\n\n'
  for (const msg of history) {
    const role = msg.role === 'user' ? '用户' : 'AI巴菲特'
    fullPrompt += `${role}：${msg.content}\n\n`
  }
  fullPrompt += `用户：${message}`

  // SSE headers
  res.setHeader('Content-Type', 'text/event-stream')
  res.setHeader('Cache-Control', 'no-cache')
  res.setHeader('Connection', 'keep-alive')

  try {
    // Spawn claude CLI with --print flag (uses your local Claude subscription)
    const proc = spawn(CLAUDE_BIN, ['--print', '--output-format', 'text', fullPrompt], {
      env: { ...process.env, NO_COLOR: '1' },
      stdio: ['ignore', 'pipe', 'pipe'],
    })

    proc.stdout.on('data', (chunk) => {
      const text = chunk.toString()
      if (text) {
        res.write(`data: ${JSON.stringify({ text })}\n\n`)
      }
    })

    proc.stderr.on('data', (chunk) => {
      console.error('claude stderr:', chunk.toString())
    })

    proc.on('close', (code) => {
      if (code !== 0) {
        console.error(`claude exited with code ${code}`)
      }
      const sourceNames = matchedPages.map(p => p.title)
      res.write(`data: ${JSON.stringify({ done: true, sources: sourceNames })}\n\n`)
      res.end()
    })

    proc.on('error', (error) => {
      console.error('claude spawn error:', error)
      res.write(`data: ${JSON.stringify({ text: `无法启动 claude CLI：${error.message}` })}\n\n`)
      res.write(`data: ${JSON.stringify({ done: true, sources: [] })}\n\n`)
      res.end()
    })
  } catch (error) {
    console.error('Chat error:', error)
    res.write(`data: ${JSON.stringify({ text: `错误：${error.message}` })}\n\n`)
    res.write(`data: ${JSON.stringify({ done: true, sources: [] })}\n\n`)
    res.end()
  }
})

// ── Start ────────────────────────────────────────────────────────────────────

app.listen(3001, () => {
  console.log('Server running on http://localhost:3001')
  console.log(`Loaded ${wikiIndex.length} wiki pages, ${graphData.nodes.length} graph nodes`)
})
