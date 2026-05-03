from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.claude_client import generate_narrative

router = APIRouter()


class StoryRequest(BaseModel):
    effective_level: str
    spot_name: str
    wave_height: float | None = None
    wave_period: float | None = None
    wind_speed: float | None = None
    wind_direction: float | None = None
    gust: float | None = None
    tide: float | None = None
    sea_temp: float | None = None
    sar_speed_ms: float | None = None
    endpoint_dangerous: bool = False
    irregular_wave: bool = False


@router.post("/story")
async def post_story(req: StoryRequest):
    try:
        narrative = await generate_narrative(req.model_dump())
        return {"narrative": narrative}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
