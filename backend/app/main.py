from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.api.scans import router as scans_router
from app.api.health import router as health_router

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="SiteGuard API",
    description="Автоматическая проверка сайтов на юридико-технические риски",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(scans_router)


@app.on_event("startup")
def on_startup():
    # Ensure tables exist (for dev without alembic)
    pass
