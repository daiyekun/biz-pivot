import request from './request'

export function login(account, password) {
  return request.post('/auth/login', { account, password })
}

export function refresh(refreshToken) {
  return request.post('/auth/refresh', { refresh_token: refreshToken })
}

export function logout() {
  return request.post('/auth/logout')
}

export function getProfile() {
  return request.get('/auth/profile')
}
