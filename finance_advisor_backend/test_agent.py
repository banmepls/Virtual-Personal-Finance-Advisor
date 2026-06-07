import asyncio
import os
from app.agent.tori_agent import ask_tori
from app.core.config import get_settings

async def main():
    settings = get_settings()
    print(f"Using Google API Key: {settings.google_api_key[:5]}...")
    
    print("Testing agent with a single prompt...")
    response = await ask_tori("Hello, what is your name and what can you do?", user_id=1)
    
    print("\n--- Agent Response ---")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
