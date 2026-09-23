<template>
  <el-card shadow="never" class="placeholder-card">
    <template #header>
      <div class="placeholder-header">
        <el-icon v-if="icon"><component :is="icon" /></el-icon>
        <span>{{ title }}</span>
      </div>
    </template>
    <el-empty :description="description || '该功能将在后续阶段开发'">
      <template v-if="extra" #default>
        <div class="placeholder-extra">{{ extra }}</div>
      </template>
    </el-empty>
  </el-card>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  extra: { type: String, default: '' },
  icon: { type: String, default: '' },
})
</script>

<style scoped>
.placeholder-card {
  min-height: 420px;
}
.placeholder-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}
.placeholder-extra {
  color: #909399;
  font-size: 13px;
}
</style>