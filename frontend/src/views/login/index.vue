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

      <el-divider><span class="divider-text">阶段一演示</span></el-divider>
      <el-button type="success" plain size="large" class="login-btn" @click="onDemo">
        跳过登录，进入系统
      </el-button>
      <div class="login-tip">登录鉴权接口将在阶段二上线，当前可使用演示入口浏览系统骨架。</div>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const form = reactive({ account: 'admin', password: '' })
const loading = ref(false)

function enterSystem() {
  const redirect = route.query.redirect || '/chat'
  router.push(redirect)
}

function onLogin() {
  if (!form.account || !form.password) {
    ElMessage.warning('请输入账号和密码')
    return
  }
  loading.value = true
  ElMessage.info('登录接口将在阶段二上线')
  setTimeout(() => {
    loading.value = false
  }, 500)
}

function onDemo() {
  userStore.setLogin('demo-token', { name: form.account || '管理员', is_super: true })
  ElMessage.success('已进入演示模式')
  enterSystem()
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
.divider-text {
  color: #c0c4cc;
  font-size: 12px;
}
.login-tip {
  margin-top: 16px;
  font-size: 12px;
  color: #c0c4cc;
  text-align: center;
}
</style>