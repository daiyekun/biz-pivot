<template>
  <div class="app-shell">
    <el-container class="app-container">
      <el-header class="app-header" height="56px">
        <div class="brand">
          <span class="brand-logo">商枢</span>
          <span class="brand-name">BizPivot 企业智能AI平台</span>
        </div>
        <div class="header-right">
          <el-tag :type="healthType" size="small" effect="light">
            {{ healthText }}
          </el-tag>
          <el-dropdown v-if="userStore.isLoggedIn" @command="onCommand">
            <span class="user-entry">
              {{ userStore.userInfo?.name || '管理员' }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-container class="body-container">
        <el-aside v-if="showSidebar" width="220px" class="app-aside">
          <el-menu :default-active="route.path" router class="app-menu">
            <el-menu-item v-for="m in menus" :key="m.path" :index="m.path">
              <el-icon><component :is="m.icon" /></el-icon>
              <span>{{ m.name }}</span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        <el-main class="app-main">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getHealth } from '@/api/system'
import { logout } from '@/api/auth'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const healthOk = ref(null)
const healthText = computed(() => (healthOk.value === null ? '检测中...' : healthOk.value ? '服务正常' : '服务异常'))
const healthType = computed(() => (healthOk.value === null ? 'info' : healthOk.value ? 'success' : 'danger'))

const baseMenus = [
  { path: '/chat', name: 'AI 对话', icon: 'ChatDotRound' },
  { path: '/report', name: '智能报表', icon: 'DataAnalysis' },
]

const adminMenus = [
  { path: '/admin/dept', name: '部门管理', icon: 'OfficeBuilding' },
  { path: '/admin/user', name: '用户管理', icon: 'User' },
  { path: '/admin/role', name: '角色管理', icon: 'Avatar' },
  { path: '/admin/permission', name: '角色授权', icon: 'Key' },
  { path: '/admin/category', name: '知识库分类', icon: 'FolderOpened' },
  { path: '/admin/knowledge', name: '知识库上传', icon: 'Upload' },
  { path: '/admin/provider', name: '模型提供商', icon: 'Connection' },
  { path: '/admin/chat-role', name: '聊天角色', icon: 'ChatDotRound' },
]

const menus = computed(() => (userStore.isSuper ? [...baseMenus, ...adminMenus] : baseMenus))
const isLoginPage = computed(() => route.path === '/login')
const showSidebar = computed(() => userStore.isLoggedIn && !isLoginPage.value)

onMounted(async () => {
  try {
    const data = await getHealth()
    healthOk.value = data.status === 'ok'
  } catch (e) {
    healthOk.value = false
  }
})

async function onCommand(command) {
  if (command === 'logout') {
    try {
      await logout()
    } catch (e) {
      // 忽略登出接口异常，前端本地状态照常清理
    }
    userStore.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  background: #f5f7fa;
}
.app-container {
  min-height: 100vh;
}
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}
.brand-logo {
  font-weight: 700;
  font-size: 18px;
  color: #409eff;
}
.brand-name {
  font-size: 15px;
  color: #303133;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.user-entry {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  color: #303133;
}
.body-container {
  min-height: calc(100vh - 56px);
}
.app-aside {
  background: #fff;
  border-right: 1px solid #e4e7ed;
}
.app-menu {
  border-right: none;
}
.app-main {
  padding: 20px;
}
</style>
