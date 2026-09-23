const TOKEN_KEY = 'biz_pivot_token'
const REFRESH_KEY = 'biz_pivot_refresh_token'
const USER_KEY = 'biz_pivot_user'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY) || ''
}

export function setRefreshToken(token) {
  localStorage.setItem(REFRESH_KEY, token)
}

export function clearRefreshToken() {
  localStorage.removeItem(REFRESH_KEY)
}

export function getUserInfo() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || 'null')
  } catch {
    return null
  }
}

export function setUserInfo(info) {
  localStorage.setItem(USER_KEY, JSON.stringify(info))
}

export function clearUserInfo() {
  localStorage.removeItem(USER_KEY)
}
