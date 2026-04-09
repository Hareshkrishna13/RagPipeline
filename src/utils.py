"""Utility functions for configuration and validation."""

import logging
import os
from pathlib import Path
from typing import Any, Dict

import yaml

logger = logging.getLogger(__name__)


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config.yaml

    Returns:
        Configuration dictionary
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    logger.info(f"Configuration loaded from {config_path}")
    return config


def validate_file_extension(file_path: str) -> str:
    """
    Validate file extension and return file type.

    Args:
        file_path: Path to the file

    Returns:
        File type (pdf, txt, csv, docx, html)
    """
    valid_extensions = {
        ".pdf": "pdf",
        ".txt": "txt",
        ".csv": "csv",
        ".docx": "docx",
        ".doc": "docx",
        ".html": "html",
        ".htm": "html",
    }

    file_extension = Path(file_path).suffix.lower()

    if file_extension not in valid_extensions:
        raise ValueError(
            f"Unsupported file type: {file_extension}. "
            f"Supported types: {', '.join(valid_extensions.keys())}"
        )

    return valid_extensions[file_extension]


def validate_file_path(file_path: str) -> bool:
    """
    Validate that file exists.

    Args:
        file_path: Path to the file

    Returns:
        True if file exists
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    return True


def setup_logging(log_level: str = "INFO"):
    """
    Setup logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
