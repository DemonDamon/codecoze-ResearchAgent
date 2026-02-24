"""
MCP (Model Context Protocol) Server for UI-Venus Research Agent

This server exposes the research agent as an MCP tool, allowing integration with
Claude Code, Cursor, and other MCP-compatible AI tools.

Usage:
    python -m src.mcp_server
    
Or with uvicorn:
    uvicorn src.mcp_server:app --host 0.0.0.0 --port 8001
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, Resource

from agents.agent import build_agent
from coze_coding_utils.runtime_ctx.context import new_context

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP server instance
server = Server("ui-venus-research-agent")

# Global agent instance
_agent_instance = None


def get_agent():
    """Get or create the agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = build_agent()
    return _agent_instance


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="deep_research",
            description="""
            对指定主题进行深度技术调研，生成专业博客文章。
            
            功能包括：
            - 多维度网络搜索（20+查询角度）
            - 网页内容爬取（含图片下载）
            - 代码分析
            - 架构图/流程图提示词生成
            - Markdown博客生成
            - 工作目录打包下载
            
            适用场景：技术研究、产品分析、竞品调研、学习笔记等
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "要调研的主题，如 'UI-Venus-1.5'、'LangGraph架构' 等"
                    },
                    "depth": {
                        "type": "string",
                        "enum": ["quick", "normal", "deep"],
                        "default": "normal",
                        "description": "调研深度：quick(快速)、normal(标准)、deep(深度)"
                    },
                    "focus_areas": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "关注的领域，如 ['架构', '应用场景', '性能']",
                        "default": []
                    }
                },
                "required": ["topic"]
            }
        ),
        Tool(
            name="web_search",
            description="执行网络搜索，获取实时信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询"
                    },
                    "count": {
                        "type": "number",
                        "description": "返回结果数量",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="crawl_webpage",
            description="爬取指定网页内容，提取文本和图片",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "要爬取的网页URL"
                    },
                    "download_images": {
                        "type": "boolean",
                        "description": "是否下载图片",
                        "default": True
                    }
                },
                "required": ["url"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    try:
        if name == "deep_research":
            return await _handle_deep_research(arguments)
        elif name == "web_search":
            return await _handle_web_search(arguments)
        elif name == "crawl_webpage":
            return await _handle_crawl_webpage(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def _handle_deep_research(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle deep research tool call."""
    topic = arguments.get("topic")
    depth = arguments.get("depth", "normal")
    focus_areas = arguments.get("focus_areas", [])
    
    # Build the prompt
    prompt = f"帮我深度调研：{topic}"
    if depth == "quick":
        prompt = f"帮我快速调研：{topic}"
    elif depth == "deep":
        prompt = f"帮我进行深度、全面的技术调研：{topic}"
    
    if focus_areas:
        prompt += f"\n\n重点关注领域：{', '.join(focus_areas)}"
    
    # Create context and invoke agent
    ctx = new_context(method="mcp_deep_research")
    agent = get_agent()
    
    # Prepare input
    config = {
        "configurable": {"thread_id": ctx.run_id}
    }
    
    # Run agent
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": prompt}]},
        config=config,
        context=ctx
    )
    
    # Extract final response
    if result and "messages" in result:
        last_message = result["messages"][-1]
        response_text = last_message.content if hasattr(last_message, 'content') else str(last_message)
    else:
        response_text = "调研完成，但未能获取结果"
    
    return [TextContent(type="text", text=response_text)]


async def _handle_web_search(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle web search tool call."""
    from coze_coding_dev_sdk import SearchClient
    
    query = arguments.get("query")
    count = arguments.get("count", 5)
    
    ctx = new_context(method="mcp_web_search")
    search_client = SearchClient(ctx=ctx)
    
    response = search_client.web_search(
        query=query,
        count=count,
        need_summary=True
    )
    
    results = []
    if response.web_items:
        for i, item in enumerate(response.web_items, 1):
            results.append(f"{i}. **{item.title}**\n   URL: {item.url}\n   摘要: {item.snippet}\n")
    
    if not results:
        return [TextContent(type="text", text="未找到相关结果")]
    
    return [TextContent(type="text", text="\n".join(results))]


async def _handle_crawl_webpage(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle webpage crawling tool call."""
    from tools.web_crawler import _crawl_webpage_internal
    
    url = arguments.get("url")
    download_images = arguments.get("download_images", True)
    
    # Use /tmp for crawled content
    workspace_dir = "/tmp/mcp_crawl"
    result = _crawl_webpage_internal(url, workspace_dir)
    
    if result["success"]:
        response = f"""# 爬取成功

**URL**: {url}
**标题**: {result.get('title', 'N/A')}
**保存位置**: {result.get('file_path', 'N/A')}
**图片数量**: {result.get('images', 0)}
**内容长度**: {result.get('content_length', 0)} 字符

## 内容预览
{result.get('content', '')[:2000]}...
"""
    else:
        response = f"爬取失败: {result.get('error', 'Unknown error')}"
    
    return [TextContent(type="text", text=response)]


async def run_server():
    """Run the MCP server using stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def main():
    """Main entry point."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
