# PPT 大纲：DataURL-Agent 之 Crawler 模块实现详解 (个人贡献部分)

---

## 幻灯片 1：标题页

* **标题**：深入解析 DataURL-Agent：Crawler 模块的设计与实现
* **副标题**：自动化 OpenReview 论文元数据获取
* **汇报人**：（你的名字 - 负责 Crawler 模块）
* **课程**：数据挖掘期末 PJ

---

## 幻灯片 2：我的任务：Crawler 模块 - 职责与目标

* **在项目中的角色**：
    * 作为 DataURL-Agent 项目数据流的起点，负责“阶段 1：爬取与下载”中的核心数据抓取任务。
    * 我的目标是为后续的PDF下载和内容分析模块提供准确、全面的论文元数据。
* **我需要解决的关键问题**：
    * 如何从用户提供的 OpenReview URL（可能指向不同会议版块）中提取有效的API查询参数？
    * 如何与 OpenReview API 高效交互，处理分页，并获取所有相关论文的元数据？
    * 如何为每篇论文构建其对应的 PDF 下载链接？
    * 如何支持直接通过论文 ID 列表进行精确抓取？
* **预期输出**：一个包含详细元数据（尤其是 `pdf_url`）的Python列表，每个元素代表一篇论文。

---

## 幻灯片 3：Crawler 模块工作流程 (Mermaid / ChatGPT 流程图)

* **此处插入流程图** (建议用 Mermaid 或让 ChatGPT 根据以下逻辑生成)
    * **建议流程图逻辑节点**：
        1.  输入 (Conference URL / Paper IDs)
        2.  IF Conference URL: 调用 `parse_openreview_url`
            * 解析 Domain, Category, Conference Name
        3.  ELSE (Paper IDs): 准备 ID 列表
        4.  IF Conference URL: 调用 `Workspace_notes_from_url` (内部调用 `Workspace_notes_via_api`)
            * 构造 `venue`
            * API 调用循环 (处理分页: `offset`, `limit`)
            * 获取 Note List
        5.  ELSE (Paper IDs): 调用 `Workspace_notes_by_ids`
            * 遍历 ID 列表
            * 单次 API 调用 (按 ID)
            * 获取 Note
        6.  For each Note: 构造 `pdf_url`
        7.  汇总结果 (List of Dictionaries)
        8.  输出 (供 Downloader 使用)

* **Mermaid 示例代码 (供参考，你可以调整)**：

    ```mermaid
    graph TD
        A["输入: Conference URL / Paper IDs"] --> B{"输入类型判断"};
        B -- "Conference URL" --> C["调用 parse_openreview_url"];
        C --> D["解析: Domain, Category, Conf. Name"];
        D --> E["调用 fetch_notes_from_url"];
        B -- "Paper IDs" --> F["准备 Paper ID 列表"];
        F --> G["调用 fetch_notes_by_ids"];
        E --> H_CORE{"fetch_notes_via_api 核心"};
        H_CORE --> I["构造 API 参数 (venue, domain)"];
        I --> J["循环API调用 (处理分页)"];
        J --> K["获取论文 Note 列表"];
        G --> L["遍历ID列表"];
        L --> M["单次API调用 (by ID)"];
        M --> N["获取单个 Note"];
        K --> O_PROCESS["处理每个 Note"];
        N --> O_PROCESS;
        O_PROCESS --> P["构造 pdf_url"];
        P --> Q["汇总结果到列表"];
        Q --> R["输出: List of Dictionaries"];
    ```

---

## 幻灯片 4：实现细节1：智能解析 OpenReview URL

* **目标**：从多样化的 OpenReview URL 中提取 API 查询所需的 `domain`, `category`, `conference_name`。
* **核心代码**：`src/crawler.py` 中的 `parse_openreview_url` 函数。
* **代码片段展示**：
    ```python
    # src/crawler.py - parse_openreview_url 节选
    parsed_url = urlparse(url) # 使用 urllib.parse 分解 URL
    query_params = parse_qs(parsed_url.query)

    domain = query_params.get('id', [''])[0] # 提取 'id' 作为 domain

    fragment = parsed_url.fragment # 获取 #tag 后面的部分
    category = ''
    if fragment.startswith('tab-accept-'): # 判断是否为特定接收类型的tab
        category = fragment.replace('tab-accept-', '') # 提取 category

    # ... (conference_name 解析逻辑) ...
    return domain, category, conference_name
    ```
* **Debug/测试信息** (示例)：
    * 输入 URL: `https://openreview.net/group?id=ICLR.cc/2025/Conference#tab-accept-oral`
    * `logging.info(f"Extracted parameters: Domain={domain}, Category={category}, Venue={venue}")` 的输出：
        ```
        INFO:Extracted parameters: Domain=ICLR.cc/2025/Conference, Category=oral, Venue=ICLR 2025 Oral
        ```
    * 这一步确保了即使用户提供的是具体版块的链接，我们也能准确构建后续 API 查询。

---

## 幻灯片 5：实现细节2：与 OpenReview API 交互和分页处理

* **目标**：高效、完整地从 API 获取所有符合条件的论文元数据，并为每篇论文构建 PDF 下载链接。
* **核心代码**：`src/crawler.py` 中的 `Workspace_notes_via_api` 函数。
* **代码片段展示 (API 调用与分页逻辑)**：
    ```python
    # src/crawler.py - fetch_notes_via_api 节选
    params = {
        "content.venue": venue,
        "domain": domain,
        "limit": limit, # 来自 config.DEFAULT_API_LIMIT_PER_REQUEST
        "offset": 0
    }
    all_notes = []
    while True:
        # ... (max_total 检查与 limit 调整) ...
        resp = requests.get(config.API_URL, params=params, timeout=config.DOWNLOAD_TIMEOUT)
        resp.raise_for_status() # 检查 HTTP 错误
        data = resp.json()
        notes_batch = data.get("notes", [])

        if not notes_batch: break # 没有更多数据则跳出

        for note in notes_batch:
            # ... (max_total 检查) ...
            note_id = note.get('id')
            if note_id:
                note['pdf_url'] = f"[https://openreview.net/attachment?id=](https://openreview.net/attachment?id=){note_id}&name=pdf" # 构造 PDF URL
                all_notes.append(note)
        
        params['offset'] += limit # 更新 offset 实现分页
    ```
* **Debug/测试信息** (示例)：
    * `logging.info(f"Fetching notes from API: offset={params['offset']}, limit={params['limit']}")` 的输出：
        ```
        INFO:Fetching notes from API: offset=0, limit=1000
        INFO:Fetched 1000 notes in this batch (offset 0). Total fetched: 1000
        INFO:Fetching notes from API: offset=1000, limit=1000
        INFO:Fetched 800 notes in this batch (offset 1000). Total fetched: 1800
        INFO:No more notes found in API response.
        ```
    * 这显示了分页逻辑的正确执行以及 `pdf_url` 的成功构建。

---

## 幻灯片 6：实现细节3：多场景入口封装

* **目标**：提供简洁易用的上层函数，根据不同输入场景（单URL、多URL、ID列表）调用核心API交互逻辑。
* **核心代码**：`src/crawler.py` 中的 `Workspace_notes_from_url`, `Workspace_notes_from_urls`, `Workspace_notes_by_ids`。
* **代码片段展示 (`Workspace_notes_from_url` 示例)**：
    ```python
    # src/crawler.py - fetch_notes_from_url 节选
    def fetch_notes_from_url(url: str, limit: int = config.DEFAULT_API_LIMIT_PER_REQUEST, max_total: Optional[int] = None) -> List[Dict[str, Any]]:
        domain, category, conference_name = parse_openreview_url(url) # 调用URL解析
        if not domain:
            # ... (错误处理) ...
            return []
        
        venue = f"{conference_name} {category.capitalize()}" if category else conference_name # 构建 venue
        
        return fetch_notes_via_api(venue=venue, domain=domain, limit=limit, max_total=max_total) # 调用核心API函数
    ```
* **Debug/测试信息** (示例)：
    * 当运行 `python -m src.crawler` (其内部测试会调用 `Workspace_notes_from_urls`) 时，日志会显示：
        ```
        INFO:Processing URL: [https://openreview.net/group?id=ICLR.cc/2025/Conference#tab-accept-oral](https://openreview.net/group?id=ICLR.cc/2025/Conference#tab-accept-oral)
        INFO:Extracted parameters: Domain=ICLR.cc/2025/Conference, Category=oral, Venue=ICLR 2025 Oral
        INFO:Fetching notes from API: offset=0, limit=10 # (假设测试时 limit 较小)
        ...
        INFO:Processing URL: [https://openreview.net/group?id=NeurIPS.cc/2024/Conference#tab-accept-spotlight](https://openreview.net/group?id=NeurIPS.cc/2024/Conference#tab-accept-spotlight)
        ...
        INFO:Finished processing all URLs. Total unique notes: X
        ```
    * 这表明不同场景的函数能正确调用下层逻辑并汇总去重。

---

## 幻灯片 7：Crawler 模块总结与贡献

* **我实现的功能小结**：
    * 智能解析多样化的 OpenReview URL，提取关键参数。
    * 与 OpenReview API 高效通信，完整获取论文元数据，并处理了API分页。
    * 为每篇论文准确构建了后续下载所需的 `pdf_url`。
    * 封装了支持多种输入场景（单/多URL，ID列表）的接口。
* **遇到的挑战与解决方案** (可选，可以说一两个点)：
    * 例如：OpenReview URL 结构不完全统一，通过 `parse_openreview_url` 的细致解析来适应。
    * 例如：API 返回大量数据时的分页处理，通过循环和 `offset` 控制实现。
* **对项目的贡献**：
    * 为整个 DataURL-Agent 流水线提供了可靠的数据源头。
    * 确保了后续模块能够获取到准确的论文信息和 PDF 下载链接。
    * 模块设计考虑了灵活性和一定的健壮性。

---

## 幻灯片 8：Q & A

* 感谢！

---