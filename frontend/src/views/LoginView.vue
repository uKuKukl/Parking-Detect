<template>
  <div class="login-page">
    <div class="login-hero">
      <div class="login-brand">
        <div class="login-logo">P</div>
        <div>
          <h1>校园违规停车报告生成系统</h1>
          <p>AI 视觉识别、人工复核、智能通报与数据分析一体化平台</p>
        </div>
      </div>
      <div class="feature-list">
        <div>YOLOv8 违规识别</div>
        <div>多角色复核流程</div>
        <div>LLM 智能通报生成</div>
      </div>
    </div>

    <el-card class="login-card" shadow="never">
      <h2>登录后台</h2>
      <p class="login-subtitle">请输入账号密码进入管理系统</p>
      <el-form :model="form" @keyup.enter="handleLogin">
        <el-form-item>
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            size="large"
            :prefix-icon="User"
            clearable
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-button
          class="login-button"
          type="primary"
          size="large"
          :loading="loading"
          @click="handleLogin"
        >
          登录
        </el-button>
      </el-form>

      <div class="login-tips">
        <p>管理员：admin / admin123</p>
        <p>审核员：auditor / auditor123</p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import request from '@/utils/request'

const router = useRouter()
const loading = ref(false)
const form = ref({ username: '', password: '' })

const handleLogin = async () => {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('请填写用户名和密码')
    return
  }
  loading.value = true
  try {
    const res = await request.post('/api/auth/login', form.value)
    if (res.success) {
      // 存到 localStorage，供全局使用
      localStorage.setItem('currentUser', JSON.stringify({
        userId: res.userId,
        username: res.username,
        realName: res.realName,
        role: res.role
      }))
      ElMessage.success(`欢迎回来，${res.realName || res.username}！`)
      router.push('/audit')
    } else {
      ElMessage.error(res.message || '登录失败')
    }
  } catch (e) {
    ElMessage.error('登录请求失败，请检查后端服务')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(360px, 1fr) 420px;
  align-items: center;
  gap: 48px;
  padding: 48px 8vw;
  background:
    radial-gradient(circle at 18% 18%, rgba(37, 99, 235, 0.16), transparent 34%),
    linear-gradient(135deg, #f8fbff 0%, #eef4ff 48%, #f8fafc 100%);
}

.login-hero {
  max-width: 680px;
}

.login-brand {
  display: flex;
  align-items: flex-start;
  gap: 18px;
}

.login-logo {
  width: 58px;
  height: 58px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 18px;
  background: var(--admin-primary);
  color: #fff;
  font-size: 26px;
  font-weight: 900;
  box-shadow: 0 18px 42px rgba(37, 99, 235, 0.24);
}

.login-brand h1 {
  margin: 0;
  color: var(--admin-text);
  font-size: 38px;
  line-height: 1.18;
  font-weight: 900;
  letter-spacing: -0.04em;
}

.login-brand p {
  margin: 14px 0 0;
  color: var(--admin-text-muted);
  font-size: 16px;
  line-height: 1.8;
}

.feature-list {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 36px;
}

.feature-list div {
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 999px;
  color: var(--admin-primary);
  font-weight: 700;
}

.login-card {
  padding: 18px;
  border-radius: 24px !important;
}

.login-card h2 {
  margin: 0;
  color: var(--admin-text);
  font-size: 26px;
  font-weight: 900;
}

.login-subtitle {
  margin: 8px 0 28px;
  color: var(--admin-text-muted);
}

.login-button {
  width: 100%;
}

.login-tips {
  margin-top: 18px;
  padding: 12px;
  border-radius: 12px;
  background: var(--admin-surface-soft);
  color: var(--admin-text-muted);
  font-size: 12px;
  line-height: 1.6;
}

.login-tips p {
  margin: 0;
}

@media (max-width: 900px) {
  .login-page {
    grid-template-columns: 1fr;
    padding: 32px;
  }
}
</style>
