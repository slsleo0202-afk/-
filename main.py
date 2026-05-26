from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, SessionLocal, engine
import app.models  # noqa: F401
from app.routers import ai, auth, fridge, ingredients, reviews, trades
from app.seed import seed_demo_data


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if settings.seed_demo_on_startup:
            seed_demo_data(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.app_name,
    description="AI 기반 식재료 나눔·교환·매매 플랫폼 MVP",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(ai.router)
app.include_router(ingredients.router)
app.include_router(fridge.router)
app.include_router(trades.router)
app.include_router(reviews.router)

app.mount("/uploads", StaticFiles(directory=str(settings.upload_dir)), name="uploads")

static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/")
    def index():
        return FileResponse(static_dir / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok", "service": settings.app_name}
