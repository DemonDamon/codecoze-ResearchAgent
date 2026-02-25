"""工具模板 - 文件管理工具"""

import os
from datetime import datetime
from typing import Optional
from langchain.tools import tool, ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context


def get_workspace_dir(name: Optional[str] = None) -> str:
    """获取工作目录路径
    
    Args:
        name: 用户指定的目录名（可选）
    
    Returns:
        工作目录路径
    """
    if name:
        return os.path.join("/tmp", name)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"/tmp/workspace_{timestamp}"


@tool
def create_workspace(output_dir: str = "", runtime: ToolRuntime = None) -> str:
    """创建工作目录结构。
    
    Args:
        output_dir: 目录名称。
                   - 如果为空：自动生成时间戳目录（如 /tmp/workspace_20260225_143000）
                   - 如果指定：创建 /tmp/{output_dir}
    
    Returns:
        成功消息和创建的目录路径。
    """
    ctx = runtime.context if runtime else new_context(method="create_workspace")
    
    # 确定目录路径
    if not output_dir or output_dir.strip() == "":
        output_dir = get_workspace_dir()
    elif not os.path.isabs(output_dir):
        output_dir = os.path.join("/tmp", output_dir)
    
    # 创建目录结构
    dirs = [
        output_dir,
        os.path.join(output_dir, "sources"),
        os.path.join(output_dir, "sources", "data"),
        os.path.join(output_dir, "generated"),
    ]
    
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    return f"""工作目录已创建: {output_dir}

目录结构:
{chr(10).join([f"  - {d}" for d in dirs])}

💡 所有文件将保存到此目录。"""


@tool
def save_file(
    content: str,
    file_path: str,
    workspace_dir: str = "/tmp/workspace",
    runtime: ToolRuntime = None
) -> str:
    """保存内容到文件。
    
    Args:
        content: 要保存的内容。
        file_path: 相对路径（如 'sources/data.txt'）。
        workspace_dir: 工作目录根路径。
    
    Returns:
        成功消息和完整文件路径。
    """
    ctx = runtime.context if runtime else new_context(method="save_file")
    
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    full_path = os.path.join(workspace_dir, file_path)
    
    # 确保目录存在
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return f"文件已保存: {full_path}"


@tool
def read_file_content(
    file_path: str,
    workspace_dir: str = "/tmp/workspace",
    runtime: ToolRuntime = None
) -> str:
    """读取文件内容。
    
    Args:
        file_path: 相对路径。
        workspace_dir: 工作目录根路径。
    
    Returns:
        文件内容。
    """
    ctx = runtime.context if runtime else new_context(method="read_file_content")
    
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    full_path = os.path.join(workspace_dir, file_path)
    
    if not os.path.exists(full_path):
        return f"文件不存在: {full_path}"
    
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return content


@tool
def list_files(
    directory: str,
    workspace_dir: str = "/tmp/workspace",
    runtime: ToolRuntime = None
) -> str:
    """列出目录下的文件。
    
    Args:
        directory: 相对目录路径。
        workspace_dir: 工作目录根路径。
    
    Returns:
        文件列表。
    """
    ctx = runtime.context if runtime else new_context(method="list_files")
    
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    full_path = os.path.join(workspace_dir, directory)
    
    if not os.path.exists(full_path):
        return f"目录不存在: {full_path}"
    
    items = []
    for item in os.listdir(full_path):
        item_path = os.path.join(full_path, item)
        if os.path.isdir(item_path):
            items.append(f"[DIR]  {item}")
        else:
            size = os.path.getsize(item_path)
            items.append(f"[FILE] {item} ({size} bytes)")
    
    if not items:
        return f"目录为空: {full_path}"
    
    return f"目录内容 {full_path}:\n" + "\n".join(items)
