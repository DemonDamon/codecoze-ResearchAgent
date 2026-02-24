# 本地运行指南

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑 .env 文件，填写你的 API Key
# OPENAI_API_KEY=sk-xxxx
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_MODEL=gpt-4o
```

### 3. 运行

**方式 A：命令行对话模式**
```bash
python run_local.py
```

**方式 B：启动 API 服务**
```bash
# Linux/macOS
chmod +x start_api.sh
./start_api.sh

# 或直接运行
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### 4. 测试 API

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "帮我调研：LangGraph"}],
    "stream": false
  }'
```

---

## 支持的模型服务

你可以使用任何兼容 OpenAI API 的服务：

| 服务 | Base URL | 获取 API Key |
|------|----------|--------------|
| OpenAI | https://api.openai.com/v1 | https://platform.openai.com |
| DeepSeek | https://api.deepseek.com/v1 | https://platform.deepseek.com |
| Kimi (月之暗面) | https://api.moonshot.cn/v1 | https://platform.moonshot.cn |
| 豆包 (火山引擎) | https://ark.cn-beijing.volces.com/api/v3 | https://console.volcengine.com/ark |
| 智谱 AI | https://open.bigmodel.cn/api/paas/v4 | https://open.bigmodel.cn |

---

## 注意事项

### 功能限制

本地运行时，以下功能依赖 Coze 平台服务，可能无法使用：

| 功能 | 状态 | 说明 |
|------|------|------|
| 网络搜索 (`search_web`) | ❌ 不可用 | 需要 Coze 搜索服务 |
| 对象存储上传 (`upload_and_generate_download_url`) | ❌ 不可用 | 需要 Coze 存储服务 |
| 网页爬取 | ✅ 可用 | 使用 requests + BeautifulSoup |
| 文件管理 | ✅ 可用 | 本地文件系统 |
| 代码分析 | ✅ 可用 | 纯文本分析 |
| 视觉提示词生成 | ✅ 可用 | 纯文本生成 |

### 替代方案

**网络搜索**：可以使用其他搜索 API（如 Serper、Tavily），需要修改 `tools/web_researcher.py`

**对象存储**：可以使用 AWS S3、阿里云 OSS 等，需要修改 `tools/export_workspace.py`

---

## 项目结构

```
.
├── .env                    # 本地配置（不提交到 Git）
├── .env.example            # 配置示例
├── run_local.py            # 本地对话脚本
├── start_api.sh            # 启动 API 服务
├── requirements.txt        # Python 依赖
├── config/
│   └── agent_llm_config.json   # Agent 配置
└── src/
    ├── agents/
    │   └── agent.py        # Agent 主逻辑
    ├── tools/              # 工具定义
    ├── storage/            # 存储相关
    └── main.py             # FastAPI 服务
```

---

## 常见问题

### Q: 提示 "未配置 OPENAI_API_KEY"

A: 确保 .env 文件存在且包含有效的 API Key：
```bash
cat .env  # 检查配置
```

### Q: 网络搜索失败

A: 本地运行不支持 Coze 搜索服务。可以：
1. 使用爬取工具 (`crawl_webpage`) 替代
2. 配置第三方搜索 API

### Q: 如何修改系统提示词

A: 编辑 `config/agent_llm_config.json` 中的 `sp` 字段。
