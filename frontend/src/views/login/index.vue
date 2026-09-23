<template>
  <div class="login-wrapper">
    <el-card class="login-card" shadow="always">
      <div class="login-title">商枢 BizPivot</div>
      <div class="login-subtitle">企业智能AI平台</div>

      <el-form :model="form" @submit.prevent>
        <el-form-item>
          <el-input v-model="form.account" placeholder="登录账号" size="large">
            <template #prefix><el-icon><User /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="登录密码"
            size="large"
            show-password
            @keyup.enter="onLogin"
          >
            <template #prefix><el-icon><Lock /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" class="login-btn" :loading="loading" @click="onLogin">
            登 录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login } from '@/api/auth'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const form = reactive({ account: '', password: '' })
const loading = ref(false)

async function onLogin() {
  if (!form.account || !form.password) {
    ElMessage.warning('请输入账号和密码')
    return
  }
  loading.value = true
  try {
    const data = await login(form.account, form.password)
    userStore.setLogin(data.access_token, data.refresh_token, data.user)
    ElMessage.success('登录成功')
    const redirect = route.query.redirect || '/chat'
    router.push(redirect)
  } catch (e) {
    // 错误提示由 request 拦截器统一处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrapper {
  min-height: calc(100vh - 96px);
  display: flex;
  align-items: center;
  justify-content: center;
}
.login-card {
  width: 400px;
  padding: 12px 8px;
}
.login-title {
  font-size: 24px;
  font-weight: 700;
  text-align: center;
  color: #409eff;
}
.login-subtitle {
  text-align: center;
  color: #909399;
  margin: 6px 0 28px;
}
.login-btn {
  width: 100%;
}
</style>
