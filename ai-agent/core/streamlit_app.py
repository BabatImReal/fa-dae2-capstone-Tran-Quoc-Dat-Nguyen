#!/usr/bin/env python3
"""
M04W01L03 Lab: Streamlit UI for AI Agent

This script provides a web interface for the persistent AI agent using Streamlit.
It includes thread management, conversation history, and a modern chat interface.
"""

import time

import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from persistent_agent import create_persistent_agent

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Agent Chatbot - M04W01L03",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


def initialize_session_state():
    """Initialize Streamlit session state"""
    if "agent" not in st.session_state:
        st.session_state.agent = create_persistent_agent()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "thread_id" not in st.session_state:
        st.session_state.thread_id = f"streamlit_thread_{int(time.time())}"

    if "user_name" not in st.session_state:
        st.session_state.user_name = "User"

    if "session_id" not in st.session_state:
        st.session_state.session_id = f"streamlit_session_{int(time.time())}"

    if "conversation_metadata" not in st.session_state:
        st.session_state.conversation_metadata = {
            st.session_state.thread_id: {
                "name": "Main Conversation",
                "created_at": time.time(),
                "message_count": 0,
                "user_name": st.session_state.user_name,
            }
        }


def create_new_thread():
    """Create a new conversation thread"""
    new_thread_id = f"thread_{int(time.time())}"
    st.session_state.thread_id = new_thread_id
    st.session_state.messages = []

    # Add to conversation metadata
    st.session_state.conversation_metadata[new_thread_id] = {
        "name": f"Conversation {len(st.session_state.conversation_metadata)}",
        "created_at": time.time(),
        "message_count": 0,
        "user_name": st.session_state.user_name,
    }
    st.rerun()


def display_conversation_history():
    """Display the conversation history"""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def get_agent_response(user_input: str):
    """Get response from the agent using PostgreSQL persistence"""
    try:
        # Create configuration for this thread
        config = {"configurable": {"thread_id": st.session_state.thread_id}}

        # Get current conversation metadata
        current_metadata = st.session_state.conversation_metadata.get(
            st.session_state.thread_id, {}
        )

        # Prepare initial state with proper metadata
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "user_name": st.session_state.user_name,
            "conversation_count": current_metadata.get("message_count", 0),
            "session_id": st.session_state.session_id,
            "thread_metadata": {
                "created_at": current_metadata.get("created_at", time.time()),
                "user_name": st.session_state.user_name,
                "thread_name": current_metadata.get("name", "Unknown"),
                "interface": "streamlit",
            },
        }

        # Get agent response
        result = st.session_state.agent.invoke(initial_state, config)
        response = result["messages"][-1].content

        # Update conversation metadata
        if st.session_state.thread_id in st.session_state.conversation_metadata:
            st.session_state.conversation_metadata[st.session_state.thread_id][
                "message_count"
            ] += 1

        return response
    except Exception as e:
        return f"❌ Error: {e}"


def main():
    """Main Streamlit application"""

    # Initialize session state
    initialize_session_state()

    # Header
    st.title("🤖 AI Agent Chatbot")
    st.markdown("**M04W01L03 Lab: Building AI Agents with LangGraph**")

    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # User name input
        user_name = st.text_input(
            "Your Name",
            value=st.session_state.user_name,
            help="Enter your name for personalized conversations",
        )
        if user_name != st.session_state.user_name:
            st.session_state.user_name = user_name
            st.rerun()

        st.divider()

        # Thread management
        st.header("🧵 Thread Management")

        # Current thread display
        st.write("**Current Thread:**")
        st.code(st.session_state.thread_id)

        # New thread button
        if st.button("🆕 New Conversation", use_container_width=True):
            create_new_thread()

        # Thread ID input
        new_thread_id = st.text_input(
            "Switch to Thread ID",
            placeholder="Enter thread ID to switch",
            help="Enter a thread ID to continue a previous conversation",
        )

        if st.button("🔄 Switch Thread", use_container_width=True) and new_thread_id:
            st.session_state.thread_id = new_thread_id
            st.session_state.messages = []

            # Add to metadata if not exists
            if new_thread_id not in st.session_state.conversation_metadata:
                st.session_state.conversation_metadata[new_thread_id] = {
                    "name": f"Conversation {len(st.session_state.conversation_metadata)}",
                    "created_at": time.time(),
                    "message_count": 0,
                    "user_name": st.session_state.user_name,
                }
            st.rerun()

        # Show current thread info
        st.write(f"**Current Thread:** {st.session_state.thread_id}")

        # Always show available conversations
        st.write("**Available Conversations:**")
        for thread_id, metadata in st.session_state.conversation_metadata.items():
            status = "🟢" if thread_id == st.session_state.thread_id else "⚪"
            st.write(
                f"{status} {thread_id}: {metadata['name']} ({metadata['message_count']} messages)"
            )

        st.divider()

        # Session info
        st.header("📊 Session Info")
        st.write(f"**Session ID:** {st.session_state.session_id}")
        st.write(f"**Messages:** {len(st.session_state.messages)}")
        st.write(f"**User:** {st.session_state.user_name}")

        # Current conversation info
        current_metadata = st.session_state.conversation_metadata.get(
            st.session_state.thread_id, {}
        )
        st.write(f"**Thread Messages:** {current_metadata.get('message_count', 0)}")
        st.write(
            f"**Thread Created:** {time.ctime(current_metadata.get('created_at', time.time()))}"
        )

        st.divider()

        # Agent info
        st.header("🤖 Agent Info")
        st.write("**Model:** GPT-3.5 Turbo")
        st.write("**Framework:** LangGraph")
        st.write("**Storage:** PostgreSQL")

        # Persistent storage info
        st.header("💾 Persistent Storage")
        st.write("**Database:** PostgreSQL")
        st.write("**Host:** localhost:5433")
        st.write("**Database:** langgraph_memory")
        st.write("**Status:** ✅ Connected")
        st.write("**Features:**")
        st.write("• Conversation persistence")
        st.write("• Thread isolation")
        st.write("• Cross-session memory")
        st.write("• Automatic table creation")

        # Clear conversation button
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # Main chat interface
    st.header("💬 Chat")

    # Display conversation history
    display_conversation_history()

    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get and display agent response
        with st.chat_message("assistant"):
            with st.spinner("Agent is thinking..."):
                response = get_agent_response(prompt)
                st.markdown(response)

        # Add agent response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

    # Footer
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <p>🤖 AI Agent powered by LangGraph | M04W01L03 Lab | Foundry AI Academy</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()