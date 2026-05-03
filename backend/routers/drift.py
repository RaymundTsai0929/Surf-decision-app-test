from fastapi import APIRouter, HTTPException
from services.drift_sim import simulate_drift

router = APIRouter()


@router.get("/drift")
async def get_drift(lat: float, lng: float, spot: str):
    try:
        return await simulate_drift(lat, lng, spot)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
