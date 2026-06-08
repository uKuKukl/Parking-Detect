<template>
  <div v-if="$route.meta.noAuth">
    <router-view />
  </div>
  <el-container v-else class="admin-layout">
    <el-aside width="236px" class="admin-sidebar">
      <div class="brand-block">
        <div class="brand-icon">P</div>
        <div>
          <div class="brand-title">违停检测后台</div>
          <div class="brand-subtitle">Parking Monitor</div>
        </div>
      </div>

      <el-menu
        class="admin-menu"
        :default-active="$route.path"
        router
      >
        <el-menu-item v-if="canAccess(['ADMIN', 'AUDITOR'])" index="/dashboard">
          <el-icon><DataLine /></el-icon>
          <span>首页数据大屏</span>
        </el-menu-item>
        <el-menu-item v-if="canAccess(['ADMIN', 'AUDITOR'])" index="/audit">
          <el-icon><View /></el-icon>
          <span>违规复核台</span>
        </el-menu-item>
        <el-menu-item v-if="canAccess(['ADMIN', 'AUDITOR'])" index="/report">
          <el-icon><Document /></el-icon>
          <span>报告管理</span>
        </el-menu-item>
        <el-menu-item v-if="canAccess(['ADMIN'])" index="/cameras">
          <el-icon><VideoCamera /></el-icon>
          <span>摄像头管理</span>
        </el-menu-item>
        <el-menu-item v-if="canAccess(['ADMIN'])" index="/roi">
          <el-icon><Location /></el-icon>
          <span>电子围栏配置</span>
        </el-menu-item>
        <el-menu-item v-if="canAccess(['ADMIN'])" index="/logs">
          <el-icon><Tickets /></el-icon>
          <span>操作日志</span>
        </el-menu-item>
        <el-menu-item v-if="canAccess(['ADMIN'])" index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container class="admin-main-layout">
      <el-header class="admin-header">
        <div>
          <div class="header-title">校园违规停车报告生成系统</div>
          <div class="header-subtitle">AI 识别 · 人工复核 · 智能通报 · 数据分析</div>
        </div>
        <div class="header-user">
          <div class="user-meta">
            <span class="user-name">{{ currentUser?.realName || currentUser?.username || 'Admin' }}</span>
            <el-tag size="small" type="primary">{{ roleLabel }}</el-tag>
          </div>
          <el-button size="small" type="danger" plain @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>

      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const router = useRouter()
const route = useRoute()
const currentUser = ref(null)

const loadCurrentUser = () => {
  const stored = localStorage.getItem('currentUser')
  if (!stored) {
    currentUser.value = null
    return
  }

  try {
    currentUser.value = JSON.parse(stored)
  } catch (_) {
    currentUser.value = null
    localStorage.removeItem('currentUser')
  }
}

watch(() => route.fullPath, loadCurrentUser, { immediate: true })

const roleLabel = computed(() => {
  if (currentUser.value?.role === 'ADMIN') return '管理员'
  if (currentUser.value?.role === 'AUDITOR') return '审核员'
  return currentUser.value?.role || '未登录'
})

const canAccess = (roles) => {
  const role = currentUser.value?.role
  return !!role && roles.includes(role)
}

const handleLogout = async () => {
  try {
    await request.post('/api/auth/logout')
  } catch (_) {}
  localStorage.removeItem('currentUser')
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.admin-layout {
  min-height: 100vh;
  background: var(--admin-bg);
}

.admin-sidebar {
  margin: 16px 0 16px 16px;
  padding: 18px 14px;
  background: var(--admin-surface);
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 22px;
  box-shadow: var(--admin-shadow);
}

.brand-block {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 8px 22px;
}

.brand-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: var(--admin-primary);
  color: #fff;
  font-size: 18px;
  font-weight: 900;
  box-shadow: 0 10px 24px rgba(37, 99, 235, 0.25);
}

.brand-title {
  color: var(--admin-text);
  font-size: 16px;
  font-weight: 800;
}

.brand-subtitle {
  margin-top: 3px;
  color: var(--admin-text-muted);
  font-size: 12px;
}

.admin-menu {
  border-right: 0;
}

.admin-menu :deep(.el-menu-item) {
  height: 44px;
  margin: 6px 0;
  border-radius: 12px;
  color: var(--admin-text-muted);
  font-weight: 700;
}

.admin-menu :deep(.el-menu-item:hover) {
  background: var(--admin-surface-soft);
  color: var(--admin-primary);
}

.admin-menu :deep(.el-menu-item.is-active) {
  background: var(--admin-primary-soft);
  color: var(--admin-primary);
}

.admin-main-layout {
  min-width: 0;
}

.admin-header {
  height: 76px;
  margin: 16px 16px 0;
  padding: 0 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 22px;
  box-shadow: var(--admin-shadow-soft);
  backdrop-filter: blur(10px);
}

.header-title {
  color: var(--admin-text);
  font-size: 18px;
  font-weight: 800;
}

.header-subtitle {
  margin-top: 4px;
  color: var(--admin-text-muted);
  font-size: 13px;
}

.header-user {
  display: flex;
  align-items: center;
  gap: 14px;
}

.user-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-name {
  color: var(--admin-text);
  font-size: 14px;
  font-weight: 700;
}

.admin-main {
  height: calc(100vh - 92px);
  padding: 22px 16px 28px;
  overflow: auto;
}
</style>
