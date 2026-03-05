import httpx
from app.core.config import get_settings

settings = get_settings()

class MarketDataService:
    BASE_URL = "https://www.alphavantage.co/query"

    async def get_stock_quote(self, symbol: str):
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": settings.alpha_vantage_api_key
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.BASE_URL, params=params)
            data = response.json()
            
            # Alpha Vantage return data using "Global Quote"
            quote = data.get("Global Quote", {})
            if not quote:
                return {"error": "Simbolul nu a fost găsit sau limita API a fost atinsă."}
            
            return {
                "symbol": quote.get("01. symbol"),
                "price": float(quote.get("05. price")),
                "change_percent": quote.get("10. change percent"),
                "volume": quote.get("06. volume")
            }
