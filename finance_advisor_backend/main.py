from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Virtual Finance Advisor API")

@app.get("/")
async def root():
    return {"message": "Active backend optimized with uvloop"}

if __name__ == "__main__":
    # Run uvicorn with uvloop active for maximum performance
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, loop="uvloop")
