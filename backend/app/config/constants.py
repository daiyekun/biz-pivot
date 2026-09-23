"""系统常量：状态枚举、权限枚举、分页参数、上下文阈值、菜单种子等。

对齐《数据库设计文档 V1.1》与 PRD V1.1。
"""

# ============ 通用状态位（state） ============
STATE_NORMAL = 0       # 启用 / 显示
STATE_DISABLED = 1     # 禁用 / 不显示
STATE_DELETED = 3      # 删除（软删除）

# ============ 分页通用规范（PRD 第 6 章） ============
DEFAULT_PAGE_NUM = 1
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100
PAGE_SIZE_OPTIONS = [10, 20, 50, 100]

# ============ 消息角色 ============
MSG_ROLE_USER = 0
MSG_ROLE_AI = 1

# ============ Token / 上下文 阈值 ============
CONTEXT_MAX_TOKENS = 8000                 # 单次请求上下文最大 token
CONTEXT_SUMMARY_THRESHOLD_RATIO = 0.8     # 达到该比例触发自动摘要压缩
CONTEXT_SUMMARY_TARGET_RATIO = 0.4        # 压缩后保留的比例

# ============ 知识库权限类型（access_type） ============
ACCESS_TYPE_PERSONAL = 1      # 个人
ACCESS_TYPE_DEPARTMENT = 2    # 部门
ACCESS_TYPE_COMPANY = 3       # 公司
ACCESS_TYPE_DEPT_TREE = 4     # 部门及子部门
ACCESS_TYPE_CROSS_DEPT = 5    # 跨部门

ACCESS_TYPE_NAMES = {
    ACCESS_TYPE_PERSONAL: "个人",
    ACCESS_TYPE_DEPARTMENT: "部门",
    ACCESS_TYPE_COMPANY: "公司",
    ACCESS_TYPE_DEPT_TREE: "部门及子部门",
    ACCESS_TYPE_CROSS_DEPT: "跨部门",
}

# ============ 文档解析 / 向量化状态 ============
PARSE_STATUS_PENDING = 0      # 待解析
PARSE_STATUS_PROCESSING = 1   # 解析中
PARSE_STATUS_SUCCESS = 2      # 成功
PARSE_STATUS_FAILED = 3       # 失败

VECTOR_STATUS_NONE = 0        # 未入库
VECTOR_STATUS_DONE = 1        # 已入库
VECTOR_STATUS_FAILED = 2      # 失败

# ============ 解析任务类型（doc_parse_task.task_type） ============
TASK_TYPE_PARSE_CHUNK = 1     # 解析切片
TASK_TYPE_VECTORIZE = 2       # 向量化

# ============ 任务状态（doc_parse_task.status） ============
TASK_STATUS_PENDING = 0
TASK_STATUS_RUNNING = 1
TASK_STATUS_SUCCESS = 2
TASK_STATUS_FAILED = 3

# ============ Redis 缓存 Key 模板（数据库设计 4.3 节） ============
REDIS_KEY_USER_PERM = "user:perm:{uid}"              # 用户权限上下文（部门链/公司/角色）
REDIS_KEY_USER_DOCS = "user:docs:{uid}"              # 用户可访问文档 ID 白名单
REDIS_KEY_ROLE_MENU = "role:menu:{role_id}"          # 角色可访问菜单
REDIS_KEY_KB_META = "kb:meta:{kb_id}"                # 文档元信息缓存

# ============ 系统菜单种子（PRD 3.1 节，启动自动写入 sys_menu） ============
MENU_SEEDS = [
    {"name": "部门管理",   "path": "/admin/dept",       "icon": "OfficeBuilding", "sort_order": 1, "page_type": "tree"},
    {"name": "用户管理",   "path": "/admin/user",       "icon": "User",           "sort_order": 2, "page_type": "list"},
    {"name": "角色管理",   "path": "/admin/role",       "icon": "Avatar",         "sort_order": 3, "page_type": "list"},
    {"name": "角色授权",   "path": "/admin/permission", "icon": "Key",            "sort_order": 4, "page_type": "list"},
    {"name": "知识库分类", "path": "/admin/category",   "icon": "FolderOpened",   "sort_order": 5, "page_type": "tree"},
    {"name": "知识库上传", "path": "/admin/knowledge",  "icon": "Upload",         "sort_order": 6, "page_type": "list"},
]

# 菜单权限标识（用于后端二次拦截）
MENU_CODE_DEPT = "dept:manage"
MENU_CODE_USER = "user:manage"
MENU_CODE_ROLE = "role:manage"
MENU_CODE_PERMISSION = "permission:grant"
MENU_CODE_CATEGORY = "category:manage"
MENU_CODE_KNOWLEDGE = "knowledge:upload"