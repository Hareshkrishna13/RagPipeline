"""Main loader orchestrator for all document types."""

from pathlib import Path
from typing import Union

from loaders import get_loader_by_file_type


class DocumentLoader:
    """Load documents from various file types."""

    def __init__(self):
        """Initialize the document loader."""
        pass

    def load(self, file_path: Union[str, Path]) -> str:
        """
        Load document from file path.

        Args:
            file_path: Path to the document file

        Returns:
            Extracted text content
        """
        file_path = str(file_path)
        loader_func = get_loader_by_file_type(file_path)
        content = loader_func(file_path)
        return content

    def load_url(self, url: str) -> str:
        """
        Load document from URL.

        Args:
            url: URL to fetch content from

        Returns:
            Extracted text content
        """
        from loaders import load_html

        content = load_html(url)
        return content
