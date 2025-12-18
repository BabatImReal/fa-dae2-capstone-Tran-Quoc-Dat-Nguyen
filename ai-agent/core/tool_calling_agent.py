#!/usr/bin/env python3
"""
M04W02L02 Lab: Tool Calling Agent with LangGraph

This script demonstrates how to integrate tools with AI agents using LangGraph.
It follows the exact pattern from the LangGraph documentation for building
agents that can use tools in a loop based on environmental feedback.

This version includes mock tools for Snowflake queries and Pinecone vector search,
similar to the capstone AI agent structure.
"""

import os
from typing import Any, Dict, Literal

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
import sys
from pathlib import Path

# Make the `ai-agent/tools` package importable when running this script directly
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.snowflake_tools import (
    get_all_product_categories_from_snowflake,
    get_product_by_category_from_snowflake, 
    get_order_summary_by_quarter_from_snowflake,
)

from tools.postgre_tools import (
    get_latest_product_summary_from_postgre
)

from tools.rag_tools import (
    search_documents
)

# Load environment variables
load_dotenv()

import json

def print_state(state: MessagesState, step_name: str):
    """Pretty print the current state for debugging purposes"""
    print(f"\n{'='*50}")
    print(f"Step: {step_name}")
    print("Current State:")
    # Convert messages to a serializable format
    serializable_messages = []
    for msg in state["messages"]:
        try:
            msg_data = {
                "type": type(msg).__name__,
                "content": str(msg.content)[:500] if hasattr(msg, 'content') else str(msg)[:500]
            }
            # Add tool calls if present
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                msg_data["tool_calls"] = []
                for tc in msg.tool_calls:
                    tool_call_data = {
                        "name": str(tc.get("name", "unknown")),
                        "args": {k: str(v) for k, v in tc.get("args", {}).items()}
                    }
                    msg_data["tool_calls"].append(tool_call_data)
            serializable_messages.append(msg_data)
        except Exception as e:
            serializable_messages.append({
                "type": type(msg).__name__,
                "error": f"Could not serialize: {str(e)}"
            })
    
    serializable_state = {
        "messages": serializable_messages,
        "message_count": len(state["messages"])
    }
    try:
        print(json.dumps(serializable_state, indent=2, default=str))
    except Exception as e:
        print(f"Error printing state: {e}")
        print(f"Message count: {len(state['messages'])}")
    print(f"{'='*50}\n")


def create_tool_calling_agent():
    """Create a tool-calling agent using LangGraph StateGraph"""

    # Initialize LLM
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0.1,  # Lower temperature for more consistent tool usage
    )

    # Create tool registry
    tools = [get_all_product_categories_from_snowflake, 
             get_product_by_category_from_snowflake, 
             get_order_summary_by_quarter_from_snowflake,
             get_latest_product_summary_from_postgre,
             search_documents]
    tools_by_name = {tool.name: tool for tool in tools}

    # Augment the LLM with tools
    llm_with_tools = llm.bind_tools(tools)

    # Define the agent nodes
    def llm_call(state: MessagesState):
        """LLM decides whether to call a tool or not"""
        print_state(state, "Before LLM Call")
        return {
            "messages": [
                llm_with_tools.invoke(
                    [
                        SystemMessage(
                            content="""You are a helpful data analyst assistant. You have access to the following tools:

Available tools:
- get_all_product_categories_from_snowflake: Get all unique product categories from Snowflake
- get_product_by_category_from_snowflake: Retrieve 1 product from a given product category
- get_order_summary_by_quarter_from_snowflake: Get order summary statistics for a specific year and quarter
- get_latest_product_summary_from_postgre: Get the latest ingested product event from PostgreSQL
- search_documents: Search for information in capstone documents using semantic similarity

Always use the appropriate tool when the user asks about:
- Product categories → use get_all_product_categories_from_snowflake
- Product information by category → use get_product_by_category_from_snowflake
- Quarterly order statistics → use get_order_summary_by_quarter_from_snowflake
- Latest product or recent ingestion → use get_latest_product_summary_from_postgre
- Document search or information retrieval → use search_documents

Be professional, friendly, and helpful. Provide clear and accurate responses based on the tool results."""
                        )
                    ]
                    + state["messages"]
                )
            ]
        }

    def tool_node(state: dict):
        """Performs the tool call"""
        print_state(state, "Before Tool Execution")
        result = []
        for tool_call in state["messages"][-1].tool_calls:
            tool = tools_by_name[tool_call["name"]]
            try:
                observation = tool.invoke(tool_call["args"])
                result.append(
                    ToolMessage(content=str(observation), tool_call_id=tool_call["id"])
                )
            except Exception as e:
                error_msg = f"Error executing {tool_call['name']}: {str(e)}"
                result.append(
                    ToolMessage(content=error_msg, tool_call_id=tool_call["id"])
                )
        return {"messages": result}

    # Conditional edge function to route based on tool calls
    def should_continue(state: MessagesState) -> Literal["tools", "end"]:
        """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""
        messages = state["messages"]
        last_message = messages[-1]

        # If the LLM makes a tool call, then perform an action
        if last_message.tool_calls:
            return "tools"
        # Otherwise, we stop (reply to the user)
        return "end"

    # Build workflow
    agent_builder = StateGraph(MessagesState)

    # Add nodes
    agent_builder.add_node("llm_call", llm_call)
    agent_builder.add_node("tools", tool_node)

    # Add edges to connect nodes
    agent_builder.add_edge(START, "llm_call")
    agent_builder.add_conditional_edges(
        "llm_call",
        should_continue,
        {
            # Name returned by should_continue : Name of next node to visit
            "tools": "tools",
            "end": END,
        },
    )
    agent_builder.add_edge("tools", "llm_call")

    # Compile the agent
    agent = agent_builder.compile()

    return agent


def visualize_agent_workflow(agent):
    """Generate and display the agent workflow diagram"""
    try:
        # Generate Mermaid diagram
        mermaid_code = agent.get_graph().draw_mermaid()
        print("🔍 Agent Workflow (Mermaid Diagram):")
        print("=" * 60)
        print(mermaid_code)
        print("=" * 60)
        print("💡 Copy the Mermaid code above to https://mermaid.live/ to visualize")

        # Try to display as PNG (works in Jupyter)
        try:
            from IPython.display import Image, display  # type: ignore

            png_image = agent.get_graph().draw_mermaid_png()
            display(Image(png_image))
        except ImportError:
            print("📊 PNG visualization requires IPython (Jupyter environment)")

    except Exception as e:
        print(f"❌ Error generating workflow diagram: {e}")


def test_tool_calling_agent():
    """Test the tool-calling agent with various inputs"""
    print("🧪 Testing Tool-Calling Agent")
    print("=" * 60)

    agent = create_tool_calling_agent()

    # Test cases
    test_cases = [
        "Find information about user Pamela",
        "Show me transactions for Pamela",
        "What is the company vacation policy?",
        "Search for user Pamela and show her transaction history",
        "What are the company policies?",
        "Find user Pamela and check the vacation policy",
    ]

    for i, test_input in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_input}")
        print("-" * 40)

        try:
            result = agent.invoke({"messages": [HumanMessage(content=test_input)]})

            # Display the conversation
            for j, message in enumerate(result["messages"]):
                if hasattr(message, "tool_calls") and message.tool_calls:
                    print(
                        f"🔧 Tool calls: {[call['name'] for call in message.tool_calls]}"
                    )
                elif hasattr(message, "content"):
                    print(f"💬 {message.content}")

        except Exception as e:
            print(f"❌ Error: {e}")

        print("-" * 40)


def interactive_demo():
    """Interactive demo of the tool-calling agent"""
    print("🤖 Tool-Calling Agent Interactive Demo")
    print("=" * 60)
    print("Available tools:")
    print("  • Snowflake User Search (returns 1 user profile)")
    print("  • Snowflake Transaction Search (returns up to 10 transactions)")
    print("  • Company Policy Search (Pinecone - comprehensive policy coverage)")
    print("")
    print("Try these examples:")
    print("  - 'Find information about user Pamela'")
    print("  - 'Show me transactions for Pamela'")
    print("  - 'What is the company vacation policy?'")
    print("  - 'Search for user Pamela and show her transaction history'")
    print("  - 'What are the company policies?'")
    print("  - 'quit' to exit")
    print("=" * 60)

    agent = create_tool_calling_agent()

    while True:
        try:
            user_input = input("\n👤 You: ").strip()

            if user_input.lower() in ["quit", "exit", "bye"]:
                print("👋 Goodbye!")
                break

            if not user_input:
                continue

            print("🤖 Agent: ", end="", flush=True)

            result = agent.invoke({"messages": [HumanMessage(content=user_input)]})

            # Display the final response
            final_message = result["messages"][-1]
            if hasattr(final_message, "content"):
                print(final_message.content)

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_tool_calling_agent()
        elif sys.argv[1] == "visualize":
            agent = create_tool_calling_agent()
            visualize_agent_workflow(agent)
        elif sys.argv[1] == "interactive":
            interactive_demo()
        else:
            print("Usage: python tool_calling_agent.py [test|visualize|interactive]")
    else:
        print("🤖 Tool-Calling Agent")
        print("=" * 50)
        print("Available commands:")
        print("  python tool_calling_agent.py test        - Run test cases")
        print("  python tool_calling_agent.py visualize   - Show workflow diagram")
        print("  python tool_calling_agent.py interactive - Interactive demo")
        print("=" * 50)