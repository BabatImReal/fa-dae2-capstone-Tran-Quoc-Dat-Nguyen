"""
Chunking strategies for document processing.
"""

import logging
import re

from langchain_text_splitters import RecursiveCharacterTextSplitter
import tiktoken

logger = logging.getLogger(__name__)


class ChunkingStrategy:
    """Base class for chunking strategies."""

    def chunk(self, text: str, **kwargs) -> list[str]:
        """Split text into chunks."""
        raise NotImplementedError


class SentenceChunking(ChunkingStrategy):
    """Simple sentence-based chunking."""

    def chunk(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
        """
        Split text into chunks based on sentences.

        Args:
            text: Input text to chunk
            chunk_size: Maximum characters per chunk
            overlap: Number of characters to overlap between chunks

        Returns:
            List of text chunks
        """
        # Split into sentences
        sentences = re.split(r"(?<=[.!?])\s+", text)

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # If adding this sentence would exceed chunk size, save current chunk
            if len(current_chunk) + len(sentence) + 1 > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                # Start new chunk with overlap
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + " " + sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence

        # Add the last chunk if it exists
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        logger.info(f"Created {len(chunks)} chunks using sentence-based chunking")
        return chunks


class TokenBasedChunking(ChunkingStrategy):
    """Token-based chunking using tiktoken for OpenAI models."""

    def chunk(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200,
        model: str = "text-embedding-3-small",
    ) -> list[str]:
        """
        Split text into chunks based on token count.

        Args:
            text: Input text to chunk
            chunk_size: Maximum tokens per chunk
            overlap: Number of tokens to overlap between chunks
            model: OpenAI model name for tokenizer

        Returns:
            List of text chunks
        """
        try:
            # Initialize tiktoken encoder
            encoder = tiktoken.encoding_for_model(model)

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=overlap,
                separators=["\n\n", "\n", " ", ""],
                length_function=lambda text: len(encoder.encode(text)),
            )

            chunks = text_splitter.split_text(text)

            # Note: tiktoken encoders don't need to be freed in newer versions

            logger.info(f"Created {len(chunks)} chunks using token-based chunking")
            return chunks

        except Exception as e:
            logger.error(f"Error in token-based chunking: {e}")
            # Fallback to sentence chunking
            logger.info("Falling back to sentence-based chunking")
            return SentenceChunking().chunk(text, chunk_size * 4, overlap * 4)  # Rough character conversion


class RecursiveChunking(ChunkingStrategy):
    """Recursive character-based chunking using LangChain."""

    def chunk(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
        """
        Split text into chunks using recursive character splitting.

        Args:
            text: Input text to chunk
            chunk_size: Maximum characters per chunk
            overlap: Number of characters to overlap between chunks

        Returns:
            List of text chunks
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )

        chunks = text_splitter.split_text(text)
        logger.info(f"Created {len(chunks)} chunks using recursive chunking")
        return chunks


class DocumentAwareChunking(ChunkingStrategy):
    """Structure-aware chunking that preserves document structure."""

    def chunk(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
        """
        Split text into chunks while preserving document structure.

        Args:
            text: Input text to chunk
            chunk_size: Maximum characters per chunk
            overlap: Number of characters to overlap between chunks

        Returns:
            List of text chunks
        """
        # Split by headers/sections first
        sections = re.split(r"\n(?=#+\s)", text)

        chunks = []
        current_chunk = ""

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # If section fits in current chunk, add it
            if len(current_chunk) + len(section) + 1 <= chunk_size:
                if current_chunk:
                    current_chunk += "\n" + section
                else:
                    current_chunk = section
            else:
                # Save current chunk if it exists
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())

                # If section is too large, split it further
                if len(section) > chunk_size:
                    # Use recursive chunking for large sections
                    recursive_chunker = RecursiveChunking()
                    section_chunks = recursive_chunker.chunk(section, chunk_size, overlap)
                    chunks.extend(section_chunks)
                    current_chunk = ""
                else:
                    current_chunk = section

        # Add the last chunk if it exists
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        logger.info(f"Created {len(chunks)} chunks using document-aware chunking")
        return chunks


def get_chunking_strategy(strategy_name: str) -> ChunkingStrategy:
    """Get a chunking strategy by name."""
    strategies = {
        "sentence": SentenceChunking(),
        "token": TokenBasedChunking(),
        "recursive": RecursiveChunking(),
        "document": DocumentAwareChunking(),
    }

    if strategy_name not in strategies:
        raise ValueError(f"Unknown chunking strategy: {strategy_name}. Available: {list(strategies.keys())}")

    return strategies[strategy_name]


def chunk_text(text: str, strategy: str = "sentence", **kwargs) -> list[str]:
    """
    Chunk text using the specified strategy.

    Args:
        text: Input text to chunk
        strategy: Chunking strategy name
        **kwargs: Additional arguments for the chunking strategy

    Returns:
        List of text chunks
    """
    chunker = get_chunking_strategy(strategy)
    return chunker.chunk(text, **kwargs)