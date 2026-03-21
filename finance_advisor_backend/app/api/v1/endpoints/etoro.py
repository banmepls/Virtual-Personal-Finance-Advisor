# app/api/v1/endpoints/etoro.py
from fastapi import APIRouter, HTTPException
from app.services.etoro import EtoroService

router = APIRouter()
etoro_service = EtoroService()


@router.get("/portfolio")
async def get_portfolio():
    data = await etoro_service.get_live_portfolio()
    if isinstance(data, dict) and "error" in data:
        raise HTTPException(status_code=400, detail=data["error"])
    return data


@router.get("/instruments")
async def get_instruments():
    """Returns all known eToro instrument mappings (no API call, cached static)."""
    return await etoro_service.get_instruments()