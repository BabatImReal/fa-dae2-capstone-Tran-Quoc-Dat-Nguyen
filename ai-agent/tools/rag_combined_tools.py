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
def hybrid_search_documents(query: str, top_k: int = 3, rrf_k: int = 60) -> dict[str, Any]:
    """
    Hybrid search combining dense (semantic) and sparse (lexical) search using RRF (Reciprocal Rank Fusion).
    
    Performs semantic search (dense) and lexical search (sparse) to get top 60 results from each,
    then merges and applies RRF scoring formula: Score(d) = Σ(1/(k + rank_i(d))) where k=60.
    Only keeps documents that appear in BOTH searches and re-ranks by RRF score.
    
    Args:
        query: Search query
        top_k: Number of top results to return (default: 3)
        rrf_k: RRF constant k (default: 60) - controls the weight given to rank position
    
    Returns:
        Dict with merged and RRF-scored results from both indexes, including:
        - rrf_score: Reciprocal Rank Fusion score combining both rankings
        - dense_rank: Position in dense search results (1-based)
        - sparse_rank: Position in sparse search results (1-based)
        - dense_score: Original semantic similarity score
        - sparse_score: Original BM25+ keyword matching score
        - content: Document text
        - source: Document source
        - chunk_id: Unique identifier
    """
    print(f"🔍 Performing hybrid search with RRF for: {query}")
    
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
        
        print(f"  [Dense Search] Querying dense index for top {rrf_k} results...")
        dense_results = dense_index.query(
            vector=dense_embedding,
            top_k=rrf_k,  # Get top 60 from dense for RRF
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
        print(f"  [Sparse Search] Querying sparse index for top {rrf_k} results...")
        sparse_results = sparse_index.query(
            sparse_vector=sparse_embedding,
            top_k=rrf_k,  # Get top 60 from sparse for RRF
            include_metadata=True,
            namespace="default",
        )
        
        print(f"  [Sparse Search] Found {len(sparse_results.matches)} sparse results")
        
        # ===== STEP 4: Build Rank Mappings =====
        print("  [Ranking] Building rank positions for dense and sparse results...")
        dense_ranks = {}  # doc_id -> rank (1-based)
        sparse_ranks = {}  # doc_id -> rank (1-based)
        
        # Dense ranks (1-based: position 1 is rank 1)
        for rank, match in enumerate(dense_results.matches, start=1):
            dense_ranks[match.id] = rank
        
        # Sparse ranks (1-based: position 1 is rank 1)
        for rank, match in enumerate(sparse_results.matches, start=1):
            sparse_ranks[match.id] = rank
        
        print(f"  [Ranking] Dense: {len(dense_ranks)} documents ranked")
        print(f"  [Ranking] Sparse: {len(sparse_ranks)} documents ranked")
        
        # ===== STEP 5: Merge and Collect Metadata =====
        print("  [Merging] Combining dense and sparse results...")
        all_docs = {}
        
        # Collect from dense results
        for match in dense_results.matches:
            all_docs[match.id] = {
                "id": match.id,
                "text": match.metadata.get("text", ""),
                "source": match.metadata.get("source", "Unknown"),
                "metadata": {k: v for k, v in match.metadata.items() if k != "text"},
                "dense_score": match.score,
                "dense_rank": dense_ranks[match.id],
                "sparse_score": None,
                "sparse_rank": None,
            }
        
        # Add/update from sparse results
        for match in sparse_results.matches:
            if match.id in all_docs:
                # Document exists in both - update with sparse info
                all_docs[match.id]["sparse_score"] = match.score
                all_docs[match.id]["sparse_rank"] = sparse_ranks[match.id]
            else:
                # Document only in sparse
                all_docs[match.id] = {
                    "id": match.id,
                    "text": match.metadata.get("text", ""),
                    "source": match.metadata.get("source", "Unknown"),
                    "metadata": {k: v for k, v in match.metadata.items() if k != "text"},
                    "dense_score": None,
                    "dense_rank": None,
                    "sparse_score": match.score,
                    "sparse_rank": sparse_ranks[match.id],
                }
        
        print(f"  [Merging] Total unique documents: {len(all_docs)}")
        
        # ===== STEP 6: Filter for documents with BOTH scores =====
        print("  [Filtering] Keeping only documents with BOTH dense AND sparse scores...")
        high_confidence_docs = {
            doc_id: doc_data 
            for doc_id, doc_data in all_docs.items() 
            if doc_data['dense_rank'] is not None and doc_data['sparse_rank'] is not None
        }
        
        print(f"  [Filtering] Filtered from {len(all_docs)} to {len(high_confidence_docs)} high-confidence documents")
        
        # Debug: Show sample high-confidence documents
        print(f"\n  [DEBUG High-Confidence] Sample documents with BOTH scores:")
        for i, (doc_id, doc) in enumerate(list(high_confidence_docs.items())[:5], 1):
            print(f"    [{i}] ID: {doc_id:30s} | Dense Rank: {doc['dense_rank']:3d} | Sparse Rank: {doc['sparse_rank']:3d}")
        
        # ===== STEP 7: Apply RRF Formula =====
        print(f"\n  [RRF] Applying Reciprocal Rank Fusion with k={rrf_k}...")
        print(f"  [RRF] Formula: Score(d) = Σ(1/(k + rank_i(d)))")
        
        rrf_results = []
        for doc_id, doc_data in high_confidence_docs.items():
            # RRF Score = 1/(k + dense_rank) + 1/(k + sparse_rank)
            dense_contribution = 1.0 / (rrf_k + doc_data['dense_rank'])
            sparse_contribution = 1.0 / (rrf_k + doc_data['sparse_rank'])
            rrf_score = dense_contribution + sparse_contribution
            
            rrf_results.append({
                **doc_data,
                "rrf_score": rrf_score,
                "dense_contribution": dense_contribution,
                "sparse_contribution": sparse_contribution,
            })
        
        # Debug: Print top 5 RRF scores with calculation breakdown
        print(f"\n  [DEBUG RRF Scores] Top 5 results after RRF calculation:")
        sorted_rrf = sorted(rrf_results, key=lambda x: x["rrf_score"], reverse=True)
        for i, result in enumerate(sorted_rrf[:5], 1):
            print(f"    [{i}] ID: {result['id']:30s}")
            print(f"        RRF Score: {result['rrf_score']:.6f} = 1/({rrf_k}+{result['dense_rank']}) + 1/({rrf_k}+{result['sparse_rank']})")
            print(f"        Dense: rank={result['dense_rank']:3d}, score={result['dense_score']:.4f}, contrib={result['dense_contribution']:.6f}")
            print(f"        Sparse: rank={result['sparse_rank']:3d}, score={result['sparse_score']:.4f}, contrib={result['sparse_contribution']:.6f}")
        
        # ===== STEP 8: Get Top K Results =====
        print(f"\n  [Top K] Selecting top {top_k} results (ranked by RRF score)...")
        
        # ===== STEP 8: Get Top K Results =====
        print(f"\n  [Top K] Selecting top {top_k} results (ranked by RRF score)...")
        
        # Sort by RRF score and get top K
        top_results = sorted(rrf_results, key=lambda x: x["rrf_score"], reverse=True)[:top_k]
        
        # Format for output
        formatted_results = []
        for i, result in enumerate(top_results, 1):
            formatted_result = {
                "rank": i,
                "rrf_score": round(result["rrf_score"], 6),
                "dense_rank": result["dense_rank"],
                "sparse_rank": result["sparse_rank"],
                "dense_score": round(result["dense_score"], 4),
                "sparse_score": round(result["sparse_score"], 4),
                "content": result["text"][:500] + "..." if len(result["text"]) > 500 else result["text"],
                "source": result["source"],
                "chunk_id": result["id"],
            }
            formatted_results.append(formatted_result)
        
        print(f"✅ RRF hybrid search completed: Found {len(high_confidence_docs)} merged results, returning top {top_k}")
        
        return {
            "query": query,
            "search_method": "rrf_hybrid_search",
            "rrf_k": rrf_k,
            "total_merged_results": len(high_confidence_docs),
            "top_k": top_k,
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
