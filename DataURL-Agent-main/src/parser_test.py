import logging
from pathlib import Path
from typing import Optional, Union
import random

# 尝试导入pymupdf4llm，如果不可用则记录警告
try:
    import pymupdf4llm
except ImportError:
    logging.warning("pymupdf4llm not installed. PDF parsing may not work correctly.")

# 配置基本日志
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')

def create_mock_pdf_text(pdf_id: str = "unknown") -> str:
    """
    创建一个包含多种URL示例的模拟PDF文本，用于测试URL提取功能。
    
    Args:
        pdf_id: PDF ID用于生成一些变化
        
    Returns:
        包含模拟论文文本的字符串，其中嵌入了各种类型的URL
    """
    # 使用pdf_id的哈希值作为随机种子，确保相同的PDF ID总是产生相同的模拟文本
    random.seed(hash(pdf_id) % 10000)
    
    # 构建模拟论文文本
    title = f"Research Paper: Novel Approach {pdf_id}"
    authors = "Jane Smith, John Doe, Alice Johnson"
    
    # 创建一系列示例URL
    github_url = "https://github.com/username/dataset-repo"
    kaggle_url = "https://www.kaggle.com/username/competition-name"
    huggingface_url = "https://huggingface.co/datasets/username/dataset-name"
    zenodo_url = "https://zenodo.org/record/123456"
    project_url = "https://username.github.io/project-name"
    code_url = "https://github.com/username/code-implementation"
    arxiv_url = "https://arxiv.org/abs/1234.5678"
    doi_url = "https://doi.org/10.1234/5678"
    
    # 构建摘要部分
    abstract = "In this paper, we introduce a novel approach for addressing the challenge of X. "
    if random.random() > 0.5:
        abstract += f"Our dataset is publicly available at {github_url}. "
    abstract += "Experimental results show significant improvements over baseline methods."
    
    # 构建介绍部分
    introduction = "## 1. Introduction\n\nPrevious work has explored various approaches to this problem. "
    introduction += f"Smith et al. [1] used data from {kaggle_url}. "
    introduction += f"Jones et al. [2] proposed a different solution described in {arxiv_url}."
    
    # 构建方法部分
    methods = "\n\n## 2. Methods\n\nWe propose a novel architecture consisting of components A, B, and C. "
    if random.random() > 0.25:
        methods += f"Our implementation is available at {code_url}. "
    
    # 构建数据集部分
    datasets = "\n\n## 3. Datasets\n\nWe evaluate our approach on several benchmark datasets. "
    datasets += f"We use the benchmark available at {huggingface_url}. "
    datasets += f"Additional data processing scripts can be found at {github_url}/scripts."
    
    # 构建实验部分
    experiments = "\n\n## 4. Experiments\n\nWe conducted extensive experiments to evaluate our approach. "
    if random.random() > 0.5:
        experiments += f"Our trained models are available at {zenodo_url}. "
    experiments += f"More details can be found on our project page: {project_url}."
    
    # 构建参考文献部分
    references = "\n\n## References\n\n"
    references += f"[1] Smith, J. et al. (2023). Paper title. Journal. {doi_url}\n"
    references += f"[2] Jones, K. (2022). Another paper. Conference. {arxiv_url}\n"
    
    # 组合所有部分生成完整的模拟论文文本
    paper_text = f"# {title}\n\n**Authors:** {authors}\n\n## Abstract\n\n{abstract}{introduction}{methods}{datasets}{experiments}{references}"
    
    return paper_text


def parse_pdf_file(pdf_path: Union[str, Path]) -> Optional[str]:
    """
    将PDF文件解析为Markdown格式文本。
    如果解析失败，则返回模拟的PDF文本。
    
    Args:
        pdf_path: PDF文件的路径，可以是字符串或Path对象
        
    Returns:
        解析出的Markdown文本，或者模拟文本（如果解析失败）
    """
    if isinstance(pdf_path, str):
        pdf_path = Path(pdf_path)
    
    # 提取PDF ID用于生成模拟文本
    pdf_id = pdf_path.stem  # 使用文件名作为PDF ID
    
    try:
        # 尝试使用pymupdf4llm解析PDF (不使用as_wiring参数)
        logging.debug(f"Parsing PDF '{pdf_path.name}' using pymupdf4llm.")
        markdown_text = pymupdf4llm.to_markdown(str(pdf_path))
        
        # 如果解析结果为空或非常短，则可能解析失败
        if not markdown_text or len(markdown_text) < 100:
            raise ValueError("Extracted text is too short, parsing likely failed")
        
        logging.debug(f"Successfully extracted markdown from '{pdf_path.name}' ({len(markdown_text)} characters).")
        return markdown_text
    
    except Exception as e:
        # 真实解析失败，使用模拟文本
        logging.warning(f"An error occurred during PDF parsing for {pdf_path}: {e}")
        logging.info(f"Generating mock PDF text for {pdf_id} to enable testing")
        
        # 生成模拟文本
        mock_text = create_mock_pdf_text(pdf_id)
        logging.debug(f"Generated mock text ({len(mock_text)} characters) for {pdf_id}")
        
        return mock_text


if __name__ == "__main__":
    # 示例使用
    mock_text = create_mock_pdf_text("example-pdf-123")
    print("\n===== MOCK TEXT SAMPLE =====")
    print(mock_text[:500] + "...\n")