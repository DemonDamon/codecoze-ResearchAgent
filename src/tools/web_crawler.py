"""Web crawler tool for research agent.

Crawls web pages, extracts content, downloads images, and saves to workspace.
"""

import os
import re
import json
from typing import List, Optional, Dict
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from langchain.tools import tool
from langchain.tools import ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context


def _crawl_webpage_internal(url: str, workspace_dir: str) -> Dict:
    """Internal function to crawl a single webpage.
    
    Args:
        url: The URL to crawl.
        workspace_dir: The workspace root directory.
    
    Returns:
        Dictionary with crawl results.
    """
    web_dir = os.path.join(workspace_dir, "sources", "web")
    images_dir = os.path.join(workspace_dir, "sources", "manual_images")
    os.makedirs(web_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)
    
    try:
        # Fetch the webpage
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "Unknown"
        
        # Extract main content
        content_selectors = [
            'article',
            'main',
            '[role="main"]',
            '.content',
            '.post-content',
            '.article-content',
            '.entry-content',
            '#content',
        ]
        
        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            main_content = soup.find('body')
        
        # Extract and process images
        image_urls = []
        if main_content:
            for img in main_content.find_all('img'):
                src = img.get('src')
                if src:
                    absolute_url = urljoin(url, src)
                    image_urls.append(absolute_url)
        
        # Download images
        downloaded_images = []
        for i, img_url in enumerate(image_urls[:10]):
            try:
                img_response = requests.get(img_url, headers=headers, timeout=10)
                img_response.raise_for_status()
                
                img_extension = os.path.splitext(urlparse(img_url).path)[1] or '.png'
                img_filename = f"{os.path.basename(urlparse(url).path)[:50]}_image_{i+1}{img_extension}"
                img_filename = re.sub(r'[^\w\-.]', '_', img_filename)
                img_path = os.path.join(images_dir, img_filename)
                
                with open(img_path, 'wb') as f:
                    f.write(img_response.content)
                
                downloaded_images.append({
                    'url': img_url,
                    'local_path': f"sources/manual_images/{img_filename}",
                    'size': len(img_response.content)
                })
            except Exception:
                pass
        
        # Extract text content
        if main_content:
            for script in main_content(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            text_content = main_content.get_text(separator='\n', strip=True)
        else:
            text_content = response.text
        
        # Create markdown content
        markdown_content = f"""# {title_text}

**来源**: {url}
**爬取时间**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**图片数量**: {len(downloaded_images)}

---

## 网页内容

{text_content}

---

## 下载的图片

"""
        
        for img_info in downloaded_images:
            markdown_content += f"### 图片\n"
            markdown_content += f"- 原始URL: {img_info['url']}\n"
            markdown_content += f"- 本地路径: {img_info['local_path']}\n"
            markdown_content += f"- 文件大小: {img_info['size']} bytes\n"
            markdown_content += f"![图片]({img_info['local_path']})\n\n"
        
        # Save markdown file
        safe_filename = re.sub(r'[^\w\-.]', '_', title_text[:100]) or "page"
        markdown_path = os.path.join(web_dir, f"{safe_filename}.md")
        
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return {
            'success': True,
            'title': title_text,
            'url': url,
            'content_length': len(text_content),
            'image_count': len(downloaded_images),
            'markdown_path': markdown_path,
            'images': downloaded_images,
            'preview': text_content[:500]
        }
    except Exception as e:
        return {
            'success': False,
            'url': url,
            'error': str(e)
        }


@tool
def crawl_webpage(
    url: str,
    workspace_dir: str = "/tmp/research_workspace",
    runtime: ToolRuntime = None
) -> str:
    """Crawl a single webpage and save its content to the workspace.
    
    Args:
        url: The URL to crawl.
        workspace_dir: The workspace root directory.
    
    Returns:
        Success message with saved file path and extracted content.
    """
    ctx = runtime.context if runtime else new_context(method="crawl_webpage")
    
    # If workspace_dir is relative, make it under /tmp/
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    result = _crawl_webpage_internal(url, workspace_dir)
    
    if result['success']:
        images_list = "\n".join([
            f"- {img['local_path']} ({img['size']} bytes)"
            for img in result['images']
        ])
        
        return f"""✅ 网页爬取成功！

**网页信息**:
- 标题: {result['title']}
- URL: {result['url']}
- 内容长度: {result['content_length']} 字符
- 下载图片: {result['image_count']} 张

**保存位置**:
- Markdown: {result['markdown_path']}
- 图片目录: {workspace_dir}/sources/manual_images/

**下载的图片**:
{images_list}

**内容预览**:
{result['preview']}...
"""
    else:
        return f"❌ 网页爬取失败: {result['error']}\n\nURL: {result['url']}"


@tool
def batch_crawl_webpages(
    urls: List[str],
    workspace_dir: str = "/tmp/research_workspace",
    runtime: ToolRuntime = None
) -> str:
    """Crawl multiple webpages in batch.
    
    Args:
        urls: List of URLs to crawl.
        workspace_dir: The workspace root directory.
    
    Returns:
        Summary of crawled pages.
    """
    ctx = runtime.context if runtime else new_context(method="batch_crawl_webpages")
    
    # If workspace_dir is relative, make it under /tmp/
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    results = []
    success_count = 0
    fail_count = 0
    
    for i, url in enumerate(urls, 1):
        result = _crawl_webpage_internal(url, workspace_dir)
        if result['success']:
            success_count += 1
            results.append(f"{i}. {url}: ✅ 成功")
        else:
            fail_count += 1
            results.append(f"{i}. {url}: ❌ 失败 - {result.get('error', 'Unknown error')}")
    
    summary = f"""# 批量网页爬取结果

**总任务数**: {len(urls)}
**成功**: {success_count}
**失败**: {fail_count}

## 详细结果

{chr(10).join(results)}

## 爬取的文件位置

- Markdown 文件: {workspace_dir}/sources/web/
- 图片文件: {workspace_dir}/sources/manual_images/
"""
    
    # Save summary
    summary_path = os.path.join(workspace_dir, "sources", "web", "crawl_summary.md")
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    return summary


@tool
def extensive_search_and_crawl(
    topic: str,
    num_queries: int = 20,
    results_per_query: int = 5,
    workspace_dir: str = "/tmp/research_workspace",
    runtime: ToolRuntime = None
) -> str:
    """Perform extensive search and crawl all found webpages.
    
    This tool performs multiple searches from different angles, aggregates results,
    and crawls all unique webpages to get full content with images.
    
    Args:
        topic: The research topic.
        num_queries: Number of different search queries to try (default: 20).
        results_per_query: Number of results per query (default: 5).
        workspace_dir: The workspace root directory.
    
    Returns:
        Summary of search and crawl results.
    """
    ctx = runtime.context if runtime else new_context(method="extensive_search_and_crawl")
    
    # If workspace_dir is relative, make it under /tmp/
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    # 检查搜索服务可用性
    is_coze_platform = bool(os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY"))
    has_bocha = bool(os.getenv("BOCHA_API_KEY"))
    
    # Ensure workspace directory exists at the start
    web_dir = os.path.join(workspace_dir, "sources", "web")
    images_dir = os.path.join(workspace_dir, "sources", "manual_images")
    os.makedirs(web_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)
    
    # 本地模式且无 Bocha：降级为 GitHub/文档站点爬取
    if not is_coze_platform and not has_bocha:
        return _local_extensive_crawl(topic, workspace_dir)
    
    # Generate diverse search queries
    query_templates = [
        f"{topic} 架构原理",
        f"{topic} 核心组件",
        f"{topic} 工作流程",
        f"{topic} 实践案例",
        f"{topic} 最佳实践",
        f"{topic} 源码分析",
        f"{topic} 配置教程",
        f"{topic} 部署指南",
        f"{topic} 性能优化",
        f"{topic} 常见问题",
        f"{topic} 对比评测",
        f"{topic} 应用场景",
        f"{topic} 开发文档",
        f"{topic} 技术细节",
        f"{topic} 使用示例",
        f"{topic} 系统设计",
        f"{topic} 数据流",
        f"{topic} 接口设计",
        f"{topic} 扩展开发",
        f"{topic} 运维管理",
    ]
    
    # Collect all URLs
    all_urls = []
    search_results = []
    
    for i in range(min(num_queries, len(query_templates))):
        query = query_templates[i]
        
        try:
            # 优先使用 Bocha 搜索
            if has_bocha:
                response = _bocha_search_request(query, results_per_query)
                web_items = response.get("web_pages", [])
                for item in web_items:
                    url = item.get("url") or item.get("link")
                    if url and url not in all_urls:
                        all_urls.append(url)
                        search_results.append({
                            'query': query,
                            'title': item.get('title', ''),
                            'url': url,
                            'snippet': item.get('snippet', item.get('description', '')),
                            'site': item.get('site_name', '')
                        })
            elif is_coze_platform:
                from coze_coding_dev_sdk import SearchClient
                search_client = SearchClient(ctx=ctx)
                response = search_client.web_search(
                    query=query,
                    count=results_per_query,
                    need_summary=True
                )
                
                if response.web_items:
                    for item in response.web_items:
                        if item.url and item.url not in all_urls:
                            all_urls.append(item.url)
                            search_results.append({
                                'query': query,
                                'title': item.title,
                                'url': item.url,
                                'snippet': item.snippet,
                                'site': item.site_name
                            })
        except Exception:
            pass
    
    # Crawl all unique URLs
    # Calculate average results for formatting
    query_count = min(num_queries, len(query_templates))
    avg_results = len(all_urls) / query_count if query_count > 0 else 0
    
    crawl_summary = f"""# 扩展搜索与爬取报告

**主题**: {topic}
**搜索查询数**: {query_count}
**收集到URL数**: {len(all_urls)}
**目标**: 至少 50 个页面

## 搜索统计

- 总查询次数: {query_count}
- 发现唯一URL: {len(all_urls)}
- 每个查询平均结果: {avg_results:.1f}

## 正在爬取网页...

"""
    
    # Crawl pages (limit to first 50 to avoid timeout)
    max_crawl = min(50, len(all_urls))
    crawled_count = 0
    failed_count = 0
    
    for i, url in enumerate(all_urls[:max_crawl]):
        result = _crawl_webpage_internal(url, workspace_dir)
        if result['success']:
            crawled_count += 1
            crawl_summary += f"✅ [{i+1}/{max_crawl}] {url}\n"
        else:
            failed_count += 1
            crawl_summary += f"❌ [{i+1}/{max_crawl}] {url} - {result.get('error', 'Unknown error')}\n"
    
    # Final summary
    crawl_summary += f"""

## 爬取完成

**成功**: {crawled_count}
**失败**: {failed_count}
**总计**: {max_crawl}

## 保存位置

- 网页内容: {workspace_dir}/sources/web/
- 下载图片: {workspace_dir}/sources/manual_images/
- 搜索结果: {workspace_dir}/sources/web/search_results.json

## 建议

如果还需要更多内容，可以：
1. 增加搜索查询数量
2. 使用不同的关键词组合
3. 手动提供更多URL进行爬取
"""
    
    # Ensure directory exists before saving
    web_dir = os.path.join(workspace_dir, "sources", "web")
    os.makedirs(web_dir, exist_ok=True)
    
    # Save search results as JSON
    results_path = os.path.join(web_dir, "search_results.json")
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(search_results, f, ensure_ascii=False, indent=2)
    
    # Save crawl summary
    summary_path = os.path.join(web_dir, "crawl_summary.md")
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(crawl_summary)
    
    return crawl_summary


def _local_extensive_crawl(topic: str, workspace_dir: str) -> str:
    """本地模式下的扩展爬取：爬取 GitHub 和常见文档站点
    
    Args:
        topic: 调研主题
        workspace_dir: 工作目录
    
    Returns:
        爬取结果摘要
    """
    import re
    
    # Ensure workspace directory exists at the start
    web_dir = os.path.join(workspace_dir, "sources", "web")
    images_dir = os.path.join(workspace_dir, "sources", "manual_images")
    os.makedirs(web_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)
    
    # 解析主题，判断是否是 GitHub URL
    github_pattern = r'https?://github\.com/([^/]+)/([^/]+)'
    github_match = re.match(github_pattern, topic)
    
    # 构建要爬取的 URL 列表
    urls_to_crawl = []
    
    if github_match:
        # 如果是 GitHub URL，爬取相关页面
        owner, repo = github_match.groups()
        base_url = f"https://github.com/{owner}/{repo}"
        urls_to_crawl = [
            base_url,
            f"{base_url}/blob/main/README.md",
            f"{base_url}/blob/master/README.md",
            f"{base_url}/wiki",
            f"{base_url}/tree/main/docs",
            f"{base_url}/tree/main/documentation",
            f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md",
            f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md",
        ]
        topic_name = repo
    else:
        # 如果是主题名称，尝试构建常见文档站点 URL
        topic_slug = topic.lower().replace(' ', '-').replace('_', '-')
        topic_name = topic
        
        # 常见文档站点模式
        urls_to_crawl = [
            f"https://github.com/search?q={topic}&type=repositories",
            f"https://{topic_slug}.readthedocs.io",
            f"https://{topic_slug}.github.io",
            f"https://docs.{topic_slug}.io",
            f"https://www.{topic_slug}.io",
            f"https://{topic_slug}.org",
        ]
    
    # 开始爬取
    summary = f"""# 本地模式爬取报告

**主题**: {topic_name}
**模式**: 本地运行（无搜索服务）

⚠️ 本地运行模式下，无法使用网络搜索服务。以下是基于常见模式的爬取结果。

## 正在爬取...

"""
    
    crawled_count = 0
    failed_count = 0
    
    for i, url in enumerate(urls_to_crawl):
        result = _crawl_webpage_internal(url, workspace_dir)
        if result['success']:
            crawled_count += 1
            summary += f"✅ [{i+1}/{len(urls_to_crawl)}] {url}\n"
        else:
            failed_count += 1
            summary += f"❌ [{i+1}/{len(urls_to_crawl)}] {url} - {result.get('error', 'Failed')}\n"
    
    summary += f"""

## 爬取完成

**成功**: {crawled_count}
**失败**: {failed_count}
**总计**: {len(urls_to_crawl)}

## 保存位置

- 网页内容: {workspace_dir}/sources/web/
- 下载图片: {workspace_dir}/sources/manual_images/

---

## 💡 获取更多资料的建议

由于本地模式下搜索服务不可用，你可以：

### 方式一：手动提供 URL
提供你知道的相关网页 URL，例如：
```
请爬取以下网页：
- https://example.com/article1
- https://example.com/article2
```

### 方式二：提供 GitHub 仓库
提供 GitHub 仓库 URL，系统会自动爬取相关文档：
```
请帮我调研：https://github.com/owner/repo
```

### 方式三：配置 Bocha AI 搜索
在 .env 文件中配置 Bocha API Key：
```
BOCHA_API_KEY=sk-xxxx
```

或部署到 Coze 平台使用内置搜索服务。

"""
    
    # Ensure directory exists before saving
    web_dir = os.path.join(workspace_dir, "sources", "web")
    os.makedirs(web_dir, exist_ok=True)
    
    # Save summary
    summary_path = os.path.join(web_dir, "crawl_summary.md")
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    return summary


def _bocha_search_request(query: str, count: int = 10) -> Dict:
    """使用 Bocha AI 执行搜索请求
    
    Args:
        query: 搜索查询
        count: 返回结果数量
    
    Returns:
        搜索结果字典
    """
    import os
    import requests
    
    api_key = os.getenv("BOCHA_API_KEY")
    if not api_key:
        return {"web_pages": [], "error": "BOCHA_API_KEY not configured"}
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": query,
        "count": count,
        "summary": False
    }
    
    try:
        response = requests.post(
            "https://api.bocha.io/v1/search",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"web_pages": [], "error": str(e)}
