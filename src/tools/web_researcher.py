"""Web research tool for research agent.

Performs web searches and saves results to the workspace.
Supports:
- Coze platform (SearchClient)
- Bocha AI search (local mode)
- Fallback mode (no search)
"""

import os
import json
import requests
from typing import List, Optional, Dict, Any
from langchain.tools import tool
from langchain.tools import ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context


def _is_coze_platform() -> bool:
    """检测是否运行在 Coze 平台"""
    return bool(os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY"))


def _has_bocha_api() -> bool:
    """检测是否配置了 Bocha API"""
    return bool(os.getenv("BOCHA_API_KEY"))


class BochaSearchClient:
    """Bocha AI 搜索客户端（官方域名 api.bochaai.com）"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.bochaai.com/v1"
    
    def search(self, query: str, count: int = 10) -> Dict[str, Any]:
        """执行搜索
        
        Args:
            query: 搜索查询
            count: 返回结果数量
        
        Returns:
            搜索结果字典
        """
        import logging
        logger = logging.getLogger(__name__)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": query,
            "count": count,
            "summary": True  # 请求 AI 摘要
        }
        
        try:
            logger.info(f"Bocha API 请求: query={query}, count={count}")
            response = requests.post(
                f"{self.base_url}/web-search",
                headers=headers,
                json=payload,
                timeout=30
            )
            logger.info(f"Bocha API 响应状态: {response.status_code}")
            response.raise_for_status()
            result = response.json()
            # 兼容新旧 API 格式：api.bochaai.com 返回 data.webPages.value
            if "data" in result and "webPages" in result["data"]:
                raw_pages = result["data"]["webPages"].get("value", [])
                web_pages = [
                    {
                        "title": p.get("name", "无标题"),
                        "url": p.get("url", ""),
                        "snippet": p.get("summary", ""),
                        "description": p.get("summary", ""),
                    }
                    for p in raw_pages
                ]
                result = {"web_pages": web_pages, "summary": result.get("data", {}).get("summary", "")}
            web_pages = result.get("web_pages", [])
            logger.info(f"Bocha API 返回结果数: {len(web_pages)}")
            return result
        except requests.exceptions.HTTPError as e:
            logger.error(f"Bocha API HTTP 错误: {e}")
            return {"error": f"HTTP错误: {e}", "web_pages": []}
        except requests.exceptions.Timeout:
            logger.error("Bocha API 超时")
            return {"error": "请求超时", "web_pages": []}
        except Exception as e:
            logger.error(f"Bocha API 异常: {e}")
            return {"error": str(e), "web_pages": []}
    
    def web_search(self, query: str, count: int = 10) -> Dict[str, Any]:
        """网页搜索（兼容接口）"""
        return self.search(query, count)


def _bocha_search(query: str, count: int = 10) -> str:
    """使用 Bocha AI 执行搜索"""
    api_key = os.getenv("BOCHA_API_KEY")
    if not api_key:
        return _local_search_fallback(query, count)
    
    client = BochaSearchClient(api_key)
    result = client.search(query, count)
    
    if "error" in result:
        return f"""# 搜索失败

**查询**: {query}

❌ 错误: {result['error']}

请检查：
1. BOCHA_API_KEY 是否正确
2. API 配额是否充足
3. 网络连接是否正常
"""
    
    # 解析搜索结果
    web_pages = result.get("web_pages", [])
    summary = result.get("summary", "")
    
    # 如果没有结果，尝试 GitHub 搜索
    if not web_pages:
        github_result = client.search(f"{query} site:github.com", count)
        github_pages = github_result.get("web_pages", [])
        if github_pages:
            web_pages = github_pages
            summary = f"（通过 GitHub 搜索找到）{github_result.get('summary', '')}"
    
    markdown_content = f"""# 网络搜索结果

## 搜索信息
- 查询: {query}
- 结果数量: {len(web_pages)}
- 搜索服务: Bocha AI

---

## AI 摘要
{summary if summary else "无摘要"}

---

## 搜索结果

"""
    
    for i, page in enumerate(web_pages, 1):
        title = page.get("title", "无标题")
        url = page.get("url", page.get("link", ""))
        snippet = page.get("snippet", page.get("description", ""))
        site_name = page.get("site_name", "")
        
        markdown_content += f"### {i}. {title}\n\n"
        markdown_content += f"- **URL**: {url}\n"
        if site_name:
            markdown_content += f"- **来源**: {site_name}\n"
        if snippet:
            markdown_content += f"- **摘要**: {snippet}\n"
        markdown_content += "\n---\n\n"
    
    if not web_pages:
        markdown_content += """未找到搜索结果。

## 建议

1. **检查项目名称**：确认名称拼写正确
2. **提供 GitHub URL**：如果你知道项目的 GitHub 地址，请直接提供
3. **提供文档链接**：如果你有相关文档链接，请提供

示例：
```
请分析 https://github.com/TurixAI/TuriX-CUA
```
"""
    
    return markdown_content


def _local_search_fallback(query: str, count: int = 10) -> str:
    """本地模式下的搜索降级方案"""
    return f"""# 搜索服务不可用

**查询**: {query}

⚠️ 本地运行模式下，网络搜索服务不可用。

## 替代方案

1. **配置 Bocha AI 搜索**: 在 .env 文件中设置 `BOCHA_API_KEY=sk-xxxx`
2. **手动搜索**: 请手动在浏览器中搜索相关内容
3. **使用爬虫工具**: 如果你已知相关网页 URL，可以使用 `crawl_webpage` 工具爬取内容
4. **提供 URL 列表**: 提供已知的相关网页 URL，使用 `batch_crawl_webpages` 批量爬取

## 示例用法

```
请爬取以下网页：
- https://example.com/article1
- https://example.com/article2
```

## 启用搜索功能

如需使用搜索功能，请：
1. 获取 Bocha AI API Key: https://bocha.io
2. 在 .env 文件中配置: `BOCHA_API_KEY=sk-xxxx`

或部署到 Coze 平台使用内置搜索服务。
"""


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
    # 优先使用 Bocha AI
    if _has_bocha_api():
        markdown_content = _bocha_search(query, count)
    # Coze 平台搜索
    elif _is_coze_platform():
        ctx = runtime.context if runtime else new_context(method="search_web")
        from coze_coding_dev_sdk import SearchClient
        search_client = SearchClient(ctx=ctx)
        
        response = search_client.web_search_with_summary(
            query=query,
            count=count
        )
        
        markdown_content = f"""# 网络搜索结果

## 搜索信息
- 查询: {query}
- 结果数量: {len(response.web_items) if response.web_items else 0}
- 搜索服务: Coze

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
    else:
        # 降级模式
        markdown_content = _local_search_fallback(query, count)
    
    # Save to file
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    web_dir = os.path.join(workspace_dir, "sources", "web")
    os.makedirs(web_dir, exist_ok=True)
    
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
    # 检查搜索服务可用性
    if not _has_bocha_api() and not _is_coze_platform():
        queries_str = "\n".join([f"- {q}" for q in queries])
        return f"""# 多查询搜索服务不可用

**查询列表**:
{queries_str}

⚠️ 本地运行模式下，网络搜索服务不可用。

## 启用搜索功能

在 .env 文件中配置 Bocha AI:
```
BOCHA_API_KEY=sk-xxxx
```

获取 API Key: https://bocha.io
"""
    
    results = []
    results.append(f"# 多查询搜索结果\n")
    results.append(f"查询数量: {len(queries)}\n")
    results.append(f"查询列表:\n")
    for i, query in enumerate(queries, 1):
        results.append(f"{i}. {query}")
    results.append("\n---\n\n")
    
    all_items = []
    
    for query in queries:
        if _has_bocha_api():
            # 使用 Bocha AI
            client = BochaSearchClient(os.getenv("BOCHA_API_KEY"))
            response = client.search(query, count=10)
            
            if "web_pages" in response:
                for item in response["web_pages"]:
                    all_items.append({
                        'query': query,
                        'title': item.get('title', ''),
                        'url': item.get('url', item.get('link', '')),
                        'snippet': item.get('snippet', item.get('description', '')),
                        'site_name': item.get('site_name', '')
                    })
        elif _is_coze_platform():
            ctx = runtime.context if runtime else new_context(method="search_multiple_queries")
            from coze_coding_dev_sdk import SearchClient
            search_client = SearchClient(ctx=ctx)
            response = search_client.web_search(query=query, count=10)
            
            if response.web_items:
                for item in response.web_items:
                    all_items.append({
                        'query': query,
                        'title': item.title,
                        'url': item.url,
                        'snippet': item.snippet,
                        'site_name': item.site_name
                    })
    
    # Deduplicate by URL
    seen_urls = set()
    unique_items = []
    for item_data in all_items:
        url = item_data['url']
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_items.append(item_data)
    
    results.append(f"去重后结果数量: {len(unique_items)}\n\n")
    
    for i, item_data in enumerate(unique_items[:20], 1):
        title = item_data['title']
        url = item_data['url']
        query = item_data['query']
        snippet = item_data['snippet']
        site_name = item_data['site_name']
        
        results.append(f"### {i}. {title}\n\n")
        results.append(f"- **URL**: {url}\n")
        if site_name:
            results.append(f"- **来源**: {site_name}\n")
        results.append(f"- **查询来源**: {query}\n")
        if snippet:
            results.append(f"- **摘要**: {snippet}\n")
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
    query = f"{technology} best practices 最佳实践"
    markdown_content = ""
    
    if _has_bocha_api():
        markdown_content = _bocha_search(query, 10)
    elif _is_coze_platform():
        ctx = runtime.context if runtime else new_context(method="search_best_practices")
        from coze_coding_dev_sdk import SearchClient
        search_client = SearchClient(ctx=ctx)
        response = search_client.web_search(query=query, count=10)
        
        markdown_content = f"""# {technology} 最佳实践搜索结果

## 搜索查询
{query}

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
        else:
            markdown_content += "未找到搜索结果。\n"
    else:
        markdown_content = _local_search_fallback(query, 10)
    
    # Save to file
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    web_dir = os.path.join(workspace_dir, "sources", "web")
    os.makedirs(web_dir, exist_ok=True)
    
    filename = f"best_practices_{technology}.md"
    full_path = os.path.join(web_dir, filename)
    
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    return f"Best practices search results saved to: {full_path}\n\n{markdown_content}"


@tool
def search_architecture_info(
    system_name: str,
    workspace_dir: str = "/tmp/research_workspace",
    runtime: ToolRuntime = None
) -> str:
    """Search for architecture information of a system.
    
    Args:
        system_name: Name of the system (e.g., "Kubernetes", "React", "LangChain").
        workspace_dir: The workspace root directory.
    
    Returns:
        Architecture information search results.
    """
    queries = [
        f"{system_name} architecture",
        f"{system_name} 架构设计",
        f"{system_name} 系统设计",
        f"{system_name} 源码分析"
    ]
    
    all_items = []
    
    for query in queries:
        if _has_bocha_api():
            client = BochaSearchClient(os.getenv("BOCHA_API_KEY"))
            response = client.search(query, count=5)
            
            if "web_pages" in response:
                for item in response["web_pages"]:
                    all_items.append({
                        'query': query,
                        'title': item.get('title', ''),
                        'url': item.get('url', item.get('link', '')),
                        'snippet': item.get('snippet', item.get('description', '')),
                        'site_name': item.get('site_name', '')
                    })
        elif _is_coze_platform():
            ctx = runtime.context if runtime else new_context(method="search_architecture_info")
            from coze_coding_dev_sdk import SearchClient
            search_client = SearchClient(ctx=ctx)
            response = search_client.web_search(query=query, count=5)
            
            if response.web_items:
                for item in response.web_items:
                    all_items.append({
                        'query': query,
                        'title': item.title,
                        'url': item.url,
                        'snippet': item.snippet,
                        'site_name': item.site_name
                    })
    
    if not all_items and not _has_bocha_api() and not _is_coze_platform():
        return _local_search_fallback(f"{system_name} 架构设计", 10)
    
    # Deduplicate by URL
    seen_urls = set()
    unique_items = []
    for item_data in all_items:
        url = item_data['url']
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_items.append(item_data)
    
    # Build markdown content
    markdown_content = f"""# {system_name} 架构信息搜索结果

## 搜索查询
"""
    for q in queries:
        markdown_content += f"- {q}\n"
    
    markdown_content += f"\n**结果数量**: {len(unique_items)}\n\n---\n\n## 搜索结果\n\n"
    
    for i, item_data in enumerate(unique_items[:15], 1):
        title = item_data['title']
        url = item_data['url']
        query = item_data['query']
        snippet = item_data['snippet']
        site_name = item_data['site_name']
        
        markdown_content += f"### {i}. {title}\n\n"
        markdown_content += f"- **URL**: {url}\n"
        if site_name:
            markdown_content += f"- **来源**: {site_name}\n"
        markdown_content += f"- **查询来源**: {query}\n"
        if snippet:
            markdown_content += f"- **摘要**: {snippet}\n"
        markdown_content += "\n---\n\n"
    
    # Save to file
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    web_dir = os.path.join(workspace_dir, "sources", "web")
    os.makedirs(web_dir, exist_ok=True)
    
    filename = f"architecture_{system_name}.md"
    full_path = os.path.join(web_dir, filename)
    
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    return f"Architecture info search results saved to: {full_path}\n\n{markdown_content}"
