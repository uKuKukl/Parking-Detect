<template>
  <div>
    <h2>系统设置</h2>
    
    <el-card shadow="never" style="max-width: 800px; margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>大模型 Prompt 模板配置</span>
        </div>
      </template>

      <el-form label-position="top">
        <el-form-item label="通报生成 Prompt">
          <el-input
            v-model="promptTemplate"
            maxlength="1000"
            show-word-limit
            type="textarea"
            :autosize="{ minRows: 6, maxRows: 15 }"
            placeholder="请输入 Prompt 模板内容，支持占位符 {{time}}, {{location}}, {{camera_id}}"
          />
        </el-form-item>
        
        <el-alert
          title="模板说明: 支持的动态变量包括 {{time}} (检测时间), {{location}} (设备位置), {{camera_id}} (设备编号)"
          type="info"
          show-icon
          style="margin-bottom: 20px;"
          :closable="false"
        />

        <el-form-item>
          <el-button type="primary" @click="savePrompt" :loading="saving">保存修改</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'

const promptTemplate = ref('')
const saving = ref(false)

const loadPrompt = async () => {
  try {
    const res = await request.get('/api/settings/prompt')
    // axios interceptor returned directly data which is a string from Spring Boot Controller
    promptTemplate.value = res
  } catch (error) {
    console.error(error)
  }
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
})
</script>
