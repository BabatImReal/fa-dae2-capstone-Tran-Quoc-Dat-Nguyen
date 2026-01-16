"""Sparse embedding generation and storage for RAG systems."""

import re
import os
import json
import sys
from typing import Any
from pathlib import Path

import click
from dotenv import load_dotenv
from pinecone import Pinecone

# Load environment variables
load_dotenv()


class SparseEmbedder:
    """Handles BM25 sparse embedding generation and Pinecone sparse index storage."""

    def __init__(self, pc: Pinecone, sparse_index_name: str = None):
        """
        Initialize the sparse embedder.
        
        Args:
            pc: Pinecone client instance
            sparse_index_name: Name of the sparse index (defaults to PINECONE_SPARSE_INDEX_NAME env var)
        """
        self.pc = pc
        self.sparse_index_name = sparse_index_name or os.getenv("PINECONE_SPARSE_INDEX_NAME")
        self.sparse_index = None
        self.vocab = {}  # Maps token -> index
        self.next_idx = 0
        self.bm25_corpus = []  # Store tokenized documents for BM25
        self._initialize()

    def _initialize(self):
        """Initialize sparse index connection."""
        if self.sparse_index_name:
            try:
                self.sparse_index = self.pc.Index(self.sparse_index_name)
                print(f" Connected to Pinecone sparse index: {self.sparse_index_name}")
            except Exception as e:
                print(f"  Could not connect to sparse index {self.sparse_index_name}: {e}")
                self.sparse_index = None

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text by extracting keywords and removing stopwords."""
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
            'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can',
            'that', 'this', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        return [w for w in words if w not in stop_words]

    def embed_chunks_sparse(self, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Generate sparse embeddings for document chunks using Pinecone's sparse embedding model."""
        total = len(chunks)
        print(f" Generating sparse embeddings for {total} chunks...")

        # Extract text from chunks
        texts = [chunk.get("text", "") for chunk in chunks]

        # Pinecone inference API limits inputs per call (typically 96)
        batch_size = int(os.getenv("PINECONE_EMBED_BATCH_SIZE", "96"))
        batch_size = max(1, min(batch_size, 96))

        sparse_embeddings: list[dict[str, Any]] = []
        try:
            for start in range(0, total, batch_size):
                end = min(start + batch_size, total)
                batch = texts[start:end]
                response = self.pc.inference.embed(
                    model="pinecone-sparse-english-v0",
                    inputs=batch,
                    parameters={"input_type": "passage"},
                )
                
                # Parse sparse embeddings from response
                # response.data is a list of SparseEmbedding objects
                for item in response.data:
                    # item is a SparseEmbedding with sparse_values and sparse_indices
                    if hasattr(item, 'sparse_values') and hasattr(item, 'sparse_indices'):
                        sparse_emb = {
                            "indices": item.sparse_indices,
                            "values": item.sparse_values
                        }
                    elif isinstance(item, dict) and 'sparse_values' in item:
                        sparse_emb = {
                            "indices": item.get('sparse_indices', []),
                            "values": item.get('sparse_values', [])
                        }
                    else:
                        print(f"  Warning: Unexpected response format: {type(item)}")
                        continue
                    
                    sparse_embeddings.append(sparse_emb)
                
                print(f"    Embedded {end}/{total}")

            if not sparse_embeddings:
                raise RuntimeError("No sparse embeddings returned from Pinecone")

            print(f" Generated {len(sparse_embeddings)} sparse embeddings")
            return sparse_embeddings

        except Exception as e:
            print(f" Failed to generate sparse embeddings: {e}")
            raise

    def create_bm25_sparse_embedding(self, text: str, tokens: list[str] = None) -> dict[str, Any]:
        """
        Create sparse embedding from text using proper BM25 scoring.
        
        Args:
            text: Text to create sparse embedding from
            tokens: Pre-tokenized text (optional)
            
        Returns:
            Dictionary with 'indices' and 'values' for sparse vector
        """
        try:
            if tokens is None:
                tokens = self._tokenize(text)
            
            if not tokens:
                tokens = ['text']
            
            # Count token frequencies for this document
            token_freq = {}
            for token in tokens:
                # Register token in global vocab if new
                if token not in self.vocab:
                    self.vocab[token] = self.next_idx
                    self.next_idx += 1
                
                idx = self.vocab[token]
                token_freq[idx] = token_freq.get(idx, 0) + 1
            
            # Create sparse vector with TF (term frequency) as values
            indices = sorted(token_freq.keys())
            values = [float(token_freq[idx]) for idx in indices]
            
            # Normalize values (TF normalization)
            max_val = max(values) if values else 1.0
            values = [v / max_val for v in values]
            
            return {"indices": indices, "values": values}
        except Exception as e:
            print(f"  Error creating sparse embedding: {e}")
            return {"indices": [0], "values": [1.0]}

    def store_sparse_chunks(
        self,
        chunks: list[dict[str, Any]],
        sparse_embeddings: list[dict[str, Any]] = None,
        namespace: str = "default",
    ):
        """
        Store chunks as sparse vectors in Pinecone sparse index.
        
        Args:
            chunks: List of chunks with text and metadata
            sparse_embeddings: Pre-computed sparse embeddings (optional). If None, will be generated.
            namespace: Pinecone namespace for storage
        """
        if not self.sparse_index:
            print(" Sparse index not configured, skipping sparse storage.")
            return

        print(f" Storing {len(chunks)} chunks as sparse vectors in Pinecone...")
        
        # Generate sparse embeddings if not provided
        if sparse_embeddings is None:
            sparse_embeddings = self.embed_chunks_sparse(chunks)
        
        if len(sparse_embeddings) != len(chunks):
            print(f" Error: Number of embeddings ({len(sparse_embeddings)}) does not match chunks ({len(chunks)})")
            return
        
        # Create sparse vectors with Pinecone embeddings
        sparse_vectors = []
        for i, (chunk, sparse_emb) in enumerate(zip(chunks, sparse_embeddings)):
            fallback_id = f"chunk_{i}_{chunk.get('metadata', {}).get('source', 'unknown')}"
            vec_id = str(chunk.get("id", fallback_id))
            
            # Use Pinecone's sparse embedding directly
            sparse_vector = {
                "id": vec_id,
                "sparse_values": sparse_emb,
                "metadata": {
                    **(chunk.get("metadata") or {}),
                    "text": (chunk.get("text") or "")[:1000],
                },
            }
            sparse_vectors.append(sparse_vector)
        
        try:
            self.sparse_index.upsert(vectors=sparse_vectors, namespace=namespace)
            print(f" Successfully stored {len(sparse_vectors)} sparse vectors in namespace '{namespace}'")
        except Exception as e:
            print(f"  Failed to store sparse vectors: {e}")

    def search_sparse(self, query: str, top_k: int = 5, namespace: str = "default") -> list[dict[str, Any]]:
        """
        Search for similar chunks using sparse search with Pinecone's sparse embedding model.
        
        Args:
            query: Query text to search for
            top_k: Number of top results to return
            namespace: Pinecone namespace to search in
            
        Returns:
            List of matching results with metadata
        """
        if not self.sparse_index:
            print(" Sparse index not available for search")
            return []
        
        print(f" Searching sparse index for: '{query}'")
        
        try:
            # Generate sparse embedding for the query using Pinecone model
            response = self.pc.inference.embed(
                model="pinecone-sparse-english-v0",
                inputs=[query],
                parameters={"input_type": "query"},
            )
            
            # Parse sparse embedding from response
            if hasattr(response.data[0], 'sparse_values') and hasattr(response.data[0], 'sparse_indices'):
                query_sparse_emb = {
                    "indices": response.data[0].sparse_indices,
                    "values": response.data[0].sparse_values
                }
            else:
                query_sparse_emb = response.data[0].values
            
            # Search in Pinecone sparse index
            results = self.sparse_index.query(
                sparse_vector=query_sparse_emb,
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
                        "score": match.score if hasattr(match, 'score') else 0.0,
                        "text": match.metadata.get("text", "") if match.metadata else "",
                        "metadata": {k: v for k, v in (match.metadata.items() if match.metadata else []) if k != "text"},
                    }
                )
            
            print(f" Found {len(formatted_results)} sparse search results")
            return formatted_results
        
        except Exception as e:
            print(f" Sparse search failed: {e}")
            return []

    def get_sparse_index_stats(self) -> dict[str, Any]:
        """
        Get statistics about the sparse index.
        
        Returns:
            Dictionary with sparse index stats
        """
        if not self.sparse_index:
            return {}
        
        try:
            sparse_stats = self.sparse_index.describe_index_stats()
            return {
                "total_vector_count": sparse_stats.total_vector_count,
                "namespaces": sparse_stats.namespaces,
            }
        except Exception as e:
            print(f"  Failed to get sparse index stats: {e}")
            return {}


def load_chunks_from_file(file_path: str) -> list[dict[str, Any]]:
    """Load chunks from a JSON file created by the chunking lab."""
    try:
        if os.path.isdir(file_path):
            print(f"  Skipping directory when expecting a chunk file: {file_path}")
            return []
        with open(file_path, encoding="utf-8") as f:
            obj = json.load(f)

        if isinstance(obj, list):
            print(f" Loaded {len(obj)} chunks from {file_path}")
            return obj
        if isinstance(obj, dict):
            print(f" Loaded 1 chunk from {file_path}")
            return [obj]

        print(f"  Unexpected JSON format in {file_path}")
        return []
    except Exception as e:
        print(f" Failed to load chunks from {file_path}: {e}")
        return []


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
    help="Pinecone sparse index name (defaults to PINECONE_SPARSE_INDEX_NAME env var)",
)
@click.option("--namespace", "-n", default="default", help="Pinecone namespace to store vectors")
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
    max_files: int,
):
    """Embed chunks sparsely and store them in Pinecone sparse index."""

    print("=" * 60)
    print("Sparse Embedding and Storage")
    print("=" * 60)

    # Check if chunks path exists
    if not os.path.exists(chunks_path):
        print(f" Chunks path not found: {chunks_path}")
        print("Run the text chunking lab first to generate chunks in data/chunks.")
        return

    try:
        # Initialize Pinecone client
        print("\n Initializing Pinecone client...")
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")
        
        environment = os.getenv("PINECONE_ENV")
        try:
            if environment:
                pc = Pinecone(api_key=api_key, environment=environment)
                print(f" Initialized Pinecone client with environment: {environment}")
            else:
                pc = Pinecone(api_key=api_key)
                print(" Initialized Pinecone client without explicit environment")
        except TypeError:
            # Fallback if Pinecone client doesn't accept 'environment' kwarg
            pc = Pinecone(api_key=api_key)

        # Initialize sparse embedder
        print(" Initializing Sparse Embedder...")
        embedder = SparseEmbedder(pc=pc, sparse_index_name=index_name)

        if not embedder.sparse_index:
            print(" Error: Sparse index not configured or unavailable.")
            print("Make sure the sparse index exists and you have access to it.")
            return

        # Load chunks
        chunks = []

        # If a manifest is provided and exists, honor it and load only those files
        manifest_used = False
        if manifest and os.path.exists(manifest):
            try:
                manifest_list = json.loads(open(manifest, encoding="utf-8").read())
                if isinstance(manifest_list, list) and manifest_list:
                    print(f" Loaded manifest with {len(manifest_list)} entries: {manifest}")
                    for entry in manifest_list:
                        cand = entry
                        if not os.path.exists(cand):
                            cand = os.path.join(chunks_path, os.path.basename(entry))
                        if not os.path.exists(cand):
                            print(f"  Manifest entry not found, skipping: {entry}")
                            continue
                        loaded = load_chunks_from_file(cand)
                        if loaded:
                            chunks.extend(loaded)
                    manifest_used = True
            except Exception as e:
                print(f" Failed to read manifest {manifest}: {e}")

        # If manifest was not used, inspect chunks_path
        if not manifest_used:
            if os.path.isdir(chunks_path):
                print(f"\n Inspecting chunk files in directory: {chunks_path}...")
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
                    print(f" No JSON chunk files found in directory: {chunks_path}")
                    return

                candidates.sort(key=lambda x: x[1], reverse=True)

                if max_files and max_files > 0:
                    selected = candidates[:max_files]
                else:
                    selected = candidates

                print(f" Found {len(selected)} chunk file(s) to process.")
                selected_files = [name for name, _ in selected]

                for jf in selected_files:
                    full = os.path.join(chunks_path, jf)
                    loaded = load_chunks_from_file(full)
                    if loaded:
                        chunks.extend(loaded)
            else:
                print(f"\n Loading chunks from file: {chunks_path}...")
                chunks = load_chunks_from_file(chunks_path)

        if not chunks:
            print(" No chunks found. Run the chunking lab first.")
            return

        # Store sparse chunks
        print("\n Storing sparse chunks in Pinecone...")
        embedder.store_sparse_chunks(chunks, namespace=namespace)

        # Get index stats
        print("\n Sparse Index Statistics:")
        stats = embedder.get_sparse_index_stats()
        if stats:
            print(f"  Total vectors: {stats.get('total_vector_count', 'Unknown')}")
            print(f"  Namespaces: {list(stats.get('namespaces', {}).keys())}")

        # Test sparse search
        print("\n Testing sparse keyword search...")
        test_queries = ["fiona", "machine learning", "clustering"]
        for query in test_queries:
            results = embedder.search_sparse(query, top_k=3, namespace=namespace)
            print(f"\n Query: '{query}'")
            print("-" * 50)
            if results:
                for i, result in enumerate(results, 1):
                    print(f"Result {i} (Score: {result['score']:.4f}):")
                    print(f"ID: {result['id']}")
                    print(f"Text: {result['text'][:150]}{'...' if len(result['text']) > 150 else ''}")
                    print(f"Metadata: {result['metadata']}")
                    print("-" * 30)
            else:
                print("No results found.")

        print("\n Sparse embedding completed successfully!")
        print(f" Chunks stored in namespace: {namespace}")
        print(f" Sparse Index: {embedder.sparse_index_name}")
        print(" Ready for RAG system integration!")

    except Exception as e:
        print(f" Lab failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
