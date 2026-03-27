import axios from 'axios'
import { ElMessage } from 'element-plus'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8080',
  timeout: 50000 // Report generation can take time
})

service.interceptors.response.use(
  response => {
    return response.data;
  },
  error => {
    ElMessage.error(error.message || '请求接口失败')
    return Promise.reject(error)
  }
)

export default service
