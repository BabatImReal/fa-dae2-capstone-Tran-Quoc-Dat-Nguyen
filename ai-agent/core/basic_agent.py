#!/usr/bin/env python3
"""
M04W01L03 Lab: Basic AI Agent with LangGraph

This script implements a basic AI agent using LangGraph with in-memory state management.
The agent can hold conversations and maintain context using LangGraph's state management.
"""

import os
from typing import Annotated, TypedDict

from dotenv import load_dotenv
import logging
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

# Load environment variables
load_dotenv()

# Configure logging for debugging state
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")


class AgentState(TypedDict):
    """State schema for our AI agent"""

    messages: Annotated[list, add_messages]
    user_name: str
    conversation_count: int


def create_basic_agent():
    """Create a basic AI agent with in-memory state management"""

    # Initialize the LLM
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "1000")),
    )

    def chatbot_node(state: AgentState):
        """Main chatbot node that processes user input"""
        messages = state["messages"]
        user_name = state.get("user_name", "User")
        conversation_count = state.get("conversation_count", 0)

        # Create system message for context
        system_message = f"""You are a helpful AI assistant for data engineering capstone projects.
        You are talking to {user_name}. This is conversation #{conversation_count + 1}.

        You can help with:
        - Data engineering concepts and best practices
        - Tool recommendations for capstone projects
        - Answering questions about data pipelines, databases, and analytics
        - Providing guidance on project planning and implementation

        Be friendly, professional, and helpful. If you don't know something, say so clearly."""

        # Prepare messages for LLM
        full_messages = [{"role": "system", "content": system_message}] + messages

        # Debug: log incoming state and prepared messages
        try:
            logging.debug(
                "[chatbot_node] incoming state: user=%s conv_count=%s messages_len=%s",
                user_name,
                conversation_count,
                len(messages) if messages is not None else 0,
            )
            logging.debug(
                "[chatbot_node] full_messages sample: %s",
                [m if isinstance(m, dict) else getattr(m, "content", str(m)) for m in full_messages],
            )
        except Exception:
            logging.debug("[chatbot_node] could not stringify full_messages")

        # Get response from LLM
        response = llm.invoke(full_messages)

        # Debug: log LLM response content (best-effort)
        try:
            resp_text = getattr(response, "content", str(response))
        except Exception:
            resp_text = str(response)
        logging.debug("[chatbot_node] LLM response (truncated): %s", resp_text[:1000] if len(str(resp_text)) > 1000 else resp_text)

        return {"messages": [response], "conversation_count": conversation_count + 1}

    # Create the state graph
    graph_builder = StateGraph(AgentState)

    # Add the chatbot node
    graph_builder.add_node("chatbot", chatbot_node)

    # Add edges
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_edge("chatbot", END)

    # Create in-memory checkpointer for state persistence
    memory = InMemorySaver()

    # Compile the graph with memory
    graph = graph_builder.compile(checkpointer=memory)

    # Expose checkpointer on the graph for runtime inspection (best-effort)
    try:
        setattr(graph, "checkpointer", memory)
    except Exception:
        logging.debug("[create_basic_agent] Could not attach checkpointer attribute to graph")

    return graph


def cli_interface():
    """Simple CLI interface for the basic agent"""
    print("🤖 Basic AI Agent with LangGraph")
    print("=" * 50)
    print("Commands:")
    print("  'quit' - Exit the application")
    print("  'new' - Start a new conversation")
    print("  'list' - List available conversations")
    print("  'switch <conversation_id>' - Switch to a conversation")
    print("=" * 50)

    # Create the agent
    agent = create_basic_agent()

    # Initialize conversation tracking
    conversations = {}  # Store conversation metadata
    thread_id = "main_conversation"
    user_name = input("What's your name? ").strip() or "User"

    # Add initial conversation
    conversations[thread_id] = {
        "name": "Main Conversation",
        "created_at": __import__("time").time(),
        "message_count": 0,
    }

    print(f"\nHello {user_name}! I'm your AI assistant. How can I help you today?")
    print(f"Current conversation: {thread_id}")

    while True:
        try:
            user_input = input(f"\n{user_name}: ").strip()

            if user_input.lower() in ["quit", "exit", "bye"]:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == "new":
                thread_id = f"conversation_{int(__import__('time').time())}"
                conversations[thread_id] = {
                    "name": f"Conversation {len(conversations)}",
                    "created_at": __import__("time").time(),
                    "message_count": 0,
                }
                print(f"🆕 New conversation started: {thread_id}")
                continue
            elif user_input.lower() == "list":
                print("\n📋 Available Conversations:")
                print("-" * 40)
                for conv_id, conv_info in conversations.items():
                    status = "🟢" if conv_id == thread_id else "⚪"
                    print(
                        f"{status} {conv_id}: {conv_info['name']} ({conv_info['message_count']} messages)"
                    )
                print("-" * 40)
                continue
            elif user_input.lower().startswith("switch "):
                new_thread_id = user_input[7:].strip()
                if new_thread_id in conversations:
                    thread_id = new_thread_id
                    print(f"🔄 Switched to conversation: {thread_id}")
                else:
                    print(
                        f"❌ Conversation '{new_thread_id}' not found. Use 'list' to see available conversations."
                    )
                continue
            elif not user_input:
                continue

            # Create configuration for this thread
            config = {"configurable": {"thread_id": thread_id}}

            # Prepare initial state
            initial_state = {
                "messages": [HumanMessage(content=user_input)],
                "user_name": user_name,
                "conversation_count": conversations[thread_id]["message_count"],
            }

            # Get agent response
            result = agent.invoke(initial_state, config)

            # Debug: show returned result structure
            try:
                logging.debug("[cli] agent returned result keys: %s", list(result.keys()) if isinstance(result, dict) else type(result))
            except Exception:
                logging.debug("[cli] agent returned result (repr): %s", repr(result))

            # If agent exposes a checkpointer, attempt a safe, best-effort inspection
            cp = getattr(agent, "checkpointer", None)
            if cp is not None:
                try:
                    snapshot = None
                    if hasattr(cp, "_store"):
                        snapshot = cp._store
                    elif hasattr(cp, "store"):
                        snapshot = cp.store
                    elif hasattr(cp, "__dict__"):
                        snapshot = {k: v for k, v in cp.__dict__.items() if not k.startswith("_")}
                    if isinstance(snapshot, dict):
                        logging.debug("[cli] checkpointer snapshot keys: %s", list(snapshot.keys()))
                    else:
                        logging.debug("[cli] checkpointer snapshot type: %s", type(snapshot))
                except Exception as e:
                    logging.debug("[cli] error inspecting checkpointer: %s", e)

            # Update conversation metadata
            conversations[thread_id]["message_count"] += 1

            # Display response
            response = result["messages"][-1].content
            print(f"🤖 Agent: {response}")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    cli_interface()