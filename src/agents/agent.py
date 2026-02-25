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
from typing import Annotated
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from coze_coding_utils.runtime_ctx.context import new_context

from utils.llm_config import get_llm_config

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

# 默认保留最近 20 轮对话 (40 条消息)
MAX_MESSAGES = 40


def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    return add_messages(old, new)[-MAX_MESSAGES:]  # type: ignore


class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]


def build_agent(ctx=None):
    """
    构建技术调研智能体
    
    支持两种运行模式：
    1. Coze 平台模式：自动使用平台认证
    2. 本地开发模式：使用 OPENAI_API_KEY
    
    Returns:
        Agent 实例
    """
    llm_config = get_llm_config(ctx)
    
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
