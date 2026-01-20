"""
Main document processing pipeline for RAG systems.
"""

from datetime import datetime
import logging
from pathlib import Path
import re
from typing import Any
import unicodedata

from .chunking_strategies import chunk_text
from .text_extractor import extract_text

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Main document processing pipeline."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        chunking_strategy: str = "sentence",
        language: str = "en",
    ):
        """
        Initialize the document processor.

        Args:
            chunk_size: Maximum size for each chunk
            chunk_overlap: Overlap between chunks
            chunking_strategy: Strategy for chunking text
            language: Target language for processing
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunking_strategy = chunking_strategy
        self.language = language

    def preprocess_text(self, text: str) -> str:
        """
        Clean and normalize text for processing.

        Args:
            text: Raw text to preprocess

        Returns:
            Cleaned and normalized text
        """
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove special characters (keep alphanumeric, spaces, punctuation)
        text = re.sub(r"[^\w\s\.\,\!\?\;\:\-\(\)]", "", text)

        # Normalize unicode
        text = unicodedata.normalize("NFKD", text)

        # Remove excessive punctuation
        text = re.sub(r"[\.]{2,}", ".", text)

        # Remove page markers and headers
        text = re.sub(r"--- Page \d+ ---", "", text)

        return text.strip()

    def create_metadata(self, chunk: str, source_doc: str, chunk_index: int, total_chunks: int) -> dict[str, Any]:
        """
        Create metadata for a document chunk.

        Args:
            chunk: The text chunk
            source_doc: Source document path
            chunk_index: Index of this chunk
            total_chunks: Total number of chunks

        Returns:
            Metadata dictionary
        """
        return {
            "source": source_doc,
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "chunk_size": len(chunk),
            "chunk_size_tokens": len(chunk.split()),  # Rough token count
            "timestamp": datetime.now().isoformat(),
            "document_type": Path(source_doc).suffix.lower(),
            "language": self.language,
            "chunking_strategy": self.chunking_strategy,
        }

    def process_document(self, file_path: str, extractor_type: str = "auto") -> list[dict[str, Any]]:
        """
        Process a document and return chunks with metadata.

        Args:
            file_path: Path to the document file
            extractor_type: Type of text extractor to use

        Returns:
            List of chunks with metadata
        """
        logger.info(f"Processing document: {file_path}")

        # Extract text
        try:
            raw_text = extract_text(file_path, extractor_type)
            if not raw_text.strip():
                logger.warning(f"No text extracted from {file_path}")
                return []
        except Exception as e:
            logger.error(f"Failed to extract text from {file_path}: {e}")
            return []

        # Preprocess text
        cleaned_text = self.preprocess_text(raw_text)
        if not cleaned_text.strip():
            logger.warning(f"No text remaining after preprocessing {file_path}")
            return []

        # Chunk text
        try:
            chunks = chunk_text(
                cleaned_text,
                strategy=self.chunking_strategy,
                chunk_size=self.chunk_size,
                overlap=self.chunk_overlap,
            )
        except Exception as e:
            logger.error(f"Failed to chunk text from {file_path}: {e}")
            return []

        # Create chunks with metadata
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            if chunk.strip():  # Only include non-empty chunks
                metadata = self.create_metadata(chunk, file_path, i, len(chunks))
                processed_chunks.append({"text": chunk.strip(), "metadata": metadata})

        logger.info(f"Successfully processed {file_path}: {len(processed_chunks)} chunks created")
        return processed_chunks

    def process_multiple_documents(self, file_paths: list[str], extractor_type: str = "auto") -> list[dict[str, Any]]:
        """
        Process multiple documents and return all chunks with metadata.

        Args:
            file_paths: List of document file paths
            extractor_type: Type of text extractor to use

        Returns:
            List of all chunks with metadata
        """
        all_chunks = []

        for file_path in file_paths:
            chunks = self.process_document(file_path, extractor_type)
            all_chunks.extend(chunks)

        logger.info(f"Processed {len(file_paths)} documents: {len(all_chunks)} total chunks")
        return all_chunks

    def get_processing_stats(self, chunks: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Get statistics about processed chunks.

        Args:
            chunks: List of processed chunks

        Returns:
            Statistics dictionary
        """
        if not chunks:
            return {"total_chunks": 0}

        chunk_sizes = [len(chunk["text"]) for chunk in chunks]
        token_counts = [chunk["metadata"]["chunk_size_tokens"] for chunk in chunks]

        return {
            "total_chunks": len(chunks),
            "avg_chunk_size": sum(chunk_sizes) / len(chunk_sizes),
            "min_chunk_size": min(chunk_sizes),
            "max_chunk_size": max(chunk_sizes),
            "avg_token_count": sum(token_counts) / len(token_counts),
            "min_token_count": min(token_counts),
            "max_token_count": max(token_counts),
            "sources": list({chunk["metadata"]["source"] for chunk in chunks}),
        }