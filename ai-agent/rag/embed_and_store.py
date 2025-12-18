import json
import os
import sys
from typing import Any
from pathlib import Path

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
        self.index_name = index_name or os.getenv("PINECONE_DENSE_INDEX_NAME")
        self.pc = None
        self.index = None
        self._initialize()

    def _initialize(self):
        """Initialize Pinecone connection."""
        # Initialize Pinecone
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")
        # Allow specifying the Pinecone environment (region) via env var
        environment = os.getenv("PINECONE_ENV")
        try:
            if environment:
                self.pc = Pinecone(api_key=api_key, environment=environment)
                print(f"✅ Initialized Pinecone client with environment: {environment}")
            else:
                self.pc = Pinecone(api_key=api_key)
                print("✅ Initialized Pinecone client without explicit environment")
        except TypeError:
            # Fallback if Pinecone client doesn't accept 'environment' kwarg
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
        total = len(chunks)
        print(f"🧠 Generating embeddings for {total} chunks...")

        # Extract text from chunks
        texts = [chunk.get("text", "") for chunk in chunks]

        # Pinecone inference API limits inputs per call (typically 96)
        batch_size = int(os.getenv("PINECONE_EMBED_BATCH_SIZE", "96"))
        batch_size = max(1, min(batch_size, 96))

        embeddings: list[list[float]] = []
        try:
            for start in range(0, total, batch_size):
                end = min(start + batch_size, total)
                batch = texts[start:end]
                response = self.pc.inference.embed(
                    model="llama-text-embed-v2",
                    inputs=batch,
                    parameters={"input_type": "passage", "truncate": "END"},
                )
                batch_embeddings = [item.values for item in response.data]
                embeddings.extend(batch_embeddings)
                print(f"   ✅ Embedded {end}/{total}")

            if not embeddings:
                raise RuntimeError("No embeddings returned from Pinecone")

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

        # Prepare vectors for upsert. Use chunk['id'] when available.
        vectors = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=False)):
            # determine vector id: prefer explicit chunk id, else fallback to deterministic id
            fallback_id = f"chunk_{i}_{chunk.get('metadata', {}).get('source', 'unknown')}"
            vec_id = str(chunk.get("id", fallback_id))

            vector = {
                "id": vec_id,
                "values": embedding,  # Use the actual embedding values
                "metadata": {
                    **(chunk.get("metadata") or {}),
                    "text": (chunk.get("text") or "")[:1000],  # Limit text length for metadata
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
        # Defensive: if caller accidentally passed a directory, skip with a clear message
        if os.path.isdir(file_path):
            print(f"⚠️  Skipping directory when expecting a chunk file: {file_path}")
            return []
        with open(file_path, encoding="utf-8") as f:
            obj = json.load(f)

        # Accept either a list of chunks or a single chunk object
        if isinstance(obj, list):
            print(f"✅ Loaded {len(obj)} chunks from {file_path}")
            return obj
        if isinstance(obj, dict):
            print(f"✅ Loaded 1 chunk from {file_path}")
            return [obj]

        print(f"⚠️  Unexpected JSON format in {file_path}")
        return []
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
    "--chunks-path",
    "-f",
    default="data/chunks",
    help="Path to the chunks JSON file or a directory containing chunk JSON files (default: data/chunks)",
)
@click.option(
    "--manifest",
    "-m",
    default="data/process_json/last_processed_chunks.json",
    help="Optional manifest file (JSON list) containing chunk file paths to embed (default: data/process_json/last_processed_chunks.json)",
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
@click.option(
    "--max-files",
    "-mf",
    default=0,
    type=int,
    help="Maximum number of latest chunk files to embed from a directory (0 => all, default: 0)",
)
def main(
    chunks_path: str,
    manifest: str,
    index_name: str,
    namespace: str,
    test_queries: list[str],
    top_k: int,
    max_files: int,
):
    """Embed chunks and store them in Pinecone for RAG systems."""

    print("=" * 60)
    print("M04W03L02 Lab: Embed and Store Chunks in Pinecone")
    print("=" * 60)

    # Check if chunks path exists
    if not os.path.exists(chunks_path):
        print(f"❌ Chunks path not found: {chunks_path}")
        print("Run the text chunking lab first to generate chunks in data/chunks.")
        return

    try:
        # Initialize embedder
        print("\n🔧 Initializing Pinecone embedder...")
        embedder = PineconeEmbedder(index_name=index_name)

        # Inspect index stats to decide upload behavior
        stats = embedder.get_index_stats()
        existing_vector_count = 0
        if stats and isinstance(stats, dict):
            existing_vector_count = int(stats.get("total_vector_count", 0) or 0)

        # Load chunks
        chunks = []

        # If a manifest is provided and exists, honor it and load only those files
        manifest_used = False
        if manifest and os.path.exists(manifest):
            try:
                manifest_list = json.loads(open(manifest, encoding="utf-8").read())
                if isinstance(manifest_list, list) and manifest_list:
                    print(f"📋 Loaded manifest with {len(manifest_list)} entries: {manifest}")
                    for entry in manifest_list:
                        # resolve possible relative paths
                        cand = entry
                        if not os.path.exists(cand):
                            # try relative to chunks_path
                            cand = os.path.join(chunks_path, os.path.basename(entry))
                        if not os.path.exists(cand):
                            print(f"⚠️  Manifest entry not found, skipping: {entry}")
                            continue
                        loaded = load_chunks_from_file(cand)
                        if loaded:
                            chunks.extend(loaded)
                    manifest_used = True
            except Exception as e:
                print(f"⚠️ Failed to read manifest {manifest}: {e}")

        # If manifest was used we already loaded desired files. Otherwise
        # inspect the `chunks_path` (it may be a directory of chunk files or a single file).
        if not manifest_used:
            if os.path.isdir(chunks_path):
                print(f"\n📁 Inspecting chunk files in directory: {chunks_path}...")
                # collect json files with mtimes
                candidates = []
                for p in os.listdir(chunks_path):
                    if p.lower().endswith('.json'):
                        fullp = os.path.join(chunks_path, p)
                        try:
                            mtime = os.path.getmtime(fullp)
                        except Exception:
                            mtime = 0
                        candidates.append((p, mtime))

                if not candidates:
                    print(f"❌ No JSON chunk files found in directory: {chunks_path}")
                    return

                # sort by modification time (latest first)
                candidates.sort(key=lambda x: x[1], reverse=True)

                # Decide which files to upload:
                # - If the Pinecone index is empty -> upload ALL chunk files
                # - Otherwise upload only the latest `max_files` (or all if max_files==0)
                if existing_vector_count == 0:
                    # index empty: upload all
                    selected = candidates
                    print("📌 Pinecone index empty — will upload all chunk files.")
                else:
                    if max_files and max_files > 0:
                        selected = candidates[:max_files]
                    else:
                        selected = candidates
                    print(f"📌 Pinecone already has {existing_vector_count} vectors — uploading latest {len(selected)} file(s).")

                selected_files = [name for name, _ in selected]

                for jf in selected_files:
                    full = os.path.join(chunks_path, jf)
                    loaded = load_chunks_from_file(full)
                    if loaded:
                        chunks.extend(loaded)
            else:
                print(f"\n📄 Loading chunks from file: {chunks_path}...")
                chunks = load_chunks_from_file(chunks_path)

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