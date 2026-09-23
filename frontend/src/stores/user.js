import { defineStore } from 'pinia'
import { getToken, setToken, clearToken, getUserInfo, setUserInfo, clearUserInfo } from '@/utils/auth'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: getToken() || '',
    userInfo: getUserInfo() || null,
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    isSuper: (state) => !!state.userInfo?.is_super,
  },
  actions: {
    setLogin(token, userInfo = null) {
      this.token = token
      this.userInfo = userInfo
      setToken(token)
      if (userInfo) setUserInfo(userInfo)
    },
    setUserInfo(userInfo) {
      this.userInfo = userInfo
      setUserInfo(userInfo)
    },
    logout() {
      this.token = ''
      this.userInfo = null
      clearToken()
      clearUserInfo()
    },
  },
})