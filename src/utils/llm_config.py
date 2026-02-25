"""共享 LLM 配置，供 agent 和 tools 使用，避免循环依赖。"""

import os
import json

LLM_CONFIG_PATH = "config/agent_llm_config.json"


def _is_coze_platform() -> bool:
    """检测是否运行在 Coze 平台"""
    return bool(os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY"))


def get_llm_config(ctx=None) -> dict:
    """获取 LLM 连接配置，支持 Coze 平台和本地开发两种模式。

    Returns:
        dict: 包含 api_key, base_url, model, temperature, timeout, thinking,
              default_headers 等，用于创建 ChatOpenAI 实例。
    """
    workspace_path = (
        os.getenv("COZE_WORKSPACE_PATH")
        or os.getenv("WORKSPACE_PATH")
        or os.getcwd()
    )
    config_path = os.path.join(workspace_path, LLM_CONFIG_PATH)

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    if _is_coze_platform():
        from coze_coding_utils.runtime_ctx.context import default_headers

        api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
        base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")
        model = cfg["config"].get("model", "doubao-seed-2-0-pro-260215")
        default_headers_dict = default_headers(ctx) if ctx else {}
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = os.getenv("OPENAI_MODEL") or cfg["config"].get("model", "gpt-4o")
        default_headers_dict = {}

        if not api_key:
            raise ValueError(
                "本地运行需要设置 OPENAI_API_KEY 环境变量！\n"
                "请创建 .env 文件并配置：\n"
                "  OPENAI_API_KEY=你的API-Key\n"
                "  OPENAI_BASE_URL=https://api.openai.com/v1\n"
                "  OPENAI_MODEL=gpt-4o"
            )

    return {
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
        "temperature": cfg["config"].get("temperature", 0.7),
        "timeout": cfg["config"].get("timeout", 600),
        "thinking": cfg["config"].get("thinking", "disabled"),
        "default_headers": default_headers_dict,
        "system_prompt": cfg.get("sp"),
    }
