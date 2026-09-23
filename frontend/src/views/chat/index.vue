<template>
  <div class="chat-shell">
    <el-aside class="chat-aside" width="240px">
      <div class="aside-header">
        <span>对话列表</span>
        <el-button type="primary" size="small" text>新建会话</el-button>
      </div>
      <el-empty description="暂无会话" :image-size="60" />
    </el-aside>

    <el-main class="chat-main">
      <div class="chat-body">
        <el-empty description="AI 闲聊对话（多会话 / 流式输出 / 上下文压缩）将在阶段五实现">
          <div class="chat-hint">
            当前阶段已完成前端骨架与 SSE 流式封装，接入 AI 能力后即可对话。
          </div>
        </el-empty>
      </div>
      <div class="chat-input">
        <el-input
          type="textarea"
          :rows="3"
          placeholder="输入消息，按 Enter 发送（阶段五开放）"
          disabled
        />
        <div class="input-bar">
          <el-switch v-model="ragEnabled" size="small" active-text="知识库问答" />
          <el-button type="primary" disabled>发送</el-button>
        </div>
      </div>
    </el-main>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const ragEnabled = ref(false)
</script>

<style scoped>
.chat-shell {
  display: flex;
  height: calc(100vh - 96px);
  background: #fff;
  border-radius: 6px;
  overflow: hidden;
}
.chat-aside {
  border-right: 1px solid #e4e7ed;
  padding: 12px;
}
.aside-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  font-weight: 600;
}
.chat-main {
  display: flex;
  flex-direction: column;
}
.chat-body {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
.chat-hint {
  margin-top: 8px;
  color: #909399;
  font-size: 13px;
}
.chat-input {
  padding: 12px;
  border-top: 1px solid #e4e7ed;
}
.input-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}
</style>