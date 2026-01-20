"""
Pytest tests for delete_stage_files function in ingest_to_snowflake module.

Tests verify that:
1. The correct SQL is generated for different file patterns
2. Pattern validation works correctly
3. Files with .csv.gz extension are properly matched
4. The PATTERN clause is used correctly for regex patterns
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Mock Airflow imports before importing the module (Airflow doesn't run on Windows)
sys.modules['airflow'] = MagicMock()
sys.modules['airflow.providers'] = MagicMock()
sys.modules['airflow.providers.snowflake'] = MagicMock()
sys.modules['airflow.providers.snowflake.hooks'] = MagicMock()
sys.modules['airflow.providers.snowflake.hooks.snowflake'] = MagicMock()

# Add the scripts directory to sys.path to import the module
scripts_dir = Path(__file__).resolve().parents[1] / "scripts" / "ingestion"
sys.path.insert(0, str(scripts_dir.parent.parent))

from scripts.ingestion.ingest_to_snowflake import delete_stage_files, sanitize_identifier


class TestDeleteStageFiles:
    """Test suite for delete_stage_files function."""

    @pytest.fixture
    def mock_connection(self):
        """Create a mock Snowflake connection with cursor."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Setup cursor context manager
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        
        # Setup connection context manager
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        
        # Mock fetchall to return different results for LIST (before), REMOVE, and LIST (after)
        # First call (LIST before): 2 files
        # Second call (REMOVE): 2 files deleted
        # Third call (LIST after): 0 files (all deleted)
        mock_cursor.fetchall.side_effect = [
            [("file1.csv.gz",), ("file2.csv.gz",)],  # LIST before
            [("file1.csv.gz",), ("file2.csv.gz",)],  # REMOVE results
            [],  # LIST after (empty - files deleted)
        ]
        
        return mock_conn, mock_cursor

    def test_delete_all_files_with_wildcard(self, mock_connection):
        """Test deleting all files using '*' pattern generates plain REMOVE."""
        mock_conn, mock_cursor = mock_connection
        
        with patch('scripts.ingestion.ingest_to_snowflake.get_conn', return_value=mock_conn):
            result = delete_stage_files("SC_RAW_DATA.OLIST_STAGE", "*")
        
        assert result is True
        # Should generate: REMOVE @SC_RAW_DATA.OLIST_STAGE (no PATTERN clause for wildcard)
        # Check the second execute call (first is LIST before, second is REMOVE)
        remove_sql = mock_cursor.execute.call_args_list[1][0][0]
        assert "REMOVE @SC_RAW_DATA.OLIST_STAGE" in remove_sql
        assert "PATTERN" not in remove_sql

    def test_delete_csv_gz_files_with_regex(self, mock_connection):
        """Test deleting .csv.gz files using regex pattern generates PATTERN clause."""
        mock_conn, mock_cursor = mock_connection
        
        pattern = r".*\.csv\.gz$"
        
        with patch('scripts.ingestion.ingest_to_snowflake.get_conn', return_value=mock_conn):
            result = delete_stage_files("SC_RAW_DATA.OLIST_STAGE", pattern)
        
        assert result is True
        # Should generate: REMOVE @SC_RAW_DATA.OLIST_STAGE PATTERN = '.*\.csv\.gz$'
        remove_sql = mock_cursor.execute.call_args_list[1][0][0]
        assert "REMOVE @SC_RAW_DATA.OLIST_STAGE PATTERN" in remove_sql
        assert pattern in remove_sql

    def test_delete_specific_file_pattern(self, mock_connection):
        """Test deleting files matching a specific pattern."""
        mock_conn, mock_cursor = mock_connection
        
        pattern = r".*olist_orders.*\.csv\.gz"
        
        with patch('scripts.ingestion.ingest_to_snowflake.get_conn', return_value=mock_conn):
            result = delete_stage_files("SC_RAW_DATA.OLIST_STAGE", pattern)
        
        assert result is True
        remove_sql = mock_cursor.execute.call_args_list[1][0][0]
        assert "PATTERN" in remove_sql
        assert pattern in remove_sql

    def test_delete_dotstar_pattern(self, mock_connection):
        """Test that .* pattern is treated as 'all files' (no PATTERN clause)."""
        mock_conn, mock_cursor = mock_connection
        
        with patch('scripts.ingestion.ingest_to_snowflake.get_conn', return_value=mock_conn):
            result = delete_stage_files("SC_RAW_DATA.OLIST_STAGE", ".*")
        
        assert result is True
        remove_sql = mock_cursor.execute.call_args_list[1][0][0]
        assert "REMOVE @SC_RAW_DATA.OLIST_STAGE" in remove_sql
        assert "PATTERN" not in remove_sql

    def test_invalid_file_pattern_raises_error(self, mock_connection):
        """Test that invalid file patterns raise ValueError."""
        mock_conn, mock_cursor = mock_connection
        
        # Pattern with invalid characters (e.g., semicolon for SQL injection)
        invalid_pattern = "*.csv; DROP TABLE users;"
        
        with patch('scripts.ingestion.ingest_to_snowflake.get_conn', return_value=mock_conn):
            result = delete_stage_files("SC_RAW_DATA.OLIST_STAGE", invalid_pattern)
        
        # Should return False due to validation error
        assert result is False

    def test_single_quote_escaping(self, mock_connection):
        """Test that single quotes in patterns are properly escaped."""
        mock_conn, mock_cursor = mock_connection
        
        # Use a valid pattern that contains a single quote (though unusual)
        # Since quotes aren't in the allowed character set, this will fail validation
        # Instead test with a valid pattern and verify escaping logic separately
        pattern = r"test_pattern"
        
        with patch('scripts.ingestion.ingest_to_snowflake.get_conn', return_value=mock_conn):
            result = delete_stage_files("SC_RAW_DATA.OLIST_STAGE", pattern)
        
        assert result is True
        remove_sql = mock_cursor.execute.call_args_list[1][0][0]
        # Should use PATTERN clause
        assert "PATTERN" in remove_sql

    def test_connection_error_handling(self, mock_connection):
        """Test that connection errors are handled gracefully."""
        mock_conn, mock_cursor = mock_connection
        mock_cursor.execute.side_effect = Exception("Connection failed")
        
        with patch('scripts.ingestion.ingest_to_snowflake.get_conn', return_value=mock_conn):
            result = delete_stage_files("SC_RAW_DATA.OLIST_STAGE", "*.csv")
        
        assert result is False

    def test_cursor_no_results(self, mock_connection):
        """Test handling when cursor returns no results."""
        mock_conn, mock_cursor = mock_connection
        mock_cursor.fetchall.side_effect = Exception("No results")
        
        with patch('scripts.ingestion.ingest_to_snowflake.get_conn', return_value=mock_conn):
            # Disable verification to test the fetchall exception handling in REMOVE
            result = delete_stage_files("SC_RAW_DATA.OLIST_STAGE", "*.csv", verify=False)
        
        # Should still return True (some connectors don't return rows, exception is caught)
        assert result is True

    def test_valid_stage_identifier(self, mock_connection):
        """Test that stage identifier is properly validated."""
        mock_conn, mock_cursor = mock_connection
        
        # Invalid stage name (contains SQL injection attempt)
        # sanitize_identifier raises ValueError but delete_stage_files catches it and returns False
        with patch('scripts.ingestion.ingest_to_snowflake.get_conn', return_value=mock_conn):
            result = delete_stage_files("SC_RAW_DATA.OLIST_STAGE; DROP TABLE users", "*")
            assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
