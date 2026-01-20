"""
Chainlit AI Agent for Data Analytics
Integrates with PostgreSQL and Snowflake databases
"""
import os
import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain.agents import create_agent, AgentState
from langgraph.prebuilt import create_react_agent

from typing import Any, Dict, Optional
import sys
from pathlib import Path

import asyncpg
import hashlib
import json

# Add project root and ai-agent to path
project_root = Path(__file__).parent.parent.parent
ai_agent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(ai_agent_dir))

# Import RAG components for PDF processing
from rag.service.document_processor import DocumentProcessor
from rag.embed_and_store import PineconeEmbedder
from rag.sparse_embedder import SparseEmbedder

# Set up data persistence with SQLAlchemy
@cl.data_layer
def get_data_layer():
    return SQLAlchemyDataLayer(
        conninfo=os.getenv(
            "CHAINLIT_POSTGRES_URL"
        )
    )

# Import tools
from tools.postgre_tools import (
    get_latest_product_summary_from_postgre
)
from tools.snowflake_tools import (
    get_all_product_categories_from_snowflake,
    get_product_by_category_from_snowflake, 
    get_order_summary_by_quarter_from_snowflake,
)
from tools.rag_combined_tools import hybrid_search_documents
from tools.rag_tools import search_documents


# ============================================================================
# AUTHENTICATION
# ============================================================================


def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


async def get_user_from_db(username: str) -> Optional[dict]:
    """
    Retrieve user from database
    
    Args:
        username: User's username
        
    Returns:
        User data dict or None
    """
    db_url = os.getenv(
        "CHAINLIT_POSTGRES_URL"
    ).replace("postgresql+asyncpg://", "postgresql://")
    
    try:
        conn = await asyncpg.connect(db_url)
        row = await conn.fetchrow(
            "SELECT identifier, metadata FROM users WHERE identifier = $1",
            username
        )
        await conn.close()
        
        if row:
            return {
                "identifier": row["identifier"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
            }
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    return None


@cl.password_auth_callback
async def auth_callback(username: str, password: str) -> Optional[cl.User]:
    """
    Authenticate user with username and password from database
    
    Args:
        username: User's username
        password: User's password
        
    Returns:
        cl.User object if authentication successful, None otherwise
    """
    print(f"🔐 Authentication attempt for user: {username}")
    
    # Get user from database
    user_data = await get_user_from_db(username)
    
    if not user_data:
        print(f"❌ User '{username}' not found")
        return None
    
    # Verify password hash
    stored_password_hash = user_data["metadata"].get("password_hash")
    if not stored_password_hash or hash_password(password) != stored_password_hash:
        print(f"❌ Invalid password for user '{username}'")
        return None
    
    print(f"✅ User '{username}' authenticated successfully")
    
    # Return User object with metadata (without password hash)
    metadata = {k: v for k, v in user_data["metadata"].items() if k != "password_hash"}
    
    return cl.User(
        identifier=username,
        metadata=metadata
    )


# ============================================================================
# HUMAN-IN-THE-LOOP
# ============================================================================

# Human-in-the-Loop: Ask for approval before executing tools
async def ask_tool_approval(tool_name: str, tool_input: Dict[str, Any]) -> bool:
    """Ask user for approval before executing a tool"""
    
    # Format everything in a code block
    if tool_input:
        input_lines = "\n".join([f"  - {k}: {v}" for k, v in tool_input.items()])
        params_section = f"Parameters:\n{input_lines}"
    else:
        params_section = "Parameters:\n  (none)"
    
    tool_info = f"Tool: {tool_name}\n{params_section}"
    
    res = await cl.AskActionMessage(
        content=f"🔧 **Tool Execution Request**\n\n"
                f"```\n{tool_info}\n```\n\n"
                f"Do you want to execute this tool?",
        actions=[
            cl.Action(name="approve", payload={"approved": True}, label="✅ Approve"),
            cl.Action(name="reject", payload={"approved": False}, label="❌ Reject"),
        ],
        timeout=120,  # 2 minutes timeout
    ).send()
    
    if res and res.get("payload", {}).get("approved"):
        await cl.Message(content="✅ Tool execution approved.").send()
        return True
    else:
        await cl.Message(content="❌ Tool execution rejected.").send()
        return False


# ============================================================================
# PDF UPLOAD AND PROCESSING
# ============================================================================

async def process_pdf_upload(file: cl.File) -> Dict[str, Any]:
    """
    Process uploaded PDF: extract text, chunk, embed (both dense & sparse), and store in Pinecone
    
    Args:
        file: Uploaded PDF file from Chainlit
        
    Returns:
        Dictionary with processing results
    """
    try:
        # Initialize document processor
        processor = DocumentProcessor(
            chunk_size=1000,
            chunk_overlap=200,
            chunking_strategy="sentence",
            language="en"
        )
        
        # Process the PDF file
        await cl.Message(content=f"📄 Processing PDF: **{file.name}**...").send()
        
        # Extract text and create chunks
        chunks = processor.process_document(file.path, extractor_type="pdfplumber")
        
        if not chunks:
            return {
                "success": False,
                "message": "No text could be extracted from the PDF."
            }
        
        await cl.Message(
            content=f"✅ Extracted and chunked into **{len(chunks)}** chunks."
        ).send()
        
        # Initialize embedders for BOTH semantic (dense) and lexical (sparse)
        dense_embedder = PineconeEmbedder()
        sparse_embedder = SparseEmbedder(
            pc=dense_embedder.pc,  # Reuse the same Pinecone client
            sparse_index_name=os.getenv("PINECONE_SPARSE_INDEX_NAME")
        )
        
        # Generate DENSE embeddings (semantic)
        await cl.Message(content="🔄 Generating dense embeddings (semantic)...").send()
        dense_embeddings = dense_embedder.embed_chunks(chunks)
        
        # Generate SPARSE embeddings (lexical/keyword)
        await cl.Message(content="🔄 Generating sparse embeddings (lexical)...").send()
        sparse_embeddings = sparse_embedder.embed_chunks_sparse(chunks)
        
        # Use default namespace for all uploads
        namespace = "default"
        
        # Store DENSE vectors in Pinecone dense index
        await cl.Message(content="💾 Storing dense vectors (semantic index)...").send()
        dense_embedder.store_chunks(chunks, dense_embeddings, namespace=namespace)
        
        # Store SPARSE vectors in Pinecone sparse index
        await cl.Message(content="💾 Storing sparse vectors (lexical index)...").send()
        sparse_embedder.store_sparse_chunks(chunks, sparse_embeddings, namespace=namespace)
        
        return {
            "success": True,
            "chunks_count": len(chunks),
            "namespace": "default",
            "filename": file.name,
            "dense_stored": True,
            "sparse_stored": True
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error processing PDF: {str(e)}"
        }


@cl.on_chat_start
async def start():
    """Initialize the chat session with AI agent"""
    
    # First, ask with action buttons
    action = await cl.AskActionMessage(
        content="📚 **Welcome to the Data Analytics AI Agent!**\n\n"
                "Would you like to upload any PDF documents for analysis?\n\n"
                "PDFs will be automatically:\n"
                "- 📄 Extracted and chunked\n"
                "- 🧠 Embedded with AI (both semantic & lexical)\n"
                "- 💾 Stored in dual vector indexes\n"
                "- 🔍 Made searchable via hybrid RAG",
        actions=[
            cl.Action(name="upload", payload={"action": "upload"}, label="📤 Upload PDF Documents"),
            cl.Action(name="skip", payload={"action": "skip"}, label="⏭️ Skip for Now"),
        ],
        timeout=60,
    ).send()
    
    # If user chooses to upload, show the file dialog
    if action and action.get("payload", {}).get("action") == "upload":
        files = None
        try:
            files = await cl.AskFileMessage(
                content="📁 **Select PDF files to upload**\n\n"
                        "Drag and drop or browse for PDF files (max 20MB each, up to 5 files):",
                accept=["application/pdf"],
                max_size_mb=20,
                max_files=5,
                timeout=300,
                raise_on_timeout=False
            ).send()
        except:
            files = None
        
        # Process uploaded PDFs if any
        if files:
            for file in files:
                result = await process_pdf_upload(file)
                
                if result["success"]:
                    await cl.Message(
                        content=f"✅ **Successfully processed:** {result['filename']}\n\n"
                                f"- Chunks: {result['chunks_count']}\n"
                                f"- Namespace: `{result['namespace']}`\n"
                                f"- Dense vectors: {'✅ Stored' if result.get('dense_stored') else '❌ Failed'}\n"
                                f"- Sparse vectors: {'✅ Stored' if result.get('sparse_stored') else '❌ Failed'}\n"
                                f"- Status: Ready for hybrid search! 🚀\n\n"
                                f"💡 All documents are stored in the default namespace for easy retrieval."
                    ).send()
                else:
                    await cl.Message(
                        content=f"❌ **Failed to process:** {file.name}\n\n"
                                f"Error: {result.get('message', 'Unknown error')}"
                    ).send()
        else:
            await cl.Message(
                content="⏭️ No files uploaded. You can upload documents anytime using the 📎 attachment icon!"
            ).send()
    else:
        # User skipped
        await cl.Message(
            content="⏭️ Skipped PDF upload. You can upload documents anytime using the 📎 attachment icon!"
        ).send()
    
    # Set up chat settings
    settings = await cl.ChatSettings(
        [
            Select(
                id="Model",
                label="OpenAI Model",
                values=["gpt-3.5-turbo", "gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
                initial_index=0,
            ),
            Switch(
                id="Streaming", 
                label="Stream Responses", 
                initial=True
            ),
            Switch(
                id="HITL",
                label="Human-in-the-Loop (Approve Tools)",
                initial=True,
                description="Ask for approval before executing tools"
            ),
            Slider(
                id="Temperature",
                label="Temperature",
                initial=0,
                min=0,
                max=2,
                step=0.1,
                description="Controls randomness: 0 is focused, 2 is creative",
            ),
        ]
    ).send()
    
    # Store initial settings
    cl.user_session.set("settings", {
        "Model": "gpt-3.5-turbo",
        "Streaming": True,
        "HITL": True,
        "Temperature": 0,
    })
    
    # Welcome message with user info if authenticated
    user = cl.user_session.get("user")
    if user:
        display_name = user.metadata.get("display_name", user.identifier)
        welcome_msg = f"👋 Welcome back, **{display_name}**!\n\n🤖 **Data Analytics AI Agent Ready!**\n\n"
    else:
        welcome_msg = "🤖 **Data Analytics AI Agent Ready!**\n\n"
    
    await cl.Message(
        content=welcome_msg +
                "I can help you analyze data from:\n"
                "- 📊 **PostgreSQL** - Staging data\n"
                "- ❄️ **Snowflake** - Data warehouse\n"
                "- 📚 **Documents** - Search project documentation\n"
                "- 📄 **Your PDFs** - Search uploaded documents\n\n"
                "💡 **Tips:**\n"
                "- Click the settings icon ⚙️ to customize the model and temperature\n"
                "- Use the 📎 attachment icon to upload more PDFs anytime\n\n"
                "📜 Your conversations are automatically saved - access them from the sidebar!\n\n"
                "Ask me anything about products, customers, sales, revenue trends, or search the documentation!"
    ).send()
    
    # Collect all tools
    tools = [
        # PostgreSQL tools
        get_latest_product_summary_from_postgre,
        # Snowflake tools
        get_all_product_categories_from_snowflake,
        get_product_by_category_from_snowflake, 
        get_order_summary_by_quarter_from_snowflake,
        # RAG tools for document search
        hybrid_search_documents,  # Hybrid search (recommended)
        search_documents,  # Simple semantic search
    ]
    
    # Get settings from session
    settings = cl.user_session.get("settings", {
        "Model": "gpt-3.5-turbo",
        "Streaming": True,
        "Temperature": 0,
    })
    
    # Initialize LLM with user settings
    llm = ChatOpenAI(
        temperature=settings["Temperature"],
        model=settings["Model"],
        streaming=settings["Streaming"]
    )
    
    # System prompt
    system_prompt = """You are a helpful data analyst assistant with access to multiple data sources.

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

HOW TO RESPOND AFTER USING TOOLS:

STRUCTURE YOUR RESPONSE IN TWO PARTS:

**Part 1: Tool Result (Show what was retrieved)**
- Display the raw tool output/data
- For searches: Show key metadata like query, search method, number of results
- For databases: Show the returned data/records

**Part 2: Meaningful Answer (Synthesize the information)**
- Extract insights from the tool results
- Provide a coherent, natural narrative that answers the user's question
- Connect information across multiple chunks/results
- Focus on what matters to the user, not technical details

EXAMPLE RESPONSE FORMAT:

For RAG/document search:
```
📊 Tool Result:
Query: "Fiona"
Search Method: hybrid (dense + sparse with reranking)
Results Found: 54 total, showing top 3

1. [Rank 1] Shrek finds Fiona asleep: "Shrek turns and goes over to her. He looks down at Fiona for a moment... FIONA: I am, awaiting a knight so bold as to rescue me."

2. [Rank 2] Fiona's combat skills: "Fiona gives a karate yell and then proceeds to beat the crap out of the Merry Men. There is a Matrix moment where Fiona pauses in mid-air to fix her hair."

3. [Rank 3] Fiona's transformation: "By night one way, by day another. I wanted to show you before." As the sun sets, she transforms into her ogre form.

---

💡 Answer:
Fiona is Princess Fiona from Shrek, awaiting rescue by a brave knight. When Shrek finds her asleep in the tower, she expects a traditional fairy tale rescue. However, Fiona subverts the typical damsel-in-distress archetype - she's a highly skilled fighter who can defeat groups of enemies with impressive martial arts moves. She also has a secret curse that transforms her between human form by day and ogre form by night, which she eventually reveals to Shrek, showing her true self and breaking from traditional princess stereotypes.
```

For database queries:
```
📊 Tool Result:
[Show the actual data returned - categories, records, counts, etc.]

---

💡 Answer:
[Explain what the data shows and what it means]
```

For MULTIPLE tools:
```
📊 Tool Results:

[Tool 1 Name]:
[Raw output from tool 1]

[Tool 2 Name]:
[Raw output from tool 2]

---

💡 Answer:
[Single cohesive synthesis combining insights from all tools to answer the question]
```

GUIDELINES:
- Keep tool results informative but concise
- Focus the answer section on direct insights
- Use natural language in the answer, avoid jargon
- Connect information meaningfully, don't just list facts

Keep your responses focused on answering the user's question with meaningful insights."""
    
    # Create agent using LangGraph
    agent_executor = create_react_agent(llm, tools, prompt=system_prompt)
    
    # Store in session
    cl.user_session.set("agent", agent_executor)
    cl.user_session.set("chat_history", [])


@cl.on_message
async def main(message: cl.Message):
    """Handle incoming user messages with optional Human-in-the-Loop for tool execution"""
    
    # Check if user uploaded files with their message
    if message.elements:
        for element in message.elements:
            if isinstance(element, cl.File) and element.mime == "application/pdf":
                # Process the uploaded PDF
                result = await process_pdf_upload(element)
                
                if result["success"]:
                    await cl.Message(
                        content=f"✅ **Successfully processed:** {result['filename']}\n\n"
                                f"- Chunks: {result['chunks_count']}\n"
                                f"- Namespace: `{result['namespace']}`\n"
                                f"- Dense vectors: {'✅ Stored' if result.get('dense_stored') else '❌ Failed'}\n"
                                f"- Sparse vectors: {'✅ Stored' if result.get('sparse_stored') else '❌ Failed'}\n"
                                f"- Status: Ready for hybrid search! 🚀\n\n"
                                f"💡 All documents are stored in the default namespace.\n"
                                f"You can now ask questions about this document!"
                    ).send()
                else:
                    await cl.Message(
                        content=f"❌ **Failed to process:** {element.name}\n\n"
                                f"Error: {result.get('message', 'Unknown error')}"
                    ).send()
                    return
    
    agent = cl.user_session.get("agent")
    chat_history = cl.user_session.get("chat_history", [])
    settings = cl.user_session.get("settings", {"HITL": True})
    hitl_enabled = settings.get("HITL", True)
    
    # Create a message to stream the response
    msg = cl.Message(content="")
    await msg.send()
    
    try:
        # Stream agent execution with optional HITL
        all_messages = chat_history + [HumanMessage(content=message.content)]
        
        async for event in agent.astream({"messages": all_messages}, stream_mode="values"):
            messages = event.get("messages", [])
            
            if not messages:
                continue
                
            last_message = messages[-1]
            
            # Check if the last message contains tool calls and HITL is enabled
            if hitl_enabled and hasattr(last_message, "tool_calls") and last_message.tool_calls:
                for tool_call in last_message.tool_calls:
                    tool_name = tool_call.get("name", "unknown")
                    tool_input = tool_call.get("args", {})
                    
                    # Ask for approval before executing tool
                    approved = await ask_tool_approval(tool_name, tool_input)
                    
                    if not approved:
                        # If rejected, send a message and stop execution
                        msg.content = f"🚫 Tool execution cancelled by user.\n\nThe agent wanted to use `{tool_name}` but you rejected it.\n\nPlease provide different instructions or allow tool execution."
                        await msg.update()
                        return
            
            # Update message with agent's response (non-tool messages)
            if hasattr(last_message, "content") and isinstance(last_message.content, str):
                if last_message.content and not hasattr(last_message, "tool_calls"):
                    msg.content = last_message.content
                    await msg.update()
        
        # Get final response
        final_messages = event.get("messages", [])
        if final_messages:
            agent_message = final_messages[-1].content
            msg.content = agent_message
            await msg.update()
            
            # Update chat history
            chat_history.append(HumanMessage(content=message.content))
            chat_history.append(AIMessage(content=agent_message))
            cl.user_session.set("chat_history", chat_history)
        
    except Exception as e:
        error_msg = f"❌ **Error occurred:**\n```\n{str(e)}\n```\n\nPlease try rephrasing your question or check if the databases are accessible."
        msg.content = error_msg
        await msg.update()


@cl.on_settings_update
async def update_settings(settings):
    """Handle settings updates"""
    print(f"⚙️ Settings updated: {settings}")
    
    # Store updated settings
    cl.user_session.set("settings", settings)
    
    # Recreate agent with new settings
    await start()
    
    # Notify user
    await cl.Message(
        content=f"✅ **Settings Updated!**\n\n"
                f"- Model: `{settings['Model']}`\n"
                f"- Temperature: `{settings['Temperature']}`\n"
                f"- Streaming: `{settings['Streaming']}`\n"
                f"- Human-in-the-Loop: `{settings.get('HITL', True)}`"
    ).send()


@cl.on_stop
async def on_stop():
    """Handle when user clicks stop button during task execution"""
    print("⏸️ User requested to stop the task")
    await cl.Message(content="⏸️ Task stopped by user.").send()


@cl.on_chat_resume
async def on_chat_resume(thread: dict):
    """
    Resume a previous conversation thread
    
    Args:
        thread: Dictionary containing thread metadata and message history
    """
    print(f"🔄 Resuming chat thread: {thread.get('id')}")
    
    # Restore chat history from thread
    chat_history = []
    
    # Get the thread steps/messages
    if "steps" in thread:
        for step in thread["steps"]:
            step_type = step.get("type")
            
            # Restore user messages
            if step_type == "user_message":
                chat_history.append(HumanMessage(content=step.get("output", "")))
            
            # Restore assistant messages
            elif step_type == "assistant_message":
                chat_history.append(AIMessage(content=step.get("output", "")))
    
    # Store restored chat history in session
    cl.user_session.set("chat_history", chat_history)
    
    # Restore settings if they exist in thread metadata
    settings = thread.get("metadata", {}).get("settings")
    if settings:
        cl.user_session.set("settings", settings)
    else:
        # Use default settings
        settings = {
            "Model": "gpt-4o-mini",
            "Temperature": 0.7,
            "Streaming": True,
            "HITL": True
        }
        cl.user_session.set("settings", settings)
    
    # Recreate the agent with restored settings
    await start()
    
    # Send welcome back message
    message_count = len([s for s in thread.get("steps", []) if s.get("type") == "user_message"])
    await cl.Message(
        content=f"👋 **Welcome back!**\n\n"
                f"Resumed conversation with {message_count} previous messages.\n"
                f"You can continue where you left off!"
    ).send()


@cl.on_chat_end
async def end():
    """Clean up when chat ends"""
    print("👋 Chat session ended")

