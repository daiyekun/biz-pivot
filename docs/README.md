# 程序初始化文档
## 数据库
### 向量库
✅ Docker Desktop 已经打开，WSL2 正常运行

打开 PowerShell / Windows Terminal，**进入你的项目根目录**（商枢 BizPivot 项目文件夹）

## 1. 拉取 Qdrant 镜像

```
docker pull qdrant/qdrant
```

## 2. 启动容器（Windows Docker Desktop 推荐这条命令）

> 
> 会在项目目录自动创建 `qdrant_storage` 文件夹，向量数据持久化保存，删掉容器数据还在

```
docker run -d `
  --name qdrant `
  -p 6333:6333 `
  -p 6334:6334 `
  -v ${PWD}/qdrant_storage:/qdrant/storage `
  --restart unless-stopped `
  qdrant/qdrant
```

- `-d`：后台守护运行
- `--name qdrant`：容器名字，方便后续管理
- `6333`：HTTP API + Web 管理面板（我们 Python 代码用这个端口）
- `6334`：gRPC 端口
- `-v ${PWD}/qdrant_storage:/qdrant/storage`：把向量数据挂载到本机项目目录，**持久化**
- `--restart unless-stopped`：Docker Desktop 重启后自动拉起 qdrant

> ⚠️ Windows WSL2 挂载本地文件夹偶尔有性能 / 锁文件问题。如果后面出现奇怪报错，可以改用**docker 命名卷**版本（数据存在 docker 内部卷，不用映射本机目录）：

```
# 备选方案：使用docker命名卷（推荐Windows长期开发用）
docker run -d `
  --name qdrant `
  -p 6333:6333 `
  -p 6334:6334 `
  -v qdrant-data:/qdrant/storage `
  --restart unless-stopped `
  qdrant/qdrant
```

## 3. 验证是否成功

浏览器打开：

```
http://localhost:6333
```

看到欢迎 json = 服务正常。

**Web 管理后台（可视化看集合、测试检索）**

```
http://localhost:6333/dashboard
```

## 4. Python 连接测试

先安装客户端

```
pip install qdrant-client
```

最小测试代码（直接复制运行）

```
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)

# 查看服务信息
print(client.get_collections())
print(client.info())
```

✅ 不报错，就是连通成功。

## 5. 常用管理命令

```
# 停止qdrant
docker stop qdrant

# 启动
docker start qdrant

# 查看日志（排查报错）
docker logs qdrant

# 删除容器（数据如果用本地卷还保留）
docker rm qdrant
```

## 6. 加入你的项目 docker-compose.yml（推荐，后面项目统一管理）

新建 `docker-compose.yml` 放在项目根目录：

```
version: "3.8"
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant-data:/qdrant/storage
    restart: unless-stopped
volumes:
  qdrant-data:
```

之后直接一行启动：

```
docker-compose up -d qdrant
```

### 关系型数据库pgsql
> 用途：存放用户、部门、角色、文档主表、对话记录等业务数据，和 Qdrant 分开。
> 版本：postgres:15（稳定常用，搭配 pgvector 扩展也方便，如果你后面想试 pgvector）

## 1. PowerShell 执行一键启动命令

```
docker run -d `
  --name pg-biz `
  -p 5432:5432 `
  -e POSTGRES_USER=bizuser `
  -e POSTGRES_PASSWORD=Biz@Pass123 `
  -e POSTGRES_DB=biz_db `
  -v pg-biz-data:/var/lib/postgresql/data `
  --restart unless-stopped `
  postgres:15
```

### 参数说明

- `--name pg-biz` 容器名称
- `-p 5432:5432` 端口映射，本地连接用 `localhost:5432`
- `POSTGRES_USER=bizuser` 数据库账号
- `POSTGRES_PASSWORD=Biz@Pass123` 密码（后面写进`.env`）
- `POSTGRES_DB=biz_db` 默认业务数据库名
- `-v pg-biz-data:/var/lib/postgresql/data` Docker 命名卷，数据持久化，删除容器数据不丢
- `postgres:15` 镜像版本

> 
> 👉 建议：**不要用本地目录挂载 PG 数据**，Windows+WSL2 容易出现权限异常，直接使用 docker 命名卷。

## 2. 验证是否启动成功

```
# 查看运行容器
docker ps

# 查看日志（等待数据库初始化完成，首次启动需要十几秒）
docker logs pg-biz
```

### 连接信息（写入你的 .env）

```
# PostgreSQL
PG_HOST=localhost
PG_PORT=5432
PG_USER=bizuser
PG_PASSWORD=Biz@Pass123
PG_DATABASE=biz_db
```
### redis 缓存库

## 方案 1：单行 docker run（带命名卷 + 密码 + AOF 持久化，推荐长期开发）

```
docker run -d `
  --name redis `
  -p 6379:6379 `
  -v redis-data:/data `
  --restart unless-stopped `
  redis:7.2-alpine `
  redis-server --requirepass Redis@123 --appendonly yes
```

参数说明

- `redis:7.2-alpine` 轻量镜像
- `--requirepass Redis@123` 设置密码，**写入.env**
- `--appendonly yes` 开启 AOF 持久化，防止宕机丢缓存数据
- `-v redis-data:/data` 命名卷，删除容器数据还在

> 
> 如果你想临时测试，**去掉 `-v redis-data:/data` 也能正常启动不报错**，只是删容器数据清空（和 PG/Qdrant 逻辑一致）

## 连接信息，写入你的 `.env`

```
# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=Redis@123
REDIS_DB=0
```

## Python 测试连通

```
pip install redis
```

```
import redis

r = redis.Redis(
    host="localhost",
    port=6379,
    password="Redis@123",
    db=0,
    decode_responses=True
)
r.set("test_key", "hello biz")
print(r.get("test_key")) # 输出 hello biz 代表成功
```

## 进入 redis-cli 命令行（容器内）

```
docker exec -it redis redis-cli -a Redis@123
```

## 常用命令

```
# 停止
docker stop redis
# 启动
docker start redis
# 查看日志
docker logs redis
# 删除容器（卷redis-data还在，数据保留）
docker rm redis
# 彻底删除容器+数据卷（谨慎）
docker rm redis
docker volume rm redis-data
```

### Rabbitmq 队列用来解析文档等功能

> 镜像标签必须用 `management`，自带 Web 后台，方便调试队列。
> PowerShell 执行，Docker Desktop 打开。

## 单行 docker run（带命名卷，长期开发推荐）

```
docker run -d `
  --name rabbitmq `
  --hostname rabbitmq `
  -p 5672:5672 `
  -p 15672:15672 `
  -e RABBITMQ_DEFAULT_USER=admin `
  -e RABBITMQ_DEFAULT_PASS=Admin@123 `
  -v rabbitmq-data:/var/lib/rabbitmq `
  --restart unless-stopped `
  rabbitmq:3.13-management
```

### 端口说明

- **5672**：AMQP 端口，Python 代码、Celery 连接用
- **15672**：Web 管理后台端口，浏览器访问

> 
> ⚠️ 重点：**hostname 必须指定**，RabbitMQ 依赖这个节点名持久化数据，不指定重启容器容易丢元数据！

### Web 管理后台

浏览器打开：`http://localhost:15672`
账号：`admin`，密码：`Admin@123`

### .env 连接配置（写入项目环境文件）

```
# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=admin
RABBITMQ_PASSWORD=Admin@123
RABBITMQ_VHOST=/
```

## Python 测试连通

```
pip install pika
```

```
import pika

credentials = pika.PlainCredentials("admin", "Admin@123")
conn_params = pika.ConnectionParameters("localhost", 5672, "/", credentials)
conn = pika.BlockingConnection(conn_params)
channel = conn.channel()
print("RabbitMQ连接成功！")
conn.close()
```

## 常用管理命令

```
# 停止
docker stop rabbitmq
# 启动
docker start rabbitmq
# 查看日志（启动较慢，需要等30秒左右完全就绪）
docker logs rabbitmq -f
# 删除容器（卷rabbitmq-data保留，数据不丢）
docker rm rabbitmq
# 彻底删除容器+数据卷（谨慎！）
docker rm rabbitmq
docker volume rm rabbitmq-data
```