<template>
  <div class="page-shell audit-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">违规复核台</h2>
        <p class="page-subtitle">筛选、查看和人工复核 YOLO 检测到的违规停车记录。</p>
      </div>
    </div>

    <div class="toolbar-card">
      <el-select v-model="filters.status" placeholder="状态" clearable style="width: 150px" @change="fetchData">
        <el-option label="待复核" :value="0" />
        <el-option label="已确认" :value="1" />
        <el-option label="已驳回" :value="2" />
        <el-option label="已生成通报" :value="3" />
        <el-option label="正常归档" :value="4" />
      </el-select>
      <el-input v-model="filters.cameraId" placeholder="设备编号" clearable style="width: 160px" @keyup.enter="fetchData" />
      <el-input v-model="filters.keyword" placeholder="地点关键词" clearable style="width: 180px" @keyup.enter="fetchData" />
      <el-date-picker
        v-model="filters.dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        value-format="YYYY-MM-DD"
        style="width: 280px"
        @change="fetchData"
      />
      <el-button type="primary" @click="fetchData">查询/刷新</el-button>
      <el-button @click="resetFilters">重置</el-button>

      <el-select v-model="selectedRoiId" placeholder="选择场地防误报规则 (可选)" clearable style="width: 250px;">
        <el-option
          v-for="rule in rulesList"
          :key="rule.id"
          :label="rule.name"
          :value="rule.id"
        />
      </el-select>

      <el-upload
        class="upload-demo"
        :action="uploadAction"
        :data="{ roiId: selectedRoiId }"
        :show-file-list="false"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        accept="image/*"
      >
        <el-button type="success" :icon="Upload">上传本地图片联调检测</el-button>
      </el-upload>
    </div>

    <div class="content-card">
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
          <div class="image-cell">
            <el-button link type="primary" @click="openImagePreview(scope.row)">
              查看检测图
            </el-button>
            <el-button link type="info" @click="openDecisionDialog(scope.row)">
              判定依据
            </el-button>
            <el-text class="image-path" truncated>{{ scope.row.imagePath }}</el-text>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column label="AI 判断" width="120">
        <template #default="scope">
          <el-tag
            :type="isZeroViolation(scope.row) ? 'success' : 'danger'"
            size="small"
          >
            {{ isZeroViolation(scope.row) ? '✓ 未检测到违停' : '⚠ 检测到违停' }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="280">
        <template #default="scope">
          <!-- 有违停：确认违规 / 误报驳回 -->
          <template v-if="!isZeroViolation(scope.row)">
            <el-button size="small" type="danger" @click="openConfirmDialog(scope.row)">
              确认违规/修正数量
            </el-button>
            <el-button size="small" type="warning" @click="handleReject(scope.row.id)">
              误报驳回
            </el-button>
          </template>
          <!-- 无违停：正常归档（AI 说没问题，人工确认） -->
          <template v-else>
            <el-button size="small" type="success" @click="handleClear(scope.row.id)">
              ✓ 正常归档
            </el-button>
            <el-button size="small" type="danger" @click="openManualConfirm(scope.row)">
              发现遗漏违停
            </el-button>
          </template>
        </template>
      </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.size"
        :page-sizes="[10, 20, 50]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchData"
        @current-change="fetchData"
        />
      </div>
    </div>

    <el-dialog
      v-model="manualDialogVisible"
      title="人工补录违停数量"
      width="520px"
      destroy-on-close
    >
      <el-form label-position="top">
        <el-form-item label="人工确认违停数量">
          <el-input-number
            v-model="manualReviewForm.manualViolationCount"
            :min="1"
            :max="99"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="复核备注（可选）">
          <el-input
            v-model="manualReviewForm.remark"
            type="textarea"
            :autosize="{ minRows: 3, maxRows: 6 }"
            placeholder="可补充填写：区域偏移、画面遮挡、逆光/夜间光照、人工确认依据等"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <span>
          <el-button @click="manualDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitManualConfirm">确认补录</el-button>
        </span>
      </template>
    </el-dialog>

    <el-dialog
      v-model="imageDialogVisible"
      title="YOLO 检测结果预览"
      width="900px"
      destroy-on-close
    >
      <div v-loading="imageLoading" class="preview-wrapper">
        <el-empty v-if="!previewImageUrl" description="暂无可预览的检测图" />
        <img
          v-else
          :src="previewImageUrl"
          alt="YOLO 检测结果图"
          class="preview-image"
          @load="handlePreviewLoaded"
          @error="handlePreviewError"
        />
      </div>
      <el-descriptions v-if="previewRow" :column="2" border size="small" class="preview-meta">
        <el-descriptions-item label="记录 ID">{{ previewRow.id }}</el-descriptions-item>
        <el-descriptions-item label="识别时间">{{ previewRow.detectTime }}</el-descriptions-item>
        <el-descriptions-item label="地点">{{ previewRow.location }}</el-descriptions-item>
        <el-descriptions-item label="设备 ID">{{ previewRow.cameraId }}</el-descriptions-item>
        <el-descriptions-item label="截图路径" :span="2">{{ previewRow.imagePath }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <el-dialog
      v-model="decisionDialogVisible"
      title="算法判定依据"
      width="860px"
      destroy-on-close
    >
      <el-empty v-if="!decisionInfo.raw && !decisionInfo.parsed" description="暂无判定详情" />

      <template v-else-if="decisionInfo.parsed">
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item label="算法" :span="3">
            {{ decisionInfo.parsed.algorithm || '未知' }}
          </el-descriptions-item>
          <el-descriptions-item label="处理帧数">
            {{ decisionInfo.parsed.processedFrames ?? '未知' }}
          </el-descriptions-item>
          <el-descriptions-item label="检测框总数">
            {{ decisionInfo.parsed.totalDetections ?? '未知' }}
          </el-descriptions-item>
          <el-descriptions-item label="确认违停目标">
            {{ decisionInfo.parsed.confirmedViolationCount ?? 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="ROI 重叠阈值">
            {{ formatRatio(decisionInfo.parsed.roiOverlapThreshold) }}
          </el-descriptions-item>
          <el-descriptions-item label="IoU 关联阈值">
            {{ formatRatio(decisionInfo.parsed.trackIouThreshold) }}
          </el-descriptions-item>
          <el-descriptions-item label="滞留帧阈值">
            {{ decisionInfo.parsed.dwellFrameThreshold ?? '未知' }}
          </el-descriptions-item>
        </el-descriptions>

        <el-table
          :data="decisionTracks"
          border
          size="small"
          class="decision-table"
        >
          <el-table-column prop="trackId" label="Track ID" width="90" />
          <el-table-column prop="className" label="类别" width="110" />
          <el-table-column label="置信度" width="100">
            <template #default="scope">{{ formatRatio(scope.row.confidence) }}</template>
          </el-table-column>
          <el-table-column label="ROI 重叠" width="110">
            <template #default="scope">{{ formatRatio(scope.row.legalOverlapRatio) }}</template>
          </el-table-column>
          <el-table-column prop="dwellFrames" label="当前滞留帧" width="110" />
          <el-table-column prop="maxDwellFrames" label="最大滞留帧" width="110" />
          <el-table-column label="候选状态" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.violationCandidate ? 'danger' : 'success'" size="small">
                {{ scope.row.violationCandidate ? '违停候选' : '合法/过滤' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="原因" min-width="180">
            <template #default="scope">{{ reasonLabel(scope.row.reason) }}</template>
          </el-table-column>
        </el-table>
      </template>

      <el-input
        v-else
        :model-value="decisionInfo.raw"
        type="textarea"
        :autosize="{ minRows: 8, maxRows: 16 }"
        readonly
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'

const tableData = ref([])
const rulesList = ref([])
const filters = ref({
  status: 0,
  cameraId: '',
  keyword: '',
  dateRange: []
})
const pagination = ref({
  page: 1,
  size: 10,
  total: 0
})
const selectedRoiId = ref(null)
const uploadAction = `${(import.meta.env.VITE_API_URL || '').replace(/\/$/, '')}/api/violations/upload-image` || '/api/violations/upload-image'
const apiBaseUrl = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')
const manualDialogVisible = ref(false)
const imageDialogVisible = ref(false)
const decisionDialogVisible = ref(false)
const imageLoading = ref(false)
const previewImageUrl = ref('')
const previewRow = ref(null)
const decisionInfo = ref({
  parsed: null,
  raw: ''
})
const manualReviewForm = ref({
  id: null,
  manualViolationCount: 1,
  remark: ''
})

const parseViolationCount = (locationText) => {
  if (!locationText) return null
  const match = locationText.match(/当前画面共发现\s*(\d+)\s*辆违停/)
  if (!match) return null
  const count = Number(match[1])
  return Number.isInteger(count) ? count : null
}

const fetchData = async () => {
  try {
    const params = new URLSearchParams()
    if (filters.value.status !== null && filters.value.status !== undefined && filters.value.status !== '') {
      params.append('status', filters.value.status)
    }
    if (filters.value.cameraId) params.append('cameraId', filters.value.cameraId.trim())
    if (filters.value.keyword) params.append('keyword', filters.value.keyword.trim())
    if (filters.value.dateRange?.length === 2) {
      params.append('startDate', filters.value.dateRange[0])
      params.append('endDate', filters.value.dateRange[1])
    }
    params.append('page', pagination.value.page)
    params.append('size', pagination.value.size)

    const data = await request.get(`/api/violations?${params.toString()}`)
    tableData.value = data.records || []
    pagination.value.total = Number(data.total) || 0
  } catch (error) {
    console.error(error)
  }
}

const resetFilters = () => {
  filters.value = { status: 0, cameraId: '', keyword: '', dateRange: [] }
  pagination.value.page = 1
  fetchData()
}

const fetchRules = async () => {
  try {
    rulesList.value = await request.get('/api/rois')
  } catch (error) {
    console.error(error)
  }
}

const openManualConfirm = (row) => {
  manualReviewForm.value = {
    id: row.id,
    manualViolationCount: 1,
    remark: ''
  }
  manualDialogVisible.value = true
}

const openConfirmDialog = (row) => {
  const detectedCount = parseViolationCount(row.location)
  manualReviewForm.value = {
    id: row.id,
    manualViolationCount: detectedCount && detectedCount > 0 ? detectedCount : 1,
    remark: ''
  }
  manualDialogVisible.value = true
}

const submitManualConfirm = async () => {
  const count = Number(manualReviewForm.value.manualViolationCount)
  if (!Number.isInteger(count) || count < 1) {
    ElMessage.warning('请填写至少 1 辆违停车辆')
    return
  }

  await request.post(`/api/violations/${manualReviewForm.value.id}/status`, {
    status: 1,
    manualViolationCount: count,
    remark: manualReviewForm.value.remark?.trim() || null
  })

  manualDialogVisible.value = false
  ElMessage.success(`已确认违规，数量更新为 ${count} 辆`)
  fetchData()
}

const handleReject = async (id) => {
  await request.post(`/api/violations/${id}/status`, { status: 2 })
  ElMessage.info('已驳回误报')
  fetchData()
}

// 无违停正常归档（status=4）
const handleClear = async (id) => {
  await request.post(`/api/violations/${id}/status`, { status: 4 })
  ElMessage.success('已归档为正常巡检记录')
  fetchData()
}

// 判断该条记录是否为“0 违停”的平常巡检
// location 字段中含有 "发现 0 辆违停" 标识
const isZeroViolation = (row) => {
  return row.location && row.location.includes('发现 0 辆违停')
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

const openImagePreview = (row) => {
  previewRow.value = row
  imageLoading.value = true
  previewImageUrl.value = `${apiBaseUrl}/api/violations/${row.id}/image?t=${Date.now()}`
  imageDialogVisible.value = true
}

const handlePreviewLoaded = () => {
  imageLoading.value = false
}

const handlePreviewError = () => {
  imageLoading.value = false
  previewImageUrl.value = ''
  ElMessage.error('检测图加载失败，请确认后端图片文件仍存在')
}

const openDecisionDialog = (row) => {
  const raw = row.decisionDetails || ''
  if (!raw) {
    decisionInfo.value = { parsed: null, raw: '' }
  } else {
    try {
      decisionInfo.value = { parsed: JSON.parse(raw), raw }
    } catch (error) {
      decisionInfo.value = { parsed: null, raw }
    }
  }
  decisionDialogVisible.value = true
}

const decisionTracks = computed(() => {
  const parsed = decisionInfo.value.parsed
  if (!parsed) return []
  const confirmed = Array.isArray(parsed.confirmedViolations) ? parsed.confirmedViolations : []
  const tracks = Array.isArray(parsed.tracks) ? parsed.tracks : []
  return confirmed.length ? confirmed : tracks
})

const formatRatio = (value) => {
  const number = Number(value)
  if (!Number.isFinite(number)) return '未知'
  return `${(number * 100).toFixed(1)}%`
}

const reasonLabel = (reason) => {
  const map = {
    INSIDE_LEGAL_ROI: '主要位于合法停放区内',
    OUTSIDE_LEGAL_ROI: '位于合法停放区外',
    NO_ROI_FULL_FRAME_RESTRICTED: '未配置 ROI，按全图禁停处理',
    MISSING_THIS_FRAME: '当前帧未匹配到该目标'
  }
  return map[reason] || reason || '未知'
}

onMounted(() => {
  fetchData()
  fetchRules()
})
</script>

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

.decision-table {
  margin-top: 16px;
}
</style>
