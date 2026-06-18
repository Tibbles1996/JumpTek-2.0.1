from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.live import router as live_router
from app.api.process_video import router as process_video_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(title="JumpTek AI Engine", version="2.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(process_video_router)
app.include_router(live_router)
