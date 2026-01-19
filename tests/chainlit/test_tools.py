"""
Tests for tool functions (PostgreSQL, Snowflake, RAG)
Target: 70%+ coverage of tool modules
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from pathlib import Path

# Add ai-agent directory to path
project_root = Path(__file__).parent.parent.parent
ai_agent_path = str(project_root / "ai-agent")
if ai_agent_path not in sys.path:
    sys.path.insert(0, ai_agent_path)

# Verify path is correct
assert os.path.exists(os.path.join(ai_agent_path, "tools", "postgre_tools.py")), f"Cannot find tools at {ai_agent_path}"


class TestPostgreSQLTools:
    """Test PostgreSQL tool functions"""
    
    @patch('tools.postgre_tools.get_connection')
    def test_get_latest_product_summary_success(self, mock_conn):
        """Test successful product summary retrieval"""
        # Mock database connection and cursor
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("Product A", "Electronics", 999.99, 10)
        mock_cursor.description = [
            ("product_name",), ("category",), ("price",), ("quantity",)
        ]
        
        mock_conn_instance = MagicMock()
        mock_conn_instance.cursor.return_value = mock_cursor
        mock_conn.return_value = mock_conn_instance
        
        from tools import get_latest_product_summary_from_postgre
        result = get_latest_product_summary_from_postgre()
        
        assert isinstance(result, dict)
        assert result["row_count"] == 1
        assert result["row"]["product_name"] == "Product A"
        assert result["row"]["category"] == "Electronics"
    
    @patch('tools.postgre_tools.get_connection')
    def test_get_latest_product_summary_empty_result(self, mock_conn):
        """Test handling of empty database result"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_cursor.description = []
        
        mock_conn_instance = MagicMock()
        mock_conn_instance.cursor.return_value = mock_cursor
        mock_conn.return_value = mock_conn_instance
        
        from tools import get_latest_product_summary_from_postgre
        result = get_latest_product_summary_from_postgre()
        
        assert isinstance(result, dict)
        assert result["row_count"] == 0
        assert result["row"] is None
    
    @patch('tools.postgre_tools.get_connection')
    def test_get_latest_product_summary_database_error(self, mock_conn):
        """Test handling of database connection error"""
        mock_conn.side_effect = Exception("Database connection failed")
        
        from tools import get_latest_product_summary_from_postgre
        
        # Should raise exception since function doesn't handle errors
        with pytest.raises(Exception) as exc_info:
            get_latest_product_summary_from_postgre()
        
        assert "Database connection failed" in str(exc_info.value)


class TestSnowflakeTools:
    """Test Snowflake tool functions"""
    
    @patch('tools.snowflake_tools.get_snowflake_connection')
    def test_get_all_product_categories_success(self, mock_conn):
        """Test successful category retrieval"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("Electronics",),
            ("Books",),
            ("Clothing",)
        ]
        mock_cursor.description = [("product_category_name_english",)]
        
        mock_conn_instance = MagicMock()
        mock_conn_instance.cursor.return_value = mock_cursor
        mock_conn.return_value = mock_conn_instance
        
        from tools import get_all_product_categories_from_snowflake
        result = get_all_product_categories_from_snowflake()
        
        assert isinstance(result, dict)
        assert result["row_count"] == 3
        assert len(result["rows"]) == 3
        assert result["rows"][0]["product_category_name_english"] == "Electronics"
    
    @patch('tools.snowflake_tools.get_snowflake_connection')
    def test_get_product_by_category_with_valid_category(self, mock_conn):
        """Test product retrieval by category"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("PROD123", "electronics", 500, 20, 10, 15)
        mock_cursor.description = [
            ("product_id",), ("product_category_name_english",),
            ("product_weight_g",), ("product_length_cm",),
            ("product_height_cm",), ("product_width_cm",)
        ]
        
        mock_conn_instance = MagicMock()
        mock_conn_instance.cursor.return_value = mock_cursor
        mock_conn.return_value = mock_conn_instance
        
        from tools import get_product_by_category_from_snowflake
        result = get_product_by_category_from_snowflake("Electronics")
        
        assert isinstance(result, dict)
        assert result["row_count"] == 1
        assert result["row"]["product_id"] == "PROD123"


class TestRAGTools:
    """Test RAG search tools"""
    
    @patch('tools.rag_tools.Pinecone')
    def test_search_documents_success(self, mock_pinecone):
        """Test successful document search"""
        # Mock Pinecone responses
        mock_match = MagicMock()
        mock_match.score = 0.95
        mock_match.id = "chunk_001"
        mock_match.metadata = {
            "text": "Data engineering best practices",
            "source": "guide.pdf"
        }
        
        mock_results = MagicMock()
        mock_results.matches = [mock_match]
        
        mock_index = MagicMock()
        mock_index.query.return_value = mock_results
        
        mock_pc_instance = MagicMock()
        mock_pc_instance.Index.return_value = mock_index
        mock_pc_instance.inference.embed.return_value.data = [
            MagicMock(values=[0.1, 0.2, 0.3])
        ]
        mock_pinecone.return_value = mock_pc_instance
        
        from tools import search_documents
        result = search_documents("data engineering")
        
        assert isinstance(result, dict)
        assert "query" in result
        assert result["query"] == "data engineering"
        assert "results" in result
        assert len(result["results"]) > 0
    
    @patch('tools.rag_tools.Pinecone')
    def test_search_documents_no_results(self, mock_pinecone):
        """Test search with no results"""
        mock_results = MagicMock()
        mock_results.matches = []
        
        mock_index = MagicMock()
        mock_index.query.return_value = mock_results
        
        mock_pc_instance = MagicMock()
        mock_pc_instance.Index.return_value = mock_index
        mock_pc_instance.inference.embed.return_value.data = [
            MagicMock(values=[0.1, 0.2, 0.3])
        ]
        mock_pinecone.return_value = mock_pc_instance
        
        from tools import search_documents
        result = search_documents("nonexistent topic")
        
        assert isinstance(result, dict)
        assert "results" in result
        assert len(result["results"]) == 0
        assert "message" in result or "suggestion" in result
    
    @patch('tools.rag_combined_tools.Pinecone')
    def test_hybrid_search_combines_results(self, mock_pinecone):
        """Test hybrid search functionality"""
        # Mock match object for both dense and sparse results
        mock_match = MagicMock()
        mock_match.score = 0.92
        mock_match.id = "chunk_ml_001"
        mock_match.metadata = {
            "text": "Machine learning fundamentals",
            "source": "ml_book.pdf"
        }
        
        mock_results = MagicMock()
        mock_results.matches = [mock_match]
        
        mock_index = MagicMock()
        mock_index.query.return_value = mock_results
        
        mock_pc_instance = MagicMock()
        mock_pc_instance.Index.return_value = mock_index
        
        # Mock both dense and sparse embeddings
        mock_dense_embed = MagicMock()
        mock_dense_embed.values = [0.1, 0.2, 0.3]
        
        mock_sparse_embed = MagicMock()
        mock_sparse_embed.sparse_indices = [1, 5, 10]
        mock_sparse_embed.sparse_values = [0.5, 0.3, 0.2]
        
        mock_pc_instance.inference.embed.return_value.data = [
            mock_dense_embed, mock_sparse_embed
        ]
        mock_pinecone.return_value = mock_pc_instance
        
        from tools import hybrid_search_documents
        result = hybrid_search_documents("machine learning")
        
        assert isinstance(result, dict)
        assert "query" in result


class TestToolInputValidation:
    """Test input validation for tools"""
    
    def test_postgre_tool_handles_special_characters(self):
        """Test that tools handle special characters in input"""
        # This would test SQL injection prevention
        pass
    
    @patch('tools.snowflake_tools.get_snowflake_connection')
    def test_snowflake_tool_validates_category_name(self, mock_conn):
        """Test category name validation"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_cursor.description = []
        
        mock_conn_instance = MagicMock()
        mock_conn_instance.cursor.return_value = mock_cursor
        mock_conn.return_value = mock_conn_instance
        
        from tools import get_product_by_category_from_snowflake
        
        # Test with valid empty category (should return empty result)
        result = get_product_by_category_from_snowflake("")
        assert isinstance(result, dict)
        assert result["row_count"] == 0
    
    @patch('tools.rag_tools.Pinecone')
    def test_rag_tool_handles_long_queries(self, mock_pinecone):
        """Test RAG tools with very long queries"""
        mock_results = MagicMock()
        mock_results.matches = []
        
        mock_index = MagicMock()
        mock_index.query.return_value = mock_results
        
        mock_pc_instance = MagicMock()
        mock_pc_instance.Index.return_value = mock_index
        mock_pc_instance.inference.embed.return_value.data = [
            MagicMock(values=[0.1] * 100)
        ]
        mock_pinecone.return_value = mock_pc_instance
        
        from tools import search_documents
        
        long_query = "test " * 1000
        result = search_documents(long_query)
        
        # Should handle gracefully, not crash
        assert isinstance(result, dict)
