# Agent Builder Skill

构建 LangChain/LangGraph 智能体和 MCP 服务的完整指南。

## 快速开始

### 1. 创建新项目

```bash
# 复制模板目录
cp -r skills/agent_builder/templates my-agent
cd my-agent

# 创建目录结构
mkdir -p src/agents src/tools config

# 复制核心文件
cp templates/agent.py src/agents/
cp templates/mcp_server.py src/
cp templates/tools/file_manager.py src/tools/
cp templates/config/agent_llm_config.json config/
cp templates/.env.example .env

# 安装依赖
pip install langchain langgraph langchain-openai mcp coze-coding-utils
```

### 2. 配置环境

```bash
# 编辑 .env
vim .env

# 填写 API Key
OPENAI_API_KEY=sk-xxxx
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o
```

### 3. 开发工具

在 `src/tools/` 下创建工具文件：

```python
# src/tools/my_tool.py
from langchain.tools import tool, ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context

@tool
def my_tool(param: str, runtime: ToolRuntime = None) -> str:
    """工具描述（显示给 LLM）
    
    Args:
        param: 参数说明
    """
    ctx = runtime.context if runtime else new_context(method="my_tool")
    return f"结果: {param}"
```

在 `src/agents/agent.py` 中导入并添加到 tools 列表。

### 4. 配置 MCP

创建 `.cursor/mcp.json`：

```json
{
    "mcpServers": {
        "my-agent": {
            "command": "/path/to/python",
            "args": ["-m", "src.mcp_server"],
            "cwd": "/path/to/my-agent",
            "env": {
                "PYTHONPATH": "/path/to/my-agent",
                "OPENAI_API_KEY": "sk-xxxx",
                "OPENAI_BASE_URL": "https://api.openai.com/v1",
                "OPENAI_MODEL": "gpt-4o"
            }
        }
    }
}
```

### 5. 测试

```bash
# 测试 MCP 服务
python -m src.mcp_server

# 或 HTTP 模式
python -m src.mcp_server --http --port 8001
```

## 模板文件

| 文件 | 说明 |
|------|------|
| `templates/agent.py` | Agent 主逻辑模板 |
| `templates/mcp_server.py` | MCP 服务模板 |
| `templates/tools/file_manager.py` | 文件管理工具模板 |
| `templates/config/agent_llm_config.json` | 配置文件模板 |
| `templates/.cursor/mcp.json.example` | MCP 配置示例 |
| `templates/.env.example` | 环境变量模板 |

## 核心概念

### Agent 状态管理

```python
from typing import Annotated
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages

MAX_MESSAGES = 40  # 保留最近 20 轮对话

def _windowed_messages(old, new):
    return add_messages(old, new)[-MAX_MESSAGES:]

class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]
```

### 工具封装规范

```python
@tool
def tool_name(
    required_param: str,        # 必填参数
    optional_param: int = 10,   # 可选参数带默认值
    workspace_dir: str = "/tmp/workspace",  # 工作目录
    runtime: ToolRuntime = None # 运行时上下文
) -> str:
    """工具描述（会显示给 LLM）
    
    Args:
        required_param: 必填参数说明
        optional_param: 可选参数说明
        workspace_dir: 工作目录路径
    """
    ctx = runtime.context if runtime else new_context(method="tool_name")
    
    # 工具逻辑
    try:
        result = do_something(required_param)
        return f"成功: {result}"
    except Exception as e:
        return f"失败: {str(e)}"
```

### 工作目录命名

```python
from datetime import datetime

def get_workspace_dir(name=None):
    if name:
        return f"/tmp/{name}"  # 用户指定
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"/tmp/workspace_{timestamp}"  # 自动时间戳
```

## 最佳实践

### 1. 工具设计
- ✅ 单一职责：每个工具只做一件事
- ✅ 清晰描述：LLM 需要理解工具用途
- ✅ 默认参数：减少必填参数
- ✅ 友好错误：帮助 LLM 理解失败原因

### 2. 系统提示词
- ✅ 角色定义清晰
- ✅ 工作流程明确
- ✅ 输出格式规范
- ✅ 边界条件说明

### 3. MCP 工具
- ✅ 3-5 个核心工具
- ✅ workspace_name 参数支持自定义目录
- ✅ 详细的使用文档

## 支持的模型

| 服务商 | Base URL | 模型示例 |
|--------|----------|----------|
| OpenAI | https://api.openai.com/v1 | gpt-4o |
| 火山引擎 | https://ark.cn-beijing.volces.com/api/v3 | doubao-seed-2-0-lite-260215 |
| DeepSeek | https://api.deepseek.com/v1 | deepseek-chat |
| Kimi | https://api.moonshot.cn/v1 | moonshot-v1-8k |

## 详细文档

完整指南请参阅 `docs/RESEARCH_AGENT_SKILL.md`
