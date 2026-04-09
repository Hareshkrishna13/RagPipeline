"""Retriever with HuggingFace embeddings and FAISS vector store."""

import logging
import os
from typing import Any, Dict, List

import numpy as np
from sentence_transformers import SentenceTransformer

try:
    import faiss
except ImportError:
    faiss = None

logger = logging.getLogger(__name__)


class SemanticRetriever:
    """Retrieve chunks using semantic similarity with FAISS."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the semantic retriever with FAISS.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.embedding_config = config.get("embeddings", {})
        self.retrieval_config = config.get("retrieval", {})

        model_name = self.embedding_config.get("model", "all-MiniLM-L6-v2")
        device = self.embedding_config.get("device", "cpu")

        logger.info(f"Loading embedding model: {model_name} on {device}")
        self.model = SentenceTransformer(model_name, device=device)

        self.chunks = []
        self.embeddings = None
        self.faiss_index = None
        self.embedding_dim = 384

    def add_chunks(self, chunks_with_metadata: List[Dict[str, Any]]):
        """
        Add chunks to retriever and create FAISS index.

        Args:
            chunks_with_metadata: List of chunks with metadata
        """
        if faiss is None:
            raise ImportError("faiss-cpu is not installed")

        self.chunks = chunks_with_metadata

        chunk_texts = [chunk["content"] for chunk in chunks_with_metadata]

        logger.info(f"Generating embeddings for {len(chunk_texts)} chunks")
        self.embeddings = self.model.encode(
            chunk_texts,
            show_progress_bar=True,
        )

        self.embeddings = np.array(self.embeddings).astype("float32")
        self.embedding_dim = self.embeddings.shape[1]

        logger.info(f"Creating FAISS index with dimension {self.embedding_dim}")
        self.faiss_index = faiss.IndexFlatL2(self.embedding_dim)
        self.faiss_index.add(self.embeddings)

        logger.info(f"FAISS index created with {len(self.chunks)} vectors")

    def retrieve(
        self,
        query: str,
        top_k: int = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve top-k most similar chunks using FAISS.

        Args:
            query: Query text
            top_k: Number of top results to return

        Returns:
            List of most similar chunks with scores
        """
        if self.faiss_index is None or len(self.chunks) == 0:
            logger.warning("No chunks available for retrieval")
            return []

        if top_k is None:
            top_k = self.retrieval_config.get("top_k", 5)

        logger.info(f"Retrieving top {top_k} chunks for query: {query}")
        query_embedding = self.model.encode([query])
        query_embedding = np.array(query_embedding).astype("float32")

        distances, indices = self.faiss_index.search(query_embedding, top_k)
        distances = distances[0]
        indices = indices[0]

        results = []
        for idx, distance in zip(indices, distances):
            if idx < len(self.chunks):
                similarity_score = 1 / (1 + distance)
                results.append(
                    {
                        "content": self.chunks[idx]["content"],
                        "metadata": self.chunks[idx]["metadata"],
                        "distance": float(distance),
                        "similarity_score": float(similarity_score),
                    }
                )

        logger.info(f"Retrieved {len(results)} relevant chunks")
        return results

    def retrieve_all(self) -> List[Dict[str, Any]]:
        """
        Get all chunks.

        Returns:
            All chunks with metadata
        """
        return self.chunks

    def save_index(self, index_path: str):
        """
        Save FAISS index to disk.

        Args:
            index_path: Path to save index
        """
        if self.faiss_index is None:
            logger.warning("No index to save")
            return

        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        faiss.write_index(self.faiss_index, index_path)
        logger.info(f"FAISS index saved to {index_path}")

    def load_index(
        self,
        index_path: str,
        chunks_path: str,
    ):
        """
        Load FAISS index from disk.

        Args:
            index_path: Path to index file
            chunks_path: Path to chunks metadata file
        """
        if faiss is None:
            raise ImportError("faiss-cpu is not installed")

        import pickle

        self.faiss_index = faiss.read_index(index_path)

        with open(chunks_path, "rb") as f:
            self.chunks = pickle.load(f)

        logger.info(f"FAISS index loaded from {index_path}")
