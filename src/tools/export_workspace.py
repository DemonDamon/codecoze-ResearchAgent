"""Workspace export tool for research agent.

Packs the workspace directory into a downloadable format or uploads to object storage.
"""

import os
import shutil
import zipfile
from typing import Optional
from pathlib import Path
from langchain.tools import tool
from langchain.tools import ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context


@tool
def pack_workspace_to_zip(
    workspace_dir: str = "/tmp/research_workspace",
    output_dir: str = "/tmp",
    runtime: ToolRuntime = None
) -> str:
    """Pack the workspace directory into a zip file for download.
    
    Args:
        workspace_dir: The workspace root directory to pack.
        output_dir: Directory where the zip file will be saved.
    
    Returns:
        Path to the generated zip file and instructions for download.
    """
    ctx = runtime.context if runtime else new_context(method="pack_workspace_to_zip")
    
    # If workspace_dir is relative, make it under /tmp/
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    # Ensure workspace exists
    if not os.path.exists(workspace_dir):
        return f"Error: Workspace directory not found: {workspace_dir}"
    
    # Get workspace name for the zip file
    workspace_name = os.path.basename(workspace_dir)
    zip_filename = f"{workspace_name}.zip"
    zip_path = os.path.join(output_dir, zip_filename)
    
    # Create zip file
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Walk through the workspace directory
            for root, dirs, files in os.walk(workspace_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Calculate relative path from workspace root
                    arcname = os.path.relpath(file_path, workspace_dir)
                    zipf.write(file_path, arcname)
        
        zip_size = os.path.getsize(zip_path)
        
        return f"""✅ 工作目录已成功打包！

**Zip 文件信息:**
- 文件路径: {zip_path}
- 文件大小: {zip_size / 1024:.2f} KB
- 包含内容: 完整的工作目录结构

**下载说明:**
当前环境下，你需要通过以下方式访问这个文件：

1. **如果支持文件下载**: 请求下载文件 `{zip_path}`
2. **手动访问**: 在沙箱环境中执行 `cat {zip_path}` 查看内容（二进制文件无法直接查看）
3. **复制文件**: 将文件复制到可访问的位置

**目录结构预览:**
```
{workspace_name}/
├── blog.md
├── generated/
│   ├── images/
│   └── visual_prompts/
└── sources/
    ├── web/
    ├── code/
    └── manual_images/
```
"""
    except Exception as e:
        return f"❌ 打包失败: {str(e)}"


@tool
def get_workspace_file_list(
    workspace_dir: str = "/tmp/research_workspace",
    runtime: ToolRuntime = None
) -> str:
    """Get a detailed list of all files in the workspace with their sizes.
    
    Args:
        workspace_dir: The workspace root directory.
    
    Returns:
        Detailed file list with sizes.
    """
    ctx = runtime.context if runtime else new_context(method="get_workspace_file_list")
    
    # If workspace_dir is relative, make it under /tmp/
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    if not os.path.exists(workspace_dir):
        return f"Error: Workspace directory not found: {workspace_dir}"
    
    result = [f"# 工作目录文件清单\n"]
    result.append(f"**路径**: {workspace_dir}\n\n")
    
    total_size = 0
    file_count = 0
    
    def build_tree(path, prefix="", is_last=True):
        nonlocal total_size, file_count
        
        items = sorted(os.listdir(path))
        for i, item in enumerate(items):
            is_last_item = i == len(items) - 1
            item_path = os.path.join(path, item)
            
            connector = "└── " if is_last_item else "├── "
            result.append(f"{prefix}{connector}{item}")
            
            if os.path.isdir(item_path):
                extension = "    " if is_last_item else "│   "
                build_tree(item_path, prefix + extension, is_last_item)
            else:
                size = os.path.getsize(item_path)
                total_size += size
                file_count += 1
                result.append(f" ({size} bytes)\n")
    
    build_tree(workspace_dir)
    
    result.append(f"\n---\n")
    result.append(f"**统计信息**:\n")
    result.append(f"- 文件总数: {file_count}\n")
    result.append(f"- 总大小: {total_size / 1024:.2f} KB\n")
    
    return "\n".join(result)


@tool
def copy_specific_file(
    file_path: str,
    destination: str,
    workspace_dir: str = "/tmp/research_workspace",
    runtime: ToolRuntime = None
) -> str:
    """Copy a specific file from workspace to a destination for easier access.
    
    Args:
        file_path: Relative path from workspace root (e.g., 'blog.md', 'generated/images/diagram.png').
        destination: Destination path (e.g., '/tmp/my_blog.md').
        workspace_dir: The workspace root directory.
    
    Returns:
        Success message with the destination path.
    """
    ctx = runtime.context if runtime else new_context(method="copy_specific_file")
    
    # If workspace_dir is relative, make it under /tmp/
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    source_path = os.path.join(workspace_dir, file_path)
    
    if not os.path.exists(source_path):
        return f"Error: Source file not found: {source_path}"
    
    try:
        # Ensure destination directory exists
        dest_dir = os.path.dirname(destination)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)
        
        shutil.copy2(source_path, destination)
        
        file_size = os.path.getsize(destination)
        
        return f"""✅ 文件复制成功！

**源文件**: {source_path}
**目标文件**: {destination}
**文件大小**: {file_size} bytes

你现在可以访问 `{destination}` 来获取这个文件。
"""
    except Exception as e:
        return f"❌ 复制失败: {str(e)}"


@tool
def generate_blog_copy_instruction(
    workspace_dir: str = "/tmp/research_workspace",
    runtime: ToolRuntime = None
) -> str:
    """Generate instructions for users to copy all workspace content.
    
    Args:
        workspace_dir: The workspace root directory.
    
    Returns:
        Step-by-step instructions for copying workspace content.
    """
    ctx = runtime.context if runtime else new_context(method="generate_blog_copy_instruction")
    
    # If workspace_dir is relative, make it under /tmp/
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    workspace_name = os.path.basename(workspace_dir)
    
    return f"""# 📦 如何获取工作目录文件

## 方法 1: 打包下载（推荐）

智能体可以帮你将整个工作目录打包成 ZIP 文件。

**命令**:
```
调用 pack_workspace_to_zip 工具
```

**之后**:
```
下载生成的 ZIP 文件: /tmp/{workspace_name}.zip
```

---

## 方法 2: 单个文件复制

如果只需要特定文件（如 `blog.md`），可以单独复制：

**示例 - 复制博客文件**:
```
调用 copy_specific_file 工具
- file_path: "blog.md"
- destination: "/tmp/my_research_blog.md"
```

**示例 - 复制视觉提示词**:
```
调用 copy_specific_file 工具
- file_path: "generated/visual_prompts/architecture_diagram_prompt.md"
- destination: "/tmp/architecture_prompt.md"
```

---

## 方法 3: 查看文件内容

如果只是想查看文件内容，可以直接读取：

**命令**:
```
调用 read_file_content 工具
- file_path: "blog.md"
```

---

## 方法 4: 完整文件列表

查看工作目录中的所有文件：

**命令**:
```
调用 get_workspace_file_list 工具
```

---

## 💡 建议

1. **如果需要全部内容**: 使用方法 1（打包下载）
2. **如果只需要博客**: 使用方法 2 复制 `blog.md`
3. **如果需要特定图片/提示词**: 使用方法 2 复制相应文件
4. **如果只是预览**: 使用方法 3 或 4

---

**工作目录位置**: `{workspace_dir}`
**工作目录名称**: `{workspace_name}`
"""
