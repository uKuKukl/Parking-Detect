<template>
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
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="cameraId" label="设备编号" width="180" />
      <el-table-column prop="name" label="设备名称" width="180" />
      <el-table-column prop="location" label="安装位置" min-width="220" />
      <el-table-column prop="roiId" label="绑定 ROI" width="120" />
      <el-table-column label="状态" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.status === 1 ? 'success' : 'info'">
            {{ scope.row.status === 1 ? '在线' : '离线' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="createTime" label="创建时间" width="180" />
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="scope">
          <el-button size="small" @click="openDialog(scope.row)">编辑</el-button>
          <el-button size="small" type="danger" @click="removeDevice(scope.row.id)">删除</el-button>
        </template>
      </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑摄像头' : '新增摄像头'" width="520px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="设备编号">
          <el-input v-model="form.cameraId" placeholder="如 CAM_SOUTH_GATE_01" />
        </el-form-item>
        <el-form-item label="设备名称">
          <el-input v-model="form.name" placeholder="如 南门入口摄像头" />
        </el-form-item>
        <el-form-item label="安装位置">
          <el-input v-model="form.location" placeholder="如 南门停车区" />
        </el-form-item>
        <el-form-item label="绑定 ROI">
          <el-select v-model="form.roiId" clearable placeholder="可选" style="width: 100%">
            <el-option v-for="roi in rois" :key="roi.id" :label="roi.name" :value="roi.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio-button :label="1">在线</el-radio-button>
            <el-radio-button :label="0">离线</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveDevice">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

const devices = ref([])
const rois = ref([])
const dialogVisible = ref(false)
const form = ref({})

const loadDevices = async () => {
  devices.value = await request.get('/api/cameras')
}

const loadRois = async () => {
  rois.value = await request.get('/api/rois')
}

const openDialog = (row) => {
  form.value = row ? { ...row } : { cameraId: '', name: '', location: '', roiId: null, status: 1 }
  dialogVisible.value = true
}

const saveDevice = async () => {
  if (!form.value.cameraId || !form.value.name) {
    ElMessage.warning('请填写设备编号和设备名称')
    return
  }
  if (form.value.id) {
    await request.put(`/api/cameras/${form.value.id}`, form.value)
  } else {
    await request.post('/api/cameras', form.value)
  }
  ElMessage.success('保存成功')
  dialogVisible.value = false
  loadDevices()
}

const removeDevice = async (id) => {
  await ElMessageBox.confirm('确认删除该摄像头？', '提示', { type: 'warning' })
  await request.delete(`/api/cameras/${id}`)
  ElMessage.success('删除成功')
  loadDevices()
}

onMounted(() => {
  loadDevices()
  loadRois()
})
</script>
