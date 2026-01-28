import { createRouter, createWebHistory } from 'vue-router'
import Screen from '../components/Screen.vue'
import Mobile from '../components/Mobile.vue'

const routes = [
  {
    path: '/',
    name: 'Screen',
    component: Screen
  },
  {
    path: '/mobile',
    name: 'Mobile',
    component: Mobile
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router







