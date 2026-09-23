<template>
  <el-card shadow="never">
    <template #header>
      <div class="page-header">
        <span>部门管理</span>
        <div>
          <el-button type="primary" @click="openCreateCompany">
            <el-icon><Plus /></el-icon>新增公司
          </el-button>
          <el-button @click="loadTree">
            <el-icon><Refresh /></el-icon>刷新
          </el-button>
        </div>
      </div>
    </template>

    <el-alert
      type="info"
      :closable="false"
      show-icon
      title="部门采用无限级树形结构；修改支持更换父级（防循环嵌套）；删除前校验下级部门与归属用户。"
      style="margin-bottom: 12px"
    />

    <el-tree
      v-loading="loading"
      :data="tree"
      node-key="id"
      :props="treeProps"
      default-expand-all
      :expand-on-click-node="false"
      empty-text="暂无部门，请先新增公司"
    >
      <template #default="{ data }">
        <div class="tree-node">
          <span class="node-name">{{ data.name }}</span>
          <el-tag v-if="data.is_company === 1" size="small" type="info">公司</el-tag>
          <span class="node-actions">
            <el-button link type="primary" size="small" @click.stop="openAddChild(data)">
              添加子部门
            </el-button>
            <el-button link type="primary" size="small" @click.stop="openEdit(data)">
              编辑
            </el-button>
            <el-button link type="danger" size="small" @click.stop="onDelete(data)">
              删除
            </el-button>
          </span>
        </div>
      </template>
    </el-tree>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="480px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="父级节点" prop="pid">
          <el-tree-select
            v-model="form.pid"
            :data="parentOptions"
            node-key="id"
            :props="treeProps"
            check-strictly
            clearable
            placeholder="不选则为顶级（公司）"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" maxlength="200" placeholder="公司名或部门名" />
        </el-form-item>
        <el-form-item label="排序" prop="sort_order">
          <el-input-number v-model="form.sort_order" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getDeptTree, createDept, updateDept, deleteDept } from '@/api/dept'

const tree = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const formRef = ref(null)

const treeProps = { label: 'name', children: 'children' }

const form = reactive({ pid: null, name: '', sort_order: 0 })

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
}

const dialogTitle = ref('')
const parentOptions = ref([])

async function loadTree() {
  loading.value = true
  try {
    tree.value = await getDeptTree()
    parentOptions.value = tree.value
  } finally {
    loading.value = false
  }
}

function resetForm() {
  Object.assign(form, { pid: null, name: '', sort_order: 0 })
}

function openCreateCompany() {
  isEdit.value = false
  editId.value = null
  resetForm()
  form.pid = null
  dialogTitle.value = '新增公司'
  dialogVisible.value = true
}

function openAddChild(data) {
  isEdit.value = false
  editId.value = null
  resetForm()
  form.pid = data.id
  dialogTitle.value = `新增「${data.name}」的子部门`
  dialogVisible.value = true
}

function openEdit(data) {
  isEdit.value = true
  editId.value = data.id
  resetForm()
  form.pid = data.pid || null
  form.name = data.name
  form.sort_order = data.sort_order
  dialogTitle.value = `编辑「${data.name}」`
  dialogVisible.value = true
}

async function onSave() {
  await formRef.value.validate()
  saving.value = true
  try {
    const payload = { name: form.name, sort_order: form.sort_order }
    if (isEdit.value) {
      payload.pid = form.pid ?? 0
      await updateDept(editId.value, payload)
      ElMessage.success('修改成功')
    } else {
      payload.pid = form.pid ?? 0
      await createDept(payload)
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    loadTree()
  } finally {
    saving.value = false
  }
}

async function onDelete(data) {
  await ElMessageBox.confirm(`确定删除「${data.name}」吗？`, '提示', { type: 'warning' })
  await deleteDept(data.id)
  ElMessage.success('删除成功')
  loadTree()
}

onMounted(loadTree)
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}
.tree-node {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  padding-right: 8px;
}
.node-name {
  font-size: 14px;
}
.node-actions {
  margin-left: auto;
  visibility: hidden;
}
.tree-node:hover .node-actions {
  visibility: visible;
}
</style>
