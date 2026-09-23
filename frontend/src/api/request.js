import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import router from '@/router'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

const bare = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

request.interceptors.request.use((config) => {
  const userStore = useUserStore()
  if (userStore.token) {
    config.headers.Authorization = `Bearer ${userStore.token}`
  }
  return config
})

let isRefreshing = false
let pendingQueue = []

function onRefreshed(token) {
  pendingQueue.forEach((cb) => cb(token))
  pendingQueue = []
}

request.interceptors.response.use(
  (response) => {
    const data = response.data
    // 后端 BizError 等业务异常返回 HTTP 200 + code!=0，需在成功分支内识别并抛错，
    // 避免「防循环嵌套/删除校验」等失败被前端误判为成功。
    if (data && typeof data === 'object' && typeof data.code === 'number' && data.code !== 0) {
      ElMessage.error(data.message || '操作失败')
      return Promise.reject(new Error(data.message || '操作失败'))
    }
    return data
  },
  async (error) => {
    const { response, config } = error
    const status = response?.status
    const url = config?.url || ''

    const isAuthUrl = url.includes('/auth/login') || url.includes('/auth/refresh')
    const userStore = useUserStore()

    if (status === 401 && !config?._retry && !isAuthUrl && userStore.refreshToken) {
      if (isRefreshing) {
        return new Promise((resolve) => {
          pendingQueue.push((token) => {
            config.headers.Authorization = `Bearer ${token}`
            config._retry = true
            resolve(request(config))
          })
        })
      }

      config._retry = true
      isRefreshing = true
      try {
        const resp = await bare.post('/auth/refresh', {
          refresh_token: userStore.refreshToken,
        })
        const data = resp.data
        userStore.setLogin(data.access_token, data.refresh_token, data.user)
        onRefreshed(data.access_token)
        config.headers.Authorization = `Bearer ${data.access_token}`
        return request(config)
      } catch (refreshErr) {
        onRefreshed('')
        userStore.logout()
        router.push('/login')
        return Promise.reject(refreshErr)
      } finally {
        isRefreshing = false
      }
    }

    if (status === 401) {
      userStore.logout()
      router.push('/login')
    }

    const msg = response?.data?.message || error.message || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(error)
  },
)

export default request
