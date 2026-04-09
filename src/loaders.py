"""Document loaders for different file types."""

import logging
import os
from pathlib import Path

try:
    import pymupdf4llm
except ImportError:
    pymupdf4llm = None

try:
    import fitz
except ImportError:
    fitz = None

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    from docx import Document
except ImportError:
    Document = None

from langchain_community.document_loaders import TextLoader, WebBaseLoader

logger = logging.getLogger(__name__)


def load_pdf_pymupdf4llm(file_path: str) -> tuple:
    """
    Load PDF using pymupdf4llm.

    Args:
        file_path: Path to PDF file

    Returns:
        Tuple of (text, metadata)
    """
    if pymupdf4llm is None:
        raise ImportError("pymupdf4llm is not installed")

    logger.info(f"Loading PDF with pymupdf4llm: {file_path}")
    text = pymupdf4llm.to_markdown(file_path)

    metadata = {
        "source": file_path,
        "format": "pdf",
        "loader": "pymupdf4llm",
    }

    return text, metadata


def load_pdf_pymupdf(file_path: str) -> tuple:
    """
    Load PDF using pymupdf (fallback).

    Args:
        file_path: Path to PDF file

    Returns:
        Tuple of (text, metadata)
    """
    if fitz is None:
        raise ImportError("pymupdf (fitz) is not installed")

    logger.info(f"Loading PDF with pymupdf: {file_path}")
    doc = fitz.open(file_path)
    text = ""

    for page_num in range(len(doc)):
        page = doc[page_num]
        text += page.get_text()

    metadata = {
        "source": file_path,
        "format": "pdf",
        "loader": "pymupdf",
    }

    return text, metadata


def load_pdf(file_path: str) -> tuple:
    """
    Load PDF with fallback from pymupdf4llm to pymupdf.

    Args:
        file_path: Path to PDF file

    Returns:
        Tuple of (text, metadata)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    try:
        return load_pdf_pymupdf4llm(file_path)
    except Exception as e:
        logger.warning(f"pymupdf4llm failed: {e}, falling back to pymupdf")
        return load_pdf_pymupdf(file_path)


def load_csv(file_path: str) -> tuple:
    """
    Load CSV file.

    Args:
        file_path: Path to CSV file

    Returns:
        Tuple of (text, metadata)
    """
    if pd is None:
        raise ImportError("pandas is not installed")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    logger.info(f"Loading CSV: {file_path}")
    df = pd.read_csv(file_path)
    text = df.to_string()

    metadata = {
        "source": file_path,
        "format": "csv",
        "loader": "pandas",
        "rows": len(df),
        "columns": list(df.columns),
    }

    return text, metadata


def load_html(url: str) -> tuple:
    """
    Load HTML from URL.

    Args:
        url: URL to load

    Returns:
        Tuple of (text, metadata)
    """
    logger.info(f"Loading HTML from URL: {url}")
    loader = WebBaseLoader(url)
    docs = loader.load()

    if not docs:
        raise ValueError(f"No content loaded from URL: {url}")

    text = "\n".join([doc.page_content for doc in docs])

    metadata = {
        "source": url,
        "format": "html",
        "loader": "langchain",
    }

    return text, metadata


def load_txt(file_path: str) -> tuple:
    """
    Load TXT file.

    Args:
        file_path: Path to TXT file

    Returns:
        Tuple of (text, metadata)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"TXT file not found: {file_path}")

    logger.info(f"Loading TXT: {file_path}")
    loader = TextLoader(file_path)
    docs = loader.load()

    if not docs:
        raise ValueError(f"No content loaded from: {file_path}")

    text = "\n".join([doc.page_content for doc in docs])

    metadata = {
        "source": file_path,
        "format": "txt",
        "loader": "langchain",
    }

    return text, metadata


def load_docs(file_path: str) -> tuple:
    """
    Load DOCX file.

    Args:
        file_path: Path to DOCX file

    Returns:
        Tuple of (text, metadata)
    """
    if Document is None:
        raise ImportError("python-docx is not installed")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"DOCX file not found: {file_path}")

    logger.info(f"Loading DOCX: {file_path}")
    doc = Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])

    metadata = {
        "source": file_path,
        "format": "docx",
        "loader": "python-docx",
    }

    return text, metadata


def load_file(file_path: str) -> tuple:
    """
    Load any supported file type.

    Args:
        file_path: Path to file

    Returns:
        Tuple of (text, metadata)
    """
    file_extension = Path(file_path).suffix.lower()

    loaders = {
        ".pdf": load_pdf,
        ".csv": load_csv,
        ".html": load_html,
        ".htm": load_html,
        ".txt": load_txt,
        ".docx": load_docs,
        ".doc": load_docs,
    }

    if file_extension not in loaders:
        raise ValueError(f"Unsupported file type: {file_extension}")

    logger.info(f"Loading file: {file_path} (type: {file_extension})")
    return loaders[file_extension](file_path)
