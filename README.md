# CodeCoze ResearchAgent 🔍

<div align="center">

**专业的 AI 技术调研智能体**

深度搜索 · 网页爬取 · 代码分析 · 博客生成

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-1.0-green?logo=langchain&logoColor=white)](https://www.langchain.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[在线演示](#) · [快速开始](#-快速开始) · [API 文档](#-api-文档) · [功能特性](#-功能特性)

</div>

---

## 📖 项目简介

CodeCoze ResearchAgent 是一个基于 **LangChain + LangGraph** 构建的智能技术调研助手。它能够像专业的技术研究员一样，自动完成从资料搜集、内容爬取、代码分析到生成深度技术博客的全流程工作。

### 核心能力

```
用户输入主题 → 多维度搜索 → 网页深度爬取 → 图片自动下载 → 代码分析 → 生成深度博客 → 打包下载
```

---

## ✨ 功能特性

### 🔍 深度搜索与爬取
- **多维度搜索**：从 20+ 个不同角度搜索，确保资料全面
- **网页爬取**：提取完整网页内容（文本 + 图片）
- **批量处理**：支持批量爬取 50+ 个网页
- **图片下载**：自动下载网页中的图片到本地

### 💻 代码分析
- 将代码落盘到工作目录
- 生成 5-10 个复杂工程问题
- 深度分析代码架构和实现

### 🎨 视觉内容生成
- 基于 **NanoBanana 规范** 生成专业视觉描述
- 支持架构图、流程图提示词生成
- 可配合 Lovart AI 生成高质量图片

### 📝 深度博客生成
- 基于真实资料生成 5000+ 字深度博客
- 包含代码示例、架构图、最佳实践
- 自动生成目录结构和引用链接

### 📦 文件导出
- 工作目录打包为 ZIP
- 生成可点击的下载链接
- 支持单个文件复制

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- pip 或 uv 包管理器

### 安装

```bash
# 克隆仓库
git clone https://github.com/DemonDamon/codecoze-ResearchAgent.git
cd codecoze-ResearchAgent

# 安装依赖
pip install -r requirements.txt
```

### 配置

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填写你的 API Key
```

`.env` 文件内容：

```bash
# 必填：你的 OpenAI API Key（或兼容服务的 Key）
OPENAI_API_KEY=sk-xxxx

# 可选：API 地址（默认 OpenAI）
OPENAI_BASE_URL=https://api.openai.com/v1

# 可选：模型名称（默认 gpt-4o）
OPENAI_MODEL=gpt-4o
```

### 运行

**方式一：命令行对话模式**

```bash
python run_local.py
```

**方式二：启动 API 服务**

```bash
# Linux/macOS
./start_api.sh

# 或直接运行
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

---

## 🔌 支持的模型服务

本项目支持任何兼容 OpenAI API 的模型服务：

| 服务商 | Base URL | 模型名称 | 获取 Key |
|--------|----------|----------|----------|
| **火山引擎（豆包）** | https://ark.cn-beijing.volces.com/api/v3 | doubao-seed-1-8-251228 | [获取](https://console.volcengine.com/ark) |
| **OpenAI** | https://api.openai.com/v1 | gpt-4o | [获取](https://platform.openai.com) |
| **DeepSeek** | https://api.deepseek.com/v1 | deepseek-chat | [获取](https://platform.deepseek.com) |
| **Kimi** | https://api.moonshot.cn/v1 | moonshot-v1-8k | [获取](https://platform.moonshot.cn) |
| **智谱** | https://open.bigmodel.cn/api/paas/v4 | glm-4 | [获取](https://open.bigmodel.cn) |

### 火山引擎（豆包）配置说明

火山引擎现在支持**直接使用模型名称**，无需创建推理接入点：

```bash
# .env 配置
OPENAI_API_KEY=你的API-Key
OPENAI_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
OPENAI_MODEL=doubao-seed-1-8-251228
```

常用模型：
- `doubao-seed-1-6-251015` - 通用对话模型
- `doubao-seed-1-8-251228` - 支持多模态（图片理解）
- `doubao-seed-2-0-lite-260215` - 轻量版
- `doubao-seed-2-0-pro-260215` - 专业版

---

## 📚 API 文档

启动服务后，访问以下端点：

### OpenAI 兼容接口

```bash
POST /v1/chat/completions
```

**请求示例：**

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [
      {"role": "user", "content": "帮我深度调研：LangGraph 架构设计"}
    ],
    "stream": true
  }'
```

**Python 调用：**

```python
from openai import OpenAI

client = OpenAI(
    api_key="any-key",
    base_url="http://localhost:8000/v1"
)

response = client.chat.completions.create(
    model="research-agent",
    messages=[
        {"role": "user", "content": "帮我深度调研：UI-Venus-1.5"}
    ],
    stream=True
)

for chunk in response:
    print(chunk.choices[0].delta.content, end="")
```

### 其他端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/run` | POST | 同步调用 Agent |
| `/stream_run` | POST | SSE 流式调用 |
| `/cancel/{run_id}` | POST | 取消执行 |

---

## 🛠️ 工具列表

Agent 内置以下工具：

### 文件管理
| 工具 | 说明 |
|------|------|
| `create_workspace` | 创建结构化工作目录 |
| `save_file` | 保存文件到工作目录 |
| `read_file_content` | 读取文件内容 |
| `list_files` | 列出目录文件 |
| `get_workspace_structure` | 获取目录结构 |

### 网络搜索与爬取
| 工具 | 说明 |
|------|------|
| `search_web` | 网络搜索 |
| `search_multiple_queries` | 多查询搜索 |
| `crawl_webpage` | 爬取单个网页 |
| `batch_crawl_webpages` | 批量爬取网页 |
| `extensive_search_and_crawl` | 扩展搜索并爬取（推荐） |

### 代码分析
| 工具 | 说明 |
|------|------|
| `save_code_to_workspace` | 保存代码到工作目录 |
| `analyze_code_and_generate_questions` | 分析代码生成问题 |
| `answer_code_questions` | 回答代码问题 |

### 图像生成
| 工具 | 说明 |
|------|------|
| `generate_flow_diagram_prompt` | 生成流程图提示词 |
| `generate_architecture_diagram_prompt` | 生成架构图提示词 |
| `save_generated_image` | 保存生成的图片 |

### 文件导出
| 工具 | 说明 |
|------|------|
| `pack_workspace_to_zip` | 打包工作目录 |
| `upload_and_generate_download_url` | 生成下载链接 |

---

## 🏗️ 项目结构

```
codecoze-ResearchAgent/
├── .env                        # 环境变量配置（不提交）
├── .env.example                # 环境变量示例
├── requirements.txt            # Python 依赖
├── run_local.py                # 本地对话脚本
├── start_api.sh                # API 服务启动脚本
├── config/
│   └── agent_llm_config.json   # Agent 配置（模型、提示词）
├── docs/
│   ├── API_INTEGRATION.md      # API 集成指南
│   └── LOCAL_RUN.md            # 本地运行指南
└── src/
    ├── agents/
    │   └── agent.py            # Agent 主逻辑
    ├── tools/
    │   ├── file_manager.py     # 文件管理工具
    │   ├── web_crawler.py      # 网页爬取工具
    │   ├── web_researcher.py   # 网络搜索工具
    │   ├── code_analyzer.py    # 代码分析工具
    │   ├── image_generator.py  # 图像生成工具
    │   └── export_workspace.py # 文件导出工具
    ├── storage/
    │   └── memory/             # 内存存储
    ├── utils/                  # 工具函数
    └── main.py                 # FastAPI 服务入口
```

---

## 🔧 集成到 Claude Code / Cursor

### 方式一：OpenAI 兼容 API

**Claude Code 配置** (`~/.claude/config.json`)：

```json
{
  "apiBaseUrl": "http://localhost:8000/v1",
  "apiKey": "local"
}
```

**Cursor 配置**：

Settings → Models → OpenAI：
- Base URL: `http://localhost:8000/v1`
- API Key: `local`

### 方式二：MCP 协议

创建 `~/.claude/claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "codecoze-research": {
      "command": "python",
      "args": ["-m", "src.mcp_server"],
      "cwd": "/path/to/codecoze-ResearchAgent"
    }
  }
}
```

详见 [API_INTEGRATION.md](docs/API_INTEGRATION.md)

---

## 📋 使用示例

### 示例 1：技术调研

```
👤 用户：帮我深度调研：LangGraph 架构设计

🤖 Agent：
1. 创建工作目录 /tmp/langgraph_research/
2. 执行 20 个维度的搜索查询
3. 爬取 50+ 个网页的完整内容
4. 下载相关图片和截图
5. 生成深度博客 blog.md
6. 打包并生成下载链接
```

### 示例 2：竞品分析

```
👤 用户：帮我对比分析 UI-Venus-1.5 和 Claude Computer Use

🤖 Agent：
1. 分别搜索两个产品的信息
2. 爬取官方文档和技术博客
3. 生成对比分析报告
4. 包含功能对比表格和架构对比图
```

---

## ⚙️ 高级配置

### 修改系统提示词

编辑 `config/agent_llm_config.json`：

```json
{
  "sp": "你的自定义提示词..."
}
```

### 修改模型参数

```json
{
  "config": {
    "temperature": 0.7,
    "max_completion_tokens": 10000
  }
}
```

### 调整搜索参数

在调用 `extensive_search_and_crawl` 时：

```json
{
  "topic": "你的主题",
  "num_queries": 30,       // 搜索查询数量
  "results_per_query": 10  // 每个查询的结果数
}
```

---

## 🐛 常见问题

### Q: 提示"未配置 OPENAI_API_KEY"

确保 `.env` 文件存在且包含有效的 API Key：

```bash
cat .env  # 检查配置
```

### Q: 网络搜索失败

本地运行时，Coze 搜索服务不可用。替代方案：
- 使用 `crawl_webpage` 直接爬取已知网页
- 配置第三方搜索 API（如 Serper、Tavily）

### Q: 网页爬取 403 错误

部分网站有反爬机制，可以：
- 使用代理
- 添加请求头模拟浏览器
- 尝试其他来源

### Q: 生成内容太短

修改 `config/agent_llm_config.json`：

```json
{
  "config": {
    "max_completion_tokens": 16000
  }
}
```

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [LangChain](https://www.langchain.com/) - Agent 框架
- [LangGraph](https://github.com/langchain-ai/langgraph) - 状态管理
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - HTML 解析
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给一个 Star！**

Made with ❤️ by [DemonDamon](https://github.com/DemonDamon)

</div>
