# src/config.py

import os
from pathlib import Path
import dotenv

# 加载环境变量（如 OPENAI_API_KEY、FREE_API_ENDPOINT、FREE_API_MODEL）
dotenv.load_dotenv()

# ─── 项目根目录 ───────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ─── 本地论文 PDF 目录 ───────────────────────────────────────────────────────
# 假设将老师提供的压缩包解压后直接放到 data/papers 下
DATA_DIR = BASE_DIR / "data" / "papers"    # 所有 PDF 放在这里

# ─── 输出目录 ──────────────────────────────────────────────────────────────────
OUTPUT_DIR = BASE_DIR / "output"           # 最终 JSON、日志等都写到这里

# ─── 日志目录 ──────────────────────────────────────────────────────────────────
LOG_DIR = BASE_DIR / "logs"               # 若要记录日志文件，可写到这里

# ─── “是否自动下载”开关（可选） ─────────────────────────────────────────────────
# 如果为 True，就调用 run_crawl.py（crawler + downloader）从 OpenReview 拉取论文并下载 PDF；
# 否则直接用 data/papers/ 下已有的 PDF。
ENABLE_AUTO_DOWNLOAD = False

# ─── 下载/爬虫相关（仅在 ENABLE_AUTO_DOWNLOAD = True 时才需要） ────────────────────
API_URL = "https://api2.openreview.net/notes"
DEFAULT_API_LIMIT_PER_REQUEST = 1000
DEFAULT_DOWNLOAD_WORKERS = 5
DOWNLOAD_TIMEOUT = 60            # 下载单个 PDF 的超时时间（秒）
DOWNLOAD_CHUNK_SIZE = 8192       # 下载文件时的 chunk size
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# ─── LLM / AI 相关配置 ──────────────────────────────────────────────────────────
# 如果要用 OpenAI 官方 API，请在 .env 文件里填入：OPENAI_API_KEY
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL", "gpt-4")  # 或其他你想使用的模型

# 如果要用校园网免费 API，请在 .env 里填：
# FREE_API_ENDPOINT=http://10.176.40.135:8091/v1
# FREE_API_MODEL=qwen-7b-instruct
FREE_API_ENDPOINT = os.getenv("FREE_API_ENDPOINT", "")
FREE_API_MODEL    = os.getenv("FREE_API_MODEL", "qwen-7b-instruct")

# 从 PDF 文本中截取上下文时，URL 前后截取多少字符作为“标准上下文”
CONTEXT_WINDOW_SIZE = int(os.getenv("CONTEXT_WINDOW_SIZE", 800))

# ─── URL 校验相关 ──────────────────────────────────────────────────────────────
# HTTP 请求校验 URL 是否可访问时的超时时间（秒）
URL_TIMEOUT = int(os.getenv("URL_TIMEOUT", 5))

# ─── 并发/多线程配置 ────────────────────────────────────────────────────────────
# 用于 PDF 解析、URL 校验等环节的线程池大小
MAX_WORKERS = int(os.getenv("MAX_WORKERS", 5))

# ─── Batch 验证时每个请求的最大 URL 数（仅在 run_extract.py 调用 AI 验证时用到） ─────────
BATCH_VALIDATION_SIZE = int(os.getenv("BATCH_VALIDATION_SIZE", 5))

# ─── 默认文件名 ──────────────────────────────────────────────────────────────────
DEFAULT_METADATA_FILENAME = "metadata.json"        # Phase1 后保存 metadata 的文件名
DEFAULT_RESULTS_FILENAME  = "urls.json"            # Phase2 后保存所有 URLs 的文件名
FINAL_JSON_FILENAME       = "formatted_results.json"  # 最终格式化 JSON 的文件名
