"""Web research tool for research agent.

Performs web searches and saves results to the workspace.
"""

import os
from typing import List, Optional
from langchain.tools import tool
from langchain.tools import ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context
from coze_coding_dev_sdk import SearchClient


@tool
def search_web(
    query: str,
    count: int = 10,
    workspace_dir: str = "/tmp/research_workspace",
    runtime: ToolRuntime = None
) -> str:
    """Search the web for information and save results.
    
    Args:
        query: Search query.
        count: Number of results to return (default: 10).
        workspace_dir: The workspace root directory.
    
    Returns:
        Search results in markdown format.
    """
    ctx = runtime.context if runtime else new_context(method="search_web")
    
    search_client = SearchClient(ctx=ctx)
    
    response = search_client.web_search_with_summary(
        query=query,
        count=count
    )
    
    # Build markdown content
    markdown_content = f"""# 网络搜索结果

## 搜索信息
- 查询: {query}
- 结果数量: {len(response.web_items) if response.web_items else 0}
- 搜索时间: [自动记录]

---

## AI 摘要
{response.summary if response.summary else "无摘要"}

---

## 搜索结果

"""
    
    if response.web_items:
        for i, item in enumerate(response.web_items, 1):
            markdown_content += f"### {i}. {item.title}\n\n"
            markdown_content += f"- **URL**: {item.url}\n"
            markdown_content += f"- **来源**: {item.site_name}\n"
            
            if item.snippet:
                markdown_content += f"- **摘要**: {item.snippet}\n"
            
            if item.auth_info_des:
                markdown_content += f"- **权威性**: {item.auth_info_des}\n"
            
            if item.publish_time:
                markdown_content += f"- **发布时间**: {item.publish_time}\n"
            
            markdown_content += "\n---\n\n"
    else:
        markdown_content += "未找到搜索结果。\n"
    
    # Save to file
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    web_dir = os.path.join(workspace_dir, "sources", "web")
    os.makedirs(web_dir, exist_ok=True)
    
    # Generate filename from query
    safe_query = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in query[:50])
    filename = f"search_{safe_query}.md"
    full_path = os.path.join(web_dir, filename)
    
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    return f"Search results saved to: {full_path}\n\n{markdown_content}"


@tool
def search_multiple_queries(
    queries: List[str],
    workspace_dir: str = "/tmp/research_workspace",
    runtime: ToolRuntime = None
) -> str:
    """Search multiple queries and aggregate results.
    
    Args:
        queries: List of search queries.
        workspace_dir: The workspace root directory.
    
    Returns:
        Aggregated search results.
    """
    ctx = runtime.context if runtime else new_context(method="search_multiple_queries")
    
    results = []
    results.append(f"# 多查询搜索结果\n")
    results.append(f"查询数量: {len(queries)}\n")
    results.append(f"查询列表:\n")
    for i, query in enumerate(queries, 1):
        results.append(f"{i}. {query}")
    results.append("\n---\n\n")
    
    all_items = []
    
    for query in queries:
        search_client = SearchClient(ctx=ctx)
        response = search_client.web_search(query=query, count=10)
        
        if response.web_items:
            for item in response.web_items:
                all_items.append({
                    'query': query,
                    'item': item
                })
    
    # Deduplicate by URL
    seen_urls = set()
    unique_items = []
    for item_data in all_items:
        url = item_data['item'].url
        if url not in seen_urls:
            seen_urls.add(url)
            unique_items.append(item_data)
    
    results.append(f"去重后结果数量: {len(unique_items)}\n\n")
    
    # Sort by relevance (using rank_score if available)
    unique_items.sort(key=lambda x: x['item'].rank_score if hasattr(x['item'], 'rank_score') else 0, reverse=True)
    
    for i, item_data in enumerate(unique_items[:20], 1):  # Top 20
        item = item_data['item']
        query = item_data['query']
        
        results.append(f"### {i}. {item.title}\n\n")
        results.append(f"- **URL**: {item.url}\n")
        results.append(f"- **来源**: {item.site_name}\n")
        results.append(f"- **查询来源**: {query}\n")
        
        if item.snippet:
            results.append(f"- **摘要**: {item.snippet}\n")
        
        if item.auth_info_des:
            results.append(f"- **权威性**: {item.auth_info_des}\n")
        
        results.append("\n---\n\n")
    
    # Save to file
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    web_dir = os.path.join(workspace_dir, "sources", "web")
    os.makedirs(web_dir, exist_ok=True)
    
    filename = "multi_search_results.md"
    full_path = os.path.join(web_dir, filename)
    
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(''.join(results))
    
    return f"Multi-query search results saved to: {full_path}\n\n{''.join(results)}"


@tool
def search_best_practices(
    technology: str,
    workspace_dir: str = "/tmp/research_workspace",
    runtime: ToolRuntime = None
) -> str:
    """Search for best practices of a specific technology.
    
    Args:
        technology: Name of the technology (e.g., "Python", "React", "Kubernetes").
        workspace_dir: The workspace root directory.
    
    Returns:
        Best practices search results.
    """
    ctx = runtime.context if runtime else new_context(method="search_best_practices")
    
    query = f"{technology} best practices 最佳实践"
    
    search_client = SearchClient(ctx=ctx)
    
    response = search_client.web_search_with_summary(
        query=query,
        count=10
    )
    
    markdown_content = f"""# {technology} 最佳实践

## 搜索信息
- 查询: {query}
- 结果数量: {len(response.web_items) if response.web_items else 0}

---

## AI 摘要
{response.summary if response.summary else "无摘要"}

---

## 搜索结果

"""
    
    if response.web_items:
        for i, item in enumerate(response.web_items, 1):
            markdown_content += f"### {i}. {item.title}\n\n"
            markdown_content += f"- **URL**: {item.url}\n"
            markdown_content += f"- **来源**: {item.site_name}\n"
            
            if item.snippet:
                markdown_content += f"- **摘要**: {item.snippet}\n"
            
            markdown_content += "\n---\n\n"
    
    # Save to file
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    web_dir = os.path.join(workspace_dir, "sources", "web")
    os.makedirs(web_dir, exist_ok=True)
    
    safe_tech = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in technology[:50])
    filename = f"best_practices_{safe_tech}.md"
    full_path = os.path.join(web_dir, filename)
    
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    return f"Best practices saved to: {full_path}\n\n{markdown_content}"


@tool
def search_architecture_info(
    technology: str,
    workspace_dir: str = "/tmp/research_workspace",
    runtime: ToolRuntime = None
) -> str:
    """Search for architecture and design information of a technology.
    
    Args:
        technology: Name of the technology.
        workspace_dir: The workspace root directory.
    
    Returns:
        Architecture search results.
    """
    ctx = runtime.context if runtime else new_context(method="search_architecture_info")
    
    query = f"{technology} architecture 架构设计 原理"
    
    search_client = SearchClient(ctx=ctx)
    
    response = search_client.web_search_with_summary(
        query=query,
        count=10
    )
    
    markdown_content = f"""# {technology} 架构信息

## 搜索信息
- 查询: {query}
- 结果数量: {len(response.web_items) if response.web_items else 0}

---

## AI 摘要
{response.summary if response.summary else "无摘要"}

---

## 搜索结果

"""
    
    if response.web_items:
        for i, item in enumerate(response.web_items, 1):
            markdown_content += f"### {i}. {item.title}\n\n"
            markdown_content += f"- **URL**: {item.url}\n"
            markdown_content += f"- **来源**: {item.site_name}\n"
            
            if item.snippet:
                markdown_content += f"- **摘要**: {item.snippet}\n"
            
            markdown_content += "\n---\n\n"
    
    # Save to file
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    web_dir = os.path.join(workspace_dir, "sources", "web")
    os.makedirs(web_dir, exist_ok=True)
    
    safe_tech = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in technology[:50])
    filename = f"architecture_{safe_tech}.md"
    full_path = os.path.join(web_dir, filename)
    
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    return f"Architecture info saved to: {full_path}\n\n{markdown_content}"
