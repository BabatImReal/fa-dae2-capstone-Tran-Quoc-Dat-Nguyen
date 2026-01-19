"""
Pytest configuration and shared fixtures for Chainlit app tests
"""
import pytest
import asyncio
import asyncpg
import os
from typing import AsyncGenerator
from unittest.mock import Mock, AsyncMock


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_connection() -> AsyncGenerator:
    """Provide a test database connection"""
    db_url = os.getenv(
        "CHAINLIT_POSTGRES_URL",
        "postgresql://chainlit:chainlit_password@localhost:5434/chainlit_db"
    ).replace("postgresql+asyncpg://", "postgresql://")
    
    conn = await asyncpg.connect(db_url)
    yield conn
    await conn.close()


@pytest.fixture
async def clean_test_db(db_connection):
    """Clean test database before and after tests"""
    # Clean before test
    await db_connection.execute("DELETE FROM users WHERE identifier LIKE 'test_%'")
    await db_connection.execute("DELETE FROM threads WHERE id LIKE 'test_%'")
    await db_connection.execute("DELETE FROM steps WHERE id LIKE 'test_%'")
    
    yield
    
    # Clean after test
    await db_connection.execute("DELETE FROM users WHERE identifier LIKE 'test_%'")
    await db_connection.execute("DELETE FROM threads WHERE id LIKE 'test_%'")
    await db_connection.execute("DELETE FROM steps WHERE id LIKE 'test_%'")


@pytest.fixture
def mock_chainlit_user():
    """Mock Chainlit User object"""
    user = Mock()
    user.identifier = "test_user"
    user.metadata = {
        "display_name": "Test User",
        "role": "user",
        "provider": "credentials"
    }
    return user


@pytest.fixture
def mock_chainlit_message():
    """Mock Chainlit Message object"""
    message = AsyncMock()
    message.content = "Test message"
    message.send = AsyncMock()
    message.update = AsyncMock()
    return message


@pytest.fixture
def sample_test_user():
    """Sample user data for testing"""
    return {
        "identifier": "test_user_123",
        "password": "testpass123",
        "display_name": "Test User",
        "role": "user"
    }


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-4o-mini",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Test response from AI"
            },
            "finish_reason": "stop"
        }]
    }


@pytest.fixture
def mock_postgres_query_result():
    """Mock PostgreSQL query result"""
    return [
        {"product_name": "Product A", "category": "Electronics", "sales": 1000},
        {"product_name": "Product B", "category": "Electronics", "sales": 1500},
    ]


@pytest.fixture
def mock_rag_search_result():
    """Mock RAG search result"""
    return {
        "results": [
            {
                "id": "chunk_001",
                "score": 0.95,
                "metadata": {"source": "document.pdf", "page": 1},
                "text": "Test document content about data engineering"
            }
        ]
    }
