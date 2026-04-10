"""Main document processing pipeline using LangGraph."""

import logging
import sys
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from src.chunking import TextChunker
from src.loaders import load_file
from src.retriever import SemanticRetriever
from src.utils import (
    load_config,
    setup_logging,
    validate_file_extension,
    validate_file_path,
)

# Load environment variables
load_dotenv()

setup_logging("INFO")
logger = logging.getLogger(__name__)


class PipelineState(TypedDict):
    """State object for the document processing pipeline."""

    file_path: str
    text: str
    metadata: dict
    file_format: str
    chunks: list
    index_created: bool
    query: str
    top_k: int
    search_results: list
    error: str
    llm_summary: str


class DocumentPipelineGraph:
    """LangGraph-based document processing pipeline."""

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize the pipeline.

        Args:
            config_path: Path to configuration file
        """
        self.config = load_config(config_path)
        self.chunker = TextChunker(self.config)
        self.retriever = SemanticRetriever(self.config)
        self.index_dir = Path("faiss_indices")
        self.index_dir.mkdir(exist_ok=True)

        # Initialize LLM
        self.llm = self._initialize_llm()

        # Build the graph
        self.graph = self._build_graph()
        self.compiled_graph = self.graph.compile()

    def _initialize_llm(self):
        """Initialize the LLM based on environment configuration."""
        import os

        provider = os.getenv("LLM_PROVIDER", "anthropic").lower()

        if provider == "openai":
            logger.info("Using OpenAI LLM")
            return ChatOpenAI(
                model=os.getenv("OPENAI_MODEL", "gpt-4"),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            )
        elif provider == "anthropic":
            logger.info("Using Anthropic Claude LLM")
            return ChatAnthropic(
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            )
        elif provider == "groq":
            logger.info("Using Groq LLM")
            return ChatGroq(
                model=os.getenv("GROQ_MODEL", "mixtral-8x7b-32768"),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
                groq_api_key=os.getenv("GROQ_API_KEY"),
            )
        else:
            logger.warning(f"Unknown LLM provider: {provider}, using Anthropic")
            return ChatAnthropic(
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            )

    def _build_graph(self):
        """Build the LangGraph workflow."""
        graph = StateGraph(PipelineState)

        # Add nodes for each step
        graph.add_node("validate", self._validate_file)
        graph.add_node("load", self._load_document)
        graph.add_node("chunk", self._chunk_document)
        graph.add_node("index", self._create_index)
        graph.add_node("search", self._search_documents)
        graph.add_node("summarize", self._summarize_results)

        # Add edges (workflow connections)
        graph.set_entry_point("validate")

        graph.add_edge("validate", "load")
        graph.add_edge("load", "chunk")
        graph.add_edge("chunk", "index")

        # Conditional edge: if query provided, search; otherwise end
        graph.add_conditional_edges(
            "index",
            self._should_search,
            {"search": "search", "end": END},
        )

        graph.add_edge("search", "summarize")
        graph.add_edge("summarize", END)

        return graph

    def visualize_graph(self, output_file: str = "pipeline_graph.png"):
        """
        Visualize the graph structure.

        Args:
            output_file: Output file for visualization
        """
        try:
            # Get ASCII representation from compiled graph
            print("\n" + "=" * 80)
            print("LangGraph Pipeline Structure:")
            print("=" * 80)
            print(self.compiled_graph.get_graph().draw_ascii())
            print("=" * 80 + "\n")

            # Try to save PNG if graphviz is available
            try:
                png_data = self.compiled_graph.get_graph().draw_mermaid_png()
                with open(output_file, "wb") as f:
                    f.write(png_data)
                logger.info(f"Graph visualization saved to {output_file}")
            except Exception as e:
                logger.debug(f"Could not save PNG visualization: {e}")
                logger.info(
                    "Install graphviz for PNG visualization: " "pip install pygraphviz"
                )

        except Exception as e:
            logger.debug(f"Note: {e}. Continuing without visualization...")

    def _validate_file(self, state: PipelineState) -> PipelineState:
        """Validate the file path."""
        try:
            logger.info(f"Validating file: {state['file_path']}")
            validate_file_path(state["file_path"])
            file_format = validate_file_extension(state["file_path"])
            state["file_format"] = file_format
            state["error"] = ""
            return state
        except Exception as e:
            logger.error(f"Validation error: {e}")
            state["error"] = str(e)
            return state

    def _load_document(self, state: PipelineState) -> PipelineState:
        """Load the document."""
        try:
            logger.info(f"Loading document: {state['file_path']}")
            text, metadata = load_file(state["file_path"])
            logger.info(f"Document loaded, text length: {len(text)}")
            state["text"] = text
            state["metadata"] = metadata
            state["error"] = ""
            return state
        except Exception as e:
            logger.error(f"Loading error: {e}")
            state["error"] = str(e)
            return state

    def _chunk_document(self, state: PipelineState) -> PipelineState:
        """Chunk the document."""
        try:
            logger.info("Chunking document...")
            chunks = self.chunker.chunk_with_metadata(
                state["text"],
                state["metadata"],
                file_format=state["file_format"],
            )
            logger.info(f"Created {len(chunks)} chunks")
            state["chunks"] = chunks
            state["error"] = ""
            return state
        except Exception as e:
            logger.error(f"Chunking error: {e}")
            state["error"] = str(e)
            return state

    def _create_index(self, state: PipelineState) -> PipelineState:
        """Create FAISS index and add chunks."""
        try:
            logger.info("Creating FAISS index...")
            self.retriever.add_chunks(state["chunks"])
            logger.info("FAISS index created and embeddings generated")
            state["index_created"] = True
            state["error"] = ""
            return state
        except Exception as e:
            logger.error(f"Indexing error: {e}")
            state["error"] = str(e)
            state["index_created"] = False
            return state

    def _should_search(self, state: PipelineState) -> str:
        """Determine if we should search or end."""
        return "search" if state.get("query") else "end"

    def _search_documents(self, state: PipelineState) -> PipelineState:
        """Search for relevant documents."""
        try:
            if not state["index_created"]:
                state["error"] = "Index not created. Cannot search."
                state["search_results"] = []
                return state

            logger.info(f"Searching for: {state['query']}")
            results = self.retriever.retrieve(state["query"], state.get("top_k", 5))
            logger.info(f"Found {len(results)} results")
            state["search_results"] = results
            state["error"] = ""
            return state
        except Exception as e:
            logger.error(f"Search error: {e}")
            state["error"] = str(e)
            state["search_results"] = []
            return state

    def _summarize_results(self, state: PipelineState) -> PipelineState:
        """Summarize search results using LLM."""
        try:
            if not state["search_results"]:
                state["llm_summary"] = "No results to summarize."
                return state

            logger.info("Generating LLM summary of search results...")

            # Prepare context from search results
            context = "\n\n".join(
                [
                    f"Result {i + 1} (Similarity: "
                    f"{r['similarity_score']:.4f}):\n{r['content']}"
                    for i, r in enumerate(state["search_results"][:3])
                ]
            )

            # Create prompt for LLM
            prompt = (
                f"Based on the following search results for "
                f"the query \"{state['query']}\", "
                "provide a concise summary highlighting "
                "the key information:\n\n"
                f"Search Results:\n{context}\n\nSummary:"
            )
            # Call LLM
            response = self.llm.invoke(prompt)
            state["llm_summary"] = response.content
            logger.info("LLM summary generated successfully")
            return state

        except Exception as e:
            logger.error(f"Summarization error: {e}")
            state["llm_summary"] = f"Error generating summary: {str(e)}"
            return state

    def process_document(self, file_path: str) -> bool:
        """
        Process a document.

        Args:
            file_path: Path to the document

        Returns:
            True if successful
        """
        initial_state: PipelineState = {
            "file_path": file_path,
            "text": "",
            "metadata": {},
            "file_format": "",
            "chunks": [],
            "index_created": False,
            "query": "",
            "top_k": 5,
            "search_results": [],
            "error": "",
            "llm_summary": "",
        }

        result = self.compiled_graph.invoke(initial_state)
        return result.get("error") == ""

    def search(self, query: str, top_k: int = None) -> list:
        """
        Search for relevant chunks.

        Args:
            query: Search query
            top_k: Number of top results

        Returns:
            List of retrieved chunks
        """
        try:
            logger.info(f"Searching for: {query}")
            results = self.retriever.retrieve(query, top_k or 5)
            return results
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return []

    def search_with_summary(self, query: str, top_k: int = None) -> tuple:
        """
        Search for relevant chunks and get LLM summary.

        Args:
            query: Search query
            top_k: Number of top results

        Returns:
            Tuple of (results, summary)
        """
        try:
            logger.info(f"Searching with summary for: {query}")
            results = self.retriever.retrieve(query, top_k or 5)

            if not results:
                return results, "No results found."

            # Prepare context from search results
            context = "\n\n".join(
                [
                    f"Result {i + 1} (Similarity: "
                    f"{r['similarity_score']:.4f}):\n{r['content']}"
                    for i, r in enumerate(results[:3])
                ]
            )

            # Create prompt for LLM
            prompt = f"""Based on the following search results for the query "{query}",
provide a concise summary highlighting the key information:

Search Results:
{context}

Summary:"""

            # Call LLM
            response = self.llm.invoke(prompt)
            summary = response.content

            logger.info("LLM summary generated successfully")
            return results, summary

        except Exception as e:
            logger.error(f"Error during search with summary: {e}")
            return [], f"Error: {str(e)}"

    def save_index(self, index_name: str = "default"):
        """
        Save the FAISS index to disk.

        Args:
            index_name: Name for the saved index
        """
        try:
            self.retriever.save_index(str(self.index_dir / index_name))
            logger.info(f"Index saved as '{index_name}'")
            return True
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            return False

    def load_index(self, index_name: str = "default") -> bool:
        """
        Load a FAISS index from disk.

        Args:
            index_name: Name of the index to load

        Returns:
            True if successful
        """
        try:
            index_path = self.index_dir / index_name
            if not index_path.exists():
                logger.error(f"Index '{index_name}' not found")
                return False
            self.retriever.load_index(str(index_path))
            logger.info(f"Index '{index_name}' loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            return False

    def list_saved_indices(self) -> list:
        """
        List all saved indices.

        Returns:
            List of saved index names
        """
        if not self.index_dir.exists():
            return []
        return [d.name for d in self.index_dir.iterdir() if d.is_dir()]


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


def display_results_with_summary(results: list, summary: str):
    """
    Display search results with LLM summary.

    Args:
        results: List of retrieved chunks
        summary: LLM-generated summary
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

    # Display LLM Summary
    print(f"\n{'='*80}")
    print("AI-Generated Summary:")
    print(f"{'='*80}\n")
    print(summary)
    print(f"\n{'='*80}\n")


def main():
    """Main CLI interface using LangGraph pipeline."""
    try:
        print("\n" + "=" * 80)
        print("Document Processing Pipeline with LangGraph & FAISS")
        print("=" * 80 + "\n")

        config_path = "config/config.yaml"
        pipeline = DocumentPipelineGraph(config_path)

        # Show graph visualization
        pipeline.visualize_graph()

        # Check for saved indices
        saved_indices = pipeline.list_saved_indices()
        if saved_indices:
            print(f"\nSaved indices available: {', '.join(saved_indices)}")
            load_choice = input("Load an existing index? (y/n): ").strip().lower()
            if load_choice == "y":
                index_name = input(
                    f"Enter index name " f"({', '.join(saved_indices)}): "
                ).strip()
                if pipeline.load_index(index_name):
                    print("Index loaded successfully!\n")
                    query_mode = True
                else:
                    print("Failed to load index. Proceeding with new document.")
                    query_mode = False
            else:
                query_mode = False
        else:
            query_mode = False

        # If no index loaded, process a new document
        if not query_mode:
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

            # Offer to save the index
            save_choice = input("Save this index? (y/n): ").strip().lower()
            if save_choice == "y":
                index_name = input(
                    "Enter a name for this index (default 'default'): "
                ).strip()
                index_name = index_name or "default"
                pipeline.save_index(index_name)

        # Search loop
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

            use_summary = (
                input("Generate AI summary? (y/n, default: y): ").strip().lower()
            )
            use_summary = use_summary != "n"

            if use_summary:
                results, summary = pipeline.search_with_summary(query, top_k)
                display_results_with_summary(results, summary)
            else:
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
