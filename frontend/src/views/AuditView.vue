<template>
  <div>
    <h2>违规复核台 (待处理事件)</h2>
    
    <div style="margin-bottom: 20px; display: flex; align-items: center; gap: 12px;">
      <el-button type="primary" @click="fetchData">刷新列表</el-button>
      <el-upload
        class="upload-demo"
        action="http://localhost:8080/api/violations/upload-image"
        :show-file-list="false"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        accept="image/*"
      >
        <el-button type="success" :icon="Upload">上传本地图片联调检测</el-button>
      </el-upload>
    </div>

    <el-table :data="tableData" border style="width: 100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="detectTime" label="识别时间" width="180" />
      <el-table-column prop="location" label="地点" width="180" />
      <el-table-column prop="cameraId" label="设备 ID" width="150" />
      <el-table-column prop="confidence" label="置信度" width="100">
        <template #default="scope">
          {{ (scope.row.confidence * 100).toFixed(1) }}%
        </template>
      </el-table-column>
      <el-table-column prop="imagePath" label="现场截图" width="200">
        <template #default="scope">
          <el-text class="w-150px mb-2" truncated>{{ scope.row.imagePath }}</el-text>
        </template>
      </el-table-column>
      
      <el-table-column label="操作" width="200">
        <template #default="scope">
          <el-button size="small" type="success" @click="handleConfirm(scope.row.id)">
            确认违规
          </el-button>
          <el-button size="small" type="danger" @click="handleReject(scope.row.id)">
            误报驳回
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'

const tableData = ref([])

const fetchData = async () => {
  try {
    tableData.value = await request.get('/api/violations/pending')
  } catch (error) {
    console.error(error)
  }
}

const handleConfirm = async (id) => {
  await request.post(`/api/violations/${id}/status`, { status: 1 })
  ElMessage.success('已确认违规')
  fetchData()
}

const handleReject = async (id) => {
  await request.post(`/api/violations/${id}/status`, { status: 2 })
  ElMessage.info('已驳回误报')
  fetchData()
}

const handleUploadSuccess = (response) => {
  ElMessage.success(response || '已成功触发检测并返回数据！')
  // 给后端与本地 DB 写入一点缓冲时间
  setTimeout(() => {
    fetchData()
  }, 1000)
}

const handleUploadError = (err) => {
  ElMessage.error('上传图片触发检测失败！')
  console.error(err)
}

onMounted(() => {
  fetchData()
})
</script>
