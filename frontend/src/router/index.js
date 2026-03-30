import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/audit'
    },
    {
      path: '/audit',
      name: 'audit',
      component: () => import('../views/AuditView.vue')
    },
    {
      path: '/report',
      name: 'report',
      component: () => import('../views/ReportView.vue')
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('../views/SettingsView.vue')
    },
    {
      path: '/roi',
      name: 'roi',
      component: () => import('../views/RoiSettingsView.vue')
    }
  ]
})

export default router
