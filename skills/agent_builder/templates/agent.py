"""Agent 构建模板 - Agent 主逻辑"""

import os
import json
from typing import Annotated
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from coze_coding_utils.runtime_ctx.context import default_headers
from storage.memory.memory_saver import get_memory_saver

# 配置文件路径
LLM_CONFIG = "config/agent_llm_config.json"

# 滑动窗口大小（保留最近 N 条消息）
MAX_MESSAGES = 40


def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    return add_messages(old, new)[-MAX_MESSAGES:]


class AgentState(MessagesState):
    """Agent 状态，包含滑动窗口消息"""
    messages: Annotated[list[AnyMessage], _windowed_messages]


def build_agent(ctx=None):
    """构建 Agent 实例
    
    Args:
        ctx: 运行上下文（Coze 平台使用）
    
    Returns:
        Agent 实例
    """
    # 读取配置
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", os.getcwd())
    config_path = os.path.join(workspace_path, LLM_CONFIG)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    
    # 获取 API 配置
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")
    model = os.getenv("OPENAI_MODEL") or cfg['config'].get("model", "gpt-4o")
    
    # 创建 LLM
    llm = ChatOpenAI(
        model=model,
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
    
    # 导入工具
    # from tools.file_manager import create_workspace, save_file
    # from tools.my_tool import my_tool
    tools = [
        # create_workspace,
        # save_file,
        # my_tool,
    ]
    
    # 创建 Agent
    return create_agent(
        model=llm,
        system_prompt=cfg.get("sp"),
        tools=tools,
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
