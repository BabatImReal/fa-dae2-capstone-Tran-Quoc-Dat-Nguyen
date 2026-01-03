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

from tools.rag_combined_tools import (
    hybrid_search_documents
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


def create_tool_calling_agent(human_in_the_loop: bool = True):
    """Create a tool-calling agent using LangGraph StateGraph
    
    Args:
        human_in_the_loop: If True, ask for approval before executing tools (default: True)
    """

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
             search_documents,
             hybrid_search_documents]
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
                            content="""You are a helpful data analyst assistant with access to multiple data sources.

Available tools:
- get_all_product_categories_from_snowflake: Get all unique product categories from Snowflake
- get_product_by_category_from_snowflake: Retrieve 1 product from a given product category
- get_order_summary_by_quarter_from_snowflake: Get order summary statistics for a specific year and quarter
- get_latest_product_summary_from_postgre: Get the latest ingested product event from PostgreSQL
- search_documents: OLD METHOD - Search for information using ONLY semantic/dense similarity (single search method)
- hybrid_search_documents: RECOMMENDED - Search for information using BOTH semantic (dense) AND lexical (sparse) similarity with reranking

SEARCH TOOLS COMPARISON:
╔════════════════════════════════════════════════════════════════════╗
║ search_documents (Semantic Only - Legacy)                          ║
║ - Uses dense embeddings only (semantic/contextual meaning)         ║
║ - Single search method: Fast but may miss exact keyword matches    ║
║ - No reranking                                                      ║
║ - Use when: Need quick semantic search only                        ║
╠════════════════════════════════════════════════════════════════════╣
║ hybrid_search_documents (Hybrid - RECOMMENDED)                     ║
║ - Uses BOTH dense (semantic) AND sparse (keyword) embeddings      ║
║ - Combines 2 search methods: Better coverage of both meaning & keywords
║ - Merges & deduplicates results from both indexes                 ║
║ - Final reranking with bge-reranker-v2-m3 (cross-encoder model)   ║
║ - Use when: Need comprehensive search combining semantics + keywords
║ - Parameters:                                                       ║
║   • query (required): Search query                                 ║
║   • top_k (optional, default=3): Number of results                ║
║   • alpha (optional, default=0.5): 0.0=pure keywords, 1.0=pure semantic
╚════════════════════════════════════════════════════════════════════╝

RECOMMENDED TOOL SELECTION:
- ALWAYS use hybrid_search_documents for document searches (better quality results)
- ONLY use search_documents if you specifically need legacy behavior
- Character/person names (Fiona, Donkey, Pamela) → hybrid_search_documents
- Movie/book titles (BeeMovie, Shrek) → hybrid_search_documents
- Unknown topics or document content → hybrid_search_documents
- All topics not relating to products, categories, or summary of orders → hybrid_search_documents
- Product categories → get_all_product_categories_from_snowflake
- Specific product from category → get_product_by_category_from_snowflake
- Orders/quarterly data → get_order_summary_by_quarter_from_snowflake
- Latest data → get_latest_product_summary_from_postgre
- DO NOT use any search tool for general questions like:
  - Personal questions (e.g., "What is my name?", "How are you?", "What's the weather?")
  - General knowledge questions (e.g., "What is Python?", "How does machine learning work?")
  - Conversational questions (e.g., "Hello", "Thank you", "Good morning")
- For general questions, answer directly using your own knowledge

YOUR JOB AFTER TOOLS ARE CALLED:
The tool results will be displayed to the user in raw format. Your job is NOT to reformat them.
Instead, provide a brief ANALYSIS/SYNTHESIS of what the raw results mean:
- Highlight key findings from the results
- Answer the user's original question based on the results
- Provide insights or observations
- Do NOT reformat or restructure the raw data - just analyze it

IMPORTANT: If MULTIPLE TOOLS were used, you MUST provide:
1. Individual response analysis for each tool used
2. A final summary section that synthesizes all tool responses together

Format for multiple tools:
---
Tool 1 Response: [Tool Name]
[Brief analysis of what this tool returned]

Tool 2 Response: [Tool Name]
[Brief analysis of what this tool returned]

Tool 3 Response: [Tool Name] (if applicable)
[Brief analysis of what this tool returned]

---
SUMMARY:
[Synthesize all tool responses together to answer the user's question comprehensively]
---

Example:
User: "Tell me about Fiona and show me product categories"
[RAW TOOL OUTPUT SHOWN BY SYSTEM]
Your response should be:
"Tool 1 Response: hybrid_search_documents
Based on the search results, Fiona is a character from Shrek who appears in several key scenes...

Tool 2 Response: get_all_product_categories_from_snowflake  
The query returned 15 unique product categories from the Snowflake database...

SUMMARY:
The analysis shows information from two different data sources: character information from documents (Fiona from Shrek) and product catalog data (15 categories). These results address both parts of your query by providing character details and product category information."

Keep your analysis brief and focused on answering the user's question."""
                        )
                    ]
                    + state["messages"]
                )
            ]
        }

    def human_approval_node(state: dict):
        """Ask for human approval before executing tools"""
        print_state(state, "Human Approval Required")
        last_message = state["messages"][-1]
        tool_calls = last_message.tool_calls
        
        print("\n" + "="*60)
        print("🔔 TOOL APPROVAL REQUIRED")
        print("="*60)
        print(f"\nThe agent wants to execute {len(tool_calls)} tool(s):\n")
        
        for i, tool_call in enumerate(tool_calls, 1):
            print(f"  {i}. 🔧 Tool: {tool_call['name']}")
            if tool_call["args"]:
                print(f"     📝 Arguments:")
                for key, value in tool_call["args"].items():
                    # Truncate long values for readability
                    value_str = str(value)
                    if len(value_str) > 100:
                        value_str = value_str[:97] + "..."
                    print(f"        • {key}: {value_str}")
            else:
                print(f"     📝 Arguments: (none)")
            print()
        
        while True:
            decision = input("\n🤔 Approve execution? (yes/y to approve, no/n to reject): ").strip().lower()
            if decision in ['yes', 'y']:
                print("✅ Approved! Executing tools...\n")
                return {"messages": []}  # Continue to tool execution
            elif decision in ['no', 'n']:
                print("❌ Rejected! Stopping execution.\n")
                # Create a message indicating rejection
                rejection_msg = "Tool execution was rejected by the user."
                return {
                    "messages": [
                        ToolMessage(
                            content=rejection_msg,
                            tool_call_id=tool_calls[0]["id"] if tool_calls else "rejected"
                        )
                    ]
                }
            else:
                print("❓ Please enter 'yes' or 'no'")
    
    def tool_node(state: dict):
        """Performs the tool call"""
        print_state(state, "Before Tool Execution")
        result = []
        tool_calls = state["messages"][-1].tool_calls
        
        for tool_call in tool_calls:
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
        
        # Display individual tool responses and summary if human-in-the-loop is enabled
        if human_in_the_loop and len(tool_calls) > 1:
            print("\n" + "="*60)
            print("📊 TOOL EXECUTION RESULTS")
            print("="*60 + "\n")
            
            # Show each tool response individually
            for i, (tool_call, tool_result) in enumerate(zip(tool_calls, result), 1):
                print(f"🔧 Tool {i}: {tool_call['name']}")
                print("-" * 60)
                
                # Display full response
                response_content = str(tool_result.content)
                if tool_result.content.startswith("Error"):
                    print(f"❌ {response_content}")
                else:
                    # Try to format JSON nicely if possible
                    try:
                        import json
                        if isinstance(tool_result.content, str) and (tool_result.content.startswith('{') or tool_result.content.startswith('[')):
                            parsed = json.loads(tool_result.content)
                            print(json.dumps(parsed, indent=2))
                        else:
                            print(response_content)
                    except:
                        print(response_content)
                print()
            
            # Summary of all responses
            print("="*60)
            print("📋 SUMMARY OF ALL TOOL RESPONSES")
            print("="*60)
            success_count = sum(1 for r in result if not str(r.content).startswith("Error"))
            error_count = len(result) - success_count
            
            print(f"Total tools executed: {len(tool_calls)}")
            print(f"✅ Successful: {success_count}")
            if error_count > 0:
                print(f"❌ Failed: {error_count}")
            
            print("\nBrief overview:")
            for i, (tool_call, tool_result) in enumerate(zip(tool_calls, result), 1):
                status = "✅" if not str(tool_result.content).startswith("Error") else "❌"
                result_snippet = str(tool_result.content)[:100].replace('\n', ' ')
                if len(str(tool_result.content)) > 100:
                    result_snippet += "..."
                print(f"  {i}. {status} {tool_call['name']}: {result_snippet}")
            
            print("="*60 + "\n")
        
        return {"messages": result}

    # Conditional edge function to route based on tool calls
    def should_continue(state: MessagesState) -> Literal["approval", "tools", "end"]:
        """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""
        messages = state["messages"]
        last_message = messages[-1]

        # If the LLM makes a tool call, then perform an action
        if last_message.tool_calls:
            if human_in_the_loop:
                return "approval"  # Route to approval node first
            else:
                return "tools"  # Execute directly without approval
        # Otherwise, we stop (reply to the user)
        return "end"

    # Build workflow
    agent_builder = StateGraph(MessagesState)

    # Add nodes
    agent_builder.add_node("llm_call", llm_call)
    agent_builder.add_node("tools", tool_node)
    if human_in_the_loop:
        agent_builder.add_node("approval", human_approval_node)

    # Add edges to connect nodes
    agent_builder.add_edge(START, "llm_call")
    
    if human_in_the_loop:
        agent_builder.add_conditional_edges(
            "llm_call",
            should_continue,
            {
                # Name returned by should_continue : Name of next node to visit
                "approval": "approval",
                "tools": "tools",
                "end": END,
            },
        )
        agent_builder.add_edge("approval", "tools")  # After approval, execute tools
    else:
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


def interactive_demo(human_in_the_loop: bool = True):
    """Interactive demo of the tool-calling agent
    
    Args:
        human_in_the_loop: If True, ask for approval before executing tools (default: True)
    """
    print("🤖 Tool-Calling Agent Interactive Demo")
    print("=" * 60)
    if human_in_the_loop:
        print("⚠️  HUMAN-IN-THE-LOOP MODE ENABLED")
        print("   You will be asked to approve tool execution before running.")
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

    agent = create_tool_calling_agent(human_in_the_loop=human_in_the_loop)

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
            # Check for --no-hitl flag to disable (enabled by default)
            hitl = "--no-hitl" not in sys.argv
            interactive_demo(human_in_the_loop=hitl)
        else:
            print("Usage: python tool_calling_agent.py [test|visualize|interactive [--hitl]]")
    else:
        print("🤖 Tool-Calling Agent")
        print("=" * 50)
        print("Available commands:")
        print("  python tool_calling_agent.py test                     - Run test cases")
        print("  python tool_calling_agent.py visualize                - Show workflow diagram")
        print("  python tool_calling_agent.py interactive              - Interactive demo (HITL enabled by default)")
        print("  python tool_calling_agent.py interactive --no-hitl    - Interactive without Human-in-the-Loop")
        print("=" * 50)