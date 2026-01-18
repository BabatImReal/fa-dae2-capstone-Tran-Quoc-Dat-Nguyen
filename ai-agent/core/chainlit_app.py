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


@cl.on_chat_start
async def start():
    """Initialize the chat session with AI agent"""
    
    # Welcome message
    await cl.Message(
        content="🤖 **Data Analytics AI Agent Ready!**\n\n"
                "I can help you analyze data from:\n"
                "- 📊 **PostgreSQL** - Staging data\n"
                "- ❄️ **Snowflake** - Data warehouse\n\n"
                "Ask me anything about products, customers, sales, or revenue trends!"
    ).send()
    
    # Collect all tools
    tools = [
        # PostgreSQL tools
        get_latest_product_summary_from_postgre,
        # Snowflake tools
        get_all_product_categories_from_snowflake,
        get_product_by_category_from_snowflake, 
        get_order_summary_by_quarter_from_snowflake,
    ]
    
    # Initialize LLM
    llm = ChatOpenAI(
        temperature=0,
        model="gpt-4o-mini",  # or "gpt-4" for better performance
        streaming=True
    )
    
    # System prompt
    system_prompt = """You are a helpful data analytics assistant with access to PostgreSQL and Snowflake databases.

**Your capabilities:**
- Query PostgreSQL staging database for real-time data
- Query Snowflake data warehouse for analytical insights
- Analyze product performance, customer behavior, and revenue trends
- Provide data-driven recommendations

**Guidelines:**
- Always explain what data you're retrieving and why
- Format numbers with proper separators (e.g., 1,234.56)
- Use tables or bullet points for clear data presentation
- If a query fails, suggest alternatives
- Cite which database you're querying (PostgreSQL or Snowflake)

Be concise but informative. Focus on actionable insights."""
    
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
