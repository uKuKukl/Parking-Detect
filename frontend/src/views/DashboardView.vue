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

    <div class="section-grid two-columns">
      <div class="panel-card">
        <div class="card-header-row">
          <div>
            <div class="card-title">区域违规热力图</div>
            <div class="card-subtitle">颜色越深表示该区域记录越多</div>
          </div>
        </div>
        <div class="location-heatmap">
          <div
            v-for="item in summary.locationHeatmap"
            :key="item.location"
            class="heatmap-block"
            :style="{ backgroundColor: heatColor(item.count, maxLocationHeatCount) }"
          >
            <div class="heatmap-location">{{ item.location }}</div>
            <div class="heatmap-count">{{ item.count }} 条</div>
          </div>
        </div>
        <el-empty v-if="!summary.locationHeatmap.length" description="暂无区域数据" />
      </div>

      <div class="panel-card">
        <div class="card-header-row">
          <div>
            <div class="card-title">时段热力图</div>
            <div class="card-subtitle">按小时统计记录集中时段</div>
          </div>
        </div>
        <div class="hour-heatmap">
          <el-tooltip
            v-for="item in summary.hourHeatmap"
            :key="item.hour"
            :content="`${item.hour}：${item.count} 条`"
            placement="top"
          >
            <div
              class="hour-cell"
              :style="{ backgroundColor: heatColor(item.count, maxHourHeatCount) }"
            >
              {{ item.hour.slice(0, 2) }}
            </div>
          </el-tooltip>
        </div>
      </div>
    </div>

    <div class="panel-card">
      <div class="card-header-row">
        <div>
          <div class="card-title">最新违规记录</div>
          <div class="card-subtitle">按识别时间倒序展示最近记录</div>
        </div>
      </div>
      <el-table :data="summary.latest" border>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="detectTime" label="识别时间" width="180" />
        <el-table-column prop="cameraId" label="设备编号" width="150" />
        <el-table-column prop="location" label="地点" min-width="220" />
        <el-table-column label="状态" width="120">
          <template #default="scope">
            <el-tag :type="statusType(scope.row.status)">{{ statusLabel(scope.row.status) }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import request from '@/utils/request'

const summary = ref({
  todayCount: 0,
  pendingCount: 0,
  confirmedCount: 0,
  reportCount: 0,
  trend: [],
  cameraRanking: [],
  locationHeatmap: [],
  hourHeatmap: [],
  latest: []
})

const cards = computed(() => [
  { label: '今日检测数', value: summary.value.todayCount, color: '#2563eb' },
  { label: '待复核数量', value: summary.value.pendingCount, color: '#f59e0b' },
  { label: '确认违规数', value: summary.value.confirmedCount, color: '#ef4444' },
  { label: '已生成通报', value: summary.value.reportCount, color: '#10b981' }
])

const maxTrendCount = computed(() => Math.max(1, ...summary.value.trend.map(item => Number(item.count) || 0)))
const maxLocationHeatCount = computed(() => Math.max(1, ...summary.value.locationHeatmap.map(item => Number(item.count) || 0)))
const maxHourHeatCount = computed(() => Math.max(1, ...summary.value.hourHeatmap.map(item => Number(item.count) || 0)))

const trendPercentage = (count) => Math.round(((Number(count) || 0) / maxTrendCount.value) * 100)

const heatColor = (count, maxCount) => {
  const ratio = Math.min(1, (Number(count) || 0) / Math.max(1, maxCount))
  const alpha = 0.1 + ratio * 0.72
  return `rgba(37, 99, 235, ${alpha})`
}

const statusLabel = (status) => {
  const map = { 0: '待复核', 1: '已确认', 2: '已驳回', 3: '已生成通报', 4: '正常归档' }
  return map[status] || '未知'
}

const statusType = (status) => {
  const map = { 0: 'warning', 1: 'danger', 2: 'info', 3: 'success', 4: 'primary' }
  return map[status] || 'info'
}

const loadSummary = async () => {
  summary.value = await request.get('/api/dashboard/summary')
}

onMounted(loadSummary)
</script>

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
