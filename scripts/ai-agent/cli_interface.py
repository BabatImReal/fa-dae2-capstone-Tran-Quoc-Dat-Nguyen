#!/usr/bin/env python3
"""
M04W01L03 Lab: CLI Interface for Persistent AI Agent

This script provides a command-line interface for the persistent AI agent.
It imports the agent functionality from persistent_agent.py and adds CLI-specific features.
"""

import time

from langchain_core.messages import HumanMessage
from persistent_agent import create_persistent_agent, list_available_threads


def cli_interface_with_threads():
    """Enhanced CLI interface with thread management"""
    print("🤖 Persistent AI Agent with PostgreSQL")
    print("=" * 60)
    print("Commands:")
    print("  'quit' - Exit the application")
    print("  'new' - Start a new conversation thread")
    print("  'list' - List all conversation threads")
    print("  'switch <thread_id>' - Switch to a specific thread")
    print("  'current' - Show current thread information")
    print("=" * 60)

    # Create the persistent agent
    agent = create_persistent_agent()

    # Initialize session
    user_name = input("What's your name? ").strip() or "User"
    session_id = f"session_{int(time.time())}"
    current_thread_id = f"thread_{int(time.time())}"

    # Track conversation metadata locally
    conversation_metadata = {
        current_thread_id: {
            "name": "Main Conversation",
            "created_at": time.time(),
            "message_count": 0,
            "user_name": user_name,
        }
    }

    print(f"\nHello {user_name}! Session: {session_id}")
    print(f"Current thread: {current_thread_id}")
    print("How can I help you today?")

    while True:
        try:
            user_input = input(f"\n{user_name}: ").strip()

            if user_input.lower() in ["quit", "exit", "bye"]:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == "new":
                current_thread_id = f"thread_{int(time.time())}"
                conversation_metadata[current_thread_id] = {
                    "name": f"Conversation {len(conversation_metadata)}",
                    "created_at": time.time(),
                    "message_count": 0,
                    "user_name": user_name,
                }
                print(f"🆕 New thread started: {current_thread_id}")
                continue
            elif user_input.lower() == "list":
                list_available_threads(agent)
                print("\n📋 Local Conversation Tracking:")
                print("-" * 50)
                for thread_id, metadata in conversation_metadata.items():
                    status = "🟢" if thread_id == current_thread_id else "⚪"
                    print(
                        f"{status} {thread_id}: {metadata['name']} ({metadata['message_count']} messages)"
                    )
                print("-" * 50)
                continue
            elif user_input.lower() == "current":
                current_metadata = conversation_metadata.get(current_thread_id, {})
                print("\n📊 Current Thread Information:")
                print(f"  Thread ID: {current_thread_id}")
                print(f"  Name: {current_metadata.get('name', 'Unknown')}")
                print(f"  Messages: {current_metadata.get('message_count', 0)}")
                print(
                    f"  Created: {time.ctime(current_metadata.get('created_at', time.time()))}"
                )
                print(f"  User: {current_metadata.get('user_name', user_name)}")
                continue
            elif user_input.lower().startswith("switch "):
                new_thread_id = user_input[7:].strip()
                if new_thread_id:
                    current_thread_id = new_thread_id
                    # Add to metadata if not exists
                    if new_thread_id not in conversation_metadata:
                        conversation_metadata[new_thread_id] = {
                            "name": f"Conversation {len(conversation_metadata)}",
                            "created_at": time.time(),
                            "message_count": 0,
                            "user_name": user_name,
                        }
                    print(f"🔄 Switched to thread: {current_thread_id}")
                else:
                    print("❌ Please provide a thread ID")
                continue
            elif not user_input:
                continue

            # Create configuration for this thread
            config = {"configurable": {"thread_id": current_thread_id}}

            # Prepare initial state
            initial_state = {
                "messages": [HumanMessage(content=user_input)],
                "user_name": user_name,
                "conversation_count": conversation_metadata[current_thread_id][
                    "message_count"
                ],
                "session_id": session_id,
                "thread_metadata": {
                    "created_at": conversation_metadata[current_thread_id][
                        "created_at"
                    ],
                    "user_name": user_name,
                    "thread_name": conversation_metadata[current_thread_id]["name"],
                },
            }

            # Get agent response
            result = agent.invoke(initial_state, config)

            # Update conversation metadata
            conversation_metadata[current_thread_id]["message_count"] += 1

            # Display response
            response = result["messages"][-1].content
            print(f"🤖 Agent: {response}")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    cli_interface_with_threads()