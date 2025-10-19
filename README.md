<div align="center">

# 🔐 smithery-2api

**将 [Smithery.ai](https://smithery.ai/) AI 模型转换为 OpenAI API 格式**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/python-3.10+-brightgreen.svg)](https://www.python.org/)
[![Docker Support](https://img.shields.io/badge/docker-supported-blue.svg?logo=docker)](https://www.docker.com/)

</div>

---

## ✨ 核心特性

- **🎨 Web 管理界面** - 可视化管理 Cookie，无需手动编辑配置文件
- **🔐 API 密钥认证** - 安全的客户端访问控制
- **🔄 多账号轮询** - 支持多个 Smithery Cookie 自动切换
- **⚡ 真正的流式响应** - 实时传输，无缓冲延迟
- **🔌 OpenAI 兼容** - 完全兼容 OpenAI API 格式
- **☁️ Cloudflare 穿透** - 自动处理反爬虫机制
- **🐳 Docker 部署** - 一键启动服务

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/lzA6/smithery-2api.git
cd smithery-2api
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

1. 登录 [Smithery.ai](https://smithery.ai/)
2. 按 `F12` → **Application** → **Cookies** → `https://smithery.ai`
3. 找到 `sb-spjawbfpwezjfmicopsl-auth-token.0`
4. 复制其 value 值（`base64-` 开头）
5. 在管理页面点击"添加 Cookie"并粘贴

## 📖 API 使用

### cURL 示例

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

## 🎯 支持的模型

- `claude-haiku-4.5` / `claude-sonnet-4.5`
- `gpt-5` / `gpt-5-mini` / `gpt-5-nano`
- `gemini-2.5-flash-lite` / `gemini-2.5-pro`
- `grok-4-fast-reasoning` / `grok-4-fast-non-reasoning`
- `glm-4.6` / `kimi-k2` / `deepseek-reasoner`

## 📁 项目结构

```
smithery-2api/
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

## 🎨 管理界面

- **深色主题** - Dracula 配色方案
- **Cookie 管理** - 添加、编辑、删除、启用/禁用
- **API 密钥查看** - 查看当前配置的密钥
- **统计信息** - 实时显示 Cookie 状态

## 🔧 配置说明

### 环境变量

| 变量 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| `API_MASTER_KEY` | API 认证密钥 | 是 | - |
| `NGINX_PORT` | 服务端口 | 否 | 8088 |

### Cookie 存储

- Cookie 保存在 SQLite 数据库：`./data/smithery.db`
- 支持多个 Cookie 自动轮询
- 可通过管理界面实时增删改

## 🔐 安全建议

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
