"""Image generation tool for research agent.

Generates visual prompts based on nanobanana specification and creates images using Lovart AI.
"""

import os
import json
from typing import Optional
from langchain.tools import tool
from langchain.tools import ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context


@tool
def generate_visual_prompt(
    content_description: str,
    prompt_type: str = "text_to_visual",
    workspace_dir: str = "/tmp/research_workspace",
    runtime: ToolRuntime = None
) -> str:
    """Generate visual prompt based on nanobanana specification.
    
    Args:
        content_description: Description of the content to visualize (concept, flow, architecture, etc.).
        prompt_type: Type of prompt ('text_to_visual' for text/flow descriptions, 'image_to_visual' for image-based prompts).
        workspace_dir: The workspace root directory.
    
    Returns:
        Generated visual prompt in markdown format.
    """
    ctx = runtime.context if runtime else new_context(method="generate_visual_prompt")
    
    # If workspace_dir is relative, make it under /tmp/
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    # Generate visual prompt based on nanobanana specification
    # This is a template that the LLM will fill in with actual content
    
    visual_prompt = f"""# 视觉描述提示词 (基于 NanoBanana 规范)

## 输入内容
{content_description}

---

## 生成的视觉描述

### 主题与布局设想
[基于内容描述推断整体结构、流向和背景风格]

### 视觉模块详解
[将内容逻辑拆解为视觉区域，描述具体的节点形状、颜色和文字内容]

### 风格与配色方案
[指定具体的配色板，如"科技蓝"、"清新绿"等，以及线条风格]

### 技术参数建议
文字必须清晰可辨。保持文字与背景的高对比度。建议 16:9 比例。2K 分辨率。使用标准流程图符号。矢量图风格，扁平化设计，专业学术论文图表风格。

---

## 生成说明
**注意**: 以上是 visual prompt 的模板结构。在实际使用时，需要：
1. 基于具体内容描述填写"主题与布局设想"部分
2. 根据逻辑流程设计"视觉模块详解"
3. 选择合适的"风格与配色方案"
4. 确保所有文字使用简体中文（核心技术术语除外）

## 使用方式
将上述视觉描述复制到 Lovart AI (https://www.lovart.ai/zh/home) 进行图像生成。
"""
    
    # Save visual prompt to file
    prompts_dir = os.path.join(workspace_dir, "generated", "visual_prompts")
    os.makedirs(prompts_dir, exist_ok=True)
    
    # Generate filename based on content description
    safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in content_description[:50])
    filename = f"visual_prompt_{safe_name}.md"
    
    full_path = os.path.join(prompts_dir, filename)
    
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(visual_prompt)
    
    return f"Visual prompt generated and saved to: {full_path}\n\n{visual_prompt}"


@tool
def generate_flow_diagram_prompt(
    flow_description: str,
    workspace_dir: str = "/tmp/research_workspace",
    runtime: ToolRuntime = None
) -> str:
    """Generate visual prompt for flow diagram based on nanobanana specification.
    
    Args:
        flow_description: Description of the flow/process (e.g., "用户登录验证流程：用户输入密码 -> 认证服务验证 -> 成功则进入仪表盘，失败则显示错误").
        workspace_dir: The workspace root directory.
    
    Returns:
        Generated visual prompt for flow diagram.
    """
    ctx = runtime.context if runtime else new_context(method="generate_flow_diagram_prompt")
    
    # If workspace_dir is relative, make it under /tmp/
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    flow_prompt = f"""# 流程图视觉描述提示词

## 流程描述
{flow_description}

---

## 视觉描述（流程图）

### 主题与布局设想
展示上述流程的流程图。整体采用从上到下或从左到右的流向（根据流程复杂度选择）。背景为干净的纯白或浅灰色，强调逻辑清晰度。

### 视觉模块详解

1. **起点节点**:
   - 形状: 圆形或胶囊形
   - 文字: [流程开始，如"开始"或"用户输入"]
   - 颜色: 绿色系

2. **处理节点**:
   - 形状: 圆角矩形
   - 文字: [处理步骤，如"认证服务验证"]
   - 颜色: 蓝色系
   - 连接线: 标注[数据流转描述]

3. **判断节点**:
   - 形状: 菱形
   - 文字: [条件判断，如"验证成功？"]
   - 颜色: 黄色或橙色系

4. **结果分支**:
   - 分支1: 箭头向下/向右，标注"是"，指向[成功结果节点]
   - 分支2: 箭头向右，标注"否"，指向[失败结果节点]
   - 颜色: 成功用绿色，失败用红色

5. **终点节点**:
   - 形状: 圆形或胶囊形
   - 文字: [流程结束，如"结束"或具体结果]
   - 颜色: 绿色系（成功）或红色系（失败）

### 风格与配色方案
- 扁平化矢量风格
- 采用"红绿灯"逻辑：正常流程用蓝/绿，错误流程用红/橙
- 字体使用无衬线黑体
- 线条流畅，箭头清晰

### 技术参数建议
文字必须清晰可辨。保持文字与背景的高对比度。建议 16:9 比例。2K 分辨率。使用标准流程图符号。矢量图风格，扁平化设计，专业学术论文图表风格。

---

## 使用方式
将上述视觉描述复制到 Lovart AI (https://www.lovart.ai/zh/home) 进行图像生成。
"""

    # Save to file
    prompts_dir = os.path.join(workspace_dir, "generated", "visual_prompts")
    os.makedirs(prompts_dir, exist_ok=True)
    
    filename = "flow_diagram_prompt.md"
    full_path = os.path.join(prompts_dir, filename)
    
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(flow_prompt)
    
    return f"Flow diagram prompt generated and saved to: {full_path}\n\n{flow_prompt}"


@tool
def generate_architecture_diagram_prompt(
    architecture_description: str,
    workspace_dir: str = "/tmp/research_workspace",
    runtime: ToolRuntime = None
) -> str:
    """Generate visual prompt for architecture diagram based on nanobanana specification.
    
    Args:
        architecture_description: Description of the system architecture (components, relationships, layers, etc.).
        workspace_dir: The workspace root directory.
    
    Returns:
        Generated visual prompt for architecture diagram.
    """
    ctx = runtime.context if runtime else new_context(method="generate_architecture_diagram_prompt")
    
    # If workspace_dir is relative, make it under /tmp/
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    arch_prompt = f"""# 架构图视觉描述提示词

## 架构描述
{architecture_description}

---

## 视觉描述（架构图）

### 主题与布局设想
展示系统架构的分层结构。整体采用从上到下或从左到右的层级布局。背景为干净的纯白或浅灰色，突出架构的层次感和模块化。

### 视觉模块详解

1. **顶层（展示层/用户层）**:
   - 形状: 圆角矩形或卡片
   - 文字: [用户界面、前端应用等]
   - 颜色: 蓝色系
   - 位置: 图表顶部或左侧

2. **中间层（业务逻辑层/服务层）**:
   - 形状: 矩形或容器框
   - 文字: [各个微服务、API 网关、业务模块等]
   - 颜色: 绿色系或紫色系
   - 包含: 多个子模块，用虚线框分隔
   - 位置: 图表中部

3. **底层（数据层/基础设施层）**:
   - 形状: 圆柱体或横向矩形
   - 文字: [数据库、缓存、消息队列、存储等]
   - 颜色: 橙色系或灰色系
   - 位置: 图表底部或右侧

4. **连接关系**:
   - 实线箭头: 表示主要数据流或调用关系
   - 虚线箭头: 表示异步通信或事件驱动
   - 双向箭头: 表示双向交互
   - 颜色: 灰色或深蓝色

5. **外部依赖**:
   - 形状: 云朵形或特殊图标
   - 文字: [外部服务、第三方 API 等]
   - 颜色: 粉色系或特殊颜色
   - 位置: 图表边缘

### 风格与配色方案
- 扁平化矢量风格
- 不同层级使用不同色系区分
- 字体使用无衬线黑体
- 线条简洁清晰，避免过度装饰

### 技术参数建议
文字必须清晰可辨。保持文字与背景的高对比度。建议 16:9 比例。2K 分辨率。使用标准流程图符号。矢量图风格，扁平化设计，专业学术论文图表风格。

---

## 使用方式
将上述视觉描述复制到 Lovart AI (https://www.lovart.ai/zh/home) 进行图像生成。
"""

    # Save to file
    prompts_dir = os.path.join(workspace_dir, "generated", "visual_prompts")
    os.makedirs(prompts_dir, exist_ok=True)
    
    filename = "architecture_diagram_prompt.md"
    full_path = os.path.join(prompts_dir, filename)
    
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(arch_prompt)
    
    return f"Architecture diagram prompt generated and saved to: {full_path}\n\n{arch_prompt}"


@tool
def save_generated_image(
    image_url: str,
    image_name: str,
    workspace_dir: str = "/tmp/research_workspace",
    runtime: ToolRuntime = None
) -> str:
    """Save a generated image to the workspace.
    
    Args:
        image_url: URL of the generated image.
        image_name: Name to save the image as (e.g., 'architecture_diagram.png').
        workspace_dir: The workspace root directory.
    
    Returns:
        Success message with the file path.
    """
    ctx = runtime.context if runtime else new_context(method="save_generated_image")
    
    # If workspace_dir is relative, make it under /tmp/
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    images_dir = os.path.join(workspace_dir, "generated", "images")
    os.makedirs(images_dir, exist_ok=True)
    
    full_path = os.path.join(images_dir, image_name)
    
    # Note: In actual implementation, you would download the image from image_url
    # For now, this is a placeholder
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(f"Placeholder for image from: {image_url}")
    
    return f"Image placeholder saved to: {full_path}\nNote: Implement actual image download logic using image_url: {image_url}"


@tool
def list_visual_prompts(
    workspace_dir: str = "/tmp/research_workspace",
    runtime: ToolRuntime = None
) -> str:
    """List all generated visual prompts in the workspace.
    
    Args:
        workspace_dir: The workspace root directory.
    
    Returns:
        List of visual prompts.
    """
    ctx = runtime.context if runtime else new_context(method="list_visual_prompts")
    
    # If workspace_dir is relative, make it under /tmp/
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    prompts_dir = os.path.join(workspace_dir, "generated", "visual_prompts")
    
    if not os.path.exists(prompts_dir):
        return f"No visual prompts found. Directory does not exist: {prompts_dir}"
    
    files = sorted([f for f in os.listdir(prompts_dir) if f.endswith('.md')])
    
    if not files:
        return f"No visual prompts found in: {prompts_dir}"
    
    result = f"Found {len(files)} visual prompts:\n\n"
    for i, filename in enumerate(files, 1):
        file_path = os.path.join(prompts_dir, filename)
        result += f"{i}. {filename}\n"
        result += f"   Path: {file_path}\n"
    
    return result
