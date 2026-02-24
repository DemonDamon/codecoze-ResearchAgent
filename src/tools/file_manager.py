"""File management tool for research agent.

Manages the creation, saving, reading, and listing of files in the working directory.
"""

import os
import json
from typing import Optional
from pathlib import Path
from langchain.tools import tool
from langchain.tools import ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context


@tool
def create_workspace(output_dir: str, runtime: ToolRuntime = None) -> str:
    """Create the workspace directory structure for research.
    
    Args:
        output_dir: The root directory for the workspace. Can be absolute or relative path.
                   If relative, it will be relative to /tmp/ directory.
    
    Returns:
        Success message with the created directory paths.
    """
    ctx = runtime.context if runtime else new_context(method="create_workspace")
    
    # If output_dir is relative, make it under /tmp/
    if not os.path.isabs(output_dir):
        output_dir = os.path.join("/tmp", output_dir)
    
    # Create directory structure
    dirs = [
        output_dir,
        os.path.join(output_dir, "sources"),
        os.path.join(output_dir, "sources", "web"),
        os.path.join(output_dir, "sources", "code"),
        os.path.join(output_dir, "sources", "manual_images"),
        os.path.join(output_dir, "generated"),
        os.path.join(output_dir, "generated", "images"),
        os.path.join(output_dir, "generated", "visual_prompts"),
    ]
    
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    return f"Workspace created at: {output_dir}\nDirectory structure:\n" + "\n".join([f"  - {d}" for d in dirs])


@tool
def save_file(
    content: str,
    file_path: str,
    workspace_dir: str = "/tmp/research_workspace",
    runtime: ToolRuntime = None
) -> str:
    """Save content to a file in the workspace.
    
    Args:
        content: The content to save.
        file_path: Relative path from workspace root (e.g., 'sources/web/article_01.md').
        workspace_dir: The workspace root directory.
    
    Returns:
        Success message with the full file path.
    """
    ctx = runtime.context if runtime else new_context(method="save_file")
    
    # If workspace_dir is relative, make it under /tmp/
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    full_path = os.path.join(workspace_dir, file_path)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return f"File saved to: {full_path}"


@tool
def read_file_content(
    file_path: str,
    workspace_dir: str = "/tmp/research_workspace",
    runtime: ToolRuntime = None
) -> str:
    """Read content from a file in the workspace.
    
    Args:
        file_path: Relative path from workspace root (e.g., 'sources/web/article_01.md').
        workspace_dir: The workspace root directory.
    
    Returns:
        The file content.
    """
    ctx = runtime.context if runtime else new_context(method="read_file_content")
    
    # If workspace_dir is relative, make it under /tmp/
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    full_path = os.path.join(workspace_dir, file_path)
    
    if not os.path.exists(full_path):
        return f"Error: File not found: {full_path}"
    
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return content


@tool
def list_files(
    directory: str = "",
    workspace_dir: str = "/tmp/research_workspace",
    runtime: ToolRuntime = None
) -> str:
    """List files in a workspace directory.
    
    Args:
        directory: Relative path from workspace root (empty string means workspace root).
        workspace_dir: The workspace root directory.
    
    Returns:
        List of files and directories.
    """
    ctx = runtime.context if runtime else new_context(method="list_files")
    
    # If workspace_dir is relative, make it under /tmp/
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    full_path = os.path.join(workspace_dir, directory) if directory else workspace_dir
    
    if not os.path.exists(full_path):
        return f"Error: Directory not found: {full_path}"
    
    items = []
    for item in sorted(os.listdir(full_path)):
        item_path = os.path.join(full_path, item)
        if os.path.isdir(item_path):
            items.append(f"[DIR]  {item}/")
        else:
            size = os.path.getsize(item_path)
            items.append(f"[FILE] {item} ({size} bytes)")
    
    if not items:
        return f"Directory is empty: {full_path}"
    
    return f"Contents of {full_path}:\n" + "\n".join(items)


@tool
def get_workspace_structure(
    workspace_dir: str = "/tmp/research_workspace",
    runtime: ToolRuntime = None
) -> str:
    """Get the complete directory structure of the workspace.
    
    Args:
        workspace_dir: The workspace root directory.
    
    Returns:
        Tree structure of the workspace.
    """
    ctx = runtime.context if runtime else new_context(method="get_workspace_structure")
    
    # If workspace_dir is relative, make it under /tmp/
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    if not os.path.exists(workspace_dir):
        return f"Error: Workspace not found: {workspace_dir}"
    
    def build_tree(path, prefix=""):
        items = sorted(os.listdir(path))
        result = []
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            item_path = os.path.join(path, item)
            connector = "└── " if is_last else "├── "
            result.append(f"{prefix}{connector}{item}")
            if os.path.isdir(item_path):
                extension = "    " if is_last else "│   "
                result.extend(build_tree(item_path, prefix + extension))
        return result
    
    tree = [workspace_dir] + build_tree(workspace_dir)
    return "\n".join(tree)


@tool
def save_image_file(
    image_data: str,
    file_path: str,
    workspace_dir: str = "/tmp/research_workspace",
    runtime: ToolRuntime = None
) -> str:
    """Save image data to a file in the workspace.
    
    Args:
        image_data: Base64 encoded image data or URL of the image.
        file_path: Relative path from workspace root (e.g., 'sources/manual_images/architecture.png').
        workspace_dir: The workspace root directory.
    
    Returns:
        Success message with the full file path.
    
    Note:
        This is a placeholder tool. In actual implementation, you would:
        1. If image_data is a URL, download the image
        2. If image_data is base64, decode and save
        3. Save to the specified path
    """
    ctx = runtime.context if runtime else new_context(method="save_image_file")
    
    # If workspace_dir is relative, make it under /tmp/
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    full_path = os.path.join(workspace_dir, file_path)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    # Placeholder: Just create an empty file for now
    # In actual implementation, you would handle base64 decoding or URL download
    with open(full_path, 'wb') as f:
        pass
    
    return f"Image placeholder saved to: {full_path}\nNote: This is a placeholder. Implement actual image saving logic."
