from contextlib import asynccontextmanager
from fastapi import FastAPI
from routers import (
    inserate_ultra as inserate,
    inserat,
    inserate_detailed_ultra as inserate_detailed,
    stored_listings,
    scheduler as scheduler_router,
)
from utils.browser import OptimizedPlaywrightManager
from utils.asyncio_optimizations import EventLoopOptimizer
from db import init_db, close_db, get_session_factory
from services.scheduler import ScraperScheduler, load_job_configs
import logging

# Global browser manager instance for sharing across all endpoints
browser_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown events"""
    global browser_manager
    
    logger = logging.getLogger(__name__)

    # Setup uvloop for maximum performance (2-4x improvement)
    uvloop_enabled = EventLoopOptimizer.setup_uvloop()

    # Optimize event loop settings
    EventLoopOptimizer.optimize_event_loop()

    try:
        # Startup: Initialize shared browser manager with optimized settings
        logger.info("Initializing browser manager...")
        browser_manager = OptimizedPlaywrightManager(max_contexts=20, max_concurrent=10)
        await browser_manager.start()
        logger.info("Browser manager initialized successfully")

        # Initialise database and scheduler
        logger.info("Initializing database...")
        await init_db()
        session_factory = get_session_factory()
        jobs = load_job_configs()
        scheduler = ScraperScheduler(
            browser_manager=browser_manager,
            session_factory=session_factory,
            jobs=jobs,
        )
        await scheduler.start()
        logger.info("Database and scheduler initialized successfully")

        # Store browser manager in app state for access by routers
        app.state.browser_manager = browser_manager
        app.state.uvloop_enabled = uvloop_enabled
        app.state.scraper_scheduler = scheduler
        
        logger.info("Application startup completed successfully")

        yield

    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        # Clean up any partially initialized resources
        if browser_manager:
            try:
                await browser_manager.close()
            except Exception as cleanup_error:
                logger.error(f"Error cleaning up browser manager: {cleanup_error}")
        raise
    finally:
        # Shutdown: Clean up browser resources
        logger.info("Application shutdown initiated...")
        
        if browser_manager:
            try:
                await browser_manager.close()
                logger.info("Browser manager closed successfully")
            except Exception as e:
                logger.error(f"Error closing browser manager: {e}")

        scheduler = getattr(app.state, "scraper_scheduler", None)
        if scheduler:
            try:
                await scheduler.shutdown()
                logger.info("Scheduler shutdown successfully")
            except Exception as e:
                logger.error(f"Error shutting down scheduler: {e}")

        try:
            await close_db()
            logger.info("Database connections closed successfully")
        except Exception as e:
            logger.error(f"Error closing database: {e}")
            
        logger.info("Application shutdown completed")


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
            "/scheduler/jobs",
        ],
        "status": "operational",
    }


app.include_router(inserate.router)
app.include_router(inserat.router)
app.include_router(inserate_detailed.router)
app.include_router(stored_listings.router)
app.include_router(scheduler_router.router)
