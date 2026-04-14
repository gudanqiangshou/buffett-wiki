import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    component: () => import('./views/Home.vue')
  },
  {
    path: '/page/:category/:slug',
    component: () => import('./views/PageView.vue')
  },
  {
    path: '/category/:type',
    component: () => import('./views/CategoryView.vue')
  },
  {
    path: '/graph',
    component: () => import('./views/GraphView.vue')
  },
  {
    path: '/chat',
    component: () => import('./views/ChatView.vue')
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
