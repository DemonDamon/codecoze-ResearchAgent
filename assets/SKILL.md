---
name: tech-blog-generator
description: 基于种子信息（关键词、URL、GitHub 仓库等）进行网络检索与资料爬取，然后生成图文并茂的中文技术博客。包含两个阶段：信息搜集（网络搜索、网页爬取、GitHub 仓库深度研究）和博客写作（结构化、带插图与 Lovart/NanoBanana 视觉描述提示词生成的信息图）。Use when the user wants to research a technical topic and generate a blog post, or mentions writing a tech blog, creating technical content, or deep-diving into a technology topic.
---

# Tech Blog Generator

基于种子信息进行深度研究，搜集充足资料后生成一篇高质量中文技术博客。

## 参数（用户输入）

用户需提供：
- **种子信息**（必选）：主题关键词、技术名称、论文标题等
- **参考 URL 列表**（可选）：相关博客/推文/文档的网页链接
- **GitHub 仓库地址**（可选）：`https://github.com/<owner>/<repo>`
- **输出目录**（可选）：博客物料与最终文件的存放路径

## 产物目录结构

所有产物落盘到一个工作目录（用户指定或默认 `~/tech-blog/<topic>/`）：

```
<output_dir>/
├── sources/                # 原始搜集资料
│   ├── search_summary.md   # 搜索结果摘要
│   ├── web/                # 网页爬取的 markdown 文件
│   ├── github/             # GitHub 研究资料
│   │   ├── <repo>/         # git clone 的仓库代码
│   │   ├── <repo>_deepwiki.md   # DeepWiki 问答记录
│   │   └── <repo>_code_analysis.md  # 本地代码分析记录
│   └── pdfs/               # 下载的 PDF 原文（如有）
├── images/                 # 博客用图（爬取/截图/生成）
├── visual-prompts/         # 视觉描述提示词（用于 Lovart/NanoBanana 生图）
└── blog.md                 # 最终技术博客
```

## 工作流程（严格按顺序执行）

### Phase 0: 澄清与确认

用不超过 5 个问题确认关键信息（已知则跳过）：

1. **主题**：技术博客的核心主题是什么？
2. **种子信息**：你目前有哪些初始资料（关键词/URL/GitHub 仓库/论文 PDF）？
3. **侧重点**：架构原理 / 工程实践 / 源码分析 / 论文解读 / 对比评测？
4. **目标读者**：算法研究 / 算法工程 / 平台架构 / 通用技术人员？
5. **输出路径**：博客产物存放在哪个目录？（默认 `~/tech-blog/<topic>/`）

> 能默认就默认，能推断就推断，不要反复确认。

确认后创建产物目录结构。

### Phase 1: 信息搜集（Research）

详细操作参考 [research-guide.md](research-guide.md)。

#### 1.1 网络搜索

使用搜索 MCP 工具，基于种子信息进行多轮检索：

**工具优先级**：
1. `bocha-search-mcp`（bocha_web_search / bocha_ai_search）— 首选，返回结构化摘要
2. `zhipu-web-search-sse`（webSearchPro / webSearchQuark）— 补充搜索，扩大覆盖面

**搜索策略**：
- 围绕主题构造 **5~8 组**不同角度的搜索 query（原理、实现、对比、最佳实践、踩坑经验、性能评测等）
- 每组 query 取 top 10 结果
- 将所有搜索结果的标题、URL、摘要汇总到 `sources/search_summary.md`
- 从结果中筛选出 **至少 10 篇**高价值页面进入下一步爬取

#### 1.2 网页爬取与落盘

使用 `basic-web-crawler` MCP 工具爬取筛选出的高价值页面：

**爬取数量要求：至少 10 篇网页**，其中应包含：
- 官方文档/官网页面（必须有）
- 技术博客/深度分析文章
- 对比评测/benchmark 文章
- 社区讨论/Issue 讨论

**工具选择策略**：
- 普通页面：`crawl_single_url` 直接爬取
- 需要质量检查的重要页面：`crawl_with_quality_check`
- JS 渲染页面（SPA/动态加载）：`smart_crawl_single_url`（自动切换浏览器模式）
- 批量爬取多个页面：`crawl_urls_from_text`

**落盘要求**：
- 每个页面保存为独立 `.md` 文件到 `sources/web/`
- 文件名格式：`<序号>_<简短标题>.md`
- 文件顶部记录来源 URL 和爬取时间
- 爬取图片保存到 `images/` 目录（供博客引用）

#### 1.3 官方页面截图（重要！）

对于**官方网站**、**产品主页**、**关键文档页面**，必须使用浏览器工具进行截图：

**方式 A — MCP 浏览器工具（单页逐步截取）：**
1. 使用 `browser_navigate` 打开官方页面
2. 使用 `browser_snapshot` 获取页面结构
3. 使用 `browser_take_screenshot` 截取关键内容区域
4. 将截图保存到 `images/` 目录，文件名格式：`screenshot_<简述>.png`
5. 在 `search_summary.md` 中记录截图路径与对应 URL

**方式 B — Playwright 批量截图工具：**
当需要截取 **3 个以上** 网站时，优先使用 `tools/capture_screenshots.py`：
```bash
python tools/capture_screenshots.py -o <output_dir>/images --tasks '[
  {"url": "<官网URL>", "name": "<项目名>_homepage", "scrolls": [0, 1, 2], "scroll_names": ["hero", "features", "details"]},
  {"url": "<文档URL>", "name": "<项目名>_docs", "full_page": true}
]'
```

**必须截图的页面类型**：
- 项目官网首页（展示产品定位/核心功能）
- 架构图/流程图/系统图（官方提供的可视化内容）
- Benchmark/评测结果页
- 关键 Demo/示例效果页

#### 1.4 GitHub 仓库深度研究（若提供了 GitHub 地址）

分为两步：**① git clone 代码到本地**，**② DeepWiki 架构研究**。

##### 1.4.1 git clone 代码到本地（必须！）

将仓库完整 clone 到 `sources/github/<repo>/` 目录，用于后续本地代码阅读与分析：

```bash
cd <output_dir>/sources/github/
git clone --depth 1 https://github.com/<owner>/<repo>.git
```

clone 完成后，使用本地文件系统工具（Read / Grep / Glob）进行代码研究：

1. **获取目录结构**：使用 `ls` 或 Glob 工具扫描项目布局
2. **阅读核心源码**：Read 工具读取入口文件、核心模块、抽象类/接口
3. **搜索关键实现**：Grep 工具搜索关键函数、类、配置项
4. **阅读配置与依赖**：requirements.txt / package.json / Dockerfile 等

**代码分析落盘**：将分析结果写入 `sources/github/<repo>_code_analysis.md`，包含：
- 目录结构树
- 核心模块列表（文件路径 + 一句话说明）
- 关键代码片段（带注释，标注文件路径和行号）
- 数据流与调用关系

##### 1.4.2 DeepWiki 架构研究

使用 DeepWiki MCP 工具，侧重架构理解与设计原理：

1. `read_wiki_structure` — 获取仓库文档结构
2. `read_wiki_contents` — 阅读关键文档
3. `ask_question` — 针对性提问（架构、设计决策、核心机制等，至少 5 个问题）
4. 所有问答落盘到 `sources/github/<repo>_deepwiki.md`（Q/A 编号格式）

**降级策略**：
- DeepWiki 不可用 → 用网络搜索补充仓库文档信息，加大本地代码分析力度

#### 1.5 深度技术提问：10 个面向生产落地的工程问题（核心环节！）

在完成上述信息搜集后，**必须**基于已有物料（网页资料 + 本地代码 + DeepWiki 分析），提出 **10 个复杂的、面向真实工程落地的技术问题**，然后逐一深入研究回答。

**目的**：暴露该技术在真实生产环境中的优缺点、工程难点和落地注意事项，让博客具备深度工程价值。

**问题设计要求**：
- 假设读者要**真正将该技术投入生产使用**
- 问题需覆盖以下维度（每维度 1~2 个问题）：
  1. **性能与可扩展性**：大规模数据/高并发下的表现？瓶颈在哪？
  2. **可靠性与容错**：失败模式有哪些？如何降级？
  3. **成本与资源**：LLM 调用成本？存储/计算开销？
  4. **适用边界**：什么场景适用？什么场景不适用？反例是什么？
  5. **集成复杂度**：与现有系统集成的难点？API 兼容性？
  6. **安全与合规**：数据隐私？内容安全？审计需求？
  7. **维护与演进**：版本升级成本？社区活跃度？长期维护风险？
  8. **与竞品对比**：相比同类方案的真实优劣？
  9. **关键依赖风险**：依赖哪些外部服务？这些依赖的稳定性？
  10. **工程实战陷阱**：常见踩坑点？文档中未提及但实际遇到的问题？

**执行流程**：
1. 列出 10 个问题，写入 `sources/github/<repo>_engineering_questions.md`
2. 对每个问题：
   - 先从已有物料（代码、网页、DeepWiki）中寻找答案
   - 若信息不足，用 DeepWiki `ask_question` 追问，或用搜索工具补充检索
   - 用 Grep 在本地代码中搜索相关实现
3. 每个问题写出详细回答（含代码引用、数据支撑）
4. 所有问答落盘到 `sources/github/<repo>_engineering_questions.md`

**落盘格式**：

```markdown
# <repo> 工程落地深度分析

## 研究基础
- 代码版本: <commit hash>
- 研究时间: <时间>
- 已有物料: <列出已参考的物料>

## Q1: <问题>
**分析**: <详细回答，含代码引用、数据、对比>
**结论**: <一句话结论>
**风险等级**: 高/中/低

## Q2: <问题>
...
```

#### 1.6 搜集完成检查

搜集阶段结束后，输出一份物料清单（勾选形式）：

```
物料清单：
- [x/  ] search_summary.md（搜索摘要）
- [x/  ] sources/web/ 下至少 10 篇网页 markdown
- [x/  ] images/ 下至少 3 张官方页面截图
- [x/  ] sources/github/<repo>/ 仓库代码已 clone
- [x/  ] sources/github/<repo>_code_analysis.md（代码分析）
- [x/  ] sources/github/<repo>_deepwiki.md（架构研究）
- [x/  ] sources/github/<repo>_engineering_questions.md（10 问深度分析）
```

确认物料充足后进入写作阶段。若关键材料不足，向用户说明并建议补充。

### Phase 2: 博客写作（Writing）

详细写作规范参考 [writing-guide.md](writing-guide.md)。

#### 2.1 物料盘点与图片资产审计（关键质量门禁！）

进入写作前，**必须**对已搜集的图片素材做一轮结构化审计。图片质量直接决定博客的"图文并茂"程度，审计不通过则自动触发补救。

##### 第一步：盘点所有图片

扫描 `images/` 目录下所有文件，对每张图片逐一分类：

| 分类 | 判定标准 | 标记 |
|------|---------|------|
| **A 级：高价值** | 官方截图、架构图、Benchmark 图表、产品界面、流程图 | ✅ 直接可用 |
| **B 级：可用** | 爬取的相关配图（logo、示意图等），内容与主题相关 | ⚠️ 可用但非核心 |
| **C 级：噪声** | 网站导航栏/页脚图标、广告图、无关装饰图、空白/损坏图片、favicon | ❌ 标记删除 |

将盘点结果写入一份简表（不需要落盘，心里有数即可）：
```
图片审计结果：
- A 级（高价值）: N 张  → [列出文件名和简述]
- B 级（可用）:   N 张  → [列出文件名]
- C 级（噪声）:   N 张  → [可删除]
- 合计可用（A+B）: N 张
```

##### 第二步：判定是否触发补救

按以下**量化门槛**判定图片资产是否达标：

| 检查项 | 达标标准 | 不达标则触发 |
|--------|---------|-------------|
| A 级图片数量 | **≥ 3 张** | 触发补救动作 1 或 2 |
| 可用图片总量（A+B） | **≥ 5 张** | 触发补救动作 1 或 2 |
| 噪声占比 | C 级占总量 **< 50%** | 先清理噪声，再评估是否需要补救 |
| 覆盖博客章节 | 至少覆盖 **3 个不同章节** 的配图需求 | 触发补救动作 1、2 或 3 |

> **一句话规则**：如果写博客时发现某个核心章节（架构图、评测结果、产品界面）找不到合适配图，就必须补救，不能硬写纯文字章节。

##### 第三步：自动补救动作

根据缺口类型，**按优先级依次执行**以下补救动作：

**补救动作 1 — 浏览器截图补充（首选）**

当缺少官方页面截图、产品界面、Benchmark 图表时：

```bash
# 回到 Phase 1 搜集的 URL 列表中，筛选出未截图的高价值页面
# 使用 tools/capture_screenshots.py 批量截取
python tools/capture_screenshots.py -o <output_dir>/images --tasks '[
  {"url": "<官网或文档URL>", "name": "<描述性名称>", "scrolls": [0, 1, 2], "scroll_names": ["hero", "features", "details"]},
  {"url": "<Benchmark页面URL>", "name": "benchmark", "full_page": true}
]'
```

或者用 MCP 浏览器工具逐页截取：
1. `browser_navigate` → 打开目标页面
2. `browser_snapshot` → 确认内容可见
3. `browser_take_screenshot` → 截取并保存到 `images/`

**补救动作 2 — PDF 关键页提取**

当用户提供了 PDF 种子（论文、白皮书、报告）但忘记提取配图时：

```bash
# 提取 PDF 中的架构图、评测表格、关键图表页
python tools/extract_pdf_pages.py <pdf_path> -o <output_dir>/images --mapping '{
  "<页码>": "<描述性文件名>"
}'
```

**补救动作 3 — 搜索补充高清图片**

当上述两种方式都无法满足时，通过搜索引擎寻找可用的高质量图片：
1. 用 `bocha_web_search` 搜索 `"<主题> architecture diagram"` / `"<主题> benchmark"` / `"<主题> screenshot"`
2. 从搜索结果中找到高质量图片的 URL
3. 用 `curl` 下载到 `images/` 目录
4. 记录图片来源 URL（博客中需注明出处）

**补救动作 4 — 生成视觉描述提示词（兜底但高质量）**

当外部图片实在无法获取时，基于已搜集的文字资料**生成视觉描述提示词**，由用户到 [Lovart.ai](https://lovart.ai) 平台用 NanoBanana Pro 模型生成高质量中文信息图。

**生成流程**（严格遵循 [protocols/text-to-visual-prompt.md](protocols/text-to-visual-prompt.md) 规约）：

1. 确定需要图表的章节内容（架构图、流程图、对比图、决策树等）
2. 按以下指令模板驱动 LLM 生成视觉描述提示词：

```
你现在的身份是【高级视觉信息设计师】。你的任务是将我提供的【文本/代码】转化为一段用于绘图的【中文视觉描述】。

请仔细阅读并严格执行 protocols/text-to-visual-prompt.md 中的所有定义，特别是以下两点：
1. **视觉化映射**：对于抽象逻辑，你需要主动想象并定义它的形状（如：判断用菱形）和布局（如：从上到下）。
2. **输出格式**：必须严格遵守规约中【Section 3 输出模板】的格式输出。

---
【待处理的输入内容】：
{{博客中需要可视化的文字内容/数据/逻辑}}
---

请开始处理，直接输出最终的中文解析结果，不要包含任何解释性废话。
```

3. 将生成的提示词保存到 `visual-prompts/<序号>_<图表简述>.txt`
4. 在 `blog.md` 中用占位符标记：`![<图表描述>](images/<序号>_<图表简述>.png)` + `<!-- 视觉描述提示词见 visual-prompts/<序号>_<图表简述>.txt，请在 lovart.ai 生成后替换 -->`

**适用场景**：
- 架构图 → 水平流 / 垂直流布局
- 流程图 → 垂直流 + 菱形判断分支
- 对比图 → 水平 VS 左右对称布局
- 决策树 → 垂直树状布局
- 时序图 → 水平时间线布局

> 视觉描述提示词生成的信息图质量远高于 mermaid，是首选的自绘图方案。官方截图和真实数据图仍然永远优先。

##### 第四步：补救后再次审计

执行补救动作后，**必须重新执行第一步和第二步**，确认图片资产达标后再进入写作。如果两轮补救后仍不达标，向用户说明缺口并给出建议。

---

同时盘点文字素材：
- 标注各资料的核心要点（供写作时快速定位）
- 梳理 10 问分析中的关键结论（融入博客的工程实践/局限章节）

#### 2.2 写作要求

- **语言**：中文
- **风格**：资深技术人员写作，面向工程/研究读者，信息密度高
- **结构**：由粗到细、先总览后拆解
- **篇幅**：默认 4000–6000 中文字（可按用户要求调整）

**内容框架**（按需裁剪）：
1. 背景与问题定义（要解决什么、为什么重要）
2. 方法/架构总览（系统级视角）
3. 核心模块拆解（每模块：输入输出、关键机制、复杂度）
4. 核心创新/亮点（为什么有效：直觉 + 机制 + 理论依据）
5. 工程实现要点（关键代码片段/伪代码、部署注意事项）
6. 实验/评测（指标、对比、消融实验）
7. **生产落地评估**（来自 10 问分析：适用场景、边界、成本、风险）
8. 局限与展望（可操作的改进方向）

**插图要求**：
- **优先使用官方页面截图**（`images/screenshot_*.png`）
- 其次使用爬取的原始图（`images/` 目录）
- Markdown 语法引用 `![描述](images/xxx.png)`
- 图下方写一句说明
- **禁止使用 mermaid**：需要自绘图表时，必须生成视觉描述提示词（参考 2.3 节），由用户到 Lovart.ai 用 NanoBanana Pro 生成高质量中文信息图
- 对于已有图片需要重绘优化的场景，参考 [protocols/image-to-visual-prompt.md](protocols/image-to-visual-prompt.md) 规约生成重绘提示词

**代码块**：
- 引用 clone 到本地的真实代码片段（标注文件路径）
- 仅放核心实现片段/伪代码
- 强调接口、数据流、关键 trick
- 代码要短，带注释

#### 2.3 视觉描述提示词生成（替代 Mermaid）

当博客需要架构图、流程图、对比图、决策树等自绘图表时，**不使用 mermaid**，而是生成视觉描述提示词，由用户在 [Lovart.ai](https://lovart.ai) 平台用 NanoBanana Pro 模型生成高质量中文信息图。

##### 生成规约

本 skill 在 `protocols/` 目录下提供两套规约：

| 规约文件 | 输入类型 | 使用场景 |
|---------|---------|---------|
| [text-to-visual-prompt.md](protocols/text-to-visual-prompt.md) | 文本/代码（Mermaid、自然语言流程描述、算法步骤等） | 将博客中的抽象逻辑转化为视觉描述提示词 |
| [image-to-visual-prompt.md](protocols/image-to-visual-prompt.md) | 已有图片（爬取的架构图、流程图等） | 对低质量/英文图片进行中文化重绘优化 |

##### 核心驱动指令

生成视觉描述提示词时，使用以下指令模板：

**场景 A — 文本转绘图（最常用）：**

```
你现在的身份是【高级视觉信息设计师】。你的任务是将我提供的【文本/代码】转化为一段用于绘图的【中文视觉描述】。

请仔细阅读并严格执行 protocols/text-to-visual-prompt.md 中的所有定义，特别是以下两点：
1. **视觉化映射**：对于抽象逻辑，你需要主动想象并定义它的形状（如：判断用菱形）和布局（如：从上到下）。
2. **输出格式**：必须严格遵守规约中【Section 3 输出模板】的格式输出。

---
【待处理的输入内容】：
{{博客中需要可视化的文字内容/数据/逻辑}}
---

请开始处理，直接输出最终的中文解析结果，不要包含任何解释性废话。
```

**场景 B — 图片重绘优化：**

```
你现在的身份是【高级视觉信息设计师】。你的任务是精确解析我提供的【架构图/流程图】，并转化为一段用于重绘的【中文视觉描述】。

请仔细阅读并严格执行 protocols/image-to-visual-prompt.md 中的所有定义，特别是以下两点：
1. **深度中文化**：所有通用描述必须翻译为中文，仅保留核心技术缩写和专有名词。
2. **输出格式**：必须严格遵守规约中【Section 3 解析输出模板】的格式输出。

---
【待处理的图片】：
{{附上需要重绘的图片}}
---

请开始处理，直接输出最终的中文解析结果，不要包含任何解释性废话。
```

##### 执行流程

1. **识别需图章节**：写作时标记需要自绘图表的章节（架构总览、流程说明、对比分析、选型决策等）
2. **生成提示词**：按上述指令模板生成视觉描述提示词
3. **落盘提示词**：保存到 `visual-prompts/<序号>_<图表简述>.txt`
4. **博客中占位**：在 `blog.md` 对应位置插入：
   ```markdown
   ![<图表描述>](images/<序号>_<图表简述>.png)
   *<图注说明>*
   <!-- 🎨 视觉描述提示词: visual-prompts/<序号>_<图表简述>.txt → 请在 lovart.ai 用 NanoBanana Pro 生成后替换 -->
   ```
5. **告知用户**：在交付时列出所有待生成的视觉描述提示词文件，提醒用户到 Lovart.ai 生成并替换

##### 质量要求

- 每个提示词必须包含完整的四段结构：`[主题与布局设想]` → `[视觉模块详解]` → `[风格与配色方案]` → `[技术参数建议]`
- 技术参数建议必须包含固定话术："文字必须清晰可辨。保持文字与背景的高对比度。建议 16:9 比例。2K 分辨率。使用标准流程图符号。矢量图风格，扁平化设计，专业学术论文图表风格。"
- 所有描述性内容必须为简体中文，仅保留核心技术缩写

---

#### 2.4 落盘与交付

最终博客保存为 `<output_dir>/blog.md`。

保存后在对话中回报：
- 最终保存路径
- 博客大纲（一级/二级标题列表）
- 引用的图片路径列表（含官方截图）
- **待生成的视觉描述提示词列表**（文件路径 + 简述，提醒用户到 Lovart.ai 生成）
- 主要参考资料列表

**不要在聊天中完整贴出文章内容**，以落盘文件为准。

## 执行约束

- **先搜集，后写作**：必须完成 Phase 1 再进入 Phase 2，不要边搜集边写
- **必须落盘**：所有中间产物和最终博客都必须写入磁盘文件
- **代码必须 clone**：涉及 GitHub 仓库的，必须 git clone 到本地，不能只用远程工具
- **至少 10 篇网页**：网页爬取不少于 10 篇，官方页面必须截图
- **10 问必须完成**：GitHub 仓库项目必须完成 10 个工程落地深度问题分析
- **爬取失败处理**：若网页爬取失败，记录失败原因，尝试替代方案（换工具/用搜索摘要替代）
- **图片处理**：官方页面必须截图保存，爬取图片也保存到 `images/`，博客中引用相对路径
- **图片质量门禁**：进入写作前必须通过 2.1 节的图片资产审计（A 级 ≥ 3 张，可用总量 ≥ 5 张），不达标则自动触发补救动作，补救后再次审计通过才能开始写作
- **不允许纯文字核心章节**：架构总览、评测对比、产品界面等核心章节必须有配图（截图/爬取图/视觉描述提示词生成图），不能全是文字
- **禁止使用 mermaid**：所有需要自绘的图表（架构图、流程图、对比图、决策树等）必须生成视觉描述提示词（参考 2.3 节），不使用 mermaid 代码块
- **视觉描述提示词规范**：每个提示词必须严格遵循 `protocols/text-to-visual-prompt.md` 规约的四段式输出模板，保存到 `visual-prompts/` 目录

## 附带规约文档

本 skill 在 `protocols/` 目录下提供两套视觉描述提示词生成规约，用于替代 mermaid 生成高质量中文信息图：

| 文件 | 用途 |
|------|------|
| [protocols/text-to-visual-prompt.md](protocols/text-to-visual-prompt.md) | **文本→绘图描述**：将文本/代码（Mermaid、流程描述、算法步骤等）转化为结构化中文视觉描述 |
| [protocols/image-to-visual-prompt.md](protocols/image-to-visual-prompt.md) | **图片→重绘描述**：解析已有架构图/流程图，生成中文化重绘提示词 |

生成的视觉描述提示词用于在 [Lovart.ai](https://lovart.ai) 平台用 NanoBanana Pro 模型生成高质量图表。详见 2.3 节。

## 附带工具脚本

本 skill 在 `tools/` 目录下提供两个通用 Python 工具，可在信息搜集阶段直接调用：

### tools/capture_screenshots.py — 浏览器批量截图

基于 Playwright 的通用浏览器截图工具，支持三种使用模式：

```bash
# 快速截取单个网站（自动滚动 3 屏）
python tools/capture_screenshots.py --url https://example.com -o <output_dir>/images

# JSON 配置文件批量截取多个网站
python tools/capture_screenshots.py --config screenshots.json

# 内联 JSON 任务
python tools/capture_screenshots.py -o <output_dir>/images --tasks '[
  {"url": "https://example.com", "name": "example", "scrolls": [0, 1, 2], "scroll_names": ["hero", "features", "footer"]},
  {"url": "https://docs.example.com", "name": "docs", "full_page": true}
]'
```

**依赖**：`pip install playwright && playwright install chromium`

**适用场景**：SKILL.md 1.3 节"官方页面截图"——当需要批量截取多个官方页面时，比逐一使用 `browser_navigate` + `browser_take_screenshot` 更高效。

### tools/extract_pdf_pages.py — PDF 页面提取

基于 PyMuPDF 的通用 PDF 页面提取工具，将指定页面导出为高清 PNG：

```bash
# 提取指定页面
python tools/extract_pdf_pages.py report.pdf --pages 1 2 5 8 -o <output_dir>/images

# 提取并自定义文件名
python tools/extract_pdf_pages.py report.pdf -o <output_dir>/images --mapping '{
  "1": "cover", "5": "architecture", "8": "benchmark"
}'

# 提取全部页面
python tools/extract_pdf_pages.py report.pdf --all -o <output_dir>/images

# 调整分辨率（默认 2x）
python tools/extract_pdf_pages.py report.pdf --pages 1 --zoom 3.0 -o <output_dir>/images
```

**依赖**：`pip install PyMuPDF`

**适用场景**：当用户提供了论文 PDF 或报告 PDF 作为种子信息时，用此工具提取关键页面为图片，保存到 `images/` 目录供博客引用。

## 附加参考

- 信息搜集阶段详细指南：[research-guide.md](research-guide.md)
- 博客写作阶段详细规范：[writing-guide.md](writing-guide.md)
