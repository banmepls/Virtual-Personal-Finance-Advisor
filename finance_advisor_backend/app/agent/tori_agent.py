"""
app/agent/tori_agent.py
-----------------------
Updated to use the newest langchain-mcp-adapters API.
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from app.mcp.server import mcp_server
from app.core.config import get_settings

settings = get_settings()

def create_tori_agent(user_id: int):
    # Initialize LLM with Google Gemini
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        temperature=0,
        api_key=settings.google_api_key
    )

    from langchain_core.tools import StructuredTool
    
    tools = []
    # FastMCP list_tools()
    for tool in mcp_server._tool_manager.list_tools():
        st = StructuredTool.from_function(
            func=tool.fn,
            name=tool.name,
            description=tool.description,
            coroutine=tool.fn
        )
        tools.append(st)

    agent = create_react_agent(llm, tools=tools)
    return agent

async def ask_tori(user_input: str, user_id: int, chat_history: list = None):
    agent = create_tori_agent(user_id)
    history = chat_history or []
    
    SYSTEM_PROMPT = (
        "You are Tori, a Senior Financial AI Advisor for the Virtual Personal Finance Advisor platform. "
        "Your goal is to help users manage their portfolio, suggest investments, and analyze financial health. "
        "You have access to tools for fetching eToro portfolio data and Alpha Vantage market quotes. "
        "Always be professional, data-driven, and cautious when giving advice. "
        "Remind the user that your advice is for educational purposes and you do not execute trades. "
        "If asked about anomalies, refer to the Anomaly Detection dashboard."
    )
    
    # Prepend the system prompt manually 
    messages = [("system", SYSTEM_PROMPT)] + history + [("human", user_input)]
    
    # ainvoke returns a dict with the updated 'messages' list
    response = await agent.ainvoke({"messages": messages})
    return response["messages"][-1].content

