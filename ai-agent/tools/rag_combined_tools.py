"""Combined RAG tools for hybrid search combining dense and sparse embeddings."""

import os
from typing import Any

from dotenv import load_dotenv
from langchain_core.tools import tool
from pinecone import Pinecone

# Load environment variables
load_dotenv()


def normalize_score(score: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Normalize score to 0-1 range."""
    if max_val == min_val:
        return 0.5
    return (score - min_val) / (max_val - min_val)


@tool
def hybrid_search_documents(query: str, top_k: int = 3, alpha: float = 0.5) -> dict[str, Any]:
    """
    Hybrid search combining dense (semantic) and sparse (lexical) search.
    
    Performs semantic search (dense) and lexical search (sparse) to get top 10 results from each,
    then merges, deduplicates (keeping only documents found in BOTH searches), and re-ranks them
    by a weighted hybrid score.
    
    Args:
        query: Search query
        top_k: Number of top results to return (default: 3)
        alpha: Weight for dense results (0.0-1.0). 
               - 0.0 = pure lexical/sparse (keyword matching)
               - 0.5 = balanced (default)
               - 1.0 = pure semantic/dense (contextual meaning)
    
    Returns:
        Dict with merged and re-ranked results from both indexes, including:
        - hybrid_score: Weighted average of normalized dense and sparse scores
        - dense_score: Semantic similarity score (0-1)
        - sparse_score: BM25+ keyword matching score (variable range)
        - content: Document text
        - source: Document source
        - chunk_id: Unique identifier
    """
    print(f"🔍 Performing hybrid search for: {query}")
    
    try:
        # Initialize Pinecone
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        dense_index = pc.Index(os.getenv("PINECONE_DENSE_INDEX_NAME"))
        sparse_index = pc.Index(os.getenv("PINECONE_SPARSE_INDEX_NAME"))
        
        # ===== STEP 3: Dense Search (Semantic) =====
        print("  [Dense Search] Generating semantic embedding...")
        dense_response = pc.inference.embed(
            model="llama-text-embed-v2",
            inputs=[query],
            parameters={"input_type": "query", "truncate": "END"},
        )
        dense_embedding = dense_response.data[0].values
        
        print("  [Dense Search] Querying dense index...")
        dense_results = dense_index.query(
            vector=dense_embedding,
            top_k=10,  # Get top 10 from dense
            include_metadata=True,
            namespace="default",
        )
        
        # ===== STEP 3: Sparse Search (Lexical) =====
        print("  [Sparse Search] Generating sparse embedding...")
        sparse_response = pc.inference.embed(
            model="pinecone-sparse-english-v0",
            inputs=[query],
            parameters={"input_type": "query"},
        )
        sparse_embedding = {
            "indices": sparse_response.data[0].sparse_indices,
            "values": sparse_response.data[0].sparse_values
        }
        
        print(f"  [Sparse Search] Generated embedding with {len(sparse_embedding['indices'])} indices")
        print("  [Sparse Search] Querying sparse index...")
        sparse_results = sparse_index.query(
            sparse_vector=sparse_embedding,
            top_k=10,  # Get top 10 from sparse
            include_metadata=True,
            namespace="default",
        )
        
        print(f"  [Sparse Search] Found {len(sparse_results.matches)} sparse results")
        
        # ===== STEP 4: Merge and Deduplicate =====
        print("  [Merging] Combining dense and sparse results...")
        merged_scores = {}
        dense_scores = {}
        sparse_scores = {}
        
        # Debug: Print dense search results
        print(f"\n  [DEBUG Dense] Found {len(dense_results.matches)} dense results:")
        for i, match in enumerate(dense_results.matches[:3], 1):
            print(f"    [{i}] ID: {match.id}, Score: {match.score:.4f}")
        
        # Collect dense scores
        for match in dense_results.matches:
            dense_scores[match.id] = match.score
            if match.id not in merged_scores:
                merged_scores[match.id] = {
                    "id": match.id,
                    "text": match.metadata.get("text", ""),
                    "source": match.metadata.get("source", "Unknown"),
                    "metadata": {k: v for k, v in match.metadata.items() if k != "text"},
                    "dense_score": match.score,
                    "sparse_score": None,
                }
            else:
                merged_scores[match.id]["dense_score"] = match.score
        
        # Debug: Print sparse search results
        print(f"\n  [DEBUG Sparse] Found {len(sparse_results.matches)} sparse results:")
        for i, match in enumerate(sparse_results.matches[:3], 1):
            print(f"    [{i}] ID: {match.id}, Score: {match.score:.4f}")
        
        # Collect sparse scores
        for match in sparse_results.matches:
            sparse_scores[match.id] = match.score
            if match.id not in merged_scores:
                merged_scores[match.id] = {
                    "id": match.id,
                    "text": match.metadata.get("text", ""),
                    "source": match.metadata.get("source", "Unknown"),
                    "metadata": {k: v for k, v in match.metadata.items() if k != "text"},
                    "dense_score": None,
                    "sparse_score": match.score,
                }
            else:
                merged_scores[match.id]["sparse_score"] = match.score
        
        print(f"\n  [Merging] Total merged documents: {len(merged_scores)}")
        
        # Filter to keep ONLY chunks with BOTH dense AND sparse scores (high-confidence matches)
        print("  [Filtering] Keeping only documents with BOTH dense AND sparse scores...")
        high_confidence_merged = {}
        
        for doc_id, doc_data in merged_scores.items():
            if doc_data['dense_score'] is not None and doc_data['sparse_score'] is not None:
                high_confidence_merged[doc_id] = doc_data
        
        print(f"  [Filtering] Filtered from {len(merged_scores)} to {len(high_confidence_merged)} high-confidence documents")
        
        # Use filtered results
        merged_scores = high_confidence_merged
        
        # Recalculate dense and sparse score lists
        dense_scores = {doc_id: doc_data['dense_score'] for doc_id, doc_data in merged_scores.items()}
        sparse_scores = {doc_id: doc_data['sparse_score'] for doc_id, doc_data in merged_scores.items()}
        
        # Debug: Show high-confidence documents
        print(f"\n  [DEBUG High-Confidence Documents] All {len(merged_scores)} results with BOTH scores:")
        merged_list = list(merged_scores.values())
        for i, doc in enumerate(sorted(merged_list, key=lambda x: x['id']), 1):
            print(f"    [{i:2d}] ID: {doc['id']:30s} | Dense: {doc['dense_score']:>7.4f} | Sparse: {doc['sparse_score']:>7.4f}")
        
        # ===== STEP 5: Re-rank by Hybrid Score =====
        print("\n  [Re-ranking] Computing hybrid scores...")
        
        # Find min/max for normalization
        dense_values = [s for s in dense_scores.values()]
        sparse_values = [s for s in sparse_scores.values()]
        
        dense_min, dense_max = (min(dense_values), max(dense_values)) if dense_values else (0, 1)
        sparse_min, sparse_max = (min(sparse_values), max(sparse_values)) if sparse_values else (0, 1)
        
        print(f"  [DEBUG Scores] Dense range: {dense_min:.4f} - {dense_max:.4f}")
        print(f"  [DEBUG Scores] Sparse range: {sparse_min:.4f} - {sparse_max:.4f}")
        
        # Calculate hybrid scores
        hybrid_results = []
        for doc_id, doc_data in merged_scores.items():
            # Normalize both scores to 0-1
            norm_dense = normalize_score(doc_data["dense_score"], dense_min, dense_max) if doc_data["dense_score"] is not None else 0
            norm_sparse = normalize_score(doc_data["sparse_score"], sparse_min, sparse_max) if doc_data["sparse_score"] is not None else 0
            
            # Hybrid score = weighted average
            hybrid_score = (alpha * norm_dense) + ((1 - alpha) * norm_sparse)
            
            hybrid_results.append({
                **doc_data,
                "hybrid_score": hybrid_score,
            })
        
        # Debug: Print top 3 hybrid scores
        print(f"\n  [DEBUG Hybrid Scores] Top 3 results after hybrid score calculation:")
        sorted_hybrid = sorted(hybrid_results, key=lambda x: x["hybrid_score"], reverse=True)
        for i, result in enumerate(sorted_hybrid[:3], 1):
            print(f"    [{i}] ID: {result['id']:30s} | Hybrid: {result['hybrid_score']:>7.4f} | Dense: {result['dense_score']:>7.4f} | Sparse: {result['sparse_score']:>7.4f}")
        
        # ===== STEP 6: Get Top K Results =====
        print(f"\n  [Top K] Selecting top {top_k} results (ranked by hybrid_score)...")
        
        # Sort by hybrid score and get top K
        top_results = sorted(hybrid_results, key=lambda x: x["hybrid_score"], reverse=True)[:top_k]
        
        # Format for output
        formatted_results = []
        for i, result in enumerate(top_results, 1):
            formatted_result = {
                "rank": i,
                "hybrid_score": round(result["hybrid_score"], 4),
                "dense_score": round(result["dense_score"], 4) if result["dense_score"] else None,
                "sparse_score": round(result["sparse_score"], 4) if result["sparse_score"] else None,
                "content": result["text"][:500] + "..." if len(result["text"]) > 500 else result["text"],
                "source": result["source"],
                "chunk_id": result["id"],
            }
            formatted_results.append(formatted_result)
        
        print(f"✅ Hybrid search completed: Found {len(merged_scores)} merged results, returning top {top_k}")
        
        return {
            "query": query,
            "search_method": "hybrid_search",
            "total_merged_results": len(merged_scores),
            "top_k": top_k,
            "alpha": alpha,
            "results": formatted_results,
            "indices_used": [os.getenv("PINECONE_DENSE_INDEX_NAME"), os.getenv("PINECONE_SPARSE_INDEX_NAME")],
        }
        
    except Exception as e:
        print(f"❌ Hybrid search failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": f"Failed to perform hybrid search: {str(e)}",
            "query": query,
            "results": [],
            "suggestion": "Check Pinecone configuration and ensure both dense and sparse indexes exist.",
        }
