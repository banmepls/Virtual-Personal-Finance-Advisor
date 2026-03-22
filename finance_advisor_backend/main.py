"""
main.py — Virtual Finance Advisor Backend
==========================================
FastAPI application with:
- uvloop async event loop
- Full CORS configuration
- MCP + Agent + Anomaly + Auth + Health routers
- Lifespan startup: pre-warms circuit breakers & ML models
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import app.models
from app.api.v1.endpoints import market, etoro, auth, anomaly, health, agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup hooks run before the server begins accepting requests."""
    logger.info("🚀 Virtual Finance Advisor Backend starting...")

    # Pre-register circuit breakers so they appear in /health from the start
    from app.core.circuit_breaker import get_circuit_breaker
    get_circuit_breaker("etoro")
    get_circuit_breaker("alpha_vantage")

    # Warm up ML models (will auto-train on synthetic data on first call)
    logger.info("🧠 ML models ready (lazy init — train on first /anomaly/analyze call)")

    logger.info("✅ Backend ready")
    yield
    logger.info("🛑 Backend shutting down")


app = FastAPI(
    title="Virtual Finance Advisor API",
    description=(
        "Backend for the Virtual Personal Finance Advisor. "
        "Integrates eToro, Alpha Vantage, ML anomaly detection, and AI Tori agent."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: restrict to Flutter app origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(market.router,   prefix="/api/v1/market",   tags=["Market Data"])
app.include_router(etoro.router,    prefix="/api/v1/etoro",    tags=["eToro"])
app.include_router(auth.router,     prefix="/api/v1/auth",     tags=["Authentication"])
app.include_router(anomaly.router,  prefix="/api/v1/anomaly",  tags=["Anomaly Detection"])
app.include_router(health.router,   prefix="/api/v1",          tags=["Health"])
app.include_router(agent.router,    prefix="/api/v1/agent",    tags=["AI Agent"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Virtual Finance Advisor API — Active",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        loop="uvloop",
    )
