"""Main document processing pipeline."""

import logging
import sys

from src.chunking import TextChunker
from src.loaders import load_file
from src.retriever import SemanticRetriever
from src.utils import (
    load_config,
    setup_logging,
    validate_file_extension,
    validate_file_path,
)

setup_logging("INFO")
logger = logging.getLogger(__name__)


class DocumentPipeline:
    """End-to-end document processing pipeline."""

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize the pipeline.

        Args:
            config_path: Path to configuration file
        """
        self.config = load_config(config_path)
        self.chunker = TextChunker(self.config)
        self.retriever = SemanticRetriever(self.config)
        self.document_loaded = False

    def process_document(self, file_path: str) -> bool:
        """
        Load and process a document.

        Args:
            file_path: Path to document file

        Returns:
            True if successful
        """
        try:
            validate_file_path(file_path)
            file_format = validate_file_extension(file_path)

            logger.info(f"Processing document: {file_path}")

            text, metadata = load_file(file_path)
            logger.info(f"Document loaded, text length: {len(text)}")

            chunks = self.chunker.chunk_with_metadata(
                text,
                metadata,
                file_format=file_format,
            )

            logger.info(f"Created {len(chunks)} chunks")

            self.retriever.add_chunks(chunks)
            logger.info("FAISS index created and embeddings generated")

            self.document_loaded = True
            return True

        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return False

    def search(self, query: str, top_k: int = None) -> list:
        """
        Search for relevant chunks.

        Args:
            query: Search query
            top_k: Number of top results

        Returns:
            List of retrieved chunks
        """
        if not self.document_loaded:
            logger.error("No document loaded. Load a document first.")
            return []

        try:
            logger.info(f"Searching for: {query}")
            results = self.retriever.retrieve(query, top_k)
            return results
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return []


def display_results(results: list):
    """
    Display search results.

    Args:
        results: List of retrieved chunks
    """
    if not results:
        print("\nNo results found.\n")
        return

    print(f"\n{'='*80}")
    print(f"Found {len(results)} relevant chunks:")
    print(f"{'='*80}\n")

    for i, result in enumerate(results, 1):
        print(f"Result #{i}")
        print(f"   Similarity Score: {result['similarity_score']:.4f}")
        print(f"   Distance: {result['distance']:.4f}")
        print(f"   Source: {result['metadata'].get('source', 'Unknown')}")
        print(
            f"   Chunk "
            f"{result['metadata'].get('chunk_index', 'N/A')} of "
            f"{result['metadata'].get('total_chunks', 'N/A')}"
        )
        print(f"\n   Content:\n{result['content'][:500]}...")
        print(f"\n{'-'*80}\n")


def main():
    """Main CLI interface."""
    try:
        print("\n" + "=" * 80)
        print("Document Processing Pipeline with FAISS")
        print("=" * 80 + "\n")

        config_path = "config/config.yaml"
        pipeline = DocumentPipeline(config_path)

        file_path = input(
            "Enter document path " "(PDF, TXT, CSV, DOCX, HTML): "
        ).strip()

        if not file_path:
            print("Invalid file path.")
            sys.exit(1)

        print(f"\nProcessing document: {file_path}")
        success = pipeline.process_document(file_path)

        if not success:
            print("Failed to process document.")
            sys.exit(1)

        print("Document processed successfully!\n")

        while True:
            query = input("Enter search query (or 'exit' to quit): ").strip()

            if query.lower() == "exit":
                print("\n Exiting...")
                break

            if not query:
                print("Invalid query.\n")
                continue

            top_k_str = input("Number of results (default 5): ").strip()
            top_k = int(top_k_str) if top_k_str else None

            results = pipeline.search(query, top_k)
            display_results(results)

    except KeyboardInterrupt:
        print("\n\n Interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
