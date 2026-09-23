import request from './request'

// 阶段二实现登录接口；此处预留统一封装
export function login(account, password) {
  return request.post('/auth/login', { account, password })
}

export function logout() {
  return request.post('/auth/logout')
}

export function getProfile() {
  return request.get('/auth/profile')
}