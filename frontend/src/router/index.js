import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'

function getCurrentUser() {
  const raw = localStorage.getItem('currentUser')
  if (!raw) return null

  try {
    return JSON.parse(raw)
  } catch (_) {
    localStorage.removeItem('currentUser')
    return null
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { noAuth: true }
    },
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { roles: ['ADMIN', 'AUDITOR'] }
    },
    {
      path: '/audit',
      name: 'audit',
      component: () => import('../views/AuditView.vue'),
      meta: { roles: ['ADMIN', 'AUDITOR'] }
    },
    {
      path: '/report',
      name: 'report',
      component: () => import('../views/ReportView.vue'),
      meta: { roles: ['ADMIN', 'AUDITOR'] }
    },
    {
      path: '/cameras',
      name: 'cameras',
      component: () => import('../views/CameraDeviceView.vue'),
      meta: { roles: ['ADMIN'] }
    },
    {
      path: '/roi',
      name: 'roi',
      component: () => import('../views/RoiSettingsView.vue'),
      meta: { roles: ['ADMIN'] }
    },
    {
      path: '/logs',
      name: 'logs',
      component: () => import('../views/AuditLogView.vue'),
      meta: { roles: ['ADMIN'] }
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('../views/SettingsView.vue'),
      meta: { roles: ['ADMIN'] }
    }
  ]
})

// 全局路由守卫：未登录则跳转到登录页
router.beforeEach((to) => {
  if (to.meta.noAuth) return true
  const user = getCurrentUser()
  if (!user) return { name: 'login' }

  if (to.meta.roles && !to.meta.roles.includes(user.role)) {
    ElMessage.warning('当前账号无权访问该页面')
    return { name: user.role === 'ADMIN' ? 'audit' : 'audit' }
  }

  return true
})

export default router
