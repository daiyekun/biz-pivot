<template>
  <el-row :gutter="16">
    <el-col :span="8">
      <el-card shadow="never">
        <template #header>
          <span class="card-title">选择角色</span>
        </template>

        <div class="toolbar">
          <el-input
            v-model="query.keyword"
            placeholder="按角色名称搜索"
            clearable
            @keyup.enter="onSearch"
            @clear="onSearch"
          />
          <el-button type="primary" @click="onSearch">
            <el-icon><Search /></el-icon>查询
          </el-button>
        </div>

        <el-table
          v-loading="roleLoading"
          :data="roleList"
          border
          stripe
          highlight-current-row
          max-height="420"
          @current-change="onSelectRole"
        >
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="name" label="角色名称" min-width="120" />
          <el-table-column prop="desc" label="角色描述" min-width="140" show-overflow-tooltip />
        </el-table>

        <div class="pagination">
          <el-pagination
            v-model:current-page="query.pageNum"
            v-model:page-size="query.pageSize"
            :total="roleTotal"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @current-change="loadRoles"
            @size-change="onSizeChange"
          />
        </div>
      </el-card>
    </el-col>

    <el-col :span="16">
      <el-card shadow="never">
        <template #header>
          <div class="auth-header">
            <span class="card-title">授权配置</span>
            <el-tag v-if="currentRoleName" type="primary" effect="light">
              当前角色：{{ currentRoleName }}
            </el-tag>
          </div>
        </template>

        <el-alert
          type="info"
          :closable="false"
          show-icon
          title="角色授权分为「系统菜单权限」与「知识库权限」两层：勾选菜单控制角色成员可见/可用的功能入口，知识库权限控制文档上传/管理与分类管理能力，保存即时生效。"
          style="margin-bottom: 16px"
        />

        <div v-if="currentRoleId" v-loading="grantLoading" class="auth-body">
          <div class="section">
            <div class="section-title">系统菜单权限</div>
            <el-tree
              ref="treeRef"
              :data="menuTree"
              node-key="id"
              show-checkbox
              default-expand-all
              :props="{ label: 'name', children: 'children' }"
              :expand-on-click-node="false"
              @check="onTreeCheck"
              empty-text="暂无菜单"
            />
          </div>

          <el-divider />

          <div class="section">
            <div class="section-title">知识库权限配置</div>
            <div v-for="item in knowledgeItems" :key="item.code" class="knowledge-item">
              <div class="knowledge-info">
                <div class="knowledge-label">{{ item.label }}</div>
                <div class="knowledge-desc">{{ item.desc }}</div>
              </div>
              <el-switch
                :model-value="isKnowledgeOn(item.code)"
                @change="(val) => onKnowledgeToggle(item.code, val)"
              />
            </div>

            <div class="section-subtitle">可访问分类范围</div>
            <el-alert
              type="info"
              :closable="false"
              show-icon
              title="不勾选任何分类 = 该角色可访问全部分类；勾选后仅可访问所选分类。"
              style="margin-bottom: 12px"
            />
            <el-tree
              ref="categoryTreeRef"
              :data="categoryTree"
              node-key="id"
              show-checkbox
              default-expand-all
              :props="{ label: 'name', children: 'children' }"
              :expand-on-click-node="false"
              empty-text="暂无知识库分类"
            />
          </div>

          <div class="save-bar">
            <el-button type="primary" :loading="saving" @click="onSave">
              保存授权
            </el-button>
          </div>
        </div>

        <el-empty v-else description="请在左侧选择角色后进行授权配置" />
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { listRoles } from '@/api/role'
import { getMenuTree, getRoleMenus, saveRoleMenus, getRoleCategories, saveRoleCategories } from '@/api/menu'
import { getCategoryTree } from '@/api/category'

const roleList = ref([])
const roleTotal = ref(0)
const roleLoading = ref(false)
const query = reactive({ pageNum: 1, pageSize: 10, keyword: '' })

const menuTree = ref([])
const treeRef = ref(null)
const checkedIds = ref([])

const categoryTree = ref([])
const categoryTreeRef = ref(null)

const grantLoading = ref(false)
const saving = ref(false)

const currentRoleId = ref(null)
const currentRoleName = ref('')

const knowledgeItems = [
  { code: 'knowledge:upload', label: '文档上传/管理权限', desc: '拥有者可上传、删除知识库文档（默认所有普通角色无此权限）' },
  { code: 'category:manage', label: '分类管理权限', desc: '拥有者可新增、修改、删除知识库分类' },
]

const menuIdByCode = computed(() => {
  const map = {}
  const walk = (nodes) => {
    nodes.forEach((n) => {
      if (n.code) map[n.code] = n.id
      if (n.children && n.children.length) walk(n.children)
    })
  }
  walk(menuTree.value)
  return map
})

function isKnowledgeOn(code) {
  const id = menuIdByCode.value[code]
  return id != null && checkedIds.value.includes(id)
}

async function loadRoles() {
  roleLoading.value = true
  try {
    const data = await listRoles(query)
    roleList.value = data.records
    roleTotal.value = data.total
  } finally {
    roleLoading.value = false
  }
}

async function loadMenuTree() {
  menuTree.value = await getMenuTree()
}

async function loadCategoryTree() {
  categoryTree.value = await getCategoryTree()
}

function onSearch() {
  query.pageNum = 1
  loadRoles()
}

function onSizeChange() {
  query.pageNum = 1
  loadRoles()
}

async function onSelectRole(row) {
  if (!row) return
  currentRoleId.value = row.id
  currentRoleName.value = row.name
  grantLoading.value = true
  try {
    const [menus, categories] = await Promise.all([
      getRoleMenus(row.id),
      getRoleCategories(row.id),
    ])
    checkedIds.value = menus.menu_ids || []
    treeRef.value?.setCheckedKeys(checkedIds.value)
    categoryTreeRef.value?.setCheckedKeys(categories.category_ids || [])
  } finally {
    grantLoading.value = false
  }
}

function collectCategoryChecked() {
  const checked = categoryTreeRef.value?.getCheckedKeys() || []
  const half = categoryTreeRef.value?.getHalfCheckedKeys() || []
  return [...new Set([...checked, ...half])]
}

function collectChecked() {
  const checked = treeRef.value?.getCheckedKeys() || []
  const half = treeRef.value?.getHalfCheckedKeys() || []
  return [...new Set([...checked, ...half])]
}

function onTreeCheck() {
  checkedIds.value = collectChecked()
}

function onKnowledgeToggle(code, val) {
  const id = menuIdByCode.value[code]
  if (id == null) return
  if (val) {
    if (!checkedIds.value.includes(id)) checkedIds.value = [...checkedIds.value, id]
    treeRef.value?.setChecked(id, true, false)
  } else {
    checkedIds.value = checkedIds.value.filter((x) => x !== id)
    treeRef.value?.setChecked(id, false, false)
  }
}

async function onSave() {
  if (!currentRoleId.value) {
    ElMessage.warning('请先选择角色')
    return
  }
  saving.value = true
  try {
    await Promise.all([
      saveRoleMenus(currentRoleId.value, collectChecked()),
      saveRoleCategories(currentRoleId.value, collectCategoryChecked()),
    ])
    ElMessage.success('授权保存成功')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadMenuTree(), loadCategoryTree()])
  await loadRoles()
})
</script>

<style scoped>
.card-title {
  font-weight: 600;
}
.toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}
.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
.auth-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.auth-body {
  min-height: 300px;
}
.section-title {
  font-weight: 600;
  margin-bottom: 12px;
  color: #303133;
}
.section-subtitle {
  font-weight: 600;
  margin: 16px 0 10px;
  color: #303133;
}
.knowledge-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  margin-bottom: 12px;
}
.knowledge-label {
  font-size: 14px;
  color: #303133;
}
.knowledge-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
.save-bar {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
