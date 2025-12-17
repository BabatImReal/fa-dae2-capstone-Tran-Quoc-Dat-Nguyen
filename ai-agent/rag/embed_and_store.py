#!/usr/bin/env python3
"""
M04W03L02 Lab: Embed and Store Chunks in Pinecone

This script demonstrates how to:
1. Load chunked documents from the text chunking lab
2. Generate embeddings using OpenAI
3. Store embeddings in Pinecone vector database
4. Test similarity search functionality

Following the RAG architecture pattern from M04W03L02__rag_architecture.md
"""

import json
import os
import sys
from typing import Any

import click
from dotenv import load_dotenv

# Using Pinecone's built-in embedding instead of OpenAI
from pinecone import Pinecone

# Load environment variables
load_dotenv()


class PineconeEmbedder:
    """Handles embedding generation and Pinecone storage for RAG systems."""

    def __init__(self, index_name: str = None):
        """Initialize the Pinecone embedder."""
        self.index_name = index_name or os.getenv("PINECONE_INDEX_NAME", "fa-dae2-capstone")
        self.pc = None
        self.index = None
        self._initialize()

    def _initialize(self):
        """Initialize Pinecone connection."""
        # Initialize Pinecone
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")

        self.pc = Pinecone(api_key=api_key)

        # Connect to index
        try:
            self.index = self.pc.Index(self.index_name)
            print(f"✅ Connected to Pinecone index: {self.index_name}")
        except Exception as e:
            print(f"❌ Failed to connect to index {self.index_name}: {e}")
            print("Make sure the index exists and you have access to it")
            raise

    def embed_chunks(self, chunks: list[dict[str, Any]]) -> list[list[float]]:
        """Generate embeddings for document chunks using Pinecone's built-in embedding."""
        print(f"🧠 Generating embeddings for {len(chunks)} chunks...")

        # Extract text from chunks
        texts = [chunk["text"] for chunk in chunks]

        # Use Pinecone's built-in embedding (llama-text-embed-v2)
        try:
            response = self.pc.inference.embed(
                model="llama-text-embed-v2",
                inputs=texts,
                parameters={"input_type": "passage", "truncate": "END"},
            )

            embeddings = [item.values for item in response.data]
            print(f"✅ Generated {len(embeddings)} embeddings with {len(embeddings[0])} dimensions")
            return embeddings

        except Exception as e:
            print(f"❌ Failed to generate embeddings: {e}")
            raise

    def store_chunks(
        self,
        chunks: list[dict[str, Any]],
        embeddings: list[list[float]],
        namespace: str = "default",
    ):
        """Store chunks and embeddings in Pinecone."""
        print(f"📦 Storing {len(chunks)} chunks in Pinecone...")

        # Prepare vectors for upsert
        vectors = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=False)):
            vector = {
                "id": f"chunk_{i}_{chunk['metadata'].get('source', 'unknown')}",
                "values": embedding,  # Use the actual embedding values
                "metadata": {
                    **chunk["metadata"],
                    "text": chunk["text"][:1000],  # Limit text length for metadata
                },
            }
            vectors.append(vector)

        # Upsert to Pinecone
        try:
            self.index.upsert(vectors=vectors, namespace=namespace)
            print(f"✅ Successfully stored {len(vectors)} vectors in namespace '{namespace}'")
        except Exception as e:
            print(f"❌ Failed to store vectors: {e}")
            raise

    def search_similar(self, query: str, top_k: int = 5, namespace: str = "default") -> list[dict[str, Any]]:
        """Search for similar chunks using a query."""
        print(f"🔍 Searching for similar chunks to: '{query}'")

        # Generate query embedding using Pinecone's built-in embedding
        try:
            query_response = self.pc.inference.embed(
                model="llama-text-embed-v2",
                inputs=[query],
                parameters={"input_type": "query", "truncate": "END"},
            )
            query_embedding = query_response.data[0].values

            # Search in Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=namespace,
            )

            # Format results
            formatted_results = []
            for match in results.matches:
                formatted_results.append(
                    {
                        "id": match.id,
                        "score": match.score,
                        "text": match.metadata.get("text", ""),
                        "metadata": {k: v for k, v in match.metadata.items() if k != "text"},
                    }
                )

            print(f"✅ Found {len(formatted_results)} similar chunks")
            return formatted_results

        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []

    def get_index_stats(self) -> dict[str, Any]:
        """Get statistics about the Pinecone index."""
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "namespaces": stats.namespaces,
            }
        except Exception as e:
            print(f"❌ Failed to get index stats: {e}")
            return {}


def load_chunks_from_file(file_path: str) -> list[dict[str, Any]]:
    """Load chunks from a JSON file created by the chunking lab."""
    try:
        with open(file_path, encoding="utf-8") as f:
            chunks = json.load(f)
        print(f"✅ Loaded {len(chunks)} chunks from {file_path}")
        return chunks
    except Exception as e:
        print(f"❌ Failed to load chunks from {file_path}: {e}")
        return []


def display_search_results(results: list[dict[str, Any]], query: str):
    """Display search results in a formatted way."""
    print(f"\n🔍 Query: '{query}'")
    print("-" * 50)

    if not results:
        print("No results found.")
        return

    for i, result in enumerate(results, 1):
        print(f"Result {i} (Score: {result['score']:.3f}):")
        print(f"ID: {result['id']}")
        print(f"Text: {result['text'][:200]}{'...' if len(result['text']) > 200 else ''}")
        print(f"Metadata: {result['metadata']}")
        print("-" * 30)


@click.command()
@click.option(
    "--chunks-file",
    "-f",
    default="chunking_output/sentence_chunks.json",
    help="Path to the chunks JSON file from chunking lab",
)
@click.option(
    "--index-name",
    "-i",
    default=None,
    help="Pinecone index name (defaults to PINECONE_INDEX_NAME env var)",
)
@click.option("--namespace", "-n", default="default", help="Pinecone namespace to store vectors")
@click.option(
    "--test-queries",
    "-q",
    multiple=True,
    default=["data engineering", "machine learning", "artificial intelligence"],
    help="Test queries for similarity search",
)
@click.option("--top-k", "-k", default=3, help="Number of top results to return for each query")
def main(
    chunks_file: str,
    index_name: str,
    namespace: str,
    test_queries: list[str],
    top_k: int,
):
    """Embed chunks and store them in Pinecone for RAG systems."""

    print("=" * 60)
    print("M04W03L02 Lab: Embed and Store Chunks in Pinecone")
    print("=" * 60)

    # Check if chunks file exists
    if not os.path.exists(chunks_file):
        print(f"❌ Chunks file not found: {chunks_file}")
        print("Run the text chunking lab first to generate chunks.")
        return

    try:
        # Initialize embedder
        print("\n🔧 Initializing Pinecone embedder...")
        embedder = PineconeEmbedder(index_name=index_name)

        # Load chunks
        print(f"\n📄 Loading chunks from {chunks_file}...")
        chunks = load_chunks_from_file(chunks_file)

        if not chunks:
            print("❌ No chunks found. Run the chunking lab first.")
            return

        # Generate embeddings
        print("\n🧠 Generating embeddings...")
        embeddings = embedder.embed_chunks(chunks)

        # Store in Pinecone
        print("\n📦 Storing chunks in Pinecone...")
        embedder.store_chunks(chunks, embeddings, namespace=namespace)

        # Get index stats
        print("\n📊 Index Statistics:")
        stats = embedder.get_index_stats()
        if stats:
            print(f"Total vectors: {stats.get('total_vector_count', 'Unknown')}")
            print(f"Dimension: {stats.get('dimension', 'Unknown')}")
            print(f"Namespaces: {list(stats.get('namespaces', {}).keys())}")

        # Test similarity search
        print("\n🔍 Testing similarity search...")
        for query in test_queries:
            results = embedder.search_similar(query, top_k=top_k, namespace=namespace)
            display_search_results(results, query)

        print("\n✅ Lab completed successfully!")
        print(f"🎯 Chunks stored in namespace: {namespace}")
        print(f"🎯 Index: {embedder.index_name}")
        print("🎯 Ready for RAG system integration!")

    except Exception as e:
        print(f"❌ Lab failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()