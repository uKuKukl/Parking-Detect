<template>
  <div class="page-shell roi-settings">
    <div class="page-header">
      <div>
        <h2 class="page-title">电子围栏配置</h2>
        <p class="page-subtitle">配置 ROI 区域规则，并为摄像头检测提供场地边界约束。</p>
      </div>
    </div>

    <el-row :gutter="20">
      <!-- 左侧：新建规则 -->
      <el-col :span="12">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="card-header">新增场地围栏规则 (合法停车区)</div>
          </template>
          
          <el-form label-width="100px">
            <el-form-item label="地点预设">
              <el-select v-model="selectedPresetCode" style="width: 100%;" @change="applyPresetSelection">
                <el-option
                  v-for="preset in locationPresets"
                  :key="preset.code"
                  :label="preset.label"
                  :value="preset.code"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="场地名称">
              <el-input
                v-model="newRuleName"
                placeholder="例如：南大门停车区"
                :disabled="selectedPresetCode !== 'custom'"
              />
            </el-form-item>

            <el-form-item v-if="selectedPresetCode === 'custom'" label="英文地点">
              <el-input
                v-model="customCameraSuffix"
                placeholder="例如：SOUTH_GATE"
                @input="normalizeCustomCameraSuffix"
              />
            </el-form-item>

            <el-form-item label="绑定摄像头">
              <el-input :model-value="generatedCameraId" disabled placeholder="会自动生成摄像头编号" />
            </el-form-item>
            
            <el-form-item label="参考底图">
              <input type="file" accept="image/*" @change="onImageSelected" />
              <div style="font-size: 12px; color: #999; margin-top: 5px;">
                请先选择地点预设，再上传一张真实的监控截图作为参考底图，在图上点击绘制“合法停车范围”。
              </div>
            </el-form-item>
            
            <div v-if="imageUrl" class="canvas-container">
              <img ref="bgImage" :src="imageUrl" @load="onImageLoad" style="display: none;" />
              <canvas 
                ref="roiCanvas" 
                @click="onCanvasClick" 
                @contextmenu.prevent="undoPoint"
                class="roi-canvas"
              ></canvas>
            </div>
            
            <div style="margin-top: 15px;" v-if="imageUrl">
              <el-button type="info" @click="clearPoints" size="small">清空重画</el-button>
              <span style="font-size: 12px; color: #666; margin-left: 10px;">
                操作提示：左键点击描点，右键撤销上一点。画一个闭合的绿色多边形表示能停车的区域。
              </span>
            </div>
            
            <div style="margin-top: 20px; text-align: right;">
              <el-button type="primary" @click="saveRule" :disabled="!newRuleName || !generatedCameraId || points.length < 3">保存该场景规则</el-button>
            </div>
          </el-form>
        </el-card>
      </el-col>
      
      <!-- 右侧：现有规则列表 -->
      <el-col :span="12">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="card-header">已有规则列表</div>
          </template>
          
          <el-table :data="rulesList" stripe style="width: 100%">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="name" label="场地名称" />
            <el-table-column label="绑定摄像头" width="170">
              <template #default="scope">
                {{ getBoundCameraId(scope.row.id) || '未绑定' }}
              </template>
            </el-table-column>
            <el-table-column prop="createTime" label="创建时间" width="180" />
            <el-table-column label="操作" width="120">
              <template #default="scope">
                <el-button size="small" type="danger" @click="deleteRule(scope.row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import request from '@/utils/request'
import { ElMessage, ElMessageBox } from 'element-plus'

const rulesList = ref([])
const newRuleName = ref('')
const cameraList = ref([])
const selectedPresetCode = ref('south_gate')
const customCameraSuffix = ref('')
const imageUrl = ref('')
const points = ref([])

const locationPresets = [
  { code: 'south_gate', label: '南门', ruleName: '南门', cameraSuffix: 'SOUTH_GATE' },
  { code: 'west_gate', label: '西门', ruleName: '西门', cameraSuffix: 'WEST_GATE' },
  { code: 'east_gate', label: '东门', ruleName: '东门', cameraSuffix: 'EAST_GATE' },
  { code: 'north_gate', label: '北门', ruleName: '北门', cameraSuffix: 'NORTH_GATE' },
  { code: 'custom', label: '自定义', ruleName: '', cameraSuffix: '' }
]

const bgImage = ref(null)
const roiCanvas = ref(null)
let imageOriginalWidth = 0
let imageOriginalHeight = 0
let currentObjectUrl = ''

const selectedPreset = computed(() => {
  return locationPresets.find(item => item.code === selectedPresetCode.value) || locationPresets[0]
})

const generatedCameraId = computed(() => {
  const suffix = selectedPresetCode.value === 'custom'
    ? customCameraSuffix.value.trim()
    : selectedPreset.value.cameraSuffix

  return suffix ? `CAM_${suffix}` : ''
})

// 获取已有规则
const fetchRules = async () => {
  try {
    const res = await request.get('/api/rois')
    rulesList.value = res
  } catch (error) {
    console.error(error)
  }
}

const fetchCameras = async () => {
  try {
    cameraList.value = await request.get('/api/cameras')
  } catch (error) {
    console.error(error)
  }
}

const applyPresetSelection = () => {
  if (selectedPresetCode.value === 'custom') {
    newRuleName.value = ''
    customCameraSuffix.value = ''
    return
  }
  newRuleName.value = selectedPreset.value.ruleName
}

const normalizeCustomCameraSuffix = () => {
  customCameraSuffix.value = customCameraSuffix.value
    .toUpperCase()
    .replace(/\s+/g, '_')
    .replace(/[^A-Z0-9_-]+/g, '')
    .replace(/_+/g, '_')
    .replace(/-+/g, '-')
}

const getBoundCameraId = (roiId) => {
  const camera = cameraList.value.find(item => item.roiId === roiId)
  return camera?.cameraId || ''
}

// 选择图片后展示
const onImageSelected = (e) => {
  const file = e.target.files[0]
  if (file) {
    if (currentObjectUrl) {
      URL.revokeObjectURL(currentObjectUrl)
    }
    currentObjectUrl = URL.createObjectURL(file)
    imageUrl.value = currentObjectUrl
    points.value = [] // 重置点
  }
}

// 图片加载完毕后初始化 Canvas 大小
const onImageLoad = () => {
  const img = bgImage.value
  const canvas = roiCanvas.value
  imageOriginalWidth = img.naturalWidth
  imageOriginalHeight = img.naturalHeight
  
  canvas.width = imageOriginalWidth
  canvas.height = imageOriginalHeight
  
  redrawCanvas()
}

// 在 Canvas 上点击落点
const onCanvasClick = (e) => {
  const canvas = roiCanvas.value
  const rect = canvas.getBoundingClientRect()
  // 计算点击在真实的 CSS 渲染坐标占 canvas 的比例，转换为真实原图坐标
  const scaleX = canvas.width / rect.width
  const scaleY = canvas.height / rect.height
  const x = Math.round((e.clientX - rect.left) * scaleX)
  const y = Math.round((e.clientY - rect.top) * scaleY)
  
  points.value.push([x, y])
  redrawCanvas()
}

// 右键撤销
const undoPoint = () => {
  if (points.value.length > 0) {
    points.value.pop()
    redrawCanvas()
  }
}

const clearPoints = () => {
  points.value = []
  redrawCanvas()
}

// 重新绘制底图和走线
const redrawCanvas = () => {
  const canvas = roiCanvas.value
  const ctx = canvas.getContext('2d')
  
  // 1. 画底图
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.drawImage(bgImage.value, 0, 0, canvas.width, canvas.height)
  
  // 2. 画点与线
  if (points.value.length > 0) {
    ctx.strokeStyle = '#00FF00'
    ctx.lineWidth = 3
    ctx.fillStyle = '#FF0000'
    
    ctx.beginPath()
    points.value.forEach((p, index) => {
      // 画面
      if (index === 0) ctx.moveTo(p[0], p[1])
      else ctx.lineTo(p[0], p[1])
      
      // 画点
      ctx.fillRect(p[0]-4, p[1]-4, 8, 8)
    })
    
    // 如果点数 > 2，闭合多边形并填充半透明色
    if (points.value.length > 2) {
      ctx.closePath()
      ctx.fillStyle = 'rgba(0, 255, 0, 0.2)'
      ctx.fill()
    }
    ctx.stroke()
  }
}

// 保存规则到后端
const saveRule = async () => {
  try {
    const payload = {
      name: newRuleName.value,
      pointsJson: JSON.stringify(points.value), // 转换成 "[[x,y],[x,y]]" 字符串
      referenceWidth: imageOriginalWidth,
      referenceHeight: imageOriginalHeight,
      cameraId: generatedCameraId.value,
      cameraName: generatedCameraId.value,
      location: newRuleName.value
    }
    await request.post('/api/rois/bind-camera', payload)
    ElMessage.success(`规则保存成功，已绑定摄像头 ${generatedCameraId.value}`)
    
    selectedPresetCode.value = 'south_gate'
    newRuleName.value = ''
    customCameraSuffix.value = ''
    points.value = []
    imageOriginalWidth = 0
    imageOriginalHeight = 0
    if (currentObjectUrl) {
      URL.revokeObjectURL(currentObjectUrl)
      currentObjectUrl = ''
    }
    imageUrl.value = ''
    fetchRules()
    fetchCameras()
    applyPresetSelection()
  } catch (error) {
    console.error(error)
  }
}

const deleteRule = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除吗？', '提示', { type: 'warning' })
    await request.delete(`/api/rois/${id}`)
    ElMessage.success('删除成功')
    fetchRules()
    fetchCameras()
  } catch (cancel) {}
}

onMounted(() => {
  applyPresetSelection()
  fetchRules()
  fetchCameras()
})
</script>

<style scoped>
.card-header {
  font-weight: 800;
  color: var(--admin-text);
}

.canvas-container {
  margin-top: 15px;
  width: 100%;
  max-width: 600px;
  border: 1px solid var(--admin-border);
  border-radius: 14px;
  overflow: hidden;
  background-color: var(--admin-surface-soft);
}

.roi-canvas {
  width: 100%;
  height: auto;
  display: block;
  cursor: crosshair;
}
</style>
