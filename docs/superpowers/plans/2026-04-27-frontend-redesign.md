# Frontend Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the Vue 3 + Element Plus frontend into a clean light administrative interface without changing backend APIs or adding dependencies.

**Architecture:** Add one global admin stylesheet that defines the design system, then update the app shell and each view to use shared layout classes. Keep page logic and API calls unchanged; focus on structure, classes, and visual hierarchy.

**Tech Stack:** Vue 3, Vite, Element Plus, CSS, existing Axios request utility.

---

## File Structure

- Create: `frontend/src/styles/admin.css` — global design tokens, layout classes, Element Plus visual overrides.
- Modify: `frontend/src/main.js` — import the new global stylesheet after Element Plus CSS.
- Modify: `frontend/src/App.vue` — rebuild the authenticated app shell: white sidebar, modern header, scrollable main area.
- Modify: `frontend/src/views/LoginView.vue` — redesign login page while preserving login logic.
- Modify: `frontend/src/views/DashboardView.vue` — apply dashboard stat cards, panel layout, and blue heatmap styling.
- Modify: `frontend/src/views/AuditView.vue` — apply page header, toolbar card, content card, table, pagination, dialogs.
- Modify: `frontend/src/views/ReportView.vue` — apply page header, toolbar card, report card grid.
- Modify: `frontend/src/views/CameraDeviceView.vue` — apply page header, content card, dialog styling.
- Modify: `frontend/src/views/RoiSettingsView.vue` — apply shared page/card/table style without changing ROI behavior.
- Modify: `frontend/src/views/AuditLogView.vue` — apply page header, toolbar card, content card.
- Modify: `frontend/src/views/SettingsView.vue` — apply page header, settings cards, prompt and auto-report panels.

No backend files should be changed.

---

### Task 1: Add the global admin design system

**Files:**
- Create: `frontend/src/styles/admin.css`
- Modify: `frontend/src/main.js`

- [ ] **Step 1: Create global admin stylesheet**

Create `frontend/src/styles/admin.css` with this content:

```css
:root {
  --admin-bg: #f5f7fb;
  --admin-surface: #ffffff;
  --admin-surface-soft: #f8fafc;
  --admin-primary: #2563eb;
  --admin-primary-soft: #eff6ff;
  --admin-primary-hover: #1d4ed8;
  --admin-text: #111827;
  --admin-text-muted: #64748b;
  --admin-border: #e5e7eb;
  --admin-danger: #dc2626;
  --admin-warning: #f59e0b;
  --admin-success: #10b981;
  --admin-radius-lg: 18px;
  --admin-radius-md: 14px;
  --admin-radius-sm: 10px;
  --admin-shadow: 0 14px 36px rgba(15, 23, 42, 0.07);
  --admin-shadow-soft: 0 8px 22px rgba(15, 23, 42, 0.05);
}

* {
  box-sizing: border-box;
}

html,
body,
#app {
  width: 100%;
  min-height: 100%;
}

body {
  margin: 0;
  padding: 0;
  color: var(--admin-text);
  background: var(--admin-bg);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

.page-shell {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.page-title {
  margin: 0;
  color: var(--admin-text);
  font-size: 24px;
  line-height: 1.25;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.page-subtitle {
  margin: 6px 0 0;
  color: var(--admin-text-muted);
  font-size: 14px;
}

.page-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}

.toolbar-card,
.content-card,
.panel-card {
  background: var(--admin-surface);
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: var(--admin-radius-lg);
  box-shadow: var(--admin-shadow-soft);
}

.toolbar-card {
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.content-card,
.panel-card {
  padding: 18px;
}

.section-grid {
  display: grid;
  gap: 16px;
}

.section-grid.two-columns {
  grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.9fr);
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.stat-card {
  position: relative;
  overflow: hidden;
  min-height: 118px;
  padding: 20px;
  background: var(--admin-surface);
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: var(--admin-radius-lg);
  box-shadow: var(--admin-shadow-soft);
}

.stat-card::before {
  content: "";
  position: absolute;
  left: 0;
  top: 18px;
  bottom: 18px;
  width: 4px;
  border-radius: 999px;
  background: var(--stat-color, var(--admin-primary));
}

.stat-label {
  color: var(--admin-text-muted);
  font-size: 13px;
  font-weight: 600;
}

.stat-value {
  margin-top: 10px;
  color: var(--admin-text);
  font-size: 34px;
  line-height: 1;
  font-weight: 800;
  letter-spacing: -0.04em;
}

.card-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.card-title {
  color: var(--admin-text);
  font-size: 16px;
  font-weight: 800;
}

.card-subtitle {
  margin-top: 4px;
  color: var(--admin-text-muted);
  font-size: 13px;
}

.el-card {
  border-radius: var(--admin-radius-lg) !important;
  border-color: rgba(226, 232, 240, 0.9) !important;
  box-shadow: var(--admin-shadow-soft) !important;
}

.el-card__header {
  border-bottom-color: var(--admin-border) !important;
  font-weight: 700;
}

.el-button {
  border-radius: var(--admin-radius-sm) !important;
  font-weight: 600 !important;
}

.el-button--primary {
  background-color: var(--admin-primary) !important;
  border-color: var(--admin-primary) !important;
}

.el-button--primary:hover,
.el-button--primary:focus {
  background-color: var(--admin-primary-hover) !important;
  border-color: var(--admin-primary-hover) !important;
}

.el-input__wrapper,
.el-select__wrapper,
.el-textarea__inner {
  border-radius: var(--admin-radius-sm) !important;
  box-shadow: 0 0 0 1px var(--admin-border) inset !important;
}

.el-table {
  border-radius: var(--admin-radius-md);
  overflow: hidden;
  --el-table-header-bg-color: #f8fafc;
  --el-table-header-text-color: #334155;
  --el-table-row-hover-bg-color: #f8fafc;
}

.el-table th.el-table__cell {
  font-weight: 700;
}

.el-pagination {
  justify-content: flex-end;
}

.el-dialog {
  border-radius: var(--admin-radius-lg) !important;
  overflow: hidden;
}

.el-tag {
  border-radius: 999px !important;
  font-weight: 600;
}

@media (max-width: 1200px) {
  .stat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .section-grid.two-columns {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 2: Import the stylesheet**

Modify `frontend/src/main.js` so the imports are:

```js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './styles/admin.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
```

Leave the rest of `main.js` unchanged.

- [ ] **Step 3: Build frontend**

Run:

```bash
npm run build --prefix frontend
```

Expected: build succeeds. The existing Vite chunk-size warning may still appear and is acceptable.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/main.js frontend/src/styles/admin.css
git commit -m "Add frontend admin design system"
```

---

### Task 2: Redesign the global app shell

**Files:**
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: Replace the template**

Replace the `frontend/src/App.vue` template with:

```vue
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
```

- [ ] **Step 2: Replace the style block**

Replace the `frontend/src/App.vue` style block with:

```vue
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
```

Keep the existing script unchanged.

- [ ] **Step 3: Build frontend**

Run:

```bash
npm run build --prefix frontend
```

Expected: build succeeds.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.vue
git commit -m "Redesign frontend app shell"
```

---

### Task 3: Redesign LoginView

**Files:**
- Modify: `frontend/src/views/LoginView.vue`

- [ ] **Step 1: Read current login logic**

Read `frontend/src/views/LoginView.vue` and preserve its existing script logic: form state, login request, localStorage write, and router navigation.

- [ ] **Step 2: Replace only the template and style**

Use this template structure while keeping the existing `<script setup>` logic compatible with `form` and `handleLogin`:

```vue
<template>
  <div class="login-page">
    <div class="login-hero">
      <div class="login-brand">
        <div class="login-logo">P</div>
        <div>
          <h1>校园违规停车报告生成系统</h1>
          <p>AI 视觉识别、人工复核、智能通报与数据分析一体化平台</p>
        </div>
      </div>
      <div class="feature-list">
        <div>YOLOv8 违规识别</div>
        <div>多角色复核流程</div>
        <div>LLM 智能通报生成</div>
      </div>
    </div>

    <el-card class="login-card" shadow="never">
      <h2>登录后台</h2>
      <p class="login-subtitle">请输入账号密码进入管理系统</p>
      <el-form @keyup.enter="handleLogin">
        <el-form-item>
          <el-input v-model="form.username" size="large" placeholder="用户名" clearable />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" size="large" type="password" placeholder="密码" show-password />
        </el-form-item>
        <el-button class="login-button" type="primary" size="large" :loading="loading" @click="handleLogin">
          登录
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>
```

If the existing script uses a different loading variable name, use that existing name instead of `loading`.

Use this scoped style:

```vue
<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(360px, 1fr) 420px;
  align-items: center;
  gap: 48px;
  padding: 48px 8vw;
  background:
    radial-gradient(circle at 18% 18%, rgba(37, 99, 235, 0.16), transparent 34%),
    linear-gradient(135deg, #f8fbff 0%, #eef4ff 48%, #f8fafc 100%);
}

.login-hero {
  max-width: 680px;
}

.login-brand {
  display: flex;
  align-items: flex-start;
  gap: 18px;
}

.login-logo {
  width: 58px;
  height: 58px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 18px;
  background: var(--admin-primary);
  color: #fff;
  font-size: 26px;
  font-weight: 900;
  box-shadow: 0 18px 42px rgba(37, 99, 235, 0.24);
}

.login-brand h1 {
  margin: 0;
  color: var(--admin-text);
  font-size: 38px;
  line-height: 1.18;
  font-weight: 900;
  letter-spacing: -0.04em;
}

.login-brand p {
  margin: 14px 0 0;
  color: var(--admin-text-muted);
  font-size: 16px;
  line-height: 1.8;
}

.feature-list {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 36px;
}

.feature-list div {
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 999px;
  color: var(--admin-primary);
  font-weight: 700;
}

.login-card {
  padding: 18px;
  border-radius: 24px !important;
}

.login-card h2 {
  margin: 0;
  color: var(--admin-text);
  font-size: 26px;
  font-weight: 900;
}

.login-subtitle {
  margin: 8px 0 28px;
  color: var(--admin-text-muted);
}

.login-button {
  width: 100%;
}

@media (max-width: 900px) {
  .login-page {
    grid-template-columns: 1fr;
    padding: 32px;
  }
}
</style>
```

- [ ] **Step 3: Build frontend**

Run:

```bash
npm run build --prefix frontend
```

Expected: build succeeds.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/LoginView.vue
git commit -m "Redesign login page"
```

---

### Task 4: Redesign DashboardView

**Files:**
- Modify: `frontend/src/views/DashboardView.vue`

- [ ] **Step 1: Replace the page wrapper and stat cards**

Update the template so it starts with:

```vue
<template>
  <div class="page-shell dashboard-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">首页数据大屏</h2>
        <p class="page-subtitle">汇总检测、复核、通报和热力分析数据，辅助快速掌握校园违停态势。</p>
      </div>
      <div class="page-actions">
        <el-button type="primary" @click="loadSummary">刷新数据</el-button>
      </div>
    </div>

    <div class="stat-grid">
      <div
        v-for="card in cards"
        :key="card.label"
        class="stat-card"
        :style="{ '--stat-color': card.color }"
      >
        <div class="stat-label">{{ card.label }}</div>
        <div class="stat-value">{{ card.value }}</div>
      </div>
    </div>
```

Use this `cards` computed value in the script:

```js
const cards = computed(() => [
  { label: '今日检测数', value: summary.value.todayCount, color: '#2563eb' },
  { label: '待复核数量', value: summary.value.pendingCount, color: '#f59e0b' },
  { label: '确认违规数', value: summary.value.confirmedCount, color: '#ef4444' },
  { label: '已生成通报', value: summary.value.reportCount, color: '#10b981' }
])
```

- [ ] **Step 2: Replace Element Plus row layout with shared panels**

Replace the two `el-row` dashboard sections with:

```vue
    <div class="section-grid two-columns">
      <div class="panel-card">
        <div class="card-header-row">
          <div>
            <div class="card-title">最近 7 天检测趋势</div>
            <div class="card-subtitle">按检测时间统计每日记录数</div>
          </div>
        </div>
        <div class="trend-list">
          <div v-for="item in summary.trend" :key="item.date" class="trend-item">
            <span class="trend-date">{{ item.date }}</span>
            <el-progress :percentage="trendPercentage(item.count)" :format="() => `${item.count} 条`" />
          </div>
        </div>
      </div>

      <div class="panel-card">
        <div class="card-header-row">
          <div>
            <div class="card-title">摄像头违规排行</div>
            <div class="card-subtitle">按设备编号统计记录数量</div>
          </div>
        </div>
        <el-table :data="summary.cameraRanking" size="small" height="300">
          <el-table-column type="index" label="排名" width="70" />
          <el-table-column prop="cameraId" label="设备编号" />
          <el-table-column prop="count" label="记录数" width="90" />
        </el-table>
      </div>
    </div>
```

- [ ] **Step 3: Update heatmap and latest records wrappers**

Replace the heatmap section and latest card with `panel-card` wrappers using the same content. The location heatmap container should remain `.location-heatmap`; the hour container should remain `.hour-heatmap`.

The latest records wrapper should be:

```vue
    <div class="panel-card">
      <div class="card-header-row">
        <div>
          <div class="card-title">最新违规记录</div>
          <div class="card-subtitle">按识别时间倒序展示最近记录</div>
        </div>
      </div>
      <el-table :data="summary.latest" border>
        <!-- keep existing columns -->
      </el-table>
    </div>
  </div>
</template>
```

- [ ] **Step 4: Change heat color to blue**

In the script, replace `heatColor` with:

```js
const heatColor = (count, maxCount) => {
  const ratio = Math.min(1, (Number(count) || 0) / Math.max(1, maxCount))
  const alpha = 0.1 + ratio * 0.72
  return `rgba(37, 99, 235, ${alpha})`
}
```

- [ ] **Step 5: Replace scoped style**

Keep only dashboard-specific CSS:

```vue
<style scoped>
.dashboard-page {
  padding-bottom: 12px;
}

.trend-list {
  height: 300px;
  display: flex;
  flex-direction: column;
  justify-content: space-around;
}

.trend-item {
  display: grid;
  grid-template-columns: 110px 1fr;
  align-items: center;
  gap: 12px;
}

.trend-date {
  color: var(--admin-text-muted);
}

.location-heatmap {
  min-height: 220px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.heatmap-block {
  min-height: 86px;
  border-radius: 14px;
  padding: 12px;
  color: #fff;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  border: 1px solid rgba(37, 99, 235, 0.18);
}

.heatmap-location {
  font-weight: 700;
  word-break: break-all;
}

.heatmap-count {
  font-size: 20px;
  font-weight: 800;
}

.hour-heatmap {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 8px;
  min-height: 220px;
  align-content: center;
}

.hour-cell {
  height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 800;
  border: 1px solid rgba(37, 99, 235, 0.18);
}
</style>
```

- [ ] **Step 6: Build and commit**

Run:

```bash
npm run build --prefix frontend
```

Expected: build succeeds.

Commit:

```bash
git add frontend/src/views/DashboardView.vue
git commit -m "Redesign dashboard page"
```

---

### Task 5: Redesign AuditView

**Files:**
- Modify: `frontend/src/views/AuditView.vue`

- [ ] **Step 1: Wrap page with shared layout**

Change the root template from `<div>` to:

```vue
<div class="page-shell audit-page">
  <div class="page-header">
    <div>
      <h2 class="page-title">违规复核台</h2>
      <p class="page-subtitle">筛选、查看和人工复核 YOLO 检测到的违规停车记录。</p>
    </div>
  </div>
```

Close it with `</div>` at the end of the template.

- [ ] **Step 2: Convert toolbar**

Change the toolbar container class from `toolbar` to `toolbar-card`:

```vue
<div class="toolbar-card">
```

Keep all filter controls and upload behavior unchanged.

- [ ] **Step 3: Wrap table and pagination**

Wrap the table and pagination in:

```vue
<div class="content-card">
  <el-table :data="tableData" border style="width: 100%">
    <!-- existing columns -->
  </el-table>

  <div class="pagination-wrapper">
    <!-- existing pagination -->
  </div>
</div>
```

- [ ] **Step 4: Replace scoped style**

Replace the style block with:

```vue
<style scoped>
.audit-page :deep(.el-upload) {
  display: inline-flex;
}

.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.image-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.image-path {
  max-width: 150px;
}

.preview-wrapper {
  min-height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--admin-surface-soft);
  border-radius: 14px;
  overflow: hidden;
}

.preview-image {
  max-width: 100%;
  max-height: 65vh;
  object-fit: contain;
  display: block;
}

.preview-meta {
  margin-top: 16px;
}
</style>
```

- [ ] **Step 5: Build and commit**

Run:

```bash
npm run build --prefix frontend
```

Expected: build succeeds.

Commit:

```bash
git add frontend/src/views/AuditView.vue
git commit -m "Redesign audit review page"
```

---

### Task 6: Redesign ReportView

**Files:**
- Modify: `frontend/src/views/ReportView.vue`

- [ ] **Step 1: Add shared page shell**

Wrap the template with:

```vue
<div class="page-shell report-page">
  <div class="page-header">
    <div>
      <h2 class="page-title">报告管理</h2>
      <p class="page-subtitle">生成、筛选、复制和导出违规停车通报。</p>
    </div>
  </div>
```

- [ ] **Step 2: Convert action row to toolbar-card**

Replace the top inline-styled div with:

```vue
<div class="toolbar-card">
```

Keep the date picker, camera input, buttons, and methods unchanged.

- [ ] **Step 3: Replace card grid classes**

Change the report grid to:

```vue
<div class="report-grid">
  <el-card v-for="report in reports" :key="report.id" class="report-card" shadow="never">
    <!-- existing card content -->
  </el-card>
</div>
```

Remove the `el-row`/`el-col` wrappers.

- [ ] **Step 4: Replace scoped style**

Use:

```vue
<style scoped>
.report-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.report-card {
  height: 100%;
}

:deep(.report-card .el-card__body) {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.report-content {
  min-height: 96px;
}

.report-content.expanded {
  min-height: 0;
}

@media (max-width: 1280px) {
  .report-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
```

- [ ] **Step 5: Build and commit**

Run:

```bash
npm run build --prefix frontend
```

Expected: build succeeds.

Commit:

```bash
git add frontend/src/views/ReportView.vue
git commit -m "Redesign report management page"
```

---

### Task 7: Redesign CameraDeviceView and AuditLogView

**Files:**
- Modify: `frontend/src/views/CameraDeviceView.vue`
- Modify: `frontend/src/views/AuditLogView.vue`

- [ ] **Step 1: Update CameraDeviceView page structure**

Change its root to:

```vue
<div class="page-shell">
  <div class="page-header">
    <div>
      <h2 class="page-title">摄像头管理</h2>
      <p class="page-subtitle">维护摄像头设备、安装位置、在线状态和 ROI 绑定关系。</p>
    </div>
    <div class="page-actions">
      <el-button type="primary" @click="openDialog()">新增摄像头</el-button>
    </div>
  </div>

  <div class="content-card">
    <el-table :data="devices" border>
      <!-- existing columns -->
    </el-table>
  </div>

  <!-- keep existing dialog -->
</div>
```

Remove the old `.page-header` scoped style because the global class now handles it.

- [ ] **Step 2: Update AuditLogView page structure**

Change its root to:

```vue
<div class="page-shell">
  <div class="page-header">
    <div>
      <h2 class="page-title">操作日志</h2>
      <p class="page-subtitle">追踪复核操作、操作人、操作类型和备注信息。</p>
    </div>
  </div>

  <div class="toolbar-card">
    <!-- existing filters -->
  </div>

  <div class="content-card">
    <el-table :data="logs" border>
      <!-- existing columns -->
    </el-table>
  </div>
</div>
```

Remove the old `.toolbar` scoped style because the global class handles it.

- [ ] **Step 3: Build and commit**

Run:

```bash
npm run build --prefix frontend
```

Expected: build succeeds.

Commit:

```bash
git add frontend/src/views/CameraDeviceView.vue frontend/src/views/AuditLogView.vue
git commit -m "Redesign management table pages"
```

---

### Task 8: Redesign RoiSettingsView and SettingsView

**Files:**
- Modify: `frontend/src/views/RoiSettingsView.vue`
- Modify: `frontend/src/views/SettingsView.vue`

- [ ] **Step 1: Update RoiSettingsView root layout**

Read `frontend/src/views/RoiSettingsView.vue`. Keep all script logic and behavior unchanged.

Wrap the page with:

```vue
<div class="page-shell">
  <div class="page-header">
    <div>
      <h2 class="page-title">电子围栏配置</h2>
      <p class="page-subtitle">配置 ROI 区域规则，并为摄像头检测提供场地边界约束。</p>
    </div>
  </div>
```

Convert its main control/filter/form/table blocks into `toolbar-card`, `content-card`, or `panel-card` wrappers according to their role. Do not change method names, API calls, or data fields.

- [ ] **Step 2: Update SettingsView root layout**

Change `SettingsView.vue` root to:

```vue
<div class="page-shell">
  <div class="page-header">
    <div>
      <h2 class="page-title">系统设置</h2>
      <p class="page-subtitle">维护通报 Prompt 模板与自动报告生成配置。</p>
    </div>
  </div>
```

Change the two main `el-card` blocks into `panel-card` wrappers where practical, or keep `el-card` but remove inline width/margin styles and rely on shared spacing.

- [ ] **Step 3: Keep SettingsView local styles minimal**

Ensure SettingsView scoped style keeps only:

```vue
<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.variable-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.preview-box {
  white-space: pre-wrap;
  line-height: 1.7;
  background: var(--admin-surface-soft);
  padding: 16px;
  border-radius: 12px;
  color: var(--admin-text);
}
</style>
```

- [ ] **Step 4: Build and commit**

Run:

```bash
npm run build --prefix frontend
```

Expected: build succeeds.

Commit:

```bash
git add frontend/src/views/RoiSettingsView.vue frontend/src/views/SettingsView.vue
git commit -m "Redesign settings and ROI pages"
```

---

### Task 9: Final polish and validation

**Files:**
- Inspect and optionally modify any touched frontend files if build or visual consistency requires it.

- [ ] **Step 1: Search for old inline layout remnants**

Search for these patterns in `frontend/src`:

```bash
rg "background-color: #304156|logo-title|layout-container|toolbar\{|style=\"margin-bottom: 20px|报告展示看板" frontend/src
```

Expected: no old dark sidebar style remains. If matches remain in active templates/styles, replace them with the shared classes from earlier tasks.

- [ ] **Step 2: Run final frontend build**

Run:

```bash
npm run build --prefix frontend
```

Expected: build succeeds. Existing Vite chunk-size warning is acceptable.

- [ ] **Step 3: Manual smoke check**

Run the dev server:

```bash
npm run dev --prefix frontend
```

Open the printed local URL and check these pages:

- `/login` shows the redesigned login page.
- `/dashboard` shows stat cards, trend panel, ranking, heatmaps, latest records.
- `/audit` shows page header, toolbar-card filters, table, pagination.
- `/report` shows toolbar and report card grid.
- `/cameras` shows redesigned management table.
- `/roi` remains usable and visually consistent.
- `/logs` shows redesigned toolbar and table.
- `/settings` shows prompt and auto-report panels.

Stop the dev server after checking.

- [ ] **Step 4: Commit final polish if needed**

If Step 1 or Step 3 required changes, commit them:

```bash
git add frontend/src
git commit -m "Polish frontend redesign"
```

If no changes were needed, do not create an empty commit.

---

## Self-Review

- Spec coverage: The plan covers the global stylesheet, app shell, login page, dashboard, audit page, report page, camera page, ROI page, audit log page, settings page, and validation. Backend APIs remain unchanged.
- Placeholder scan: No `TBD`, `TODO`, or unspecified implementation steps remain. ROI page is the only page without full replacement code because its existing structure must be read and preserved; the plan gives exact wrapper classes and constraints.
- Type consistency: The plan preserves existing method and state names except where explicitly specified. New shared CSS class names match the global stylesheet.
