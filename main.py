from contextlib import asynccontextmanager
from fastapi import FastAPI
from routers import (
    inserate_ultra as inserate,
    inserat,
    inserate_detailed_ultra as inserate_detailed,
    stored_listings,
    scheduler as scheduler_router,
    metrics,
)
from utils.browser import OptimizedPlaywrightManager
from utils.asyncio_optimizations import EventLoopOptimizer
from db import init_db, close_db, get_session_factory
from services.event_bus import EventBus
from services.image_analysis import ImageAnalysisService
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

    event_bus: EventBus | None = None
    image_analysis_service: ImageAnalysisService | None = None

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
        event_bus = EventBus()
        await event_bus.start()
        image_analysis_service = ImageAnalysisService(
            session_factory=session_factory,
            event_bus=event_bus,
        )
        await image_analysis_service.start()
        jobs = load_job_configs()
        scheduler = ScraperScheduler(
            browser_manager=browser_manager,
            session_factory=session_factory,
            jobs=jobs,
            event_bus=event_bus,
        )
        await scheduler.start()
        logger.info("Database and scheduler initialized successfully")

        # Store browser manager in app state for access by routers
        app.state.browser_manager = browser_manager
        app.state.uvloop_enabled = uvloop_enabled
        app.state.scraper_scheduler = scheduler
        app.state.event_bus = event_bus
        app.state.image_analysis_service = image_analysis_service
        
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

        service = getattr(app.state, "image_analysis_service", None)
        if service:
            try:
                await service.stop()
                logger.info("Image analysis service stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping image analysis service: {e}")

        bus = getattr(app.state, "event_bus", None)
        if bus:
            try:
                await bus.stop()
                logger.info("Event bus stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping event bus: {e}")

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
            "/metrics",
        ],
        "status": "operational",
    }


app.include_router(inserate.router)
app.include_router(inserat.router)
app.include_router(inserate_detailed.router)
app.include_router(stored_listings.router)
app.include_router(scheduler_router.router)
app.include_router(metrics.router)
