from fastapi import FastAPI
import uvicorn
from app.api.v1.endpoints import market
from app.api.v1.endpoints import etoro

app = FastAPI(title="Virtual Finance Advisor API")

app.include_router(market.router, prefix="/api/v1/market", tags="")
app.include_router(etoro.router, prefix="/api/v1/etoro", tags="")

@app.get("/")
async def root():
    return {"message": "Active backend optimized with uvloop"}

if __name__ == "__main__":
    # Run uvicorn with uvloop active for maximum performance
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, loop="uvloop")
