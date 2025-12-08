#!/usr/bin/env python3
"""
Streamlit UI for Tool-Calling Agent

A modern web interface for the data analyst AI agent with Snowflake and PostgreSQL tools.
"""

import time
import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from tool_calling_agent import create_tool_calling_agent

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Data Analyst AI Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better UI
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .tool-call {
        background-color: #f0f2f6;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin: 0.5rem 0;
        font-family: monospace;
        font-size: 0.9em;
    }
    .tool-result {
        background-color: #e8f4f8;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin: 0.5rem 0;
        font-size: 0.9em;
    }
    .stButton > button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state"""
    if "agent" not in st.session_state:
        with st.spinner("🔧 Initializing AI Agent..."):
            st.session_state.agent = create_tool_calling_agent()
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "show_debug" not in st.session_state:
        st.session_state.show_debug = False


def format_tool_call(tool_call):
    """Format tool call for display"""
    name = tool_call.get("name", "unknown")
    args = tool_call.get("args", {})
    
    args_str = ", ".join([f"{k}='{v}'" for k, v in args.items()]) if args else "no args"
    return f"🔧 **Tool Call:** `{name}({args_str})`"


def format_tool_result(content):
    """Format tool result for display"""
    # Truncate very long results
    if len(content) > 1000:
        content = content[:1000] + "... (truncated)"
    return f"📋 **Tool Result:**\n```\n{content}\n```"


def display_message(message):
    """Display a message in the chat interface"""
    if isinstance(message, HumanMessage):
        with st.chat_message("user", avatar="👤"):
            st.markdown(message.content)
    
    elif isinstance(message, AIMessage):
        with st.chat_message("assistant", avatar="🤖"):
            # Show tool calls if present
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    if st.session_state.show_debug:
                        st.markdown(format_tool_call(tool_call))
            
            # Show content if present
            if message.content:
                st.markdown(message.content)
    
    elif isinstance(message, ToolMessage):
        if st.session_state.show_debug:
            with st.chat_message("assistant", avatar="⚙️"):
                st.markdown(format_tool_result(message.content))


def clear_conversation():
    """Clear the conversation history"""
    st.session_state.messages = []
    st.rerun()


def main():
    """Main Streamlit application"""
    initialize_session_state()
    
    # Sidebar
    with st.sidebar:
        st.title("📊 Data Analyst Agent")
        st.markdown("---")
        
        st.markdown("### 🛠️ Available Tools")
        st.markdown("""
        - **Product Categories** (Snowflake)
        - **Product by Category** (Snowflake)
        - **Order Summary by Quarter** (Snowflake)
        - **Latest Product Summary** (PostgreSQL)
        """)
        
        st.markdown("---")
        
        st.markdown("### 💡 Example Queries")
        example_queries = [
            "Show me all product categories",
            "Get a product from the health_beauty category",
            "What were the order statistics for Q3 2018?",
            "Get me the latest product summary from PostgreSQL",
        ]
        
        for query in example_queries:
            if st.button(query, key=f"example_{query}"):
                st.session_state.temp_input = query
        
        st.markdown("---")
        
        # Settings
        st.markdown("### ⚙️ Settings")
        st.session_state.show_debug = st.checkbox(
            "Show Debug Info",
            value=st.session_state.show_debug,
            help="Show tool calls and results"
        )
        
        st.markdown("---")
        
        # Clear conversation
        if st.button("🗑️ Clear Conversation", type="secondary"):
            clear_conversation()
        
        st.markdown("---")
        
        # Stats
        st.markdown("### 📈 Statistics")
        st.metric("Total Messages", len(st.session_state.messages))
        
        user_messages = sum(1 for m in st.session_state.messages if isinstance(m, HumanMessage))
        st.metric("User Messages", user_messages)
    
    # Main chat interface
    st.title("🤖 Data Analyst AI Agent")
    st.markdown("Ask me about products, orders, and analytics data!")
    
    # Display chat history
    for message in st.session_state.messages:
        display_message(message)
    
    # Chat input
    if prompt := st.chat_input("Ask me about your data..."):
        # Add user message to history
        user_message = HumanMessage(content=prompt)
        st.session_state.messages.append(user_message)
        
        # Display user message
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        
        # Get agent response
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🤔 Thinking..."):
                try:
                    # Invoke agent with current conversation
                    result = st.session_state.agent.invoke({
                        "messages": [user_message]
                    })
                    
                    # Process all messages from result
                    for msg in result["messages"]:
                        if isinstance(msg, HumanMessage):
                            continue  # Skip, already displayed
                        
                        # Add to history
                        st.session_state.messages.append(msg)
                        
                        # Display based on message type
                        if isinstance(msg, AIMessage):
                            # Show tool calls if debug mode
                            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                if st.session_state.show_debug:
                                    for tool_call in msg.tool_calls:
                                        st.markdown(format_tool_call(tool_call))
                            
                            # Show content
                            if msg.content:
                                st.markdown(msg.content)
                        
                        elif isinstance(msg, ToolMessage):
                            if st.session_state.show_debug:
                                st.markdown(format_tool_result(msg.content))
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.exception(e)
        
        # Rerun to update the display
        st.rerun()
    
    # Handle example query button clicks
    if hasattr(st.session_state, 'temp_input'):
        prompt = st.session_state.temp_input
        del st.session_state.temp_input
        st.rerun()


if __name__ == "__main__":
    main()
