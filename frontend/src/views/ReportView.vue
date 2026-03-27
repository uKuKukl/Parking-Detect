<template>
  <div>
    <h2>违规通报看板</h2>
    <div style="margin-bottom: 20px; display: flex; gap: 15px; flex-wrap: wrap;">
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
      <el-button type="primary" @click="fetchReports">条件查询</el-button>
      <el-button type="success" @click="generateReports" :loading="generating">生成新通报</el-button>
      <el-button type="warning" @click="exportWord" :icon="Download">导出当前查询为 Word</el-button>
    </div>

    <el-row :gutter="20">
      <el-col :span="8" v-for="(report, index) in reports" :key="report.id" style="margin-bottom: 20px;">
        <el-card class="box-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>通报ID: {{ report.id }}</span>
              <el-button class="button" type="primary" link @click="copyText(report.reportText)">复制内容</el-button>
            </div>
          </template>
          
          <!-- Report Text Context -->
          <div class="text item" style="white-space: pre-wrap; line-height: 1.6; color: #555;">
            <template v-if="!report.expanded">
              {{ truncateText(report.reportText, 60) }}
            </template>
            <template v-else>
              {{ report.reportText }}
            </template>
            
            <div style="text-align: right; margin-top: 5px;" v-if="report.reportText && report.reportText.length > 60">
              <el-button link type="info" style="font-size: 12px" @click="report.expanded = !report.expanded">
                {{ report.expanded ? '收起详情 ▲' : '展开全文 ▼' }}
              </el-button>
            </div>
          </div>
          
          <el-divider border-style="dashed" />
          <div style="font-size: 12px; color: #999;">
            设备: {{ report.cameraId }} <br>
            时间: {{ report.detectTime }}
          </div>
        </el-card>
      </el-col>
    </el-row>
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

const fetchReports = async () => {
  try {
    let url = '/api/violations/reports'
    if (dateRange.value && dateRange.value.length === 2) {
      url += `?startDate=${dateRange.value[0]}&endDate=${dateRange.value[1]}`
    }
    const data = await request.get(url)
    // Add expanded property
    reports.value = data.map(item => ({ ...item, expanded: false }))
  } catch (error) {
    console.error(error)
  }
}

const exportWord = () => {
  let url = 'http://localhost:8080/api/violations/export/word'
  if (dateRange.value && dateRange.value.length === 2) {
    url += `?startDate=${dateRange.value[0]}&endDate=${dateRange.value[1]}`
  }
  window.open(url, '_blank')
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
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
