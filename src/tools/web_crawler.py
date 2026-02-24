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
    
    from coze_coding_dev_sdk import SearchClient
    
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
    crawl_summary = f"""# 扩展搜索与爬取报告

**主题**: {topic}
**搜索查询数**: {min(num_queries, len(query_templates))}
**收集到URL数**: {len(all_urls)}
**目标**: 至少 50 个页面

## 搜索统计

- 总查询次数: {min(num_queries, len(query_templates))}
- 发现唯一URL: {len(all_urls)}
- 每个查询平均结果: {len(all_urls) / min(num_queries, len(query_templates)):.1f if min(num_queries, len(query_templates)) > 0 else 0}

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
    
    # Save search results as JSON
    results_path = os.path.join(workspace_dir, "sources", "web", "search_results.json")
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(search_results, f, ensure_ascii=False, indent=2)
    
    # Save crawl summary
    summary_path = os.path.join(workspace_dir, "sources", "web", "crawl_summary.md")
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(crawl_summary)
    
    return crawl_summary
