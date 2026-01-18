"""
Chainlit AI Agent for Data Analytics
Integrates with PostgreSQL and Snowflake databases
"""
import chainlit as cl
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import create_agent, AgentState
from langgraph.prebuilt import create_react_agent
import sys
from pathlib import Path

# Add project root and ai-agent to path
project_root = Path(__file__).parent.parent.parent
ai_agent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(ai_agent_dir))

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


@cl.on_chat_start
async def start():
    """Initialize the chat session with AI agent"""
    
    # Welcome message
    await cl.Message(
        content="🤖 **Data Analytics AI Agent Ready!**\n\n"
                "I can help you analyze data from:\n"
                "- 📊 **PostgreSQL** - Staging data\n"
                "- ❄️ **Snowflake** - Data warehouse\n"
                "- 📚 **Documents** - Search project documentation\n\n"
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
    
    # Initialize LLM
    llm = ChatOpenAI(
        temperature=0,
        model="gpt-3.5-turbo",  # or "gpt-4" for better performance
        streaming=True
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
    """Handle incoming user messages"""
    
    agent = cl.user_session.get("agent")
    chat_history = cl.user_session.get("chat_history", [])
    
    # Create a message to stream the response
    msg = cl.Message(content="")
    await msg.send()
    
    # Run agent with streaming
    try:
        # LangGraph agents use "messages" key instead of "input"
        response = await agent.ainvoke({
            "messages": chat_history + [HumanMessage(content=message.content)]
        })
        
        # Extract the last message from agent response
        agent_message = response["messages"][-1].content
        
        # Update message with final response
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


@cl.on_chat_end
async def end():
    """Clean up when chat ends"""
    await cl.Message(content="👋 Thanks for using the Data Analytics AI Agent!").send()
