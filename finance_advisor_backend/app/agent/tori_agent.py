"""
app/agent/tori_agent.py
-----------------------
Updated to use the newest langchain-mcp-adapters API.
"""
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.mcp.server import mcp_server
from app.core.config import get_settings

settings = get_settings()

def create_tori_agent(user_id: int):
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)

    # Use the tools directly from our FastMCP server
    # FastMCP tools can be converted to LangChain tools easily
    from langchain_core.tools import StructuredTool
    
    tools = []
    for tool in mcp_server._tool_manager.list_tools():
        # Create a StructuredTool from the MCP tool
        # In a real production scenario with multiple processes, 
        # we'd use a proper MCP Client, but here we can be more direct.
        st = StructuredTool.from_function(
            func=tool.fn,
            name=tool.name,
            description=tool.description,
        )
        tools.append(st)
    
    # Actually, let's use the adapter if possible, but the local method is safer
    # for a single-process FastAPI deployment.
    # tools = mcp_server.get_langchain_tools() # if available in this version

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are Tori, a Senior Financial AI Advisor for the Virtual Personal Finance Advisor platform. "
            "Your goal is to help users manage their portfolio, suggest investments, and analyze financial health. "
            "You have access to tools for fetching eToro portfolio data and Alpha Vantage market quotes. "
            "Always be professional, data-driven, and cautious when giving advice. "
            "Remind the user that your advice is for educational purposes and you do not execute trades. "
            "If asked about anomalies, refer to the Anomaly Detection dashboard."
        )),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_functions_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    return executor

async def ask_tori(user_input: str, user_id: int, chat_history: list = None):
    agent = create_tori_agent(user_id)
    history = chat_history or []
    response = await agent.ainvoke({"input": user_input, "chat_history": history})
    return response["output"]
