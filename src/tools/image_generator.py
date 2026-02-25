"""Image generation tool for research agent.

Generates visual prompts based on「文本转绘图描述」规约 and creates images using Lovart AI.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

from langchain.tools import tool
from langchain.tools import ToolRuntime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from coze_coding_utils.runtime_ctx.context import new_context
from utils.llm_config import get_llm_config

# 规约文件路径（相对于工作区根目录）
SPEC_FILE = "prompts/nanobanana_prompt_generation_instruct.md"

SYSTEM_PROMPT = """\
你现在的身份是【高级视觉信息设计师】，精通信息设计与视觉传达。
你的核心任务是将用户提供的【文本/代码】转化为一段用于绘图的【中文视觉描述】。
严格遵循用户给出的规约，直接输出最终结果，不要包含任何解释性废话。"""


def _load_spec_content() -> str:
    """加载「文本转绘图描述」规约内容，作为参考资料嵌入 prompt。"""
    workspace_path = (
        os.getenv("COZE_WORKSPACE_PATH")
        or os.getenv("WORKSPACE_PATH")
        or os.getcwd()
    )
    spec_path = os.path.join(workspace_path, SPEC_FILE)
    if os.path.isfile(spec_path):
        with open(spec_path, "r", encoding="utf-8") as f:
            content = f.read()
        logger.info("规约文件加载成功: %s (%d 字符)", spec_path, len(content))
        return content
    logger.warning("规约文件未找到: %s，将使用 fallback 模式", spec_path)
    return ""


def _invoke_llm_for_visual_prompt(user_content: str) -> str:
    """使用规约驱动 LLM 将文本转为结构化中文视觉描述。"""
    llm_config = get_llm_config()
    spec_content = _load_spec_content()

    llm = ChatOpenAI(
        model=llm_config["model"],
        api_key=llm_config["api_key"],
        base_url=llm_config["base_url"],
        temperature=0.3,
        streaming=False,
        timeout=llm_config.get("timeout", 600),
        extra_body={"thinking": {"type": "disabled"}},
        default_headers=llm_config.get("default_headers", {}),
    )

    if spec_content:
        user_msg = (
            "请仔细阅读并严格执行以下【文本转绘图描述规约】中的所有定义，特别是以下两点：\n"
            "1. **视觉化映射**：对于抽象逻辑，你需要主动想象并定义它的形状（如：判断用菱形）和布局（如：从上到下）。\n"
            "2. **输出格式**：必须严格遵守规约中【Section 3 输出模板】的格式输出。\n\n"
            f"<规约>\n{spec_content}\n</规约>\n\n"
            "---\n"
            f"【待处理的输入内容】：\n{user_content}\n\n"
            "---\n\n"
            "请开始处理，直接输出最终的中文视觉描述结果，不要包含任何解释性废话。"
        )
    else:
        user_msg = (
            "请将以下文本/代码转化为结构化的中文视觉描述，用于驱动文生图模型。\n"
            "要求：主动推断布局和配色，输出包含【主题与布局设想】【视觉模块详解】【风格与配色方案】【技术参数建议】四个部分。\n\n"
            "---\n"
            f"【待处理的输入内容】：\n{user_content}\n\n"
            "---\n\n"
            "请直接输出最终的中文视觉描述结果。"
        )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_msg),
    ]

    response = llm.invoke(messages)
    return response.content if hasattr(response, "content") else str(response)


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
    
    # 使用「文本转绘图描述」规约 + LLM 生成结构化视觉描述
    visual_prompt = _invoke_llm_for_visual_prompt(content_description)
    
    # 包装为完整 markdown 文档
    full_prompt = f"""# 视觉描述提示词 (基于「文本转绘图描述」规约)

## 输入内容
{content_description}

---

## 生成的视觉描述

{visual_prompt}

---

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
        f.write(full_prompt)
    
    return f"Visual prompt generated and saved to: {full_path}\n\n{full_prompt}"


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
    
    # 使用「文本转绘图描述」规约 + LLM 生成流程图视觉描述
    flow_content = _invoke_llm_for_visual_prompt(
        f"【流程图描述】\n{flow_description}"
    )
    
    flow_prompt = f"""# 流程图视觉描述提示词 (基于「文本转绘图描述」规约)

## 流程描述
{flow_description}

---

## 视觉描述（流程图）

{flow_content}

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
    
    # 使用「文本转绘图描述」规约 + LLM 生成架构图视觉描述
    arch_content = _invoke_llm_for_visual_prompt(
        f"【架构图描述】\n{architecture_description}"
    )
    
    arch_prompt = f"""# 架构图视觉描述提示词 (基于「文本转绘图描述」规约)

## 架构描述
{architecture_description}

---

## 视觉描述（架构图）

{arch_content}

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
