<template>
  <el-card shadow="never">
    <template #header>
      <div class="page-header">
        <span>模型提供商</span>
        <el-button type="primary" @click="openCreate">
          <el-icon><Plus /></el-icon>新增提供商
        </el-button>
      </div>
    </template>

    <el-table v-loading="loading" :data="list" border stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="提供商名称" min-width="160" />
      <el-table-column prop="endpoint" label="API调用地址" min-width="220" show-overflow-tooltip />
      <el-table-column prop="model" label="模型名称" min-width="140" />
      <el-table-column label="API密钥" min-width="130">
        <template #default="{ row }">{{ maskKey(row.api_key) }}</template>
      </el-table-column>
      <el-table-column prop="create_time" label="创建时间" width="180" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑提供商' : '新增提供商'" width="560px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
        <el-form-item label="提供商名称" prop="name">
          <el-input v-model="form.name" maxlength="100" placeholder="如：OpenAI / 通义千问" />
        </el-form-item>
        <el-form-item label="API调用地址" prop="endpoint">
          <el-input v-model="form.endpoint" maxlength="255" placeholder="如：https://api.example.com/v1" />
        </el-form-item>
        <el-form-item label="模型名称" prop="model">
          <el-input v-model="form.model" maxlength="100" placeholder="如：gpt-4o / qwen-plus" />
        </el-form-item>
        <el-form-item label="API密钥" prop="api_key">
          <el-input v-model="form.api_key" type="password" show-password maxlength="500" :placeholder="isEdit ? '留空表示不修改' : '请输入API密钥'" />
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
import { listProviders, createProvider, updateProvider, deleteProvider } from '@/api/provider'

const list = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const formRef = ref(null)

const form = reactive({ name: '', endpoint: '', model: '', api_key: '' })

const rules = {
  name: [{ required: true, message: '请输入提供商名称', trigger: 'blur' }],
  endpoint: [{ required: true, message: '请输入API调用地址', trigger: 'blur' }],
  model: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
}

function maskKey(key) {
  if (!key) return '—'
  if (key.length <= 6) return '******'
  return `${key.slice(0, 3)}****${key.slice(-3)}`
}

async function loadList() {
  loading.value = true
  try {
    list.value = await listProviders()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  isEdit.value = false
  editId.value = null
  Object.assign(form, { name: '', endpoint: '', model: '', api_key: '' })
  dialogVisible.value = true
}

function openEdit(row) {
  isEdit.value = true
  editId.value = row.id
  Object.assign(form, { name: row.name, endpoint: row.endpoint, model: row.model, api_key: '' })
  dialogVisible.value = true
}

async function onSave() {
  await formRef.value.validate()
  saving.value = true
  try {
    if (isEdit.value) {
      const payload = { name: form.name, endpoint: form.endpoint, model: form.model }
      if (form.api_key) payload.api_key = form.api_key
      await updateProvider(editId.value, payload)
      ElMessage.success('修改成功')
    } else {
      await createProvider({ ...form })
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    loadList()
  } finally {
    saving.value = false
  }
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确定删除提供商「${row.name}」吗？`, '提示', { type: 'warning' })
  await deleteProvider(row.id)
  ElMessage.success('删除成功')
  loadList()
}

onMounted(loadList)
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}
</style>
