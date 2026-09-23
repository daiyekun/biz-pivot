import { defineStore } from 'pinia'
import {
  getToken,
  setToken,
  clearToken,
  getRefreshToken,
  setRefreshToken,
  clearRefreshToken,
  getUserInfo,
  setUserInfo,
  clearUserInfo,
} from '@/utils/auth'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: getToken() || '',
    refreshToken: getRefreshToken() || '',
    userInfo: getUserInfo() || null,
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    isSuper: (state) => !!state.userInfo?.is_super,
  },
  actions: {
    setLogin(token, refreshToken, userInfo = null) {
      this.token = token
      this.refreshToken = refreshToken || ''
      this.userInfo = userInfo
      setToken(token)
      setRefreshToken(this.refreshToken)
      if (userInfo) setUserInfo(userInfo)
    },
    setUserInfo(userInfo) {
      this.userInfo = userInfo
      setUserInfo(userInfo)
    },
    logout() {
      this.token = ''
      this.refreshToken = ''
      this.userInfo = null
      clearToken()
      clearRefreshToken()
      clearUserInfo()
    },
  },
})
