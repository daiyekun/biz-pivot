<template>
  <el-card shadow="never">
    <template #header>
      <div class="page-header">
        <span>智能聊天角色</span>
        <el-button type="primary" @click="openCreate">
          <el-icon><Plus /></el-icon>新增角色
        </el-button>
      </div>
    </template>

    <el-table v-loading="loading" :data="list" border stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="角色名称" min-width="140" />
      <el-table-column prop="description" label="角色描述" min-width="180" show-overflow-tooltip />
      <el-table-column label="系统提示词" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">{{ row.system_prompt || '—' }}</template>
      </el-table-column>
      <el-table-column prop="temperature" label="温度" width="90" />
      <el-table-column label="模型提供商" min-width="150">
        <template #default="{ row }">{{ providerName(row.provider_id) }}</template>
      </el-table-column>
      <el-table-column prop="create_time" label="创建时间" width="180" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑聊天角色' : '新增聊天角色'" width="600px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
        <el-form-item label="角色名称" prop="name">
          <el-input v-model="form.name" maxlength="100" placeholder="如：通用助手 / 意图识别" />
        </el-form-item>
        <el-form-item label="角色描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="2" maxlength="200" placeholder="角色用途说明" />
        </el-form-item>
        <el-form-item label="系统提示词" prop="system_prompt">
          <el-input v-model="form.system_prompt" type="textarea" :rows="4" maxlength="4000" show-word-limit placeholder="设定角色人设与回答规则" />
        </el-form-item>
        <el-form-item label="模型温度" prop="temperature">
          <el-input-number v-model="form.temperature" :min="0" :max="2" :step="0.1" :precision="1" />
        </el-form-item>
        <el-form-item label="模型提供商" prop="provider_id">
          <el-select v-model="form.provider_id" clearable placeholder="选择模型提供商（可空）" style="width: 100%">
            <el-option v-for="p in providers" :key="p.id" :label="`${p.name}（${p.model}）`" :value="p.id" />
          </el-select>
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
import { listChatRoles, createChatRole, updateChatRole, deleteChatRole } from '@/api/chatrole'
import { listProviders } from '@/api/provider'

const list = ref([])
const providers = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const formRef = ref(null)

const form = reactive({ name: '', description: '', system_prompt: '', temperature: 0.7, provider_id: null })

const rules = {
  name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }],
  temperature: [{ required: true, message: '请设置模型温度', trigger: 'blur' }],
}

function providerName(id) {
  const found = providers.value.find((p) => p.id === id)
  return found ? `${found.name}（${found.model}）` : '未指定'
}

async function loadList() {
  loading.value = true
  try {
    const [roles, provs] = await Promise.all([listChatRoles(), listProviders()])
    list.value = roles
    providers.value = provs
  } finally {
    loading.value = false
  }
}

function openCreate() {
  isEdit.value = false
  editId.value = null
  Object.assign(form, { name: '', description: '', system_prompt: '', temperature: 0.7, provider_id: null })
  dialogVisible.value = true
}

function openEdit(row) {
  isEdit.value = true
  editId.value = row.id
  Object.assign(form, {
    name: row.name,
    description: row.description || '',
    system_prompt: row.system_prompt || '',
    temperature: row.temperature,
    provider_id: row.provider_id ?? null,
  })
  dialogVisible.value = true
}

async function onSave() {
  await formRef.value.validate()
  saving.value = true
  try {
    const payload = { ...form }
    if (isEdit.value) {
      await updateChatRole(editId.value, payload)
      ElMessage.success('修改成功')
    } else {
      await createChatRole(payload)
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    loadList()
  } finally {
    saving.value = false
  }
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确定删除聊天角色「${row.name}」吗？`, '提示', { type: 'warning' })
  await deleteChatRole(row.id)
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
