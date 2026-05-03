from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import cwb, drift, ai

app = FastAPI(title="Surf Decision API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cwb.router, prefix="/api/v1")
app.include_router(drift.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
