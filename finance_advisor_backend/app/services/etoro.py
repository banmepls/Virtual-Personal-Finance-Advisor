# app/services/etoro.py
import httpx
import uuid
from app.core.config import get_settings

settings = get_settings()

class EtoroService:
    def __init__(self):
        self.base_url = "https://public-api.etoro.com/api/v1"
        self.headers = {
            "x-api-key": settings.etoro_api_key,
            "x-user-key": settings.etoro_user_key,
            "Content-Type": "application/json"
        }

    async def get_live_portfolio(self):
        """Preluăm portofoliul live conform documentației oficiale eToro"""
        request_headers = self.headers.copy()
        request_headers["x-request-id"] = str(uuid.uuid4()) # Generăm un UUID unic pentru fiecare request
        
        # Endpoint-ul identificat: /user-info/people/{username}/portfolio/live
        url = f"{self.base_url}/user-info/people/{settings.etoro_username}/portfolio/live"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=request_headers)
            
            if response.status_code!= 200:
                return {
                    "error": f"Eroare eToro: {response.status_code}", 
                    "detail": response.text
                }
            
            return response.json()