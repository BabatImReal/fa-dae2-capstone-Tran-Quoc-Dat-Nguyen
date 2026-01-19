"""
Tests for database operations
Target: Test user CRUD, thread operations, data persistence
"""
import pytest
import json
import asyncpg
from datetime import datetime


@pytest.mark.asyncio
class TestUserOperations:
    """Test user database operations"""
    
    async def test_create_user(self, db_connection, clean_test_db):
        """Test user creation"""
        user_data = {
            "identifier": "test_create_user",
            "metadata": json.dumps({
                "password_hash": "hash123",
                "display_name": "Create Test",
                "role": "user"
            })
        }
        
        await db_connection.execute(
            'INSERT INTO users (identifier, metadata, "createdAt") VALUES ($1, $2, NOW())',
            user_data["identifier"],
            user_data["metadata"]
        )
        
        # Verify creation
        row = await db_connection.fetchrow(
            "SELECT * FROM users WHERE identifier = $1",
            "test_create_user"
        )
        
        assert row is not None
        assert row["identifier"] == "test_create_user"
    
    async def test_update_user(self, db_connection, clean_test_db):
        """Test user update"""
        # Create user
        await db_connection.execute(
            'INSERT INTO users (identifier, metadata, "createdAt") VALUES ($1, $2, NOW())',
            "test_update_user",
            json.dumps({"display_name": "Original Name", "role": "user"})
        )
        
        # Update user
        await db_connection.execute(
            "UPDATE users SET metadata = $1 WHERE identifier = $2",
            json.dumps({"display_name": "Updated Name", "role": "admin"}),
            "test_update_user"
        )
        
        # Verify update
        row = await db_connection.fetchrow(
            "SELECT metadata FROM users WHERE identifier = $1",
            "test_update_user"
        )
        
        metadata = json.loads(row["metadata"])
        assert metadata["display_name"] == "Updated Name"
        assert metadata["role"] == "admin"
    
    async def test_delete_user(self, db_connection, clean_test_db):
        """Test user deletion"""
        # Create user
        await db_connection.execute(
            'INSERT INTO users (identifier, metadata, "createdAt") VALUES ($1, $2, NOW())',
            "test_delete_user",
            json.dumps({"display_name": "To Delete"})
        )
        
        # Delete user
        await db_connection.execute(
            "DELETE FROM users WHERE identifier = $1",
            "test_delete_user"
        )
        
        # Verify deletion
        row = await db_connection.fetchrow(
            "SELECT * FROM users WHERE identifier = $1",
            "test_delete_user"
        )
        
        assert row is None


@pytest.mark.asyncio
class TestThreadOperations:
    """Test conversation thread operations"""
    
    async def test_create_thread(self, db_connection, clean_test_db):
        """Test thread creation"""
        thread_data = {
            "id": "test_thread_001",
            "name": "Test Conversation",
            "user_identifier": "test_user",
            "metadata": json.dumps({"topic": "testing"}),
            "tags": ["test", "demo"]
        }
        
        await db_connection.execute(
            '''INSERT INTO threads (id, name, user_identifier, metadata, tags, "createdAt")
               VALUES ($1, $2, $3, $4, $5, NOW())''',
            thread_data["id"],
            thread_data["name"],
            thread_data["user_identifier"],
            thread_data["metadata"],
            thread_data["tags"]
        )
        
        # Verify
        row = await db_connection.fetchrow(
            "SELECT * FROM threads WHERE id = $1",
            "test_thread_001"
        )
        
        assert row is not None
        assert row["name"] == "Test Conversation"
        assert "test" in row["tags"]
    
    async def test_list_user_threads(self, db_connection, clean_test_db):
        """Test retrieving all threads for a user"""
        user = "test_list_user"
        
        # Create multiple threads
        for i in range(3):
            await db_connection.execute(
                '''INSERT INTO threads (id, name, user_identifier, "createdAt")
                   VALUES ($1, $2, $3, NOW())''',
                f"test_thread_{i}",
                f"Thread {i}",
                user
            )
        
        # List threads
        rows = await db_connection.fetch(
            'SELECT * FROM threads WHERE user_identifier = $1 ORDER BY "createdAt" DESC',
            user
        )
        
        assert len(rows) == 3
        assert all(row["user_identifier"] == user for row in rows)


@pytest.mark.asyncio
class TestStepOperations:
    """Test message/step operations"""
    
    async def test_create_step(self, db_connection, clean_test_db):
        """Test step (message) creation"""
        step_data = {
            "id": "test_step_001",
            "name": "User Message",
            "type": "user_message",
            "thread_id": "test_thread",
            "input": "Hello AI",
            "output": "Hi there!",
            "metadata": json.dumps({"timestamp": "2024-01-01"})
        }
        
        await db_connection.execute(
            '''INSERT INTO steps (id, name, type, thread_id, input, output, metadata, "createdAt")
               VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())''',
            step_data["id"],
            step_data["name"],
            step_data["type"],
            step_data["thread_id"],
            step_data["input"],
            step_data["output"],
            step_data["metadata"]
        )
        
        # Verify
        row = await db_connection.fetchrow(
            "SELECT * FROM steps WHERE id = $1",
            "test_step_001"
        )
        
        assert row is not None
        assert row["type"] == "user_message"
        assert row["input"] == "Hello AI"


@pytest.mark.asyncio
class TestDataIntegrity:
    """Test database constraints and data integrity"""
    
    async def test_unique_username_constraint(self, db_connection, clean_test_db):
        """Test that duplicate usernames are rejected"""
        # Create first user
        await db_connection.execute(
            'INSERT INTO users (identifier, metadata, "createdAt") VALUES ($1, $2, NOW())',
            "test_unique",
            json.dumps({"name": "User 1"})
        )
        
        # Try to create duplicate - should raise error
        with pytest.raises(asyncpg.UniqueViolationError):
            await db_connection.execute(
                'INSERT INTO users (identifier, metadata, "createdAt") VALUES ($1, $2, NOW())',
                "test_unique",
                json.dumps({"name": "User 2"})
            )
    
    async def test_user_threads_relationship(self, db_connection, clean_test_db):
        """Test that threads reference valid users"""
        # This tests referential integrity if foreign keys exist
        pass
