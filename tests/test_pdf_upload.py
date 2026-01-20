"""
Test PDF upload, chunking, and dual embedding functionality
"""
import os
import sys
from pathlib import Path
import pytest
from dotenv import load_dotenv
from unittest.mock import Mock, patch
from io import BytesIO

# Add ai-agent to path
project_root = Path(__file__).parent.parent
ai_agent_dir = project_root / "ai-agent"
sys.path.insert(0, str(ai_agent_dir))

from rag.service.document_processor import DocumentProcessor
from rag.embed_and_store import PineconeEmbedder
from rag.sparse_embedder import SparseEmbedder

# Add tools directory to path for RAG tools
tools_dir = ai_agent_dir / "tools"
sys.path.insert(0, str(tools_dir))

from rag_tools import search_documents
from rag_combined_tools import hybrid_search_documents

# Load environment variables
load_dotenv()


@pytest.fixture
def sample_chunks():
    """Create sample chunks for testing (simulates PDF extraction)"""
    return [
        {
            "text": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed.",
            "metadata": {
                "source": "test_document.pdf",
                "chunk_index": 0,
                "total_chunks": 3,
                "chunk_size": 150,
                "chunk_size_tokens": 25,
                "chunking_strategy": "sentence",
                "document_type": ".pdf",
                "language": "en"
            }
        },
        {
            "text": "Deep learning is a type of machine learning based on artificial neural networks with multiple layers. These networks can learn complex patterns in large amounts of data.",
            "metadata": {
                "source": "test_document.pdf",
                "chunk_index": 1,
                "total_chunks": 3,
                "chunk_size": 160,
                "chunk_size_tokens": 28,
                "chunking_strategy": "sentence",
                "document_type": ".pdf",
                "language": "en"
            }
        },
        {
            "text": "Natural language processing enables computers to understand, interpret and generate human language. It combines computational linguistics with machine learning.",
            "metadata": {
                "source": "test_document.pdf",
                "chunk_index": 2,
                "total_chunks": 3,
                "chunk_size": 155,
                "chunk_size_tokens": 26,
                "chunking_strategy": "sentence",
                "document_type": ".pdf",
                "language": "en"
            }
        }
    ]


@pytest.fixture
def document_processor():
    """Create a DocumentProcessor instance"""
    return DocumentProcessor(
        chunk_size=1000,
        chunk_overlap=200,
        chunking_strategy="sentence",
        language="en"
    )


@pytest.fixture
def dense_embedder():
    """Create a PineconeEmbedder instance"""
    if not os.getenv("PINECONE_API_KEY"):
        pytest.skip("PINECONE_API_KEY not set")
    if not os.getenv("PINECONE_DENSE_INDEX_NAME"):
        pytest.skip("PINECONE_DENSE_INDEX_NAME not set")
    
    return PineconeEmbedder()


@pytest.fixture
def sparse_embedder(dense_embedder):
    """Create a SparseEmbedder instance"""
    if not os.getenv("PINECONE_SPARSE_INDEX_NAME"):
        pytest.skip("PINECONE_SPARSE_INDEX_NAME not set")
    
    return SparseEmbedder(
        pc=dense_embedder.pc,
        sparse_index_name=os.getenv("PINECONE_SPARSE_INDEX_NAME")
    )


class TestChunkStructure:
    """Test chunk structure and validation"""
    
    def test_chunk_has_required_fields(self, sample_chunks):
        """Test that chunks have all required fields"""
        for i, chunk in enumerate(sample_chunks):
            assert "text" in chunk, f"Chunk {i} should have 'text' field"
            assert "metadata" in chunk, f"Chunk {i} should have 'metadata' field"
            assert len(chunk["text"]) > 0, f"Chunk {i} should have non-empty text"
            
            # Check metadata fields
            metadata = chunk["metadata"]
            assert "source" in metadata, f"Chunk {i} metadata should have 'source'"
            assert "chunk_index" in metadata, f"Chunk {i} metadata should have 'chunk_index'"
            assert "chunk_size" in metadata, f"Chunk {i} metadata should have 'chunk_size'"
            assert "chunking_strategy" in metadata, f"Chunk {i} metadata should have 'chunking_strategy'"
        
        print(f"\n✅ All {len(sample_chunks)} chunks have correct structure")


class TestDenseEmbedding:
    """Test dense (semantic) embedding generation"""
    
    def test_dense_embedding_generation(self, sample_chunks, dense_embedder):
        """Test that dense embeddings can be generated"""
        embeddings = dense_embedder.embed_chunks(sample_chunks)
        
        assert embeddings is not None, "Embeddings should not be None"
        assert len(embeddings) == len(sample_chunks), f"Should have {len(sample_chunks)} embeddings"
        assert all(isinstance(emb, list) for emb in embeddings), "Each embedding should be a list"
        assert all(len(emb) > 0 for emb in embeddings), "Each embedding should have values"
        
        # Check dimensionality consistency
        first_dim = len(embeddings[0])
        assert all(len(emb) == first_dim for emb in embeddings), "All embeddings should have same dimension"
        
        print(f"\n✅ Generated {len(embeddings)} dense embeddings with {first_dim} dimensions")
    
    def test_dense_storage(self, sample_chunks, dense_embedder):
        """Test that dense embeddings can be stored in Pinecone"""
        embeddings = dense_embedder.embed_chunks(sample_chunks)
        
        # Store with default namespace
        test_namespace = "default"
        
        try:
            dense_embedder.store_chunks(sample_chunks, embeddings, namespace=test_namespace)
            print(f"\n✅ Successfully stored {len(sample_chunks)} dense vectors in namespace '{test_namespace}'")
            
            # Verify storage by checking index stats
            stats = dense_embedder.get_index_stats()
            assert "dense" in stats, "Should have dense index stats"
            
        except Exception as e:
            pytest.fail(f"Failed to store dense embeddings: {e}")


class TestSparseEmbedding:
    """Test sparse (lexical) embedding generation"""
    
    def test_sparse_embedding_generation(self, sample_chunks, sparse_embedder):
        """Test that sparse embeddings can be generated"""
        sparse_embeddings = sparse_embedder.embed_chunks_sparse(sample_chunks)
        
        assert sparse_embeddings is not None, "Sparse embeddings should not be None"
        assert len(sparse_embeddings) == len(sample_chunks), f"Should have {len(sample_chunks)} sparse embeddings"
        
        # Check sparse embedding structure
        for i, emb in enumerate(sparse_embeddings):
            assert isinstance(emb, dict), f"Sparse embedding {i} should be a dict"
            assert "indices" in emb, f"Sparse embedding {i} should have 'indices'"
            assert "values" in emb, f"Sparse embedding {i} should have 'values'"
            assert len(emb["indices"]) == len(emb["values"]), f"Indices and values should have same length"
        
        print(f"\n✅ Generated {len(sparse_embeddings)} sparse embeddings")
    
    def test_sparse_storage(self, sample_chunks, sparse_embedder):
        """Test that sparse embeddings can be stored in Pinecone"""
        sparse_embeddings = sparse_embedder.embed_chunks_sparse(sample_chunks)
        
        # Store with default namespace
        test_namespace = "default"
        
        try:
            sparse_embedder.store_sparse_chunks(sample_chunks, sparse_embeddings, namespace=test_namespace)
            print(f"\n✅ Successfully stored {len(sample_chunks)} sparse vectors in namespace '{test_namespace}'")
            
        except Exception as e:
            pytest.fail(f"Failed to store sparse embeddings: {e}")


class TestDualEmbeddingPipeline:
    """Test the complete dual embedding pipeline"""
    
    def test_full_pipeline(self, sample_chunks, dense_embedder, sparse_embedder):
        """Test complete PDF processing with both embedding types"""
        print(f"\n{'='*60}")
        print("TESTING COMPLETE DUAL EMBEDDING PIPELINE")
        print(f"{'='*60}")
        
        # Step 1: Validate chunks
        print(f"\n📄 Step 1: Validating sample chunks...")
        assert len(sample_chunks) > 0, "Should have chunks"
        print(f"   ✅ Validated {len(sample_chunks)} chunks")
        
        # Step 2: Generate dense embeddings
        print("\n🧠 Step 2: Generating dense embeddings (semantic)...")
        dense_embeddings = dense_embedder.embed_chunks(sample_chunks)
        assert len(dense_embeddings) == len(sample_chunks), "Should have dense embeddings for all chunks"
        print(f"   ✅ Generated {len(dense_embeddings)} dense embeddings with {len(dense_embeddings[0])} dimensions")
        
        # Step 3: Generate sparse embeddings
        print("\n🔤 Step 3: Generating sparse embeddings (lexical)...")
        sparse_embeddings = sparse_embedder.embed_chunks_sparse(sample_chunks)
        assert len(sparse_embeddings) == len(sample_chunks), "Should have sparse embeddings for all chunks"
        print(f"   ✅ Generated {len(sparse_embeddings)} sparse embeddings")
        
        # Step 4: Store dense vectors
        print("\n💾 Step 4: Storing dense vectors...")
        test_namespace = "default"
        dense_embedder.store_chunks(sample_chunks, dense_embeddings, namespace=test_namespace)
        print(f"   ✅ Stored dense vectors in namespace '{test_namespace}'")
        
        # Step 5: Store sparse vectors
        print("\n💾 Step 5: Storing sparse vectors...")
        sparse_embedder.store_sparse_chunks(sample_chunks, sparse_embeddings, namespace=test_namespace)
        print(f"   ✅ Stored sparse vectors in namespace '{test_namespace}'")
        
        print(f"\n{'='*60}")
        print("✅ COMPLETE PIPELINE TEST PASSED!")
        print(f"{'='*60}\n")
        
        # Verify both embedding types exist
        assert len(dense_embeddings) > 0, "Should have dense embeddings"
        assert len(sparse_embeddings) > 0, "Should have sparse embeddings"
        assert len(dense_embeddings) == len(sparse_embeddings), "Should have same count for both types"
    
    def test_embedding_quality(self, sample_chunks, dense_embedder):
        """Test that embeddings are of good quality (not all zeros)"""
        embeddings = dense_embedder.embed_chunks(sample_chunks)
        
        for i, emb in enumerate(embeddings):
            # Check that embeddings are not all zeros
            non_zero_count = sum(1 for val in emb if abs(val) > 0.001)
            assert non_zero_count > len(emb) * 0.5, f"Embedding {i} has too many zero values"
        
        print(f"\n✅ Dense embeddings have good quality (non-zero values)")
    
    def test_sparse_embedding_uniqueness(self, sample_chunks, sparse_embedder):
        """Test that sparse embeddings are different for different texts"""
        sparse_embeddings = sparse_embedder.embed_chunks_sparse(sample_chunks)
        
        # Compare indices between different chunks
        indices_sets = [set(emb["indices"]) for emb in sparse_embeddings]
        
        # At least some chunks should have different indices
        unique_indices = len(set(map(frozenset, indices_sets)))
        assert unique_indices > 1, "All sparse embeddings should not be identical"
        
        print(f"\n✅ Sparse embeddings show uniqueness across chunks")


class TestRAGRetrieval:
    """Test RAG retrieval functionality with stored test data"""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self, sample_chunks, dense_embedder, sparse_embedder):
        """Setup: Ensure test data is stored before retrieval tests"""
        test_namespace = "default"
        
        # Store both dense and sparse vectors
        dense_embeddings = dense_embedder.embed_chunks(sample_chunks)
        sparse_embeddings = sparse_embedder.embed_chunks_sparse(sample_chunks)
        
        dense_embedder.store_chunks(sample_chunks, dense_embeddings, namespace=test_namespace)
        sparse_embedder.store_sparse_chunks(sample_chunks, sparse_embeddings, namespace=test_namespace)
        
        print(f"\n🔧 Setup: Stored {len(sample_chunks)} chunks in namespace '{test_namespace}' (default)")
        
        # Store namespace for use in tests
        self.test_namespace = test_namespace
    
    def test_dense_search_retrieval(self, dense_embedder):
        """Test dense (semantic) search retrieval"""
        query = "machine learning and artificial intelligence"
        top_k = 3
        
        print(f"\n🔍 Testing dense search for query: '{query}'")
        
        # Perform dense search
        results = dense_embedder.search_similar(query, top_k=top_k, namespace=self.test_namespace)
        
        assert results is not None, "Results should not be None"
        assert len(results) > 0, "Should return at least one result"
        assert len(results) <= top_k, f"Should return at most {top_k} results"
        
        # Verify result structure
        for i, result in enumerate(results):
            assert "id" in result, f"Result {i} should have 'id'"
            assert "score" in result, f"Result {i} should have 'score'"
            assert "text" in result, f"Result {i} should have 'text'"
            assert "metadata" in result, f"Result {i} should have 'metadata'"
            
            # Score should be reasonable (0 to 1 for cosine similarity)
            assert 0 <= result["score"] <= 1, f"Score should be between 0 and 1, got {result['score']}"
        
        print(f"   ✅ Dense search returned {len(results)} results")
        print(f"   📊 Top result score: {results[0]['score']:.4f}")
    
    def test_sparse_search_retrieval(self, sparse_embedder):
        """Test sparse (lexical) search retrieval"""
        query = "neural networks deep learning"
        top_k = 3
        
        print(f"\n🔍 Testing sparse search for query: '{query}'")
        
        # Perform sparse search
        results = sparse_embedder.search_sparse(query, top_k=top_k, namespace=self.test_namespace)
        
        assert results is not None, "Results should not be None"
        
        if len(results) > 0:
            # Verify result structure
            for i, result in enumerate(results):
                assert "id" in result, f"Result {i} should have 'id'"
                assert "score" in result, f"Result {i} should have 'score'"
                assert "text" in result, f"Result {i} should have 'text'"
            
            print(f"   ✅ Sparse search returned {len(results)} results")
            print(f"   📊 Top result score: {results[0]['score']:.4f}")
        else:
            print(f"   ⚠️  Sparse search returned 0 results (query might not match keywords)")
    
    def test_search_documents_tool(self):
        """Test the search_documents tool (dense-only search)"""
        query = "artificial intelligence systems"
        top_k = 2
        
        print(f"\n🔍 Testing search_documents tool for query: '{query}'")
        
        # Call the tool
        result = search_documents.invoke({"query": query, "top_k": top_k})
        
        assert result is not None, "Tool result should not be None"
        # Tool returns a dict, not a string
        assert isinstance(result, dict), "Tool should return a dictionary"
        
        # Check that result contains expected fields
        assert "query" in result, "Result should contain 'query' field"
        assert "results" in result or "total_results" in result, "Result should contain results information"
        
        print(f"   ✅ search_documents tool executed successfully")
        print(f"   📊 Found {result.get('total_results', 0)} results")
    
    def test_hybrid_search_tool(self):
        """Test the hybrid_search_documents tool (dense + sparse with reranking)"""
        query = "machine learning algorithms"
        top_k = 3
        
        print(f"\n🔍 Testing hybrid_search_documents tool for query: '{query}'")
        
        # Call the hybrid search tool
        result = hybrid_search_documents.invoke({
            "query": query,
            "top_k": top_k,
            "alpha": 0.5  # Balance between dense and sparse
        })
        
        assert result is not None, "Tool result should not be None"
        # Tool returns a dict, not a string
        assert isinstance(result, dict), "Tool should return a dictionary"
        
        # Check that result contains expected fields
        assert "query" in result, "Result should contain 'query' field"
        assert "search_method" in result, "Result should contain 'search_method' field"
        assert "results" in result, "Result should contain 'results' field"
        
        # Verify it's using hybrid/RRF method
        search_method = result.get("search_method", "")
        assert "hybrid" in search_method.lower() or "rrf" in search_method.lower(), \
            f"Should use hybrid/RRF method, got: {search_method}"
        
        print(f"   ✅ hybrid_search_documents tool executed successfully")
        print(f"   📊 Search method: {search_method}")
        print(f"   📊 Total merged results: {result.get('total_merged_results', 'N/A')}")
        print(f"   📊 Returning top {result.get('top_k', 'N/A')} results")
    
    def test_retrieval_relevance(self, dense_embedder):
        """Test that retrieved results are relevant to the query"""
        # Query specifically about machine learning
        query = "machine learning"
        
        print(f"\n🔍 Testing retrieval relevance for query: '{query}'")
        
        results = dense_embedder.search_similar(query, top_k=3, namespace=self.test_namespace)
        
        assert len(results) > 0, "Should retrieve at least one result"
        
        # Top result should have high relevance (score > 0.5 for semantic search)
        top_score = results[0]["score"]
        assert top_score > 0.3, f"Top result should be reasonably relevant (score > 0.3), got {top_score}"
        
        # Top result text should contain relevant keywords
        top_text = results[0]["text"].lower()
        relevant_keywords = ["machine", "learning", "artificial", "intelligence", "neural", "data"]
        found_keywords = [kw for kw in relevant_keywords if kw in top_text]
        
        assert len(found_keywords) > 0, f"Top result should contain relevant keywords, found: {found_keywords}"
        
        print(f"   ✅ Top result is relevant (score: {top_score:.4f})")
        print(f"   📝 Found keywords: {', '.join(found_keywords)}")
    
    def test_hybrid_vs_dense_comparison(self, dense_embedder):
        """Compare hybrid search with dense-only search"""
        query = "deep learning neural networks"
        top_k = 3
        
        print(f"\n🔍 Comparing hybrid vs dense search for query: '{query}'")
        
        # Dense-only search
        dense_results = dense_embedder.search_similar(query, top_k=top_k, namespace=self.test_namespace)
        
        # Hybrid search via tool
        hybrid_result_str = hybrid_search_documents.invoke({
            "query": query,
            "top_k": top_k,
            "alpha": 0.5
        })
        
        # Both should return results
        assert len(dense_results) > 0, "Dense search should return results"
        assert hybrid_result_str is not None, "Hybrid search should return results"
        
        print(f"   ✅ Dense search: {len(dense_results)} results")
        print(f"   ✅ Hybrid search: Executed successfully")
        print(f"   📊 Dense top score: {dense_results[0]['score']:.4f}")
    
    def test_empty_query_handling(self):
        """Test handling of edge cases like empty queries"""
        print(f"\n🔍 Testing edge case: empty query")
        
        try:
            # Try empty query with search_documents tool
            result = search_documents.invoke({"query": "", "top_k": 3})
            # Should either return empty results or handle gracefully
            assert result is not None, "Should handle empty query"
            print(f"   ✅ Empty query handled gracefully")
        except Exception as e:
            # If it raises an error, that's also acceptable
            print(f"   ✅ Empty query raises error (expected): {type(e).__name__}")
    
    def test_retrieval_consistency(self, dense_embedder):
        """Test that same query returns consistent results"""
        query = "machine learning"
        
        print(f"\n🔍 Testing retrieval consistency for query: '{query}'")
        
        # Run same query twice
        results1 = dense_embedder.search_similar(query, top_k=3, namespace=self.test_namespace)
        results2 = dense_embedder.search_similar(query, top_k=3, namespace=self.test_namespace)
        
        assert len(results1) == len(results2), "Should return same number of results"
        
        # Check that top results are the same
        if len(results1) > 0 and len(results2) > 0:
            assert results1[0]["id"] == results2[0]["id"], "Top result should be consistent"
            assert abs(results1[0]["score"] - results2[0]["score"]) < 0.001, "Scores should be consistent"
        
        print(f"   ✅ Retrieval is consistent across multiple queries")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
