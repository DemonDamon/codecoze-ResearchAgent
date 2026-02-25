"""MCP Server 模板"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, Resource

# 设置 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.agent import build_agent
from coze_coding_utils.runtime_ctx.context import new_context

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 MCP 服务实例
server = Server("your-agent-name")

# 全局 Agent 实例
_agent_instance = None


def get_agent():
    """获取或创建 Agent 实例"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = build_agent()
    return _agent_instance


def get_workspace_dir(name: Optional[str] = None) -> str:
    """获取工作目录路径
    
    Args:
        name: 用户指定的目录名（可选）
    
    Returns:
        工作目录路径
    """
    if name:
        return os.path.join("/tmp", name)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"/tmp/workspace_{timestamp}"


@server.list_tools()
async def list_tools() -> List[Tool]:
    """列出可用的 MCP 工具"""
    return [
        Tool(
            name="your_main_tool",
            description="""
执行主要功能的描述。

功能包括：
- 功能1
- 功能2
- 功能3

适用场景：xxx
            """.strip(),
            inputSchema={
                "type": "object",
                "properties": {
                    "input_param": {
                        "type": "string",
                        "description": "输入参数说明"
                    },
                    "workspace_name": {
                        "type": "string",
                        "description": "工作目录名称（可选）。如 'my_workspace'，将保存到 /tmp/my_workspace。不指定则自动生成时间戳目录。"
                    },
                    "option": {
                        "type": "string",
                        "enum": ["option1", "option2"],
                        "default": "option1",
                        "description": "选项说明"
                    }
                },
                "required": ["input_param"]
            }
        ),
        Tool(
            name="simple_tool",
            description="简单工具描述",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "查询内容"
                    }
                },
                "required": ["query"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """处理工具调用"""
    try:
        if name == "your_main_tool":
            return await _handle_main_tool(arguments)
        elif name == "simple_tool":
            return await _handle_simple_tool(arguments)
        else:
            return [TextContent(type="text", text=f"未知工具: {name}")]
    except Exception as e:
        logger.error(f"工具 {name} 执行错误: {e}", exc_info=True)
        return [TextContent(type="text", text=f"错误: {str(e)}")]


async def _handle_main_tool(arguments: Dict[str, Any]) -> List[TextContent]:
    """处理主要工具调用"""
    input_param = arguments.get("input_param")
    workspace_name = arguments.get("workspace_name", "")
    option = arguments.get("option", "option1")
    
    # 构建提示词
    prompt = f"执行任务: {input_param}"
    if workspace_name:
        prompt += f"，保存在 {workspace_name} 下面"
    
    logger.info(f"执行任务: {input_param}, 工作目录: {workspace_name}")
    
    # 创建上下文并调用 Agent
    ctx = new_context(method="mcp_main_tool")
    agent = get_agent()
    
    config = {
        "configurable": {"thread_id": ctx.run_id}
    }
    
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": prompt}]},
        config=config,
        context=ctx
    )
    
    # 提取结果
    if result and "messages" in result:
        last_message = result["messages"][-1]
        response_text = last_message.content if hasattr(last_message, 'content') else str(last_message)
    else:
        response_text = "执行完成，但无返回结果"
    
    return [TextContent(type="text", text=response_text)]


async def _handle_simple_tool(arguments: Dict[str, Any]) -> List[TextContent]:
    """处理简单工具调用"""
    query = arguments.get("query")
    
    # 直接处理逻辑
    result = f"处理结果: {query}"
    
    return [TextContent(type="text", text=result)]


async def run_server():
    """运行 MCP 服务（stdio 模式）"""
    logger.info("启动 MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent MCP Server")
    parser.add_argument("--http", action="store_true", help="HTTP 模式（测试用）")
    parser.add_argument("--port", type=int, default=8001, help="HTTP 端口")
    args = parser.parse_args()
    
    if args.http:
        # HTTP 模式用于测试
        import uvicorn
        from starlette.applications import Starlette
        from mcp.server.sse import SseServerTransport
        
        app = Starlette()
        sse = SseServerTransport("/sse")
        app.add_route("/sse", sse.handle_sse)
        
        logger.info(f"HTTP 模式启动，端口: {args.port}")
        uvicorn.run(app, host="0.0.0.0", port=args.port)
    else:
        # Stdio 模式用于 Cursor/Claude Code
        asyncio.run(run_server())


if __name__ == "__main__":
    main()
