import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 50000, // Report generation can take time
  withCredentials: true
})

service.interceptors.response.use(
  response => {
    return response.data;
  },
  error => {
    const status = error.response?.status
    const message = typeof error.response?.data === 'string' && error.response.data
      ? error.response.data
      : error.message

    if (status === 401) {
      localStorage.removeItem('currentUser')
      if (router.currentRoute.value.name !== 'login') {
        ElMessage.error('登录状态已失效，请重新登录')
        router.push({ name: 'login' })
      }
      return Promise.reject(error)
    }

    if (status === 403) {
      ElMessage.error(message || '当前账号无权访问该功能')
      return Promise.reject(error)
    }

    ElMessage.error(message || '请求接口失败')
    return Promise.reject(error)
  }
)

export default service
