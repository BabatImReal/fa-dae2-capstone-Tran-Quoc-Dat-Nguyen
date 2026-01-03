import sys
from pathlib import Path
from typing import Dict, Any

# ensure local modules are importable when running this script directly
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain_core.messages import HumanMessage

# Import the agent creation function robustly. Try several styles depending on how
# the repository is executed. If imports fail, load the module directly from file.
try:
    # when running from the repo root with ai-agent on sys.path
    from core.tool_calling_agent import create_tool_calling_agent
except Exception:
    try:
        # when running from ai-agent/core as cwd
        from tool_calling_agent import create_tool_calling_agent
    except Exception:
        # Last resort: load module directly by file path
        import importlib.util

        module_path = Path(__file__).resolve().parents[1] / "core" / "tool_calling_agent.py"
        spec = importlib.util.spec_from_file_location("tool_calling_agent", str(module_path))
        tool_module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(tool_module)
        create_tool_calling_agent = getattr(tool_module, "create_tool_calling_agent")

def cli_interface_with_tools(human_in_the_loop: bool = True):
    """CLI interface for the tool-calling agent
    
    Args:
        human_in_the_loop: If True, ask for approval before executing tools (default: True)
    """
    print("🤖 Tool-Calling AI Agent")
    print("=" * 60)
    if human_in_the_loop:
        print("⚠️  HUMAN-IN-THE-LOOP MODE ENABLED")
        print("   You will be asked to approve tool execution before running.")
        print("=" * 60)
    print("This agent can:")
    print("  • Retrieve a product from a specific category")
    print("  • Get order summary for a specific year and quarter")
    print("  • Get latest product information from PostgreSQL")
    print("  • Search capstone documents using semantic similarity")
    print("  • Use multiple tools in sequence for complex queries")
    print("")
    print("Commands:")
    print("  'quit'     - Exit the application")
    print("  'help'     - Show available tools and their usage")
    print("  'examples' - Show example queries")
    print("=" * 60)

    # Create the tool-calling agent with human-in-the-loop option
    agent = create_tool_calling_agent(human_in_the_loop=human_in_the_loop)

    # Get user name
    user_name = input("What's your name? ").strip() or "User"
    print(f"\nHello {user_name}! How can I help you today?")
    print("Try asking me about products, shipping tiers, or order summaries!")

    while True:
        try:
            user_input = input(f"\n{user_name}: ").strip()

            if user_input.lower() in ["quit", "exit", "bye"]:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == "help":
                show_help()
                continue
            elif user_input.lower() == "examples":
                show_examples()
                continue
            elif not user_input:
                continue

            print("🤖 Agent: ", end="", flush=True)

            # Get agent response
            result = agent.invoke({"messages": [HumanMessage(content=user_input)]})

            # Display the conversation flow
            display_conversation_flow(result)

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def show_help():
    """Show available tools and their usage"""
    print("\n🛠️ Available Tools:")
    print("-" * 60)

    print("📊 Database & Product Tools:")
    print("  • get_product_by_category(category) - Retrieve 1 product from a given product category")
    print("  • get_order_summary_by_quarter(year, quarter) - Get order summary for a specific year & quarter")
    print("  • get_latest_product_summary_from_postgre() - Get the latest ingested product event")
    print("")

    print("📚 Document & Knowledge Tools:")
    print("  • search_documents(query) - Search capstone documents using semantic similarity")
    print("")

    print("📋 Tool Capabilities:")
    print("  • Product Search: Returns one product per category")
    print("  • Order Analytics: Returns aggregated order stats per quarter")
    print("  • Document Search: Uses semantic similarity to find relevant information")
    print("-" * 60)


def show_examples():
    """Show example queries"""
    print("\n💡 Example Queries:")
    print("-" * 60)

    print("📦 Product & Order Examples:")
    print("  • 'Get a product from the electronics category'")
    print("  • 'Show order summary for Q4 2023'")
    print("  • 'What is the latest product information?'")
    print("")

    print("📚 Document Search Examples:")
    print("  • 'Search for information about data engineering'")
    print("  • 'Find information about machine learning in the documents'")
    print("  • 'What does the document say about architecture?'")
    print("")

    print("🔄 Combined Queries:")
    print("  • 'Get a product from electronics and search documents for related topics'")
    print("  • 'Show order summary for Q4 2023 and search for quarterly trends'")
    print("-" * 60)




def display_conversation_flow(result: Dict[str, Any]):
    """Display the conversation flow showing tool usage and results"""
    import json
    
    messages = result["messages"]

    # Show the conversation flow
    for i, message in enumerate(messages):
        # Show tool calls and capture which ones we made
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                args_str = ", ".join(f"{k}={v}" for k, v in tool_args.items())
                print(f"\n🔧 Using {tool_name}({args_str})")
        
        # Show tool results (ToolMessage responses)
        elif message.__class__.__name__ == "ToolMessage":
            tool_call_id = getattr(message, "tool_call_id", "unknown")
            content = message.content
            
            try:
                # Try to parse as JSON for pretty printing
                if isinstance(content, str):
                    result_data = json.loads(content)
                    # Pretty print tool result
                    if isinstance(result_data, dict):
                        print(f"\n📊 Tool Result:")
                        if "error" in result_data:
                            print(f"   ❌ Error: {result_data.get('error')}")
                        else:
                            # Format based on tool type
                            for key, value in result_data.items():
                                if key == "results" and isinstance(value, list):
                                    print(f"   {key}: {len(value)} result(s)")
                                    for j, res in enumerate(value[:3], 1):  # Show first 3
                                        if isinstance(res, dict):
                                            print(f"     [{j}] {res.get('content', str(res)[:100])}")
                                elif key not in ["query", "search_method", "index_name"]:
                                    print(f"   {key}: {str(value)[:100]}")
                    else:
                        print(f"\n📊 Result: {str(result_data)[:200]}")
                else:
                    print(f"\n📊 Result: {str(content)[:200]}")
            except (json.JSONDecodeError, TypeError):
                # Fall back to raw display
                content_str = str(content)
                if len(content_str) > 500:
                    print(f"\n📊 Tool Result: {content_str[:500]}...")
                else:
                    print(f"\n📊 Tool Result: {content_str}")
        
        # Show final LLM response
        elif hasattr(message, "content") and message.content and message.__class__.__name__ == "AIMessage":
            print(f"\n🤖 Agent Response:")
            print(message.content)

    # Show tool usage summary
    tool_calls_count = sum(
        1 for msg in messages if hasattr(msg, "tool_calls") and msg.tool_calls
    )
    if tool_calls_count > 0:
        print(f"\n📊 Used {tool_calls_count} tool call(s) to answer your question")


if __name__ == "__main__":
    # Check for --no-hitl flag to disable (enabled by default)
    hitl = "--no-hitl" not in sys.argv
    cli_interface_with_tools(human_in_the_loop=hitl)
