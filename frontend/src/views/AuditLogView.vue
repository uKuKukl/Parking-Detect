<template>
  <div class="page-shell">
    <div class="page-header">
      <div>
        <h2 class="page-title">操作日志</h2>
        <p class="page-subtitle">追踪复核操作、操作人、操作类型和备注信息。</p>
      </div>
    </div>

    <div class="toolbar-card">
      <el-input v-model="filters.violationId" placeholder="违规记录 ID" clearable style="width: 160px" @keyup.enter="loadLogs" />
      <el-input v-model="filters.operatorId" placeholder="操作人 ID" clearable style="width: 160px" @keyup.enter="loadLogs" />
      <el-select v-model="filters.action" placeholder="操作类型" clearable style="width: 160px" @change="loadLogs">
        <el-option label="确认违规" value="CONFIRM" />
        <el-option label="驳回误报" value="REJECT" />
        <el-option label="正常归档" value="CLEAR" />
        <el-option label="更新" value="UPDATE" />
      </el-select>
      <el-button type="primary" @click="loadLogs">查询</el-button>
      <el-button @click="resetFilters">重置</el-button>
    </div>

    <div class="content-card">
      <el-table :data="logs" border>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="violationId" label="违规记录 ID" width="120" />
        <el-table-column prop="operatorId" label="操作人 ID" width="120" />
        <el-table-column label="操作类型" width="130">
          <template #default="scope">
            <el-tag>{{ actionLabel(scope.row.action) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="260" />
        <el-table-column prop="actionTime" label="操作时间" width="180" />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import request from '@/utils/request'

const logs = ref([])
const filters = ref({ violationId: '', operatorId: '', action: '' })

const actionLabel = (action) => {
  const map = { CONFIRM: '确认违规', REJECT: '驳回误报', CLEAR: '正常归档', UPDATE: '更新' }
  return map[action] || action
}

const loadLogs = async () => {
  const params = new URLSearchParams()
  if (filters.value.violationId) params.append('violationId', filters.value.violationId)
  if (filters.value.operatorId) params.append('operatorId', filters.value.operatorId)
  if (filters.value.action) params.append('action', filters.value.action)
  logs.value = await request.get(`/api/audit-logs?${params.toString()}`)
}

const resetFilters = () => {
  filters.value = { violationId: '', operatorId: '', action: '' }
  loadLogs()
}

onMounted(loadLogs)
</script>
