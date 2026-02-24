#!/usr/bin/env python3
"""
本地运行脚本

使用方法：
    1. 复制 .env.example 为 .env
    2. 填写你的 OPENAI_API_KEY
    3. 运行：python run_local.py
"""

import os
import sys
import asyncio

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv()

# 添加 src 到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 设置工作目录
if not os.getenv("COZE_WORKSPACE_PATH"):
    os.environ["WORKSPACE_PATH"] = os.path.dirname(__file__)


async def main():
    from agents.agent import build_agent
    
    print("=" * 60)
    print("🚀 Coze Research Agent - 本地运行模式")
    print("=" * 60)
    
    # 检查配置
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n❌ 错误：未配置 OPENAI_API_KEY")
        print("\n请创建 .env 文件并配置：")
        print("  OPENAI_API_KEY=sk-xxxx")
        print("  OPENAI_BASE_URL=https://api.openai.com/v1  # 可选")
        print("  OPENAI_MODEL=gpt-4o  # 可选")
        sys.exit(1)
    
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    print(f"\n📋 配置信息：")
    print(f"  - 模型: {model}")
    print(f"  - API 地址: {base_url}")
    print(f"  - 工作目录: {os.getenv('WORKSPACE_PATH', os.getcwd())}")
    
    print("\n💬 开始对话 (输入 'quit' 退出, 'clear' 清空历史)")
    print("-" * 60)
    
    # 构建 agent
    agent = build_agent()
    
    # 会话配置
    config = {"configurable": {"thread_id": "local-session"}}
    
    while True:
        try:
            # 获取用户输入
            user_input = input("\n👤 你: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                print("\n👋 再见！")
                break
            
            if user_input.lower() == 'clear':
                # 清空会话（使用新的 thread_id）
                import uuid
                config = {"configurable": {"thread_id": str(uuid.uuid4())}}
                print("\n✅ 对话历史已清空")
                continue
            
            # 调用 agent
            print("\n🤖 Agent: ", end="", flush=True)
            
            response_text = ""
            async for chunk in agent.astream(
                {"messages": [{"role": "user", "content": user_input}]},
                config=config
            ):
                # 处理流式输出
                if "agent" in chunk:
                    if "messages" in chunk["agent"]:
                        for msg in chunk["agent"]["messages"]:
                            if hasattr(msg, "content") and msg.content:
                                content = msg.content
                                if content != response_text:
                                    # 只打印新增的部分
                                    new_part = content[len(response_text):]
                                    print(new_part, end="", flush=True)
                                    response_text = content
            
            print()  # 换行
            
        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
