#!/bin/bash
# 本地启动 API 服务脚本

# 加载 .env 文件
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 设置工作目录
export WORKSPACE_PATH=$(pwd)

# 启动服务
echo "🚀 启动 API 服务..."
echo "📍 API 地址: http://localhost:8000"
echo "📍 OpenAI 兼容接口: http://localhost:8000/v1/chat/completions"
echo ""

uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
