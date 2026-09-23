<template>
  <el-card shadow="never">
    <template #header>
      <div class="page-header">
        <span>用户管理</span>
        <el-button type="primary" @click="openCreate">
          <el-icon><Plus /></el-icon>新增用户
        </el-button>
      </div>
    </template>

    <div class="toolbar">
      <el-input
        v-model="query.account"
        placeholder="按用户名搜索"
        clearable
        style="width: 200px"
        @keyup.enter="onSearch"
        @clear="onSearch"
      />
      <el-tree-select
        v-model="query.dept_id"
        :data="deptTree"
        node-key="id"
        :props="treeProps"
        check-strictly
        clearable
        placeholder="按部门筛选"
        style="width: 220px"
        @change="onSearch"
      />
      <el-button type="primary" @click="onSearch">
        <el-icon><Search /></el-icon>查询
      </el-button>
      <el-button @click="onReset">重置</el-button>
    </div>

    <el-table v-loading="loading" :data="list" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="姓名" min-width="110" />
      <el-table-column prop="account" label="登录账号" min-width="130" />
      <el-table-column prop="dept_name" label="所属部门" min-width="140" />
      <el-table-column label="角色" min-width="180">
        <template #default="{ row }">
          <el-tag v-for="n in row.role_names" :key="n" size="small" class="role-tag">{{ n }}</el-tag>
          <span v-if="!row.role_names || !row.role_names.length" class="muted">—</span>
        </template>
      </el-table-column>
      <el-table-column prop="phone" label="手机号" min-width="120" />
      <el-table-column prop="email" label="邮箱" min-width="150" show-overflow-tooltip />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.state === 0 ? 'success' : 'info'">
            {{ row.state === 0 ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="warning" @click="openResetPwd(row)">重置密码</el-button>
          <el-button v-if="!row.is_super" link :type="row.state === 0 ? 'danger' : 'success'" @click="onToggleState(row)">
            {{ row.state === 0 ? '禁用' : '启用' }}
          </el-button>
          <el-button v-if="!row.is_super" link type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="query.pageNum"
        v-model:page-size="query.pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="loadList"
        @size-change="onSizeChange"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑用户' : '新增用户'" width="540px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" maxlength="50" placeholder="显示名称" />
        </el-form-item>
        <el-form-item v-if="!isEdit" label="登录账号" prop="account">
          <el-input v-model="form.account" maxlength="50" placeholder="唯一登录账号" />
        </el-form-item>
        <el-form-item v-if="!isEdit" label="初始密码" prop="password">
          <el-input v-model="form.password" type="password" show-password maxlength="100" placeholder="登录密码" />
        </el-form-item>
        <el-form-item label="归属部门" prop="dept_id">
          <el-tree-select
            v-model="form.dept_id"
            :data="deptTree"
            node-key="id"
            :props="treeProps"
            check-strictly
            placeholder="必选归属部门"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="绑定角色" prop="role_ids">
          <el-select v-model="form.role_ids" multiple clearable placeholder="可多选角色" style="width: 100%">
            <el-option v-for="r in roles" :key="r.id" :label="r.name" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" maxlength="20" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" maxlength="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="pwdVisible" title="重置密码" width="420px" destroy-on-close>
      <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="90px">
        <el-form-item label="新密码" prop="password">
          <el-input v-model="pwdForm.password" type="password" show-password maxlength="100" placeholder="请输入新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingPwd" @click="onResetPwd">确定</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listUsers, createUser, updateUser, deleteUser, resetPassword, setUserState } from '@/api/user'
import { listAllRoles } from '@/api/role'
import { getDeptTree } from '@/api/dept'

const list = ref([])
const total = ref(0)
const roles = ref([])
const deptTree = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const formRef = ref(null)

const pwdVisible = ref(false)
const pwdFormRef = ref(null)
const savingPwd = ref(false)
const pwdForm = reactive({ password: '' })
const pwdTargetId = ref(null)

const treeProps = { label: 'name', children: 'children' }

const query = reactive({ pageNum: 1, pageSize: 10, account: '', dept_id: null })
const form = reactive({ name: '', account: '', password: '', dept_id: null, phone: '', email: '', role_ids: [] })

const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  account: [{ required: true, message: '请输入登录账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入初始密码', trigger: 'blur' }],
  dept_id: [{ required: true, message: '请选择归属部门', trigger: 'change' }],
}
const pwdRules = {
  password: [{ required: true, message: '请输入新密码', trigger: 'blur' }],
}

async function loadList() {
  loading.value = true
  try {
    const params = { pageNum: query.pageNum, pageSize: query.pageSize }
    if (query.account) params.account = query.account
    if (query.dept_id) params.dept_id = query.dept_id
    const data = await listUsers(params)
    list.value = data.records
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function loadMeta() {
  const [depts, roleList] = await Promise.all([getDeptTree(), listAllRoles()])
  deptTree.value = depts
  roles.value = roleList
}

function onSearch() {
  query.pageNum = 1
  loadList()
}

function onReset() {
  query.account = ''
  query.dept_id = null
  query.pageNum = 1
  loadList()
}

function onSizeChange() {
  query.pageNum = 1
  loadList()
}

function openCreate() {
  isEdit.value = false
  editId.value = null
  Object.assign(form, { name: '', account: '', password: '', dept_id: null, phone: '', email: '', role_ids: [] })
  dialogVisible.value = true
}

function openEdit(row) {
  isEdit.value = true
  editId.value = row.id
  Object.assign(form, {
    name: row.name,
    account: row.account,
    password: '',
    dept_id: row.dept_id,
    phone: row.phone || '',
    email: row.email || '',
    role_ids: row.role_ids || [],
  })
  dialogVisible.value = true
}

async function onSave() {
  await formRef.value.validate()
  saving.value = true
  try {
    if (isEdit.value) {
      const payload = {
        name: form.name,
        dept_id: form.dept_id,
        phone: form.phone,
        email: form.email,
        role_ids: form.role_ids,
      }
      await updateUser(editId.value, payload)
      ElMessage.success('修改成功')
    } else {
      await createUser({ ...form })
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    loadList()
  } finally {
    saving.value = false
  }
}

function openResetPwd(row) {
  pwdTargetId.value = row.id
  pwdForm.password = ''
  pwdVisible.value = true
}

async function onResetPwd() {
  await pwdFormRef.value.validate()
  savingPwd.value = true
  try {
    await resetPassword(pwdTargetId.value, pwdForm.password)
    ElMessage.success('密码重置成功')
    pwdVisible.value = false
  } finally {
    savingPwd.value = false
  }
}

async function onToggleState(row) {
  const target = row.state === 0 ? 1 : 0
  const label = target === 1 ? '禁用' : '启用'
  await ElMessageBox.confirm(`确定${label}用户「${row.name}」吗？`, '提示', { type: 'warning' })
  await setUserState(row.id, target)
  ElMessage.success(`${label}成功`)
  loadList()
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确定删除用户「${row.name}」吗？`, '提示', { type: 'warning' })
  await deleteUser(row.id)
  ElMessage.success('删除成功')
  loadList()
}

onMounted(() => {
  loadMeta()
  loadList()
})
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 14px;
}
.role-tag {
  margin-right: 4px;
}
.muted {
  color: #909399;
}
.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
}
</style>
