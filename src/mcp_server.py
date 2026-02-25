"""
MCP (Model Context Protocol) Server for Research Agent

This server exposes the research agent as an MCP tool, allowing integration with
Claude Code, Cursor, and other MCP-compatible AI tools.

Usage:
    # Stdio mode (for Cursor/Claude Code)
    python -m src.mcp_server
    
    # HTTP mode (for testing)
    python -m src.mcp_server --http --port 8001

Configuration for Cursor:
    Add to ~/.cursor/mcp.json or project's .cursor/mcp.json:
    {
        "mcpServers": {
            "research-agent": {
                "command": "python",
                "args": ["-m", "src.mcp_server"],
                "cwd": "/path/to/this/project"
            }
        }
    }
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, Resource

# Setup path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent import build_agent
from coze_coding_utils.runtime_ctx.context import new_context

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create MCP server instance
server = Server("research-agent")

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
- GitHub 仓库分析
- 代码分析
- 架构图/流程图提示词生成
- Markdown 博客生成
- 工作目录打包

适用场景：技术研究、产品分析、竞品调研、学习笔记等

返回：工作目录路径、博客文件路径、相关文件列表
            """.strip(),
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "要调研的主题，如 'TuriX-CUA'、'LangGraph架构'、'https://github.com/user/repo' 等"
                    },
                    "workspace_name": {
                        "type": "string",
                        "description": "工作目录名称（可选）。如 'turix_analysis'，将保存到 /tmp/turix_analysis。不指定则自动生成时间戳目录。"
                    },
                    "depth": {
                        "type": "string",
                        "enum": ["quick", "normal", "deep"],
                        "default": "normal",
                        "description": "调研深度：quick(快速,5个页面)、normal(标准,20个页面)、deep(深度,50个页面)"
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
            description="执行网络搜索，获取实时信息。支持 Bocha AI 搜索或 Coze 平台搜索。",
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
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="crawl_webpage",
            description="爬取指定网页内容，提取文本和图片，保存到本地。",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "要爬取的网页URL"
                    },
                    "workspace_name": {
                        "type": "string",
                        "description": "工作目录名称（可选），保存到 /tmp/{workspace_name}/sources/web/"
                    },
                    "download_images": {
                        "type": "boolean",
                        "description": "是否下载图片",
                        "default": True
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="crawl_github",
            description="爬取 GitHub 仓库的 README、文档、Wiki 等内容。",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_url": {
                        "type": "string",
                        "description": "GitHub 仓库 URL，如 'https://github.com/user/repo'"
                    },
                    "workspace_name": {
                        "type": "string",
                        "description": "工作目录名称（可选）"
                    }
                },
                "required": ["repo_url"]
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
        elif name == "crawl_github":
            return await _handle_crawl_github(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def _handle_deep_research(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle deep research tool call."""
    topic = arguments.get("topic")
    workspace_name = arguments.get("workspace_name", "")
    depth = arguments.get("depth", "normal")
    focus_areas = arguments.get("focus_areas", [])
    
    # Build the prompt
    prompt_parts = [f"帮我深度调研：{topic}"]
    
    # Add workspace name if specified
    if workspace_name:
        prompt_parts.append(f"保存在 {workspace_name} 下面")
    
    # Add depth instruction
    if depth == "quick":
        prompt_parts.insert(0, "帮我快速调研：")
    elif depth == "deep":
        prompt_parts.insert(0, "帮我进行深度、全面的技术调研：")
    
    if focus_areas:
        prompt_parts.append(f"\n\n重点关注领域：{', '.join(focus_areas)}")
    
    prompt = " ".join(prompt_parts)
    
    logger.info(f"Starting deep research: {topic}, workspace: {workspace_name}, depth: {depth}")
    
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
    query = arguments.get("query")
    count = arguments.get("count", 10)
    
    logger.info(f"Web search: {query}")
    
    # Try Bocha search first
    bocha_api_key = os.getenv("BOCHA_API_KEY")
    
    if bocha_api_key:
        import requests
        try:
            response = requests.post(
                "https://api.bocha.io/v1/search",
                headers={
                    "Authorization": f"Bearer {bocha_api_key}",
                    "Content-Type": "application/json"
                },
                json={"query": query, "count": count, "summary": True},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            web_pages = data.get("web_pages", [])
            summary = data.get("summary", "")
            
            results = [f"# 搜索结果: {query}\n"]
            if summary:
                results.append(f"## AI 摘要\n{summary}\n")
            results.append(f"## 搜索结果 ({len(web_pages)} 条)\n")
            
            for i, page in enumerate(web_pages, 1):
                title = page.get("title", "无标题")
                url = page.get("url") or page.get("link", "")
                snippet = page.get("snippet") or page.get("description", "")
                results.append(f"{i}. **{title}**\n   - URL: {url}\n   - 摘要: {snippet}\n")
            
            return [TextContent(type="text", text="\n".join(results))]
        except Exception as e:
            logger.error(f"Bocha search error: {e}")
    
    # Fallback to Coze platform search
    try:
        from coze_coding_dev_sdk import SearchClient
        ctx = new_context(method="mcp_web_search")
        search_client = SearchClient(ctx=ctx)
        
        response = search_client.web_search(
            query=query,
            count=count,
            need_summary=True
        )
        
        results = [f"# 搜索结果: {query}\n"]
        if response.summary:
            results.append(f"## AI 摘要\n{response.summary}\n")
        
        if response.web_items:
            results.append(f"## 搜索结果 ({len(response.web_items)} 条)\n")
            for i, item in enumerate(response.web_items, 1):
                results.append(f"{i}. **{item.title}**\n   - URL: {item.url}\n   - 摘要: {item.snippet}\n")
        else:
            results.append("未找到相关结果")
        
        return [TextContent(type="text", text="\n".join(results))]
    except Exception as e:
        logger.error(f"Coze search error: {e}")
        return [TextContent(type="text", text=f"搜索失败: {str(e)}\n\n请配置 BOCHA_API_KEY 环境变量以启用搜索功能。")]


async def _handle_crawl_webpage(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle webpage crawling tool call."""
    from tools.web_crawler import _crawl_webpage_internal
    
    url = arguments.get("url")
    workspace_name = arguments.get("workspace_name", f"crawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    download_images = arguments.get("download_images", True)
    
    logger.info(f"Crawling webpage: {url}")
    
    # Use /tmp for crawled content
    workspace_dir = f"/tmp/{workspace_name}"
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


async def _handle_crawl_github(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle GitHub repository crawling tool call."""
    from tools.web_crawler import extensive_search_and_crawl
    
    repo_url = arguments.get("repo_url")
    workspace_name = arguments.get("workspace_name", f"github_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    logger.info(f"Crawling GitHub: {repo_url}")
    
    # Call the extensive_search_and_crawl with the GitHub URL
    result = extensive_search_and_crawl.func(
        topic=repo_url,
        num_queries=5,
        results_per_query=5,
        workspace_dir=f"/tmp/{workspace_name}"
    )
    
    return [TextContent(type="text", text=result)]


async def run_server():
    """Run the MCP server using stdio transport."""
    logger.info("Starting Research Agent MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Research Agent MCP Server")
    parser.add_argument("--http", action="store_true", help="Run in HTTP mode (for testing)")
    parser.add_argument("--port", type=int, default=8001, help="HTTP port (default: 8001)")
    args = parser.parse_args()
    
    if args.http:
        # HTTP mode for testing
        import uvicorn
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Route
        
        @asynccontextmanager
        async def lifespan(app: Starlette):
            """Server lifespan handler."""
            yield
        
        app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=SseServerTransport("/sse").handle_sse),
            ],
            lifespan=lifespan
        )
        
        logger.info(f"Starting HTTP server on port {args.port}")
        uvicorn.run(app, host="0.0.0.0", port=args.port)
    else:
        # Stdio mode for Cursor/Claude Code
        asyncio.run(run_server())


if __name__ == "__main__":
    main()
