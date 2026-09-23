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

# ============ 消息角色（chat_message.role，枚举） ============
MSG_ROLE_SYSTEM = 0       # 系统消息
MSG_ROLE_USER = 1         # 用户消息
MSG_ROLE_ASSISTANT = 2    # AI 助手消息
MSG_ROLE_TOOL = 3         # 工具消息

MSG_ROLE_NAMES = {
    MSG_ROLE_SYSTEM: "系统",
    MSG_ROLE_USER: "用户",
    MSG_ROLE_ASSISTANT: "助手",
    MSG_ROLE_TOOL: "工具",
}

# ============ 聊天角色默认温度 ============
DEFAULT_TEMPERATURE = 0.7

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

# ============ 菜单权限标识（用于后端二次拦截） ============
MENU_CODE_DEPT = "dept:manage"
MENU_CODE_USER = "user:manage"
MENU_CODE_ROLE = "role:manage"
MENU_CODE_PERMISSION = "permission:grant"
MENU_CODE_CATEGORY = "category:manage"
MENU_CODE_KNOWLEDGE = "knowledge:upload"
MENU_CODE_PROVIDER = "provider:manage"
MENU_CODE_CHAT_ROLE = "chat_role:manage"

# ============ 系统菜单种子（PRD 3.1 节，启动自动写入 sys_menu） ============
MENU_SEEDS = [
    {"name": "部门管理",   "path": "/admin/dept",       "icon": "OfficeBuilding", "sort_order": 1, "page_type": "tree", "code": MENU_CODE_DEPT},
    {"name": "用户管理",   "path": "/admin/user",       "icon": "User",           "sort_order": 2, "page_type": "list", "code": MENU_CODE_USER},
    {"name": "角色管理",   "path": "/admin/role",       "icon": "Avatar",         "sort_order": 3, "page_type": "list", "code": MENU_CODE_ROLE},
    {"name": "角色授权",   "path": "/admin/permission", "icon": "Key",            "sort_order": 4, "page_type": "list", "code": MENU_CODE_PERMISSION},
    {"name": "知识库分类", "path": "/admin/category",   "icon": "FolderOpened",   "sort_order": 5, "page_type": "tree", "code": MENU_CODE_CATEGORY},
    {"name": "知识库上传", "path": "/admin/knowledge",  "icon": "Upload",         "sort_order": 6, "page_type": "list", "code": MENU_CODE_KNOWLEDGE},
    {"name": "模型提供商", "path": "/admin/provider",   "icon": "Connection",     "sort_order": 7, "page_type": "list", "code": MENU_CODE_PROVIDER},
    {"name": "聊天角色",   "path": "/admin/chat-role",  "icon": "ChatDotRound",   "sort_order": 8, "page_type": "list", "code": MENU_CODE_CHAT_ROLE},
]

# ============ 默认模型提供商（启动种子，来源于 .env LLM 配置） ============
DEFAULT_PROVIDER_NAME = "默认模型提供商"

# ============ 系统聊天角色种子（系统发起聊天时程序直接指定） ============
CHAT_ROLE_SEEDS = [
    {
        "name": "通用助手",
        "description": "通用 AI 对话助手，回答企业日常咨询",
        "system_prompt": "你是商枢 BizPivot 企业智能助手，请以专业、准确、友好的方式回答用户问题。",
        "temperature": 0.7,
    },
    {
        "name": "意图识别",
        "description": "系统内置角色：识别用户提问意图",
        "system_prompt": "你是意图识别模型，请分析用户输入并输出其意图分类（闲聊/知识库问答/数据报表等）。",
        "temperature": 0.3,
    },
    {
        "name": "语义识别",
        "description": "系统内置角色：对文本进行语义理解与改写",
        "system_prompt": "你是语义识别模型，请对用户文本进行语义理解、纠错与规范化改写。",
        "temperature": 0.3,
    },
]