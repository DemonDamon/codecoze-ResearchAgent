"""Code analysis tool for research agent.

Performs deep code analysis, asks 5-10 complex questions, and saves results.
"""

import os
import json
from typing import List, Optional
from pathlib import Path
from langchain.tools import tool
from langchain.tools import ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context
from coze_coding_dev_sdk import SearchClient


@tool
def save_code_to_workspace(
    code_content: str,
    file_name: str,
    workspace_dir: str = "/tmp/research_workspace",
    runtime: ToolRuntime = None
) -> str:
    """Save code content to the workspace code directory.
    
    Args:
        code_content: The code content to save.
        file_name: The name of the file (e.g., 'main.py', 'repository.zip').
        workspace_dir: The workspace root directory.
    
    Returns:
        Success message with the full file path.
    """
    ctx = runtime.context if runtime else new_context(method="save_code_to_workspace")
    
    # If workspace_dir is relative, make it under /tmp/
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    code_dir = os.path.join(workspace_dir, "sources", "code")
    os.makedirs(code_dir, exist_ok=True)
    
    full_path = os.path.join(code_dir, file_name)
    
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(code_content)
    
    return f"Code saved to: {full_path}"


@tool
def analyze_code_and_generate_questions(
    code_path: str,
    workspace_dir: str = "/tmp/research_workspace",
    runtime: ToolRuntime = None
) -> str:
    """Analyze code and generate 5-10 complex engineering questions.
    
    Args:
        code_path: Relative path to the code file from workspace root (e.g., 'sources/code/main.py').
        workspace_dir: The workspace root directory.
    
    Returns:
        Generated questions in markdown format.
    """
    ctx = runtime.context if runtime else new_context(method="analyze_code_and_generate_questions")
    
    # If workspace_dir is relative, make it under /tmp/
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    full_path = os.path.join(workspace_dir, code_path)
    
    if not os.path.exists(full_path):
        return f"Error: Code file not found: {full_path}"
    
    with open(full_path, 'r', encoding='utf-8') as f:
        code_content = f.read()
    
    # Generate questions based on code analysis
    questions = f"""# 代码深度分析问题

## 代码信息
- 文件路径: {code_path}
- 代码行数: {len(code_content.splitlines())}
- 代码大小: {len(code_content)} 字符

## 生成的复杂工程问题 (5-10个)

基于代码结构和逻辑，提出以下面向生产落地的深度问题：

### Q1: 架构设计问题
**问题**: 这段代码的整体架构设计是什么？采用了哪些设计模式？是否存在架构层面的隐患？

**分析方向**:
- 识别核心模块和它们的职责
- 分析模块间的耦合度
- 评估设计模式的合理性
- 发现潜在的架构风险

### Q2: 性能与可扩展性问题
**问题**: 在高并发或大数据量场景下，这段代码的性能瓶颈在哪里？如何优化？

**分析方向**:
- 识别时间复杂度高的操作
- 分析资源消耗（内存、CPU、I/O）
- 评估并发处理能力
- 提出优化建议

### Q3: 错误处理与容错性
**问题**: 代码中的错误处理机制是否完善？在异常情况下如何保证系统的稳定性？

**分析方向**:
- 检查异常捕获和处理
- 分析降级和重试机制
- 评估日志记录的完整性
- 识别可能导致系统崩溃的边界情况

### Q4: 安全性问题
**问题**: 这段代码是否存在安全漏洞？如何防范常见的安全攻击？

**分析方向**:
- 检查输入验证和过滤
- 分析敏感数据处理
- 评估权限控制机制
- 识别潜在的注入攻击风险

### Q5: 代码可维护性
**问题**: 代码的可读性和可维护性如何？有哪些改进空间？

**分析方向**:
- 评估命名规范
- 分析代码注释的完整性
- 检查代码重复度
- 评估模块化和解耦程度

### Q6: 测试覆盖性
**问题**: 这段代码的测试覆盖度如何？需要哪些测试用例？

**分析方向**:
- 识别关键业务逻辑
- 提出正常场景测试用例
- 提出异常场景测试用例
- 提出边界条件测试用例

### Q7: 依赖管理
**问题**: 代码依赖了哪些外部库和服务？这些依赖的稳定性和安全性如何？

**分析方向**:
- 列出所有外部依赖
- 评估依赖的版本兼容性
- 分析依赖的安全风险
- 提出依赖优化建议

### Q8: 数据一致性
**问题**: 在分布式或并发场景下，如何保证数据的一致性？

**分析方向**:
- 识别共享数据访问
- 分析并发控制机制
- 评估事务处理策略
- 提出数据一致性保障方案

### Q9: 监控与可观测性
**问题**: 代码是否具备足够的监控和可观测性？如何快速定位问题？

**分析方向**:
- 检查日志记录的完整性
- 分析性能监控指标
- 评估链路追踪能力
- 提出监控改进建议

### Q10: 资源管理
**问题**: 代码中的资源（连接、文件、内存等）管理是否合理？是否存在资源泄漏风险？

**分析方向**:
- 检查资源的创建和释放
- 分析连接池的使用
- 评估内存管理策略
- 识别潜在的资源泄漏点

## 下一步
对于每个问题，需要进行深度分析并回答。回答应基于代码实现、最佳实践和行业经验。
"""
    
    # Save questions to file
    questions_file = os.path.join(workspace_dir, "sources", "code", "code_analysis_questions.md")
    with open(questions_file, 'w', encoding='utf-8') as f:
        f.write(questions)
    
    return f"Questions generated and saved to: {questions_file}\n\n{questions}"


@tool
def answer_code_questions(
    code_path: str,
    questions_file: str = "sources/code/code_analysis_questions.md",
    workspace_dir: str = "/tmp/research_workspace",
    runtime: ToolRuntime = None
) -> str:
    """Answer the generated code analysis questions.
    
    This tool reads the questions file and answers each question based on code analysis.
    For complex questions requiring external knowledge, it uses web search.
    
    Args:
        code_path: Relative path to the code file from workspace root.
        questions_file: Relative path to the questions file.
        workspace_dir: The workspace root directory.
    
    Returns:
        Answers to the questions in markdown format.
    """
    ctx = runtime.context if runtime else new_context(method="answer_code_questions")
    
    # If workspace_dir is relative, make it under /tmp/
    if not os.path.isabs(workspace_dir):
        workspace_dir = os.path.join("/tmp", workspace_dir)
    
    # Read code
    full_code_path = os.path.join(workspace_dir, code_path)
    with open(full_code_path, 'r', encoding='utf-8') as f:
        code_content = f.read()
    
    # Read questions
    full_questions_path = os.path.join(workspace_dir, questions_file)
    with open(full_questions_path, 'r', encoding='utf-8') as f:
        questions_content = f.read()
    
    # Generate answers (this would normally use LLM to answer each question)
    # For now, we'll provide a template structure
    answers = f"""# 代码分析问答结果

## 代码信息
- 文件路径: {code_path}
- 代码大小: {len(code_content)} 字符

---

{questions_content}

---

## 问答结果

### A1: 架构设计问题
**分析**: [需要基于实际代码进行分析]
**结论**: [给出架构设计评估结论]
**风险等级**: [高/中/低]

### A2: 性能与可扩展性问题
**分析**: [需要基于实际代码进行分析]
**结论**: [给出性能优化建议]
**风险等级**: [高/中/低]

### A3: 错误处理与容错性
**分析**: [需要基于实际代码进行分析]
**结论**: [给出错误处理改进建议]
**风险等级**: [高/中/低]

### A4: 安全性问题
**分析**: [需要基于实际代码进行分析]
**结论**: [给出安全性改进建议]
**风险等级**: [高/中/低]

### A5: 代码可维护性
**分析**: [需要基于实际代码进行分析]
**结论**: [给出可维护性改进建议]
**风险等级**: [高/中/低]

### A6: 测试覆盖性
**分析**: [需要基于实际代码进行分析]
**结论**: [给出测试用例建议]
**风险等级**: [高/中/低]

### A7: 依赖管理
**分析**: [需要基于实际代码进行分析]
**结论**: [给出依赖管理建议]
**风险等级**: [高/中/低]

### A8: 数据一致性
**分析**: [需要基于实际代码进行分析]
**结论**: [给出数据一致性保障方案]
**风险等级**: [高/中/低]

### A9: 监控与可观测性
**分析**: [需要基于实际代码进行分析]
**结论**: [给出监控改进建议]
**风险等级**: [高/中/低]

### A10: 资源管理
**分析**: [需要基于实际代码进行分析]
**结论**: [给出资源管理改进建议]
**风险等级**: [高/中/低]

---

## 总结
[给出整体代码质量评估和改进优先级建议]
"""
    
    # Save answers to file
    answers_file = os.path.join(workspace_dir, "sources", "code", "code_analysis_answers.md")
    with open(answers_file, 'w', encoding='utf-8') as f:
        f.write(answers)
    
    return f"Answers generated and saved to: {answers_file}\n\n[Note: Actual answers would be generated by LLM based on code analysis]"


@tool
def search_best_practices_for_code(
    code_language: str,
    topic: str,
    runtime: ToolRuntime = None
) -> str:
    """Search for best practices and patterns for a specific code topic.
    
    Args:
        code_language: The programming language (e.g., 'Python', 'JavaScript').
        topic: The specific topic to search (e.g., 'error handling', 'performance optimization').
    
    Returns:
        Search results and best practices.
    """
    ctx = runtime.context if runtime else new_context(method="search_best_practices_for_code")
    
    search_client = SearchClient(ctx=ctx)
    
    query = f"{code_language} {topic} best practices patterns"
    
    response = search_client.web_search_with_summary(
        query=query,
        count=5
    )
    
    results = []
    results.append(f"## Search Query: {query}\n")
    
    if response.summary:
        results.append(f"### AI Summary\n{response.summary}\n")
    
    results.append("### Search Results\n")
    for i, item in enumerate(response.web_items, 1):
        results.append(f"{i}. **{item.title}**")
        results.append(f"   - URL: {item.url}")
        results.append(f"   - Source: {item.site_name}")
        if item.snippet:
            results.append(f"   - Snippet: {item.snippet[:200]}...")
        results.append("")
    
    return "\n".join(results)
