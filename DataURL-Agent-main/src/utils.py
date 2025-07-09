# src/utils.py

import os
from typing import List
from glob import glob
import logging

def init_logging():
    """
    在项目根目录下创建 logs/，并初始化日志配置。
    """
    # 这里可以调用 logging.basicConfig 之类的，或者直接在各模块 import logging 时统一设置
    pass

def list_all_pdfs(data_dir: str) -> List[str]:
    """
    返回 data_dir 目录下所有 .pdf 文件的完整路径列表。
    """
    pdf_paths = []
    for root, dirs, files in os.walk(data_dir):
        for f in files:
            if f.lower().endswith(".pdf"):
                pdf_paths.append(os.path.join(root, f))
    return pdf_paths
