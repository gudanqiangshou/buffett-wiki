<template>
  <div class="graph-page">
    <!-- Hero Area -->
    <div class="hero">
      <h1 class="hero-title">知识图谱</h1>
      <p class="hero-stats">{{ nodeCount }} 个节点 · {{ edgeCount }} 条连接</p>
    </div>

    <!-- Legend Bar -->
    <div class="legend-bar">
      <div class="legend-item" v-for="item in legendItems" :key="item.label">
        <span class="legend-dot" :style="{ background: item.color }"></span>
        <span class="legend-label">{{ item.label }}</span>
      </div>
    </div>

    <!-- Graph Container -->
    <div class="graph-card" ref="containerRef">
      <svg ref="svgRef" class="graph-svg"></svg>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import * as d3 from 'd3'

const router = useRouter()

const containerRef = ref(null)
const svgRef = ref(null)

const graphData = ref({ nodes: [], edges: [] })
const wikiIndex = ref([])

const nodeCount = computed(() => graphData.value.nodes.length)
const edgeCount = computed(() => graphData.value.edges.length)

const legendItems = [
  { color: '#3B7DD8', label: '概念' },
  { color: '#47956A', label: '公司' },
  { color: '#C5961B', label: '人物' },
  { color: '#7E5FAD', label: '访谈' },
  { color: '#C2604A', label: '信件' },
  { color: '#9B9B9B', label: '其他' },
]

function getNodeColor(node) {
  const colors = {
    concepts: '#3B7DD8',
    companies: '#47956A',
    people: '#C5961B',
    interviews: '#7E5FAD',
    letters: '#C2604A',
  }
  return colors[node.category] || '#9B9B9B'
}

function getNodeRadius(node) {
  return node.category === 'unknown' || !node.category ? 3 : 6
}

let simulation = null
let resizeObserver = null
let svgSelection = null
let gSelection = null
let linkSelection = null
let nodeSelection = null
let labelSelection = null

function buildGraph(nodes, edges, width, height) {
  const svg = d3.select(svgRef.value)
  svg.selectAll('*').remove()

  svg.attr('width', width).attr('height', height)

  // Zoom behavior
  const zoom = d3.zoom()
    .scaleExtent([0.2, 5])
    .on('zoom', (event) => {
      g.attr('transform', event.transform)
    })

  svg.call(zoom)

  const g = svg.append('g')
  gSelection = g

  // Edges
  linkSelection = g.append('g')
    .attr('class', 'links')
    .selectAll('line')
    .data(edges)
    .enter()
    .append('line')
    .attr('stroke', '#E5E5EA')
    .attr('stroke-width', 0.5)

  // Node groups
  const nodeGroup = g.append('g')
    .attr('class', 'nodes')
    .selectAll('g')
    .data(nodes)
    .enter()
    .append('g')
    .attr('class', 'node-group')
    .style('cursor', d => (d.category === 'unknown' || !d.category) ? 'default' : 'pointer')
    .call(
      d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended)
    )
    .on('click', (event, d) => {
      if (d.category === 'unknown' || !d.category) return
      handleNodeClick(d)
    })

  nodeSelection = nodeGroup.append('circle')
    .attr('r', d => getNodeRadius(d))
    .attr('fill', d => getNodeColor(d))
    .attr('stroke', '#ffffff')
    .attr('stroke-width', 1.5)

  // Labels — only for non-unknown nodes
  labelSelection = nodeGroup
    .filter(d => d.category && d.category !== 'unknown')
    .append('text')
    .text(d => d.name || d.id)
    .attr('font-size', '9px')
    .attr('fill', '#6B6B6B')
    .attr('dx', 8)
    .attr('dy', 3)
    .style('pointer-events', 'none')
    .style('user-select', 'none')

  // Simulation
  const isLarge = nodes.length > 200

  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(edges).id(d => d.id).distance(80))
    .force('charge', d3.forceManyBody().strength(-120))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(20))

  if (isLarge) {
    simulation.alphaDecay(0.02)
  }

  simulation.on('tick', () => {
    linkSelection
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)

    nodeGroup.attr('transform', d => `translate(${d.x},${d.y})`)
  })

  svgSelection = svg

  return { svg, g, zoom }
}

function dragstarted(event, d) {
  if (!event.active) simulation.alphaTarget(0.3).restart()
  d.fx = d.x
  d.fy = d.y
}

function dragged(event, d) {
  d.fx = event.x
  d.fy = event.y
}

function dragended(event, d) {
  if (!event.active) simulation.alphaTarget(0)
  if (!event.sourceEvent?.altKey) {
    d.fx = null
    d.fy = null
  }
}

function handleNodeClick(node) {
  // Look up in wiki-index by name
  const name = node.name || node.id
  const entry = wikiIndex.value.find(
    item => item.title === name || item.slug === node.id || item.slug === name
  )

  if (entry) {
    router.push(`/page/${entry.category}/${entry.slug}`)
  } else if (node.category && node.slug) {
    router.push(`/page/${node.category}/${node.slug}`)
  } else if (node.category && node.id) {
    router.push(`/page/${node.category}/${node.id}`)
  }
}

let graphContext = null

onMounted(async () => {
  // Fetch data in parallel
  const [graphRes, wikiRes] = await Promise.all([
    fetch('/data/graph.json').catch(() => null),
    fetch('/data/wiki-index.json').catch(() => null),
  ])

  if (wikiRes?.ok) {
    wikiIndex.value = await wikiRes.json()
  }

  if (graphRes?.ok) {
    const data = await graphRes.json()
    graphData.value = data

    const container = containerRef.value
    const width = container.clientWidth || 800
    const height = container.clientHeight || 600

    graphContext = buildGraph(data.nodes, data.edges, width, height)

    // ResizeObserver
    resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width: w, height: h } = entry.contentRect
        if (svgRef.value && simulation) {
          d3.select(svgRef.value).attr('width', w).attr('height', h)
          simulation.force('center', d3.forceCenter(w / 2, h / 2))
          simulation.alpha(0.3).restart()
        }
      }
    })
    resizeObserver.observe(container)
  }
})

onUnmounted(() => {
  if (simulation) {
    simulation.stop()
    simulation = null
  }
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
})
</script>

<style scoped>
.graph-page {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-sizing: border-box;
}

/* Hero */
.hero {
  background: linear-gradient(135deg, #191D2B 0%, #252D45 100%);
  padding: 32px;
  border-radius: 16px;
}

.hero-title {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 700;
  color: #ffffff;
  line-height: 1.2;
}

.hero-stats {
  margin: 0;
  font-size: 14px;
  color: #9B9B9B;
}

/* Legend */
.legend-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  align-items: center;
  padding: 4px 0;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-label {
  font-size: 13px;
  color: #555;
}

/* Graph card */
.graph-card {
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  width: 100%;
  height: calc(100vh - 280px);
  min-height: 500px;
  box-sizing: border-box;
}

.graph-svg {
  display: block;
  width: 100%;
  height: 100%;
}
</style>
