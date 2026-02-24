# Agent API 集成指南

本文档说明如何将调研Agent集成到Claude Code、Cursor等AI工具中。

---

## 方案一：OpenAI 兼容 API（推荐）

项目已提供 OpenAI 兼容接口，可直接被支持 OpenAI API 的工具调用。

### 启动服务

```bash
# 在项目根目录执行
python -m src.main

# 或使用 uvicorn
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/v1/chat/completions` | POST | OpenAI 兼容接口（流式） |
| `/run` | POST | 同步调用 |
| `/stream_run` | POST | SSE 流式调用 |
| `/cancel/{run_id}` | POST | 取消执行 |

### 在 Claude Code 中配置

创建配置文件 `~/.claude/config.json`：

```json
{
  "apiProvider": "custom",
  "apiBaseUrl": "http://localhost:8000/v1",
  "apiKey": "local-dev",
  "defaultModel": "ui-venus-research-agent"
}
```

或使用环境变量：

```bash
export ANTHROPIC_API_KEY="local-dev"
export ANTHROPIC_BASE_URL="http://localhost:8000/v1"
```

### 在 Cursor 中配置

1. 打开设置 (Cmd/Ctrl + ,)
2. 搜索 "OpenAI"
3. 配置：
   - **OpenAI API Key**: `local-dev`
   - **OpenAI Base URL**: `http://localhost:8000/v1`
   - **Model Override**: `ui-venus-research-agent`

### 调用示例

```python
import openai

client = openai.OpenAI(
    api_key="local-dev",
    base_url="http://localhost:8000/v1"
)

response = client.chat.completions.create(
    model="ui-venus-research-agent",
    messages=[
        {"role": "user", "content": "帮我深度调研：UI-Venus-1.5"}
    ],
    stream=True
)

for chunk in response:
    print(chunk.choices[0].delta.content, end="")
```

```bash
# 使用 curl 测试
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ui-venus-research-agent",
    "messages": [{"role": "user", "content": "帮我深度调研：LangGraph"}],
    "stream": true
  }'
```

---

## 方案二：MCP (Model Context Protocol)

MCP 是 Anthropic 推出的标准协议，支持更复杂的工具集成。

### 安装依赖

```bash
pip install mcp
```

### 在 Claude Code 中配置 MCP

创建或编辑 `~/.claude/claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "ui-venus-research": {
      "command": "python",
      "args": ["-m", "src.mcp_server"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

### 在 Cursor 中配置 MCP

Cursor 设置 → Features → Model Context Protocol：

```json
{
  "mcpServers": {
    "ui-venus-research": {
      "command": "python",
      "args": ["-m", "src.mcp_server"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

### MCP 工具列表

启动后，Claude Code / Cursor 可以使用以下工具：

| 工具名称 | 描述 | 参数 |
|----------|------|------|
| `deep_research` | 深度技术调研 | topic, depth, focus_areas |
| `web_search` | 网络搜索 | query, count |
| `crawl_webpage` | 网页爬取 | url, download_images |

### 使用示例

在 Claude Code 中：

```
请使用 deep_research 工具帮我调研 LangGraph 的架构设计
```

---

## 方案三：直接 HTTP API 调用

### 同步调用

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "帮我深度调研：UI-Venus-1.5"}
    ]
  }'
```

### 流式调用 (SSE)

```bash
curl -X POST http://localhost:8000/stream_run \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "帮我深度调研：UI-Venus-1.5"}
    ]
  }'
```

### Python 客户端示例

```python
import requests
import json

class ResearchAgentClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def research(self, topic: str, stream: bool = True):
        """执行调研"""
        endpoint = "/stream_run" if stream else "/run"
        
        response = requests.post(
            f"{self.base_url}{endpoint}",
            json={"messages": [{"role": "user", "content": f"帮我深度调研：{topic}"}]},
            stream=stream
        )
        
        if stream:
            for line in response.iter_lines():
                if line:
                    yield line.decode()
        else:
            return response.json()
    
    def openai_chat(self, message: str, stream: bool = True):
        """OpenAI 兼容接口调用"""
        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            json={
                "model": "ui-venus-research-agent",
                "messages": [{"role": "user", "content": message}],
                "stream": stream
            },
            stream=stream
        )
        
        if stream:
            for line in response.iter_lines():
                if line and line != b"data: [DONE]":
                    yield line.decode()
        else:
            return response.json()

# 使用示例
client = ResearchAgentClient()

# 流式调用
for chunk in client.research("UI-Venus-1.5"):
    print(chunk)

# OpenAI 兼容接口
for chunk in client.openai_chat("帮我调研 LangGraph 架构"):
    print(chunk)
```

---

## 部署到生产环境

### Docker 部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t ui-venus-research-agent .
docker run -p 8000:8000 ui-venus-research-agent
```

### 环境变量配置

```bash
# .env 文件
COZE_WORKSPACE_PATH=/app
COZE_WORKLOAD_IDENTITY_API_KEY=your-api-key
COZE_INTEGRATION_MODEL_BASE_URL=https://api.coze.cn/v1
```

---

## 常见问题

### Q: 为什么 MCP 没有显示在 Claude Code 中？

A: 检查：
1. 配置文件路径是否正确 (`~/.claude/claude_desktop_config.json`)
2. Python 环境是否正确
3. 查看 Claude Code 日志

### Q: 如何添加认证？

A: 在 `src/main.py` 中添加中间件：

```python
from fastapi import Depends, HTTPException, Header

async def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != "your-secret-key":
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

@app.post("/v1/chat/completions", dependencies=[Depends(verify_api_key)])
async def openai_chat_completions(request: Request):
    ...
```

### Q: 如何限制并发？

A: 使用信号量：

```python
from asyncio import Semaphore

MAX_CONCURRENT = 10
semaphore = Semaphore(MAX_CONCURRENT)

@app.post("/run")
async def http_run(request: Request):
    async with semaphore:
        # 处理请求
        ...
```
