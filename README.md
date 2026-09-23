# 商枢 BizPivot 企业智能AI平台****
整体目标：搭建一套企业级、权限可控、数据隔离、私有化AI智能平台，包含：

全局登录鉴权（Token + Redis 会话）
系统内置唯一、不可删除、不可禁用的超级管理员账号
系统菜单初始化 + 后台 RBAC 权限体系（部门/用户/角色/角色授权）
无限级树形结构：部门管理、知识库分类
表格列表统一分页规范
多模型提供商配置：后台配置多个模型提供商（sys_provider）
智能聊天角色体系：自定义聊天角色（系统提示词/温度/绑定提供商），会话强制关联聊天角色
企业私有 RAG 知识库问答 + 文档五级数据权限体系（个人/部门/公司/部门及子部门/跨部门）
文档上传强权限管控：仅授权角色可上传，不支持修改仅支持新增/删除
可控跨部门知识检索与隔离
AI 闲聊对话（多轮、上下文智能压缩、SSE 流式、消息角色枚举）
智能数据可视化报表 + 报表文件导出
分布式无状态、可水平扩展部署
核心开发原则：先底座、后权限、再业务、强隔离、最后部署上线

# 单体架构图
<img width="945" height="878" alt="image" src="https://github.com/user-attachments/assets/2bf15960-7569-4797-9352-d35002bfab21" />



# 最终微服务架构简要图

<img width="3753" height="2403" alt="exported_image (2)" src="https://github.com/user-attachments/assets/8a31cf7a-aa74-4b06-8450-dfca12158589" />

# admin 超级管理员界面管理
<img width="2542" height="1284" alt="image" src="https://github.com/user-attachments/assets/bec2cf06-7c9f-4fd9-9e09-1e299a02a177" />


