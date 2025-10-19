from contextlib import asynccontextmanager
from fastapi import FastAPI
from routers import (
    inserate_ultra as inserate,
    inserat,
    inserate_detailed_ultra as inserate_detailed,
    stored_listings,
)
from utils.browser import OptimizedPlaywrightManager
from utils.asyncio_optimizations import EventLoopOptimizer
from db import init_db, close_db, get_session_factory
from services.scheduler import ScraperScheduler, load_job_configs

# Global browser manager instance for sharing across all endpoints
browser_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown events"""
    global browser_manager

    # Setup uvloop for maximum performance (2-4x improvement)
    uvloop_enabled = EventLoopOptimizer.setup_uvloop()

    # Optimize event loop settings
    EventLoopOptimizer.optimize_event_loop()

    # Startup: Initialize shared browser manager with optimized settings
    browser_manager = OptimizedPlaywrightManager(max_contexts=20, max_concurrent=10)
    await browser_manager.start()

    # Initialise database and scheduler
    await init_db()
    session_factory = get_session_factory()
    jobs = load_job_configs()
    scheduler = ScraperScheduler(
        browser_manager=browser_manager,
        session_factory=session_factory,
        jobs=jobs,
    )
    scheduler.start()

    # Store browser manager in app state for access by routers
    app.state.browser_manager = browser_manager
    app.state.uvloop_enabled = uvloop_enabled
    app.state.scraper_scheduler = scheduler

    yield

    # Shutdown: Clean up browser resources
    if browser_manager:
        await browser_manager.close()

    scheduler = getattr(app.state, "scraper_scheduler", None)
    if scheduler:
        await scheduler.shutdown()

    await close_db()


app = FastAPI(version="1.0.0", lifespan=lifespan)


@app.get("/")
async def root():
    return {
        "message": "Welcome to the Kleinanzeigen API",
        "endpoints": [
            "/inserate",
            "/inserat/{id}",
            "/inserate-detailed",
            "/stored-listings",
        ],
        "status": "operational",
    }


app.include_router(inserate.router)
app.include_router(inserat.router)
app.include_router(inserate_detailed.router)
app.include_router(stored_listings.router)
