#!/usr/bin/env python3
"""
M04W03L01 Lab: Text Chunking for RAG Systems

This script demonstrates text chunking strategies for RAG systems.
Students will test different chunking approaches and then work with their own documents.
"""

import json
import logging
import os
from pathlib import Path
import sys
from typing import Any

import click
from dotenv import load_dotenv

from service.document_processor import DocumentProcessor

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def display_chunks(chunks: list[dict[str, Any]], show_metadata: bool = False):
    """
    Display chunks in a formatted way.

    Args:
        chunks: List of chunks with metadata
        show_metadata: Whether to show metadata for each chunk
    """
    print(f"\n{'=' * 60}")
    print("DOCUMENT PROCESSING RESULTS")
    print(f"{'=' * 60}")
    print(f"Total chunks created: {len(chunks)}")
    print(f"{'=' * 60}\n")

    for i, chunk_data in enumerate(chunks, 1):
        chunk_text = chunk_data["text"]
        metadata = chunk_data["metadata"]

        print(f"CHUNK {i}/{len(chunks)}")
        print(f"Source: {metadata['source']}")
        print(f"Size: {metadata['chunk_size']} chars, {metadata['chunk_size_tokens']} tokens")
        print(f"Strategy: {metadata['chunking_strategy']}")
        print("-" * 40)
        print(chunk_text)
        print("-" * 40)

        if show_metadata:
            print("Metadata:")
            for key, value in metadata.items():
                print(f"  {key}: {value}")
            print()
        else:
            print()


def display_stats(chunks: list[dict[str, Any]]):
    """Display processing statistics."""
    if not chunks:
        print("No chunks to display statistics for.")
        return

    processor = DocumentProcessor()
    stats = processor.get_processing_stats(chunks)

    print(f"\n{'=' * 60}")
    print("PROCESSING STATISTICS")
    print(f"{'=' * 60}")
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"Average chunk size: {stats['avg_chunk_size']:.1f} characters")
    print(f"Chunk size range: {stats['min_chunk_size']} - {stats['max_chunk_size']} characters")
    print(f"Average token count: {stats['avg_token_count']:.1f} tokens")
    print(f"Token count range: {stats['min_token_count']} - {stats['max_token_count']} tokens")
    print(f"Sources processed: {len(stats['sources'])}")
    for source in stats["sources"]:
        print(f"  - {source}")
    print(f"{'=' * 60}\n")


@click.command()
@click.option(
    "--file",
    "-f",
    "file_path",
    required=True,
    help="Path to the document file to process",
)
@click.option(
    "--chunk-size",
    "-s",
    default=1000,
    help="Maximum size for each chunk (default: 1000)",
)
@click.option("--overlap", "-o", default=200, help="Overlap between chunks (default: 200)")
@click.option(
    "--strategy",
    "-st",
    default="sentence",
    type=click.Choice(["sentence", "token", "recursive", "document"]),
    help="Chunking strategy to use (default: sentence)",
)
@click.option(
    "--extractor",
    "-e",
    default="auto",
    type=click.Choice(["auto", "pdfplumber", "pymupdf"]),
    help="Text extractor to use (default: auto)",
)
@click.option("--show-metadata", "-m", is_flag=True, help="Show detailed metadata for each chunk")
@click.option("--stats-only", is_flag=True, help="Show only processing statistics")
@click.option("--output", "-out", type=click.Path(), help="Save chunks to a file (JSON format)")
def main(
    file_path: str,
    chunk_size: int,
    overlap: int,
    strategy: str,
    extractor: str,
    show_metadata: bool,
    stats_only: bool,
    output: str,
):
    """
    Process documents for RAG systems.

    This tool extracts text from documents, preprocesses it, and splits it into
    chunks suitable for RAG systems. Supports PDF, Word, and text files.
    """

    # Validate file exists
    if not os.path.exists(file_path):
        click.echo(f"Error: File '{file_path}' not found.", err=True)
        sys.exit(1)

    # Get environment variables
    default_chunk_size = int(os.getenv("DEFAULT_CHUNK_SIZE", chunk_size))
    default_overlap = int(os.getenv("DEFAULT_CHUNK_OVERLAP", overlap))
    default_language = os.getenv("DEFAULT_LANGUAGE", "en")

    # Use environment defaults if not specified
    if chunk_size == 1000:  # Default value
        chunk_size = default_chunk_size
    if overlap == 200:  # Default value
        overlap = default_overlap

    try:
        # Initialize document processor
        processor = DocumentProcessor(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            chunking_strategy=strategy,
            language=default_language,
        )

        # Process document
        logger.info(f"Processing document: {file_path}")
        logger.info(f"Using strategy: {strategy}, chunk_size: {chunk_size}, overlap: {overlap}")

        chunks = processor.process_document(file_path, extractor)

        if not chunks:
            click.echo("No chunks were created. Check the document and try again.", err=True)
            sys.exit(1)

        # Display results
        if not stats_only:
            display_chunks(chunks, show_metadata)

        display_stats(chunks)

        # Save to file if requested
        if output:
            # Default to chunking_output folder if no path specified
            if not os.path.dirname(output):
                output = f"chunking_output/{output}"

            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(chunks, f, indent=2, ensure_ascii=False)

            click.echo(f"Chunks saved to: {output_path}")

        click.echo(f"✅ Successfully processed {file_path}")
        click.echo(f"   Created {len(chunks)} chunks using {strategy} strategy")

    except Exception as e:
        logger.error(f"Error processing document: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()