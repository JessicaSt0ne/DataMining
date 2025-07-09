# DataURL-Agent 团队工作指南

本文档提供关于 DataURL-Agent 项目的工作分配、Git 协作流程及具体任务指南。

## 目录

1. [Git 协作指南](#git-协作指南)
2. [成员1：增强 AI 提示词](#成员1增强-ai-提示词)
3. [成员2：爬虫功能扩展](#成员2爬虫功能扩展)
4. [成员3：上下文预处理优化](#成员3上下文预处理优化)

## Git 协作指南

由于团队成员都是首次使用 Git 进行协作，以下是详细的操作指南：

### 初始设置

1. **安装 Git**：
   ```bash
   # Ubuntu/Debian
   sudo apt-get install git
   
   # macOS (需要先安装 Homebrew)
   brew install git
   
   # Windows
   # 下载并安装 Git for Windows: https://gitforwindows.org/
   ```

2. **设置个人信息**：
   ```bash
   git config --global user.name "你的名字"
   git config --global user.email "你的邮箱"
   ```

3. **克隆仓库**：
   ```bash
   git clone https://github.com/你的用户名/DataURL-Agent.git
   cd DataURL-Agent
   ```

### 基本工作流程

1. **创建自己的分支**：
   ```bash
   # 首先更新主分支
   git checkout main
   git pull
   
   # 创建并切换到自己的功能分支（使用有描述性的名称）
   git checkout -b 你的名字-功能名称
   # 例如: git checkout -b zhang-enhance-prompt
   ```

2. **进行修改**：
   - 根据分配的任务编辑相应文件
   - 定期进行提交，每个提交应该有明确的目的

3. **提交更改**：
   ```bash
   # 查看更改的文件
   git status
   
   # 添加更改到暂存区（用 . 表示所有更改，或指定文件）
   git add .
   # 或 git add src/validator.py
   
   # 提交更改
   git commit -m "简短描述你做了什么修改"
   ```

4. **推送到远程仓库**：
   ```bash
   # 第一次推送需要设置上游分支
   git push -u origin 你的分支名
   
   # 后续推送
   git push
   ```

5. **创建拉取请求(Pull Request)**：
   - 在 GitHub 网站上打开仓库
   - 点击 "Pull requests" 标签页
   - 点击 "New pull request" 按钮
   - 选择 base 分支为 main，compare 分支为你的分支
   - 点击 "Create pull request"
   - 填写标题和描述，然后点击 "Create pull request"

### 解决冲突

如果你的分支与主分支有冲突，请按照以下步骤解决：

1. **更新主分支**：
   ```bash
   git checkout main
   git pull
   ```

2. **将主分支合并到你的分支**：
   ```bash
   git checkout 你的分支名
   git merge main
   ```

3. **解决冲突**：
   - 打开有冲突的文件
   - 查找标记为 `<<<<<<< HEAD`、`=======` 和 `>>>>>>> main` 的部分
   - 手动编辑文件以解决冲突
   - 保存文件

4. **提交解决的冲突**：
   ```bash
   git add .
   git commit -m "解决与主分支的冲突"
   git push
   ```

### 常见问题解决

1. **撤销未提交的更改**：
   ```bash
   git checkout -- 文件名
   # 或撤销所有更改
   git checkout -- .
   ```

2. **撤销最后一次提交**：
   ```bash
   # 保留更改但撤销提交
   git reset --soft HEAD~1
   
   # 完全删除最后一次提交（谨慎使用！）
   git reset --hard HEAD~1
   ```

3. **查看提交历史**：
   ```bash
   git log
   # 或简洁视图
   git log --oneline
   ```

## 成员1：增强 AI 提示词

### 任务概述

改进 AI 验证模块的提示词，提供更多论文信息，以提高 URL 分类的准确性。

### 工作文件

主要修改 `src/validator.py` 文件中的提示词模板。

### 具体工作步骤

1. **分析当前提示词模板**:
   - 打开 `src/validator.py` 文件
   - 找到 `prompt_template` 变量（大约在第 40-70 行）
   - 理解当前提示词结构和内容

2. **设计增强提示词**:
   - 增加论文元数据信息（如标题、摘要、作者）
   - 添加更多关于数据集和基准测试的上下文说明
   - 提供更具体的分类指导（例如什么类型的链接更可能是数据集）

3. **实现提示词修改**:
   ```python
   prompt_template = PromptTemplate(
       input_variables=["url", "context", "paper_title", "paper_abstract"],  # 添加更多变量
       template="""
   分析以下来自研究论文的URL及其上下文。
   
   论文标题: {paper_title}
   论文摘要: {paper_abstract}
   
   确定该URL是否指向数据集、基准测试或代码仓库。
   
   数据集/基准测试URL应指向：
   - 数据存储库（GitHub、Zenodo、Hugging Face datasets等）
   - 数据集直接下载链接
   - 专注于数据集或基准测试的项目页面
   - 实现算法或包含评估代码的代码仓库
   
   不应被视为数据集/基准测试链接的URL：
   - 一般网站链接（如组织首页）
   - 论文引用链接
   - 社交媒体资料
   - 个人网页
   
   URL: {url}
   
   PDF中的上下文（Markdown格式）：
   ---
   {context}
   ---
   
   仅基于提供的URL和上下文，此URL是否可能作为数据集、基准测试或代码仓库链接？
   
   请仅以包含两个键的有效JSON对象回复：
   1. "is_intentional_link": 布尔值（如果它看起来像数据集/基准测试/代码链接则为true，否则为false）
   2. "reason": 字符串（如果是有意链接，提供数据集或基准测试或代码的描述；如果不是有意链接，提供为什么不是有意链接的原因）
   
   示例有效JSON响应：
   {{
     "is_intentional_link": true,
     "reason": "该URL指向GitHub仓库，包含论文中描述的数据集，有10,000个用于自然语言理解任务的标记示例。"
   }}
   
   另一个示例：
   {{
     "is_intentional_link": false,
     "reason": "该URL出现在引文列表中，指向期刊主页，而不是特定的数据集或代码资源。"
   }}
   
   您的JSON响应：
   """
   )
   ```

4. **修改 `validate_url_with_ai` 函数**:
   - 更新参数以接收更多论文元数据
   - 调整函数处理逻辑以使用新的提示词变量

5. **更新 `run_extract.py` 中的调用**:
   - 确保从元数据中提取所需信息
   - 将这些信息传递给验证函数

### 测试方法

1. 使用以下命令运行验证器测试:
   ```bash
   python -m src.validator
   ```

2. 手动检查几个示例URL的分类结果

## 成员2：爬虫功能扩展

### 任务概述

扩展爬虫模块，使其支持OpenReview的口头报告(oral)、海报(poster)和研讨会(workshop)论文。

### 工作文件

主要修改 `src/crawler.py` 文件。

### 具体工作步骤

1. **分析OpenReview页面结构**:
   - 研究不同类型论文页面的URL模式和HTML结构
   - 确定提取论文ID的模式差异

2. **修改 `crawler.py` 以支持多种类型**:
   - 添加会议类型检测功能
   ```python
   def detect_conference_type(url):
       """
       检测OpenReview会议URL的类型（oral、poster或workshop）
       
       Args:
           url: OpenReview会议URL
           
       Returns:
           字符串，表示会议类型："oral"、"poster"或"workshop"
       """
       if "accept-oral" in url or "oral" in url.lower():
           return "oral"
       elif "accept-poster" in url or "poster" in url.lower():
           return "poster"
       elif "workshop" in url.lower():
           return "workshop"
       else:
           return "unknown"
   ```

3. **实现新的抓取函数**:
   ```python
   def fetch_paper_ids_from_conference_page(conference_url):
       """
       从OpenReview会议页面提取论文ID
       
       Args:
           conference_url: OpenReview会议页面URL
           
       Returns:
           论文ID列表
       """
       conf_type = detect_conference_type(conference_url)
       # 针对不同类型实现不同的抓取逻辑
       # ...具体实现代码...
       return paper_ids
   ```

4. **更新 `run_crawl.py`**:
   - 添加会议URL参数选项
   - 实现从会议URL提取论文ID的逻辑

### 测试方法

1. 使用以下命令测试爬虫功能:
   ```bash
   # 测试口头报告页面
   python -m src.run_crawl --conference-url "https://openreview.net/group?id=ICLR.cc/2025/Conference#tab-accept-oral"
   
   # 测试海报页面
   python -m src.run_crawl --conference-url "https://openreview.net/group?id=ICLR.cc/2025/Conference#tab-accept-poster"
   ```

2. 验证生成的元数据文件是否包含预期的论文

## 成员3：上下文预处理优化

### 任务概述

优化URL上下文预处理，减少对AI API的调用，降低API使用量。

### 工作文件

主要修改 `src/extractor.py` 和 `src/run_extract.py` 文件。

### 具体工作步骤

1. **实现初步过滤机制**:
   - 修改 `src/extractor.py` 中的 `extract_candidate_links` 函数
   - 添加基于规则的预过滤逻辑

   ```python
   def is_likely_dataset_url(url, context):
       """
       基于简单规则判断URL是否可能是数据集链接
       
       Args:
           url: URL字符串
           context: URL周围的上下文
           
       Returns:
           布尔值，表示URL是否可能是数据集链接
       """
       # 检查URL域名
       dataset_domains = ["github.com", "gitlab.com", "zenodo.org", "huggingface.co", "figshare.com"]
       if any(domain in url.lower() for domain in dataset_domains):
           return True
           
       # 检查上下文中的关键词
       dataset_keywords = ["dataset", "数据集", "benchmark", "基准", "code", "代码", "repository", "仓库"]
       if any(keyword in context.lower() for keyword in dataset_keywords):
           return True
           
       return False
   ```

2. **更新URL提取逻辑**:
   ```python
   def extract_candidate_links(markdown_text):
       # 现有代码...
       
       for match in matches:
           # 提取URL和上下文
           # ...
           
           # 应用预过滤
           if is_likely_dataset_url(url, context):
               candidate_links.append({
                   'url': url,
                   'context': context,
                   'page_hint': page_hint
               })
       
       # 现有代码...
   ```

3. **实现批处理机制**:
   - 修改 `src/run_extract.py` 中的验证逻辑
   - 对URL进行分组处理，减少API调用次数

   ```python
   def batch_validate_links(candidate_links, batch_size=5):
       """
       批量验证URL，减少API调用
       """
       results = []
       for i in range(0, len(candidate_links), batch_size):
           batch = candidate_links[i:i+batch_size]
           # 构造批量上下文
           combined_context = "\n\n".join([f"URL: {link['url']}\n上下文: {link['context']}" for link in batch])
           # 进行一次AI调用处理多个URL
           # ...
       return results
   ```

### 测试方法

1. 使用以下命令测试优化效果:
   ```bash
   python -m src.run_extract --metadata ./data/metadata.json -o ./data/urls.json --verbose
   ```

2. 观察日志中的API调用次数和处理时间 