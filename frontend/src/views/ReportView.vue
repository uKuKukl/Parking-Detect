<template>
  <div class="page-shell report-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">报告管理</h2>
        <p class="page-subtitle">生成、筛选、复制和导出违规停车通报。</p>
      </div>
    </div>

    <div class="toolbar-card">
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        value-format="YYYY-MM-DD"
        @change="fetchReports"
        style="width: 300px"
      />
      <el-input v-model="cameraId" placeholder="设备编号" clearable style="width: 180px" @keyup.enter="fetchReports" />
      <el-button type="primary" @click="fetchReports">条件查询</el-button>
      <el-button type="success" @click="generateReports" :loading="generating">生成新通报</el-button>
      <el-button type="warning" @click="exportWord" :icon="Download">导出 Word</el-button>
      <el-button type="warning" plain @click="exportExcel" :icon="Download">导出 Excel</el-button>
    </div>

    <div class="report-grid">
      <el-card v-for="report in reports" :key="report.id" class="report-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>通报ID: {{ report.id }}</span>
            <el-button class="button" type="primary" link @click="copyText(report.reportText)">复制内容</el-button>
          </div>
        </template>

        <div
          class="report-content"
          :class="{ expanded: report.expanded }"
        >
          <template v-if="!report.expanded">
            {{ truncateText(report.reportText, 60) }}
          </template>
          <template v-else>
            {{ report.reportText }}
          </template>

          <div class="expand-row" v-if="report.reportText && report.reportText.length > 60">
            <el-button link type="info" @click="report.expanded = !report.expanded">
              {{ report.expanded ? '收起详情 ▲' : '展开全文 ▼' }}
            </el-button>
          </div>
        </div>

        <el-divider border-style="dashed" />
        <div class="report-meta">
          <span>设备：{{ report.cameraId }}</span>
          <span>时间：{{ report.detectTime }}</span>
        </div>
      </el-card>
    </div>
    <el-empty v-if="reports.length === 0" description="暂无符合条件的报告" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'

const reports = ref([])
const generating = ref(false)
const dateRange = ref([])
const cameraId = ref('')

const fetchReports = async () => {
  try {
    const params = buildExportParams()
    const data = await request.get(`/api/violations/reports?${params.toString()}`)
    reports.value = data.map(item => ({ ...item, expanded: false }))
  } catch (error) {
    console.error(error)
  }
}

const buildExportParams = () => {
  const params = new URLSearchParams()
  if (dateRange.value && dateRange.value.length === 2) {
    params.append('startDate', dateRange.value[0])
    params.append('endDate', dateRange.value[1])
  }
  if (cameraId.value) params.append('cameraId', cameraId.value.trim())
  return params
}

const exportWord = () => {
  const baseUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8080').replace(/\/$/, '')
  window.open(`${baseUrl}/api/violations/export/word?${buildExportParams().toString()}`, '_blank')
}

const exportExcel = () => {
  const baseUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8080').replace(/\/$/, '')
  window.open(`${baseUrl}/api/violations/export/excel?${buildExportParams().toString()}`, '_blank')
}

const generateReports = async () => {
  generating.value = true
  try {
    const res = await request.post('/api/violations/generate-reports')
    ElMessage.success(typeof res === 'string' ? res : '通报生成成功')
    fetchReports()
  } catch (error) {
    console.error(error)
  } finally {
    generating.value = false
  }
}

const truncateText = (text, maxLength) => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

const copyText = (text) => {
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(() => {
      ElMessage.success('报告已存入剪贴板')
    })
  } else {
    const textArea = document.createElement("textarea")
    textArea.value = text
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    ElMessage.success('报告已存入剪贴板')
    textArea.remove()
  }
}

onMounted(() => {
  fetchReports()
})
</script>

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
  white-space: pre-wrap;
  line-height: 1.7;
  color: var(--admin-text-muted);
}

.report-content.expanded {
  min-height: 0;
}

.expand-row {
  text-align: right;
  margin-top: 5px;
}

.report-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: var(--admin-text-muted);
  font-size: 12px;
}

@media (max-width: 1280px) {
  .report-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
