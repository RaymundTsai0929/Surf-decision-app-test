from fastapi import APIRouter, HTTPException
from services.cwa_client import fetch_conditions

router = APIRouter()


@router.get("/conditions")
async def get_conditions(spot: str):
    try:
        return await fetch_conditions(spot)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
