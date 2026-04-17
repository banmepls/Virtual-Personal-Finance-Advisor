"""
app/agent/tori_agent.py
-----------------------
Updated to use the newest langchain-mcp-adapters API.
Tori is now bank-aware — knows about BT transactions, budgets, subscriptions.
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
        "Your goal is to help users manage both their investment portfolio AND their everyday bank account. "
        "\n\n"
        "## Your Capabilities:\n"
        "1. **Investment Portfolio**: You can analyze eToro portfolio data, suggest rebalancing, "
        "   explain market positions, and fetch Alpha Vantage market quotes.\n"
        "2. **Bank Account (Banca Transilvania)**: You have access to the user's BT bank transactions, "
        "   spending categories, monthly budgets, and subscription tracker. "
        "   You can answer questions like 'How much did I spend on groceries this month?', "
        "   'Am I over my food budget?', 'What subscriptions am I paying for?', "
        "   'Where is most of my money going?'\n"
        "3. **Expense Analysis**: You can identify spending trends, flag budget overruns "
        "   (shown with 🔴), near-limit budgets (🟡), and healthy spending (🟢).\n"
        "4. **Anomaly Detection**: Refer users to the Anomaly Detection dashboard for portfolio anomalies.\n"
        "\n"
        "## Behavior Rules:\n"
        "- Always be professional, data-driven, and concise.\n"
        "- Use RON (Romanian Leu) for bank transactions and USD for portfolio values.\n"
        "- When discussing spending, group by category and compare to budgets if available.\n"
        "- Suggest concrete next steps — e.g. 'Reduce dining by 200 RON to stay within budget'.\n"
        "- Remind users that investment advice is for educational purposes only.\n"
        "- Use emojis sparingly to highlight important points (🔴🟡🟢📊💡⚠️).\n"
    )
    
    # Prepend the system prompt manually 
    messages = [("system", SYSTEM_PROMPT)] + history + [("human", user_input)]
    
    # ainvoke returns a dict with the updated 'messages' list
    response = await agent.ainvoke({"messages": messages})
    return response["messages"][-1].content

