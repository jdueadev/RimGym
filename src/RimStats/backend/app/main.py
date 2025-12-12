"""FastAPI application entry point"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import colonists, incidents, metrics, runs
from app.services.run_manager import RunManager
from app.storage.storage_manager import StorageManager
from app.websocket import router as websocket_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager"""
    # Startup
    storage_manager = StorageManager(
        redis_url=settings.redis_url,
        sqlite_path=settings.sqlite_path,
    )
    await storage_manager.initialize()

    run_manager = RunManager(storage_manager=storage_manager)
    await run_manager.start()

    app.state.storage_manager = storage_manager
    app.state.run_manager = run_manager

    yield

    # Shutdown
    await run_manager.stop()
    await storage_manager.close()


app = FastAPI(
    title="RimWorld ML Dashboard API",
    description="Real-time training visualization for RimGym/RimTCP",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(runs.router, prefix="/api/v1", tags=["runs"])
app.include_router(colonists.router, prefix="/api/v1", tags=["colonists"])
app.include_router(metrics.router, prefix="/api/v1", tags=["metrics"])
app.include_router(incidents.router, prefix="/api/v1", tags=["incidents"])
app.include_router(websocket_router, prefix="/ws", tags=["websocket"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint"""
    return {"message": "RimWorld ML Dashboard API", "version": "0.1.0"}
