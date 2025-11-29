#!/usr/bin/env python3
"""
M04W01L03 Lab: Persistent AI Agent with PostgreSQL

This script extends the basic agent with persistent database storage using PostgreSQL.
It includes thread management and conversation persistence across sessions.
"""

import os
import time
from typing import Annotated, TypedDict

import psycopg
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from psycopg.rows import dict_row

# Load environment variables
load_dotenv()


class PersistentAgentState(TypedDict):
    """Enhanced state schema for persistent agent"""

    messages: Annotated[list, add_messages]
    user_name: str
    conversation_count: int
    session_id: str
    thread_metadata: dict


def create_postgres_connection():
    """Create PostgreSQL connection for checkpointing"""
    try:
        # Build connection URI
        host = os.getenv("LANGGRAPH_POSTGRES_HOST")
        port = os.getenv("LANGGRAPH_POSTGRES_PORT")
        database = os.getenv("LANGGRAPH_POSTGRES_DB")
        user = os.getenv("LANGGRAPH_POSTGRES_USER")
        password = os.getenv("LANGGRAPH_POSTGRES_PASSWORD")

        db_uri = f"postgresql://{user}:{password}@{host}:{port}/{database}"

        # Create connection with autocommit and dict_row factory
        connection = psycopg.connect(db_uri, autocommit=True, row_factory=dict_row)
        return connection
    except Exception as e:
        print(f"❌ Error connecting to PostgreSQL: {e}")
        print("💡 Make sure PostgreSQL is running and credentials are correct in .env")
        return None


def create_persistent_agent():
    """Create an AI agent with persistent PostgreSQL storage"""

    # Initialize the LLM
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "1000")),
    )

    def enhanced_chatbot_node(state: PersistentAgentState):
        """Enhanced chatbot node with session tracking"""
        messages = state["messages"]
        user_name = state.get("user_name", "User")
        conversation_count = state.get("conversation_count", 0)
        session_id = state.get("session_id", "default")
        thread_metadata = state.get("thread_metadata", {})

        # Create enhanced system message
        system_message = f"""You are a helpful AI assistant for data engineering capstone projects.

        Session Information:
        - User: {user_name}
        - Session: {session_id}
        - Conversation: #{conversation_count + 1}
        - Thread Metadata: {thread_metadata}

        You can help with:
        - Data engineering concepts and best practices
        - Tool recommendations for capstone projects
        - Answering questions about data pipelines, databases, and analytics
        - Providing guidance on project planning and implementation
        - Remembering previous conversations in this session

        Be friendly, professional, and helpful. Reference previous conversations when relevant."""

        # Prepare messages for LLM
        full_messages = [{"role": "system", "content": system_message}] + messages

        # Get response from LLM
        response = llm.invoke(full_messages)

        # Update thread metadata
        updated_metadata = thread_metadata.copy()
        updated_metadata["last_interaction"] = time.time()
        updated_metadata["total_messages"] = len(messages) + 1

        return {
            "messages": [response],
            "conversation_count": conversation_count + 1,
            "thread_metadata": updated_metadata,
        }

    # Create the state graph
    graph_builder = StateGraph(PersistentAgentState)

    # Add the chatbot node
    graph_builder.add_node("chatbot", enhanced_chatbot_node)

    # Add an inspect node to print the state after the chatbot node runs
    def inspect_state_node(state: PersistentAgentState):
        messages = state.get("messages", [])
        messages_len = len(messages)

        # Header summary
        print(
            f"[inspect_state] user={state.get('user_name')} conv_count={state.get('conversation_count')} messages_len={messages_len}"
        )

        # Print stacked messages (role: content) one per line
        print("[inspect_state] Message stack:")
        for i, m in enumerate(messages, start=1):
            # Determine content
            if isinstance(m, dict):
                role = m.get("role", "user")
                content = m.get("content", "")
            else:
                # message objects may have .content and sometimes .role
                content = getattr(m, "content", None)
                role = getattr(m, "role", None)

                if content is None:
                    # fallback to string representation
                    try:
                        content = str(m)
                    except Exception:
                        content = "<unrepresentable>"

                if role is None:
                    # best-effort from class name
                    cname = type(m).__name__.lower()
                    if "human" in cname or "user" in cname:
                        role = "user"
                    elif "ai" in cname or "assistant" in cname:
                        role = "assistant"
                    else:
                        role = "unknown"

            # Truncate content for readability but show full lines stacked
            preview = str(content)
            # Print with index for clarity
            print(f"  {i}. {role}: {preview}")

        print("[inspect_state] end stack\n")

        # Return state unchanged; this node is purely observational
        return state

    # Add edges: run chatbot then inspect the state before ending
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_node("inspect_state", inspect_state_node)
    graph_builder.add_edge("chatbot", "inspect_state")
    graph_builder.add_edge("inspect_state", END)

    # Create PostgreSQL checkpointer
    connection = create_postgres_connection()
    if connection is None:
        print("⚠️ Falling back to in-memory storage")
        from langgraph.checkpoint.memory import InMemorySaver

        memory = InMemorySaver()
    else:
        memory = PostgresSaver(connection)
        memory.setup()  # Create necessary tables
        print("✅ Connected to PostgreSQL for persistent storage")

    # Compile the graph with persistent memory
    graph = graph_builder.compile(
        checkpointer=memory,
        interrupt_before=["tools"])

    return graph


def list_available_threads(agent):
    """List available conversation threads from the database"""
    try:
        # Get all thread IDs from the checkpointer
        # Note: This is a simplified implementation
        # In a real scenario, you'd query the database directly
        print("📋 Available Conversation Threads:")
        print("-" * 50)
        print("Note: Thread listing requires database query implementation")
        print("For now, you can switch to any thread ID you know")
        print("-" * 50)
    except Exception as e:
        print(f"❌ Error listing threads: {e}")


def test_persistent_functionality():
    """Test the persistent agent functionality"""
    print("🧪 Testing Persistent Agent Functionality")
    print("=" * 60)

    agent = create_persistent_agent()

    # Test with multiple threads
    threads = [
        ("thread_1", "Alice"),
        ("thread_2", "Bob"),
        ("thread_1", "Alice"),  # Same thread, should remember
    ]

    for thread_id, user_name in threads:
        print(f"\nTesting thread: {thread_id} with user: {user_name}")

        config = {"configurable": {"thread_id": thread_id}}

        # First message
        initial_state = {
            "messages": [HumanMessage(content=f"Hello! My name is {user_name}")],
            "user_name": user_name,
            "conversation_count": 0,
            "session_id": "test_session",
            "thread_metadata": {"test": True},
        }

        result = agent.invoke(initial_state, config)
        response = result["messages"][-1].content
        print(f"Response: {response[:100]}...")

        # Second message (should remember name)
        follow_up_state = {
            "messages": [HumanMessage(content="What's my name?")],
            "user_name": user_name,
            "conversation_count": 1,
            "session_id": "test_session",
            "thread_metadata": {"test": True},
        }

        result = agent.invoke(follow_up_state, config)
        response = result["messages"][-1].content
        print(f"Memory test: {response[:100]}...")
        print("-" * 50)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_persistent_functionality()
    else:
        print("🤖 Persistent Agent Core Module")
        print("=" * 50)
        print("This module provides the core agent functionality.")
        print("To run the CLI interface, use: uv run python cli_interface.py")
        print("To run tests, use: uv run python persistent_agent.py test")
        print("=" * 50)