"""
Research Agent - 技术调研智能体

这是一个专业的技术调研智能体，能够：
- 进行深度网络搜索和资料搜集
- 分析代码库并提出复杂工程问题
- 生成专业的视觉提示词用于图像生成
- 统一管理所有调研资料
- 生成高质量的技术博客
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


def build_agent(ctx=None):
    """
    构建技术调研智能体
    
    Returns:
        Agent 实例
    """
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    config_path = os.path.join(workspace_path, LLM_CONFIG)
    
    # Load LLM configuration
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    
    # Get API configuration from environment
    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")
    
    # Initialize LLM
    llm = ChatOpenAI(
        model=cfg['config'].get("model"),
        api_key=api_key,
        base_url=base_url,
        temperature=cfg['config'].get('temperature', 0.7),
        streaming=True,
        timeout=cfg['config'].get('timeout', 600),
        extra_body={
            "thinking": {
                "type": cfg['config'].get('thinking', 'disabled')
            }
        },
        default_headers=default_headers(ctx) if ctx else {}
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
    ]
    
    # Create agent
    agent = create_agent(
        model=llm,
        system_prompt=cfg.get("sp"),
        tools=tools,
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
    
    return agent
