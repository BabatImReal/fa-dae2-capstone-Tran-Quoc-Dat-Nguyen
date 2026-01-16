#!/usr/bin/env python3
"""
M04W03L01 Lab: Text Chunking for RAG Systems

This script demonstrates text chunking strategies for RAG systems.
Students will test different chunking approaches and then work with their own documents.
"""

import json
import logging
import os
import hashlib
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


def file_hash(path: str) -> str:
    """Return SHA256 hex digest for the given file path."""
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()


@click.command()
@click.option(
    "--file",
    "-f",
    "file_path",
    default="data/pdf",
    help="Path to a document file or folder containing documents to process (default: data/pdf)",
)
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
@click.option(
    "--file-types",
    "-ft",
    default="pdf,txt,docx,md",
    help="Comma-separated file types to process (default: pdf,txt,docx)",
)
@click.option(
    "--max-files",
    "-mf",
        default=0,
    type=int,
    help="Maximum number of latest files to process from folder (default: 0 => all)",
)
@click.option("--show-metadata", "-m", is_flag=True, help="Show detailed metadata for each chunk")
@click.option("--stats-only", is_flag=True, help="Show only processing statistics")
@click.option("--force", is_flag=True, help="Force reprocess files even if listed in process_json/processed_files.json")
@click.option("--output-dir", "-out", type=click.Path(), default="data/chunks", help="Directory to save individual chunk files (default: data/chunks)")
def main(
    file_path: str,
    strategy: str,
    extractor: str,
    file_types: str,
    max_files: int,
    force: bool,
    show_metadata: bool,
    stats_only: bool,
    output_dir: str,
):
    """
    Process documents for RAG systems.

    This tool extracts text from documents, preprocesses it, and splits it into
    chunks suitable for RAG systems. Supports PDF, Word, and text files.
    
    Can process a single file or all files in a folder (sorted by latest first).
    """

    # Validate file/folder exists
    if not os.path.exists(file_path):
        click.echo(f"Error: Path '{file_path}' not found.", err=True)
        sys.exit(1)

    # Get list of files to process
    files_to_process = []
    if os.path.isdir(file_path):
        # It's a folder - get all matching files sorted by modification time (latest first)
        allowed_types = tuple(f".{ft.lower().strip()}" for ft in file_types.split(","))
        
        for root, dirs, files in os.walk(file_path):
            for file in files:
                if file.lower().endswith(allowed_types):
                    full_path = os.path.join(root, file)
                    files_to_process.append((full_path, os.path.getmtime(full_path)))
        
        # Sort by modification time (latest first)
        files_to_process.sort(key=lambda x: x[1], reverse=True)

        # Limit to max_files (0 or negative => all files)
        if max_files and max_files > 0:
            files_to_process = files_to_process[:max_files]

        # Filter files against processed_files registry (SHA256)
        if force:
            click.echo("--force set: bypassing data/process_json/processed_files.json and processing all files")
            files_to_process = [fp for fp, _ in files_to_process]
        else:
            registry_path = Path("data") / "process_json" / "processed_files.json"
            processed = {}
            if registry_path.exists():
                try:
                    processed = json.loads(registry_path.read_text(encoding="utf-8"))
                except Exception:
                    processed = {}

            count_before = len(files_to_process)
            filtered_files = []
            for full_path, _ in files_to_process:
                # use basename as registry key (per recommendation)
                fname = os.path.basename(full_path)
                try:
                    h = file_hash(full_path)
                except Exception:
                    # if file cannot be read, skip it
                    continue

                if processed.get(fname) != h:
                    filtered_files.append(full_path)

            files_to_process = filtered_files

            skipped = count_before - len(files_to_process)

            if not files_to_process:
                click.echo(
                    "No new or changed files to process (based on process_json/processed_files.json)."
                )
                sys.exit(0)

            click.echo(
                f"📁 {len(files_to_process)} new/changed file(s) to process (skipped {skipped} up-to-date):"
            )
            for f in files_to_process:
                click.echo(f"   - {os.path.basename(f)}")
    else:
        # It's a single file
        files_to_process = [file_path]

    # Get environment variables (authoritative source)
    chunk_size = int(os.getenv("DEFAULT_CHUNK_SIZE"))
    overlap = int(os.getenv("DEFAULT_CHUNK_OVERLAP"))
    default_language = os.getenv("DEFAULT_LANGUAGE")

    try:
        # Initialize document processor
        processor = DocumentProcessor(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            chunking_strategy=strategy,
            language=default_language,
        )

        # Process all files
        all_chunks = []
        for file_to_process in files_to_process:
            click.echo(f"\n📄 Processing: {os.path.basename(file_to_process)}")
            logger.info(f"Processing document: {file_to_process}")
            logger.info(f"Using strategy: {strategy}, chunk_size: {chunk_size}, overlap: {overlap}")

            chunks = processor.process_document(file_to_process, extractor)

            if chunks:
                    # Ensure each chunk has a `metadata.source` set to the source basename (no ext)
                    src_base = os.path.splitext(os.path.basename(file_to_process))[0]
                    for c in chunks:
                        if "metadata" not in c or not isinstance(c["metadata"], dict):
                            c["metadata"] = {}
                        # set/overwrite source to canonical basename (no extension)
                        c["metadata"]["source"] = src_base

                    all_chunks.extend(chunks)
                    click.echo(f"   ✅ Created {len(chunks)} chunks")
            else:
                click.echo(f"   ⚠️  No chunks created for this file")

        if not all_chunks:
            click.echo("No chunks were created. Check the documents and try again.", err=True)
            sys.exit(1)

        # Display results
        if not stats_only:
            display_chunks(all_chunks, show_metadata)

        display_stats(all_chunks)

        # Save each chunk to individual JSON file
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Find the highest existing chunk ID so we can continue numbering from there
        highest_id = 0
        if output_path.exists():
            for existing_file in output_path.glob("chunk_*.json"):
                # Parse ID from filename: chunk_0001_source.json -> 0001
                parts = existing_file.stem.split("_")
                if len(parts) >= 2 and parts[1].isdigit():
                    try:
                        chunk_num = int(parts[1])
                        highest_id = max(highest_id, chunk_num)
                    except ValueError:
                        pass

        created_chunk_files = []
        for offset, chunk in enumerate(all_chunks, 1):
            # Continue numbering from highest existing ID
            i = highest_id + offset
            # Ensure metadata and source exist
            metadata = chunk.setdefault("metadata", {})
            source = metadata.get("source", "unknown")
            # Build deterministic chunk id and filename: chunk_{index}_{source}
            chunk_id = f"chunk_{i:04d}_{source}"
            chunk["id"] = chunk_id

            # Save using the chunk_id_source.json filename format
            safe_filename = f"{chunk_id}.json"
            chunk_filename = output_path / safe_filename
            with open(chunk_filename, "w", encoding="utf-8") as f:
                json.dump(chunk, f, indent=2, ensure_ascii=False)
            created_chunk_files.append(str(chunk_filename))

        click.echo(f"\n✅ {len(all_chunks)} chunks saved to: {output_path}/")

        # Update processed_files registry with hashes for processed input files
        try:
            registry_path = Path("data") / "process_json" / "processed_files.json"
            processed = {}
            if registry_path.exists():
                try:
                    processed = json.loads(registry_path.read_text(encoding="utf-8"))
                except Exception:
                    processed = {}

            for src in files_to_process:
                try:
                    fname = os.path.basename(src)
                    processed[fname] = file_hash(src)
                except Exception:
                    continue

            registry_path.parent.mkdir(parents=True, exist_ok=True)
            registry_path.write_text(json.dumps(processed, indent=2), encoding="utf-8")
        except Exception:
            logger.exception("Failed to update processed_files registry")

        # Write manifest of chunk files created in this run so embedding can pick them
        try:
            manifest_path = Path("data") / "process_json" / "last_processed_chunks.json"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(json.dumps(created_chunk_files, indent=2), encoding="utf-8")
        except Exception:
            logger.exception("Failed to write last_processed_chunks manifest")

        click.echo(f"\n✅ Successfully processed {len(files_to_process)} file(s)")
        click.echo(f"   Total chunks created: {len(all_chunks)} using {strategy} strategy")

    except Exception as e:
        logger.error(f"Error processing document: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()