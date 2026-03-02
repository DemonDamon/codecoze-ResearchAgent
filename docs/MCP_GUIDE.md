# MCP 工具配置指南

本文档说明如何将 Research Agent 配置为 MCP 工具，在 Cursor、Claude Code 等 AI 编辑器中使用。

## 什么是 MCP？

MCP (Model Context Protocol) 是一个开放协议，允许 AI 工具与外部服务进行标准化交互。通过 MCP，你可以：

- 在 Cursor 中直接调用深度调研工具
- 在 Claude Code 中使用搜索和爬取功能
- 自动保存文件到本地目录

## Cursor 配置

### 1. 创建配置文件

在项目根目录创建 `.cursor/mcp.json`：

```json
{
    "mcpServers": {
        "research-agent": {
            "command": "python",
            "args": ["-m", "src.mcp_server"],
            "cwd": "/path/to/codecoze-ResearchAgent",
            "env": {
                "OPENAI_API_KEY": "your-api-key",
                "OPENAI_BASE_URL": "https://ark.cn-beijing.volces.com/api/v3",
                "OPENAI_MODEL": "doubao-seed-2-0-lite-260215",
                "BOCHA_API_KEY": "sk-xxxx"
            }
        }
    }
}
```

**配置说明**：

- **Python 环境指定**：建议在 `command` 中指定虚拟环境的 Python 完整路径，避免与系统 Python 冲突：
  - Conda：`"/opt/miniconda3/envs/your-env/bin/python"`
  - venv：`"/path/to/codecoze-ResearchAgent/.venv/bin/python"`
- **版本冲突时**：用 conda 或 venv 创建独立环境后，在 `command` 中填入该环境的 Python 路径：
  - Conda：`conda create -n research-agent python=3.10` → `conda activate research-agent` → `pip install -r requirements.txt`
  - venv：`python -m venv .venv` → `source .venv/bin/activate` → `pip install -r requirements.txt`

### 2. 重启 Cursor

配置完成后，重启 Cursor 使配置生效。

### 3. 使用 MCP 工具

在 Cursor Chat 中，你可以直接使用自然语言调用工具：

```
帮我搜索 LangChain 相关信息，保存在 langchain_demo 下面
```

工具会自动：
1. 创建 `/tmp/langchain_demo/` 目录
2. 搜索相关信息
3. 爬取相关网页
4. 生成博客并保存

## Claude Code 配置

创建 `~/.claude/claude_desktop_config.json`：

```json
{
    "mcpServers": {
        "research-agent": {
            "command": "python",
            "args": ["-m", "src.mcp_server"],
            "cwd": "/path/to/codecoze-ResearchAgent"
        }
    }
}
```

## 可用的 MCP 工具

### 1. `deep_research`

深度技术调研，生成专业博客文章。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `topic` | string | 是 | 要调研的主题或 URL |
| `workspace_name` | string | 否 | 工作目录名称，如 `turix_analysis` |
| `depth` | string | 否 | 调研深度：`quick`/`normal`/`deep` |
| `focus_areas` | array | 否 | 关注的领域，如 `["架构", "应用场景"]` |

**使用示例**：

```
帮我深度调研：TuriX-CUA，保存在 turix_analysis 下面
```

等价于：

```json
{
    "topic": "TuriX-CUA",
    "workspace_name": "turix_analysis",
    "depth": "normal"
}
```

### 2. `web_search`

执行网络搜索，获取实时信息。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | 是 | 搜索查询 |
| `count` | number | 否 | 返回结果数量，默认 10 |

**使用示例**：

```
帮我搜索：最新的 AI Agent 框架
```

### 3. `crawl_webpage`

爬取指定网页内容，提取文本和图片。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `url` | string | 是 | 要爬取的网页 URL |
| `workspace_name` | string | 否 | 工作目录名称 |
| `download_images` | boolean | 否 | 是否下载图片，默认 true |

**使用示例**：

```
帮我爬取这个网页：https://github.com/user/repo
```

### 4. `crawl_github`

爬取 GitHub 仓库的 README、文档、Wiki 等内容。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `repo_url` | string | 是 | GitHub 仓库 URL |
| `workspace_name` | string | 否 | 工作目录名称 |

**使用示例**：

```
帮我分析这个 GitHub 项目：https://github.com/TurixAI/TuriX-CUA
```

### 5. `regenerate_visual_prompt`

基于「文本转绘图描述」规约，使用 LLM 将文本重新生成为 NanoBanana 格式的视觉提示词。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `content_description` | string | 是 | 要转化为视觉描述的内容（概念、流程、架构等文本） |
| `prompt_type` | string | 否 | 提示词类型：`text_to_visual`(通用)、`flow`(流程图)、`architecture`(架构图)，默认 `text_to_visual` |
| `workspace_name` | string | 否 | 工作目录名称，默认 `research_workspace`。保存到 `/tmp/{workspace_name}/generated/visual_prompts/` |

**使用示例**：

```
帮我重新生成视觉提示词：LangGraph 的 Agent 执行流程，用户输入 -> 规划 -> 工具调用 -> 结果汇总
```

等价于：

```json
{
    "content_description": "LangGraph 的 Agent 执行流程，用户输入 -> 规划 -> 工具调用 -> 结果汇总",
    "prompt_type": "flow",
    "workspace_name": "research_workspace"
}
```

## 工作目录命名规则

### 自动命名（时间戳）

当用户未指定目录名时，自动使用时间戳：

```
用户：帮我搜索 LangChain 相关信息
→ 工作目录：/tmp/research_20260225_143000
```

### 用户指定命名

当用户指定目录名时，使用用户指定的名称：

```
用户：帮我搜索 LangChain 相关信息，保存在 langchain_demo 下面
→ 工作目录：/tmp/langchain_demo
```

**支持的命名关键词**：
- 「保存在...下面」
- 「保存到...」
- 「放到...」
- 「存到...」

## 环境变量说明

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `OPENAI_API_KEY` | 是 | OpenAI 或兼容服务的 API Key |
| `OPENAI_BASE_URL` | 否 | API 地址，默认 OpenAI |
| `OPENAI_MODEL` | 否 | 模型名称，默认 gpt-4o |
| `BOCHA_API_KEY` | 否 | Bocha AI 搜索 API Key（推荐配置） |

## 测试 MCP 服务器

### HTTP 模式（用于测试）

```bash
python -m src.mcp_server --http --port 8001
```

然后在浏览器访问 `http://localhost:8001/sse`

### Stdio 模式（用于 Cursor/Claude）

```bash
python -m src.mcp_server
```

## 常见问题

### Q: MCP 工具不显示？

1. 检查配置文件路径是否正确
2. 检查 `cwd` 路径是否指向项目根目录
3. 检查 Python 环境是否正确
4. 重启 Cursor

### Q: 工具调用失败？

1. 检查环境变量是否配置正确
2. 检查 API Key 是否有效
3. 查看终端日志排查错误

### Q: 搜索没有结果？

1. 检查 BOCHA_API_KEY 是否配置
2. 尝试直接提供 GitHub URL
3. 检查网络连接

### Q: 出现「socksio 未安装」或 SOCKS 代理错误？

在 MCP 使用的虚拟环境中安装：`pip install "httpx[socks]"`（zsh 下需加引号，否则 `[]` 会被解析）。若使用代理，可在 `env` 中配置 `HTTP_PROXY`、`HTTPS_PROXY`、`ALL_PROXY` 为你的代理地址。

## 输出文件结构

每次调研会在工作目录下生成以下结构：

```
/tmp/{workspace_name}/
├── sources/
│   ├── web/           # 爬取的网页内容（Markdown）
│   ├── code/          # 代码文件
│   └── manual_images/ # 下载的图片
├── generated/
│   ├── images/        # 生成的图片
│   └── visual_prompts/# 视觉提示词
└── blog.md            # 生成的博客文章
```
