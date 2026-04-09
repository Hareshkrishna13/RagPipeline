"""Text chunking functionality."""

import logging
from typing import Any, Dict, List

from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class TextChunker:
    """Split text into chunks with metadata."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the text chunker.

        Args:
            config: Configuration dictionary with chunking parameters
        """
        self.config = config
        self.chunking_config = config.get("chunking", {})

    def _get_chunk_params(self, file_format: str) -> dict:
        """
        Get chunk parameters for specific file format.

        Args:
            file_format: File format (pdf, txt, csv, docx, html)

        Returns:
            Dictionary with chunk_size and chunk_overlap
        """
        format_config = self.chunking_config.get(file_format, self.chunking_config)

        return {
            "chunk_size": format_config.get("chunk_size", 1000),
            "chunk_overlap": format_config.get("chunk_overlap", 100),
        }

    def chunk(
        self,
        text: str,
        file_format: str = "txt",
    ) -> List[str]:
        """
        Split text into chunks.

        Args:
            text: Text to split
            file_format: File format for config lookup

        Returns:
            List of text chunks
        """
        params = self._get_chunk_params(file_format)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=params["chunk_size"],
            chunk_overlap=params["chunk_overlap"],
        )

        chunks = splitter.split_text(text)
        logger.info(f"Split text into {len(chunks)} chunks " f"(format: {file_format})")

        return chunks

    def chunk_with_metadata(
        self,
        text: str,
        metadata: Dict[str, Any],
        file_format: str = "txt",
    ) -> List[Dict[str, Any]]:
        """
        Split text into chunks with metadata.

        Args:
            text: Text to split
            metadata: Document metadata
            file_format: File format for config lookup

        Returns:
            List of chunks with metadata
        """
        chunks = self.chunk(text, file_format)

        chunks_with_metadata = [
            {
                "content": chunk,
                "metadata": {
                    **metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                },
            }
            for i, chunk in enumerate(chunks)
        ]

        logger.info(f"Created {len(chunks_with_metadata)} chunks with metadata")
        return chunks_with_metadata
