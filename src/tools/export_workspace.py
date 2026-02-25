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

try:
    from coze_coding_dev_sdk.s3 import S3SyncStorage
    STORAGE_AVAILABLE = True
except ImportError:
    STORAGE_AVAILABLE = False


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

**下一步操作:**
请调用 `upload_and_generate_download_url` 工具将文件上传到云存储，获取可下载的链接。

**或者手动访问:**
当前环境下，你需要通过以下方式访问这个文件：
- 在沙箱环境中执行 `cat {zip_path}` 查看内容（二进制文件无法直接查看）

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
def upload_and_generate_download_url(
    file_path: str = "/tmp/research_workspace.zip",
    runtime: ToolRuntime = None
) -> str:
    """Upload a file to object storage and generate a download URL.
    
    Args:
        file_path: Path to the file to upload (e.g., "/tmp/research_workspace.zip").
    
    Returns:
        Download URL for the uploaded file.
    """
    ctx = runtime.context if runtime else new_context(method="upload_and_generate_download_url")
    
    # 检查是否在 Coze 平台
    is_coze_platform = bool(os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY"))
    
    if not is_coze_platform:
        # 本地模式：直接返回文件路径
        if not os.path.exists(file_path):
            return f"❌ 文件不存在: {file_path}"
        
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        
        return f"""📁 **本地模式 - 文件已准备好**

⚠️ 本地运行模式下，对象存储服务不可用。

**文件信息:**
- 文件名: {file_name}
- 文件大小: {file_size / 1024:.2f} KB
- 本地路径: {file_path}

**如何获取文件:**
1. 直接访问本地路径: `{file_path}`
2. 使用文件管理器打开目录
3. 或在终端执行: `open {os.path.dirname(file_path)}` (macOS) / `explorer {os.path.dirname(file_path)}` (Windows)

**提示:** 如需云存储功能，请部署到 Coze 平台。
"""
    
    if not STORAGE_AVAILABLE:
        return """❌ 对象存储功能当前不可用。

请尝试以下替代方案：
1. 使用 `copy_specific_file` 工具将文件复制到可访问的位置
2. 使用 `read_file_content` 工具查看文件内容
3. 直接在沙箱环境中访问文件
"""
    
    # Check if file exists
    if not os.path.exists(file_path):
        return f"❌ 文件不存在: {file_path}"
    
    try:
        # Initialize storage client
        storage = S3SyncStorage(
            endpoint_url=os.getenv("COZE_BUCKET_ENDPOINT_URL"),
            access_key="",
            secret_key="",
            bucket_name=os.getenv("COZE_BUCKET_NAME"),
            region="cn-beijing",
        )
        
        # Get file name
        file_name = os.path.basename(file_path)
        
        # Upload file
        with open(file_path, 'rb') as f:
            file_key = storage.stream_upload_file(
                fileobj=f,
                file_name=file_name,
                content_type="application/zip",
            )
        
        # Generate presigned URL (valid for 1 hour)
        download_url = storage.generate_presigned_url(
            key=file_key,
            expire_time=3600  # 1 hour
        )
        
        file_size = os.path.getsize(file_path)
        
        return f"""🎉 **文件已上传！可点击链接下载**

**文件信息:**
- 文件名: {file_name}
- 文件大小: {file_size / 1024:.2f} KB
- 存储密钥: {file_key}

**下载链接（1小时内有效）:**
📥 [{file_name}]({download_url})

**使用说明:**
1. 点击上面的链接即可下载文件
2. 链接有效期 1 小时，过期后可重新生成
3. 下载后使用任何压缩工具解压即可

**提示:** 请尽快下载，链接将在 1 小时后过期。
"""
    except Exception as e:
        return f"""❌ 上传失败: {str(e)}

请尝试以下替代方案：
1. 检查文件路径是否正确: {file_path}
2. 使用 `copy_specific_file` 工具将文件复制到可访问的位置
3. 查看错误详情并联系技术支持
"""


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
    zip_path = os.path.join("/tmp", f"{workspace_name}.zip")
    
    return f"""# 📦 如何获取工作目录文件

## ⭐ 推荐方法：一键下载（超简单！）

**步骤 1**: 先打包文件
```
调用 pack_workspace_to_zip 工具
```

**步骤 2**: 上传并获取下载链接
```
调用 upload_and_generate_download_url 工具
- file_path: "{zip_path}"
```

**步骤 3**: 点击链接下载！
你将得到一个可点击的下载链接，直接点击即可下载 ZIP 文件。

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

## 💡 使用建议

1. **推荐**: 使用"推荐方法"，一键打包并获取下载链接
2. **快速**: 如果只需要博客，使用方法 2 复制 `blog.md`
3. **预览**: 如果只是想看看内容，使用方法 3
4. **浏览**: 如果想看看有哪些文件，使用方法 4

---

**工作目录位置**: `{workspace_dir}`
**工作目录名称**: `{workspace_name}`
"""
