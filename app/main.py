from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.live import router as live_router
from app.api.process_video import router as process_video_router

app = FastAPI(title="JumpTek AI Engine", version="2.0.1")
app.include_router(health_router)
app.include_router(process_video_router)
app.include_router(live_router)
