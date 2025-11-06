<div align="center">

# smithery-2api-web

**将 [Smithery.ai](https://smithery.ai/) AI 模型转换为 OpenAI API 格式 + Web 管理界面**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/python-3.10+-brightgreen.svg)](https://www.python.org/)
[![Docker Support](https://img.shields.io/badge/docker-supported-blue.svg?logo=docker)](https://www.docker.com/)

</div>

---

## 核心特性

- **Web 管理界面** - 可视化管理 Cookie，无需手动编辑配置文件
- **API 密钥认证** - 安全的客户端访问控制  
- **多账号轮询** - 支持多个 Smithery Cookie 自动切换
- **极致流式响应** - httpx 异步 + HTTP/2，丝滑实时传输，零缓冲延迟
- **OpenAI 兼容** - 完全兼容 OpenAI API 格式
- **高性能异步** - 基于 httpx + HTTP/2 多路复用，低延迟高并发
- **Docker 部署** - 一键启动服务

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/ImogeneOctaviap794/smithery-2api-web.git
cd smithery-2api-web
```

### 2. 配置环境

创建 `.env` 文件：

```bash
# API 主密钥（必填）
API_MASTER_KEY=your-secure-api-key-here
```

### 3. 启动服务

```bash
# 直接运行
python main.py

# 或使用 Docker
docker-compose up -d
```

### 4. 访问管理页面

打开浏览器访问：`http://localhost:8088/admin/login.html`

使用 `.env` 中的 `API_MASTER_KEY` 登录

### 5. 添加 Cookie

#### 方法1：直接复制完整Cookie（推荐）

1. 登录 [Smithery.ai](https://smithery.ai/)
2. 按 `F12` → **Application** → **Cookies** → `https://smithery.ai`
3. 全选所有Cookie，右键 → **复制所有Cookie**
4. 在管理页面粘贴完整Cookie字符串

**优势**：
- 最简单，一次复制所有Cookie
- 包含PostHog追踪Cookie，避免403错误
- 无需手动拼接

**Cookie 示例**：
```
sb-spjawbfpwezjfmicopsl-auth-token.0=base64-eyJhY2Nlc...; sb-spjawbfpwezjfmicopsl-auth-token.1=SI6eyJhdmF0...; ph_phc_WiMP1Rj0YvrdwYVYdE0AdRBNmB8MTdbsWY8oalxSrts_posthog=%7B%22distinct_id%22%3A%22df6e...
```

#### 方法2：仅复制auth-token（手动拼接）

1. 找到 `sb-spjawbfpwezjfmicopsl-auth-token.0` 的值
2. 找到 `sb-spjawbfpwezjfmicopsl-auth-token.1` 的值（如果存在）
3. 用 `|` 连接：`base64-xxx|yyy`

**注意**：此方法可能导致403错误（缺少PostHog追踪）

## API 使用

### 添加 Cookie（API方式）

可以通过API直接添加Cookie，无需登录管理页面：

```bash
curl -X POST "http://localhost:8088/v1/cookies/add" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "name": "主账号",
    "cookie_data": "base64-eyJhY2Nlc3M...|SI6eyJhdmF0YXJ..."
  }'
```

响应示例：
```json
{
  "success": true,
  "message": "Cookie 添加成功",
  "data": {
    "id": 1,
    "name": "主账号",
    "is_active": true
  }
}
```

### 聊天补全

```bash
curl -X POST "http://localhost:8088/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "claude-haiku-4.5",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true
  }'
```

### OpenAI SDK

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8088/v1",
    api_key="your-api-key"
)

response = client.chat.completions.create(
    model="claude-haiku-4.5",
    messages=[{"role": "user", "content": "Hello"}],
    stream=True
)

for chunk in response:
    print(chunk.choices[0].delta.content, end="")
```

## 支持的模型

- `claude-haiku-4.5` / `claude-sonnet-4.5`
- `gpt-5` / `gpt-5-mini` / `gpt-5-nano`
- `gemini-2.5-flash-lite` / `gemini-2.5-pro`
- `grok-4-fast-reasoning` / `grok-4-fast-non-reasoning`
- `glm-4.6` / `kimi-k2` / `deepseek-reasoner`

## 技术架构

### 核心技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| **FastAPI** | 最新 | 异步 Web 框架 |
| **httpx** | 最新 | 异步 HTTP 客户端 + HTTP/2 支持 |
| **SQLite** | - | Cookie 数据持久化 |
| **Nginx** | 最新 | 反向代理 + 负载均衡 |

### ⚡ 流式优化技术

本项目采用多层优化，实现**极致丝滑**的流式输出：

#### 1. **异步 HTTP/2 客户端**
```python
# 使用 httpx 替代同步 requests/cloudscraper
httpx.AsyncClient(
    http2=True,  # 启用 HTTP/2 多路复用
    timeout=httpx.Timeout(180.0, connect=10.0),
)
```

**优势**：
- ✅ 真正的异步非阻塞
- ✅ HTTP/2 多路复用，单连接支持多个并发请求
- ✅ 头部压缩，减少传输开销
- ✅ 更低的延迟，更高的吞吐量

#### 2. **异步流式迭代**
```python
async with client.stream("POST", url) as response:
    async for line in response.aiter_lines():
        yield data  # 立即转发，零缓冲
```

**关键点**：
- `aiter_lines()` 异步迭代器，一有数据立即处理
- 逐行实时转发，不积累缓冲
- 事件循环不阻塞，支持高并发

#### 3. **端到端禁用缓冲**

**FastAPI 层**：
```python
StreamingResponse(
    headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
    }
)
```

**Nginx 层**：
```nginx
proxy_buffering off;           # 禁用代理缓冲
proxy_request_buffering off;   # 禁用请求缓冲
chunked_transfer_encoding off; # 禁用分块编码缓冲
```

### 📊 性能对比

| 指标 | 优化前 (cloudscraper) | 优化后 (httpx + HTTP/2) |
|------|---------------------|------------------------|
| 首字延迟 | ~2-3 秒 | < 500ms |
| 流式体验 | 大段输出，卡顿 | 逐字流畅输出 |
| 并发能力 | 低（同步阻塞） | 高（异步非阻塞） |
| 协议 | HTTP/1.1 | HTTP/2 |

## 项目结构

```
smithery-2api-web/
├── app/
│   ├── core/          # 配置管理
│   ├── db/            # 数据库操作（SQLite）
│   ├── providers/     # Smithery API 适配器
│   ├── routers/       # 管理 API 路由
│   ├── middleware/    # 认证中间件
│   ├── static/        # Web 管理界面
│   └── utils/         # 工具函数
├── data/              # 数据库存储目录
├── main.py            # 应用入口
├── requirements.txt   # Python 依赖
└── docker-compose.yml # Docker 配置
```

## 管理界面

- **深色主题** - Dracula 配色方案
- **Cookie 管理** - 添加、编辑、删除、启用/禁用
- **调用统计** - 显示每个 Cookie 的调用次数
- **调用日志** - 查看所有API调用历史记录
- **API 密钥查看** - 查看当前配置的密钥

## 配置说明

### 环境变量

| 变量 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| `API_MASTER_KEY` | API 认证密钥 | 是 | - |
| `NGINX_PORT` | 服务端口 | 否 | 8088 |

### Cookie 存储

- Cookie 保存在 SQLite 数据库：`./data/smithery.db`
- 支持多个 Cookie 自动轮询
- 可通过管理界面实时增删改

## 安全建议

1. 使用强密码作为 `API_MASTER_KEY`
2. 不要在公网暴露管理页面
3. 定期备份 `data` 目录
4. 生产环境使用 HTTPS

## 🐛 常见问题

### Cookie 格式错误

确保复制的是 `sb-spjawbfpwezjfmicopsl-auth-token.0` 的完整 value 值，格式为 `base64-xxx`

### API 请求 401/403

检查 `Authorization` 头是否正确设置为 `Bearer your-api-key`

### 流式响应延迟

已优化为真正的流式传输，使用 `iter_content()` 逐块处理

## 📝 更新日志

### v2.0.0 (2025-10-19)

- ✨ 新增 Web 管理界面（DaisyUI Dracula 主题）
- ✨ 新增 Cookie 可视化管理（SQLite 数据库）
- ✨ 新增 API 密钥查看功能
- 🔒 强化 API 密钥验证逻辑
- ⚡ 优化流式响应性能（真正的无缓冲流）
- 🎨 改进请求头，更贴近真实浏览器
- 🐛 修复 Cookie 格式兼容问题

### v1.0.0

- 🎉 初始版本
- 支持 OpenAI API 格式转换
- 支持多账号轮询

## 🤝 贡献

欢迎 PR 和 Issue！

## 📄 许可证

Apache 2.0 License

## 🔗 相关链接

- [Smithery.ai 官网](https://smithery.ai/)
- [OpenAI API 文档](https://platform.openai.com/docs/api-reference)

---

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐️ 支持一下！**

</div>
