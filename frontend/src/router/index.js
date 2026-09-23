import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  { path: '/', redirect: '/chat' },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { title: '登录' },
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('@/views/chat/index.vue'),
    meta: { title: 'AI 对话' },
  },
  {
    path: '/report',
    name: 'Report',
    component: () => import('@/views/report/index.vue'),
    meta: { title: '智能报表' },
  },
  {
    path: '/admin/dept',
    name: 'AdminDept',
    component: () => import('@/views/admin/dept/index.vue'),
    meta: { title: '部门管理' },
  },
  {
    path: '/admin/user',
    name: 'AdminUser',
    component: () => import('@/views/admin/user/index.vue'),
    meta: { title: '用户管理' },
  },
  {
    path: '/admin/role',
    name: 'AdminRole',
    component: () => import('@/views/admin/role/index.vue'),
    meta: { title: '角色管理' },
  },
  {
    path: '/admin/permission',
    name: 'AdminPermission',
    component: () => import('@/views/admin/permission/index.vue'),
    meta: { title: '角色授权' },
  },
  {
    path: '/admin/category',
    name: 'AdminCategory',
    component: () => import('@/views/admin/category/index.vue'),
    meta: { title: '知识库分类' },
  },
  {
    path: '/admin/knowledge',
    name: 'AdminKnowledge',
    component: () => import('@/views/admin/knowledge/index.vue'),
    meta: { title: '知识库上传' },
  },
  {
    path: '/admin/provider',
    name: 'AdminProvider',
    component: () => import('@/views/admin/provider/index.vue'),
    meta: { title: '模型提供商' },
  },
  {
    path: '/admin/chat-role',
    name: 'AdminChatRole',
    component: () => import('@/views/admin/chatrole/index.vue'),
    meta: { title: '聊天角色' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  document.title = `${to.meta.title || '首页'} · 商枢 BizPivot`
  const userStore = useUserStore()
  if (to.path !== '/login' && !userStore.isLoggedIn) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router