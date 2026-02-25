# Research Agent 构建指南

本指南总结了构建技术调研智能体（Research Agent）的完整过程，可作为构建其他智能体、MCP 工具、插件的参考模板。

## 目录

- [项目结构](#项目结构)
- [核心组件](#核心组件)
- [智能体构建](#智能体构建)
- [工具封装](#工具封装)
- [MCP 服务开发](#mcp-服务开发)
- [配置管理](#配置管理)
- [测试与调试](#测试与调试)
- [部署与集成](#部署与集成)

---

## 项目结构

```
project/
├── .env                        # 环境变量配置（不提交）
├── .env.example                # 环境变量示例
├── requirements.txt            # Python 依赖
├── run_local.py                # 本地对话脚本
├── start_api.sh                # API 服务启动脚本
├── config/
│   └── agent_llm_config.json   # Agent 配置（模型、提示词、工具列表）
├── docs/
│   ├── API_INTEGRATION.md      # API 集成指南
│   ├── LOCAL_RUN.md            # 本地运行指南
│   └── MCP_GUIDE.md            # MCP 使用指南
└── src/
    ├── agents/
    │   └── agent.py            # Agent 主逻辑（必须）
    ├── tools/
    │   ├── file_manager.py     # 文件管理工具
    │   ├── web_crawler.py      # 网页爬取工具
    │   ├── web_researcher.py   # 网络搜索工具
    │   └── ...                 # 其他工具
    ├── storage/
    │   └── memory/             # 内存存储
    ├── utils/                  # 工具函数
    ├── main.py                 # FastAPI 服务入口
    └── mcp_server.py           # MCP 服务（可选）
```

---

## 核心组件

### 1. Agent 主逻辑 (`src/agents/agent.py`)

```python
import os
import json
from typing import Annotated
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from coze_coding_utils.runtime_ctx.context import default_headers
from storage.memory.memory_saver import get_memory_saver

LLM_CONFIG = "config/agent_llm_config.json"
MAX_MESSAGES = 40  # 滑动窗口大小

def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    return add_messages(old, new)[-MAX_MESSAGES:]

class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]

def build_agent(ctx=None):
    """构建 Agent 实例"""
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    config_path = os.path.join(workspace_path, LLM_CONFIG)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    
    # 获取 API 配置
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")
    model = os.getenv("OPENAI_MODEL") or cfg['config'].get("model", "gpt-4o")
    
    llm = ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=cfg['config'].get('temperature', 0.7),
        streaming=True,
        timeout=cfg['config'].get('timeout', 600),
        default_headers=default_headers(ctx) if ctx else {}
    )
    
    # 导入工具
    from tools.file_manager import create_workspace, save_file, read_file_content
    from tools.web_crawler import extensive_search_and_crawl, crawl_webpage
    # ... 导入其他工具
    
    tools = [
        create_workspace, save_file, read_file_content,
        extensive_search_and_crawl, crawl_webpage,
        # ... 其他工具
    ]
    
    return create_agent(
        model=llm,
        system_prompt=cfg.get("sp"),
        tools=tools,
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
```

### 2. 配置文件 (`config/agent_llm_config.json`)

```json
{
    "config": {
        "temperature": 0.7,
        "frequency_penalty": 0,
        "top_p": 0.9,
        "max_tokens": 4096,
        "max_completion_tokens": 10000,
        "thinking_type": "enabled",
        "reasoning_effort": "medium",
        "response_format": "text",
        "model": "doubao-seed-2-0-lite-260215"
    },
    "sp": "# 角色定义\n你是...",
    "tools": [
        "tool_name_1",
        "tool_name_2"
    ]
}
```

**配置规则**：
- `config`: 必须包含 `model`, `temperature`, `top_p`, `max_completion_tokens`, `timeout`, `thinking` 字段
- `sp`: 系统提示词，必须非空
- `tools`: 工具列表，无工具时为空数组 `[]`

---

## 智能体构建

### 1. 设计原则

1. **最小化工具使用**：只有当 LLM 无法独立完成任务时才封装工具
2. **工具职责单一**：每个工具只做一件事
3. **错误处理完善**：工具应该有清晰的错误提示和降级方案
4. **记忆管理**：使用滑动窗口限制上下文长度

### 2. 系统提示词设计

```markdown
# 角色定义
[清晰定义 Agent 的身份、专业领域、能力与语气]

# 任务目标
[简明描述需解决的核心问题]

# 核心能力
- **能力1**：描述
- **能力2**：描述

# 工作流程
## 第1步：xxx
- 详细说明

## 第2步：xxx
- 详细说明

# 输出要求
- 格式要求
- 质量标准

# 注意事项
- 边界条件
- 错误处理
```

### 3. 状态管理

```python
from typing import Annotated
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages

MAX_MESSAGES = 40  # 保留最近 20 轮对话

def _windowed_messages(old, new):
    """滑动窗口"""
    return add_messages(old, new)[-MAX_MESSAGES:]

class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]
```

---

## 工具封装

### 1. 基本结构

```python
import os
from langchain.tools import tool, ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context

@tool
def my_tool(
    param1: str,
    param2: int = 10,
    workspace_dir: str = "/tmp/workspace",
    runtime: ToolRuntime = None
) -> str:
    """工具描述（会显示给 LLM）
    
    Args:
        param1: 参数1说明
        param2: 参数2说明
        workspace_dir: 工作目录
    
    Returns:
        工具执行结果的字符串描述
    """
    ctx = runtime.context if runtime else new_context(method="my_tool")
    
    # 工具逻辑
    try:
        result = do_something(param1, param2)
        return f"执行成功: {result}"
    except Exception as e:
        return f"执行失败: {str(e)}"
```

### 2. 错误处理中间件

```python
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage

@wrap_tool_call
def handle_tool_errors(request, handler):
    """自定义工具错误处理"""
    try:
        return handler(request)
    except Exception as e:
        return ToolMessage(
            content=f"工具执行错误: {str(e)}",
            tool_call_id=request.tool_call["id"]
        )

# 在 build_agent 中使用
agent = create_agent(
    model=llm,
    tools=[tool1, tool2],
    middleware=[handle_tool_errors]
)
```

### 3. 外部服务集成

```python
@tool
def call_external_api(
    query: str,
    runtime: ToolRuntime = None
) -> str:
    """调用外部 API"""
    ctx = runtime.context if runtime else new_context(method="call_external_api")
    
    # 方式1：使用内置技能（推荐）
    from coze_coding_dev_sdk import SearchClient
    client = SearchClient(ctx=ctx)
    result = client.web_search(query=query)
    
    # 方式2：使用自定义 API
    import requests
    api_key = os.getenv("MY_API_KEY")
    response = requests.post(
        "https://api.example.com/search",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"query": query}
    )
    
    return response.text
```

### 4. 文件操作工具

```python
@tool
def save_file(
    content: str,
    file_path: str,
    workspace_dir: str = "/tmp/workspace",
    runtime: ToolRuntime = None
) -> str:
    """保存文件到工作目录"""
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    full_path = os.path.join(workspace_dir, file_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return f"文件已保存: {full_path}"
```

---

## MCP 服务开发

### 1. MCP Server 结构

```python
"""
MCP Server for Your Agent

Usage:
    # Stdio mode (for Cursor/Claude Code)
    python -m src.mcp_server
    
    # HTTP mode (for testing)
    python -m src.mcp_server --http --port 8001
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent import build_agent
from coze_coding_utils.runtime_ctx.context import new_context

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = Server("your-agent-name")
_agent_instance = None

def get_agent():
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = build_agent()
    return _agent_instance


@server.list_tools()
async def list_tools() -> List[Tool]:
    """列出可用的 MCP 工具"""
    return [
        Tool(
            name="your_tool_name",
            description="工具描述",
            inputSchema={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "参数说明"
                    },
                    "workspace_name": {
                        "type": "string",
                        "description": "工作目录名称（可选）"
                    }
                },
                "required": ["param1"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """处理工具调用"""
    try:
        if name == "your_tool_name":
            return await _handle_your_tool(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def _handle_your_tool(arguments: Dict[str, Any]) -> List[TextContent]:
    """处理具体工具逻辑"""
    param1 = arguments.get("param1")
    workspace_name = arguments.get("workspace_name", "")
    
    # 构建 prompt
    prompt = f"处理任务: {param1}"
    if workspace_name:
        prompt += f"，保存在 {workspace_name} 下面"
    
    # 调用 Agent
    ctx = new_context(method="mcp_tool")
    agent = get_agent()
    
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": prompt}]},
        config={"configurable": {"thread_id": ctx.run_id}},
        context=ctx
    )
    
    # 提取结果
    if result and "messages" in result:
        last_message = result["messages"][-1]
        response = last_message.content if hasattr(last_message, 'content') else str(last_message)
    else:
        response = "执行完成，但无返回结果"
    
    return [TextContent(type="text", text=response)]


async def run_server():
    """运行 MCP 服务"""
    logger.info("Starting MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--http", action="store_true")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()
    
    if args.http:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=args.port)
    else:
        asyncio.run(run_server())


if __name__ == "__main__":
    main()
```

### 2. Cursor 配置

创建 `.cursor/mcp.json`：

```json
{
    "mcpServers": {
        "your-agent": {
            "command": "/path/to/python",
            "args": ["-m", "src.mcp_server"],
            "cwd": "/path/to/your/project",
            "env": {
                "PYTHONPATH": "/path/to/your/project",
                "OPENAI_API_KEY": "your-api-key",
                "OPENAI_BASE_URL": "https://api.openai.com/v1",
                "OPENAI_MODEL": "gpt-4o"
            }
        }
    }
}
```

### 3. Claude Code 配置

创建 `~/.claude/claude_desktop_config.json`：

```json
{
    "mcpServers": {
        "your-agent": {
            "command": "python",
            "args": ["-m", "src.mcp_server"],
            "cwd": "/path/to/your/project"
        }
    }
}
```

---

## 配置管理

### 1. 环境变量 (`.env`)

```bash
# 必填：模型 API 配置
OPENAI_API_KEY=sk-xxxx
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# 可选：搜索服务
BOCHA_API_KEY=sk-xxxx

# 可选：其他服务
MY_SERVICE_API_KEY=xxxx
```

### 2. 工作目录命名规则

```python
from datetime import datetime

def get_workspace_dir(name: str = None) -> str:
    """获取工作目录路径"""
    if name:
        # 用户指定名称
        return os.path.join("/tmp", name)
    else:
        # 自动生成时间戳目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"/tmp/workspace_{timestamp}"
```

### 3. 支持的模型服务

| 服务商 | Base URL | 模型名称示例 |
|--------|----------|-------------|
| 火山引擎 | https://ark.cn-beijing.volces.com/api/v3 | doubao-seed-2-0-lite-260215 |
| OpenAI | https://api.openai.com/v1 | gpt-4o |
| DeepSeek | https://api.deepseek.com/v1 | deepseek-chat |
| Kimi | https://api.moonshot.cn/v1 | moonshot-v1-8k |
| 智谱 | https://open.bigmodel.cn/api/paas/v4 | glm-4 |

---

## 测试与调试

### 1. 本地测试脚本 (`run_local.py`)

```python
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

from agents.agent import build_agent
from coze_coding_utils.runtime_ctx.context import new_context

async def main():
    agent = build_agent()
    ctx = new_context(method="local_test")
    
    print("🤖 Agent 已启动，输入 'quit' 退出")
    
    while True:
        user_input = input("\n👤 你: ")
        if user_input.lower() == 'quit':
            break
        
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config={"configurable": {"thread_id": ctx.run_id}},
            context=ctx
        )
        
        if result and "messages" in result:
            print(f"\n🤖 Agent: {result['messages'][-1].content}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. 测试工具调用

```python
# test_tools.py
from tools.file_manager import create_workspace, save_file

def test_create_workspace():
    result = create_workspace.func("test_workspace")
    assert "test_workspace" in result
    print("✅ create_workspace 测试通过")

def test_save_file():
    result = save_file.func(
        content="Hello World",
        file_path="test.txt",
        workspace_dir="/tmp/test_workspace"
    )
    assert "已保存" in result
    print("✅ save_file 测试通过")

if __name__ == "__main__":
    test_create_workspace()
    test_save_file()
```

### 3. MCP 服务测试

```bash
# HTTP 模式测试
python -m src.mcp_server --http --port 8001

# 然后访问
curl http://localhost:8001/sse
```

---

## 部署与集成

### 1. FastAPI 服务 (`src/main.py`)

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Agent API")

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

@app.post("/chat")
async def chat(request: ChatRequest):
    agent = get_agent()
    ctx = new_context(method="api_chat")
    
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": request.message}]},
        config={"configurable": {"thread_id": request.session_id}},
        context=ctx
    )
    
    return {"response": result["messages"][-1].content}
```

### 2. 启动脚本 (`start_api.sh`)

```bash
#!/bin/bash
cd "$(dirname "$0")"
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### 3. Docker 部署

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "-m", "src.mcp_server"]
```

---

## 最佳实践总结

### 1. 工具设计原则

- ✅ **单一职责**：每个工具只做一件事
- ✅ **清晰的描述**：LLM 需要理解工具的用途
- ✅ **合理的参数**：提供默认值，减少必填参数
- ✅ **友好的错误提示**：帮助 LLM 理解失败原因
- ✅ **降级方案**：外部服务不可用时提供替代方案

### 2. 系统提示词设计

- ✅ **角色定义清晰**：让 LLM 知道它的身份
- ✅ **工作流程明确**：逐步指导 LLM 完成任务
- ✅ **输出格式规范**：指定输出结构
- ✅ **边界条件说明**：告诉 LLM 什么时候做什么

### 3. MCP 工具设计

- ✅ **工具数量适中**：3-5 个核心工具即可
- ✅ **参数简洁**：必填参数控制在 1-2 个
- ✅ **workspace_name 参数**：支持自定义目录命名
- ✅ **详细的使用文档**：帮助用户理解工具

### 4. 错误处理

```python
# 工具级别的错误处理
@tool
def my_tool(param: str) -> str:
    try:
        result = do_something(param)
        return f"成功: {result}"
    except SpecificError as e:
        return f"特定错误: {e}，请尝试 xxx"
    except Exception as e:
        return f"未知错误: {e}"

# Agent 级别的错误处理
@wrap_tool_call
def handle_errors(request, handler):
    try:
        return handler(request)
    except Exception as e:
        return ToolMessage(
            content=f"工具错误: {e}",
            tool_call_id=request.tool_call["id"]
        )
```

---

## 快速启动模板

### 创建新项目

```bash
# 1. 复制项目结构
cp -r codecoze-ResearchAgent new-agent-project
cd new-agent-project

# 2. 修改配置
# - config/agent_llm_config.json
# - src/agents/agent.py
# - src/tools/

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env

# 5. 测试
python run_local.py
```

### 最小化 Agent 模板

```python
# src/agents/agent.py
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
import os, json

LLM_CONFIG = "config/agent_llm_config.json"

def build_agent(ctx=None):
    with open(LLM_CONFIG, 'r') as f:
        cfg = json.load(f)
    
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", cfg['config']['model']),
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
    )
    
    return create_agent(
        model=llm,
        system_prompt=cfg['sp'],
        tools=[],  # 添加你的工具
    )
```
