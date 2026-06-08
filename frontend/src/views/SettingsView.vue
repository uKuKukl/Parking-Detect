<template>
  <div class="page-shell">
    <div class="page-header">
      <div>
        <h2 class="page-title">系统设置</h2>
        <p class="page-subtitle">维护通报 Prompt 模板与自动报告生成配置。</p>
      </div>
    </div>

    <div class="panel-card">
      <div class="card-header-row">
        <div>
          <div class="card-title">大模型 Prompt 模板配置</div>
          <div class="card-subtitle">调整通报生成语气、格式和动态变量。</div>
        </div>
        <el-tag type="info">{{ promptTemplate.length }} 字</el-tag>
      </div>

      <el-form label-position="top">
        <el-form-item label="快捷插入变量">
          <div class="variable-row">
            <el-button v-for="variable in variables" :key="variable.value" size="small" @click="insertVariable(variable.value)">
              {{ variable.label }} {{ variable.value }}
            </el-button>
          </div>
        </el-form-item>

        <el-form-item label="通报生成 Prompt">
          <el-input
            v-model="promptTemplate"
            maxlength="1500"
            show-word-limit
            type="textarea"
            :autosize="{ minRows: 8, maxRows: 16 }"
            placeholder="请输入 Prompt 模板内容，支持占位符 {{time}}, {{location}}, {{camera_id}}, {{violation_count}}"
          />
        </el-form-item>

        <el-alert
          title="模板说明: 支持的动态变量包括 {{time}} (检测时间), {{location}} (设备位置), {{camera_id}} (设备编号), {{violation_count}} (确认违停数量)"
          type="info"
          show-icon
          style="margin-bottom: 20px;"
          :closable="false"
        />

        <el-form-item>
          <el-button type="primary" @click="savePrompt" :loading="saving">保存修改</el-button>
          <el-button @click="previewPrompt">模板预览</el-button>
          <el-button type="warning" plain @click="resetPrompt">恢复默认模板</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="panel-card">
      <div class="card-header-row">
        <div>
          <div class="card-title">自动报告生成</div>
          <div class="card-subtitle">定时将已确认违规记录生成通报。</div>
        </div>
      </div>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="自动生成状态">
          <el-switch v-model="autoReport.enabled" @change="saveAutoReportEnabled" />
        </el-descriptions-item>
        <el-descriptions-item label="执行规则">{{ autoReport.cron }}</el-descriptions-item>
        <el-descriptions-item label="最近执行时间">{{ autoReport.lastRunTime || '暂无' }}</el-descriptions-item>
        <el-descriptions-item label="最近生成数量">{{ autoReport.lastGeneratedCount || 0 }}</el-descriptions-item>
      </el-descriptions>
      <div class="setting-actions">
        <el-button type="success" @click="runAutoReportOnce">立即执行一次</el-button>
      </div>
    </div>

    <el-dialog v-model="previewVisible" title="Prompt 预览" width="720px">
      <pre class="preview-box">{{ previewText }}</pre>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/utils/request'
import { ElMessage, ElMessageBox } from 'element-plus'

const promptTemplate = ref('')
const saving = ref(false)
const previewVisible = ref(false)
const previewText = ref('')
const autoReport = ref({
  enabled: false,
  cron: '每天 18:00 自动生成已确认违规通报',
  lastRunTime: '',
  lastGeneratedCount: 0
})
const variables = [
  { label: '检测时间', value: '{{time}}' },
  { label: '地点', value: '{{location}}' },
  { label: '设备编号', value: '{{camera_id}}' },
  { label: '违停数量', value: '{{violation_count}}' }
]

const loadPrompt = async () => {
  try {
    promptTemplate.value = await request.get('/api/settings/prompt')
  } catch (error) {
    console.error(error)
  }
}

const loadAutoReportStatus = async () => {
  try {
    autoReport.value = await request.get('/api/auto-report/status')
  } catch (error) {
    console.error(error)
  }
}

const saveAutoReportEnabled = async () => {
  await request.post('/api/auto-report/enabled', { enabled: autoReport.value.enabled })
  ElMessage.success(autoReport.value.enabled ? '已开启自动报告' : '已关闭自动报告')
  loadAutoReportStatus()
}

const runAutoReportOnce = async () => {
  const status = await request.post('/api/auto-report/run-once')
  autoReport.value = status
  ElMessage.success(`本次生成 ${status.generatedCount || 0} 条通报`)
}

const insertVariable = (variable) => {
  promptTemplate.value += variable
}

const previewPrompt = () => {
  previewText.value = promptTemplate.value
    .replaceAll('{{time}}', '2026-04-27 08:30:00')
    .replaceAll('{{location}}', '南门停车区，当前画面共发现 2 辆违停')
    .replaceAll('{{camera_id}}', 'CAM_SOUTH_GATE_01')
    .replaceAll('{{violation_count}}', '2')
  previewVisible.value = true
}

const resetPrompt = async () => {
  await ElMessageBox.confirm('确认恢复默认 Prompt 模板？当前未保存内容会被覆盖。', '提示', { type: 'warning' })
  await request.post('/api/settings/prompt/reset')
  ElMessage.success('已恢复默认模板')
  loadPrompt()
}

const savePrompt = async () => {
  if (!promptTemplate.value) {
    ElMessage.warning('Prompt 不能为空')
    return
  }
  saving.value = true
  try {
    await request.post('/api/settings/prompt', { template: promptTemplate.value })
    ElMessage.success('保存成功')
  } catch (error) {
    console.error(error)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadPrompt()
  loadAutoReportStatus()
})
</script>

<style scoped>
.variable-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.setting-actions {
  margin-top: 16px;
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
