"""
Research Agent - 技术调研智能体

这是一个专业的技术调研智能体，能够：
- 进行深度网络搜索和资料搜集
- 分析代码库并提出复杂工程问题
- 生成专业的视觉提示词用于图像生成
- 统一管理所有调研资料
- 生成高质量的技术博客

支持两种运行模式：
1. Coze 平台模式：使用 COZE_WORKLOAD_IDENTITY_API_KEY 认证
2. 本地开发模式：使用 OPENAI_API_KEY 调用模型
"""

import os
import json
from typing import Annotated
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from coze_coding_utils.runtime_ctx.context import default_headers, new_context

# Import tools
from tools.file_manager import (
    create_workspace,
    save_file,
    read_file_content,
    list_files,
    get_workspace_structure,
    save_image_file,
)
from tools.code_analyzer import (
    save_code_to_workspace,
    analyze_code_and_generate_questions,
    answer_code_questions,
    search_best_practices_for_code,
)
from tools.image_generator import (
    generate_visual_prompt,
    generate_flow_diagram_prompt,
    generate_architecture_diagram_prompt,
    save_generated_image,
    list_visual_prompts,
)
from tools.web_researcher import (
    search_web,
    search_multiple_queries,
    search_best_practices,
    search_architecture_info,
)
from tools.web_crawler import (
    crawl_webpage,
    batch_crawl_webpages,
    extensive_search_and_crawl,
)
from tools.export_workspace import (
    pack_workspace_to_zip,
    upload_and_generate_download_url,
    get_workspace_file_list,
    copy_specific_file,
    generate_blog_copy_instruction,
)

# Import checkpointer
from storage.memory.memory_saver import get_memory_saver

LLM_CONFIG = "config/agent_llm_config.json"

# 默认保留最近 20 轮对话 (40 条消息)
MAX_MESSAGES = 40


def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    return add_messages(old, new)[-MAX_MESSAGES:]  # type: ignore


class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]


def _is_coze_platform() -> bool:
    """检测是否运行在 Coze 平台"""
    return bool(os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY"))


def _get_llm_config(ctx=None):
    """获取 LLM 配置，支持 Coze 平台和本地开发两种模式"""
    
    # 确定工作目录
    workspace_path = os.getenv("COZE_WORKSPACE_PATH") or os.getenv("WORKSPACE_PATH") or os.getcwd()
    config_path = os.path.join(workspace_path, LLM_CONFIG)
    
    # 加载配置文件
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    
    if _is_coze_platform():
        # Coze 平台模式
        api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
        base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")
        model = cfg['config'].get("model", "doubao-seed-2-0-pro-260215")
        default_headers_dict = default_headers(ctx) if ctx else {}
    else:
        # 本地开发模式
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = os.getenv("OPENAI_MODEL") or cfg['config'].get("model", "gpt-4o")
        default_headers_dict = {}
        
        if not api_key:
            raise ValueError(
                "本地运行需要设置 OPENAI_API_KEY 环境变量！\n"
                "请创建 .env 文件并配置：\n"
                "  OPENAI_API_KEY=sk-xxxx\n"
                "  OPENAI_BASE_URL=https://api.openai.com/v1\n"
                "  OPENAI_MODEL=gpt-4o\n\n"
                "火山引擎用户注意：\n"
                "  OPENAI_MODEL 需要填写 endpoint_id（格式：ep-xxxx-xxxx...）\n"
                "  而不是模型名称！"
            )
        
        # 检查火山引擎配置是否正确
        if "volces.com" in base_url and not model.startswith("ep-"):
            import warnings
            warnings.warn(
                f"\n⚠️  火山引擎配置警告：\n"
                f"  当前模型名称: {model}\n"
                f"  火山引擎需要使用 endpoint_id（格式：ep-xxxx-xxxx...）\n"
                f"  请检查 OPENAI_MODEL 环境变量是否正确配置\n"
                f"  获取方式：火山引擎控制台 → 推理接入点 → 复制接入点 ID"
            )
    
    return {
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
        "temperature": cfg['config'].get('temperature', 0.7),
        "timeout": cfg['config'].get('timeout', 600),
        "thinking": cfg['config'].get('thinking', 'disabled'),
        "default_headers": default_headers_dict,
        "system_prompt": cfg.get("sp"),
    }


def build_agent(ctx=None):
    """
    构建技术调研智能体
    
    支持两种运行模式：
    1. Coze 平台模式：自动使用平台认证
    2. 本地开发模式：使用 OPENAI_API_KEY
    
    Returns:
        Agent 实例
    """
    llm_config = _get_llm_config(ctx)
    
    # Initialize LLM
    llm = ChatOpenAI(
        model=llm_config["model"],
        api_key=llm_config["api_key"],
        base_url=llm_config["base_url"],
        temperature=llm_config["temperature"],
        streaming=True,
        timeout=llm_config["timeout"],
        extra_body={
            "thinking": {
                "type": llm_config["thinking"]
            }
        },
        default_headers=llm_config["default_headers"]
    )
    
    # Define tools
    tools = [
        # File management tools
        create_workspace,
        save_file,
        read_file_content,
        list_files,
        get_workspace_structure,
        save_image_file,
        
        # Code analysis tools
        save_code_to_workspace,
        analyze_code_and_generate_questions,
        answer_code_questions,
        search_best_practices_for_code,
        
        # Image generation tools
        generate_visual_prompt,
        generate_flow_diagram_prompt,
        generate_architecture_diagram_prompt,
        save_generated_image,
        list_visual_prompts,
        
        # Web research tools
        search_web,
        search_multiple_queries,
        search_best_practices,
        search_architecture_info,
        
        # Web crawler tools
        crawl_webpage,
        batch_crawl_webpages,
        extensive_search_and_crawl,
        
        # Workspace export tools
        pack_workspace_to_zip,
        upload_and_generate_download_url,
        get_workspace_file_list,
        copy_specific_file,
        generate_blog_copy_instruction,
    ]
    
    # Create agent
    agent = create_agent(
        model=llm,
        system_prompt=llm_config["system_prompt"],
        tools=tools,
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
    
    return agent
