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
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv()

# 添加 src 到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 设置工作目录
if not os.getenv("COZE_WORKSPACE_PATH"):
    os.environ["WORKSPACE_PATH"] = os.path.dirname(__file__)


async def main():
    from agents.agent import build_agent, _get_llm_config
    
    print("=" * 60)
    print("🚀 Coze Research Agent - 本地运行模式")
    print("=" * 60)
    
    # 检查配置
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n❌ 错误：未配置 OPENAI_API_KEY")
        print("\n请创建 .env 文件并配置：")
        print("  OPENAI_API_KEY=你的API-Key")
        print("  OPENAI_BASE_URL=https://api.openai.com/v1")
        print("  OPENAI_MODEL=gpt-4o")
        sys.exit(1)
    
    # 获取并显示配置
    try:
        llm_config = _get_llm_config()
        print(f"\n📋 配置信息：")
        print(f"  - 模型: {llm_config['model']}")
        print(f"  - API 地址: {llm_config['base_url']}")
        print(f"  - 工作目录: {os.getenv('WORKSPACE_PATH', os.getcwd())}")
    except Exception as e:
        print(f"\n❌ 配置错误: {e}")
        sys.exit(1)
    
    print("\n💬 开始对话 (输入 'quit' 退出, 'clear' 清空历史, 'debug' 切换调试模式)")
    print("-" * 60)
    
    # 构建 agent
    try:
        agent = build_agent()
        print("✅ Agent 初始化成功\n")
    except Exception as e:
        print(f"❌ Agent 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # 会话配置
    config = {"configurable": {"thread_id": "local-session"}}
    debug_mode = False
    
    while True:
        try:
            # 获取用户输入
            user_input = input("👤 你: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                print("\n👋 再见！")
                break
            
            if user_input.lower() == 'clear':
                import uuid
                config = {"configurable": {"thread_id": str(uuid.uuid4())}}
                print("✅ 对话历史已清空\n")
                continue
            
            if user_input.lower() == 'debug':
                debug_mode = not debug_mode
                print(f"🔧 调试模式: {'开启' if debug_mode else '关闭'}\n")
                continue
            
            # 调用 agent
            print("\n🤖 Agent: ", end="", flush=True)
            
            try:
                # 使用 ainvoke 获取完整响应
                result = await agent.ainvoke(
                    {"messages": [{"role": "user", "content": user_input}]},
                    config=config
                )
                
                if debug_mode:
                    print(f"\n[DEBUG] result type: {type(result)}")
                    print(f"[DEBUG] result keys: {result.keys() if result else 'None'}")
                
                # 提取响应内容
                full_response = ""
                if result and "messages" in result:
                    messages = result["messages"]
                    if debug_mode:
                        print(f"[DEBUG] messages count: {len(messages)}")
                    
                    last_message = messages[-1]
                    if debug_mode:
                        print(f"[DEBUG] last_message type: {type(last_message)}")
                    
                    if hasattr(last_message, "content"):
                        full_response = last_message.content
                    elif isinstance(last_message, dict):
                        full_response = last_message.get("content", "")
                
                if full_response:
                    print(full_response)
                else:
                    print("(无响应内容)")
                    if not debug_mode:
                        print("💡 提示: 输入 'debug' 开启调试模式查看详情")
                
                print()  # 换行
                        
            except Exception as e:
                print(f"\n\n❌ API 调用失败: {e}")
                if debug_mode:
                    import traceback
                    traceback.print_exc()
                print("\n请检查：")
                print("  1. API Key 是否正确")
                print("  2. API 地址是否正确")
                print("  3. 模型名称是否正确")
                print("  4. 网络连接是否正常\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
