"""
Main FastAPI application entry point.
"""
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import logging

from app.config import get_settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.api.v1.router import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting application...")
    logger.info("Initiating MongoDB connection...")

    try:
        # Attempt to connect to MongoDB without blocking startup
        await connect_to_mongo()
    except Exception as e:
        # Log error but don't prevent startup
        logger.error(f"Failed to connect to MongoDB during startup: {e}")
        logger.warning("Application will start without database connection")

    logger.info("Application startup complete")
    yield

    # Shutdown
    logger.info("Shutting down application...")
    await close_mongo_connection()


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with server status page."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>DocuMind API</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #1e3a5f 0%, #0d1b2a 100%);
                color: white;
            }
            .container {
                text-align: center;
                padding: 40px;
            }
            .status {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                background: rgba(34, 197, 94, 0.2);
                border: 1px solid #22c55e;
                padding: 8px 16px;
                border-radius: 20px;
                margin-bottom: 20px;
            }
            .status-dot {
                width: 10px;
                height: 10px;
                background: #22c55e;
                border-radius: 50%;
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            h1 { font-size: 2.5rem; margin: 20px 0 10px; }
            p { color: #94a3b8; margin: 5px 0; }
            .links { margin-top: 30px; }
            a {
                display: inline-block;
                margin: 10px;
                padding: 12px 24px;
                background: #3b82f6;
                color: white;
                text-decoration: none;
                border-radius: 8px;
                transition: background 0.2s;
            }
            a:hover { background: #2563eb; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="status">
                <div class="status-dot"></div>
                <span>Server Running</span>
            </div>
            <h1>DocuMind API</h1>
            <p>AI-Powered Document & Multimedia Q&A Backend</p>
            <p style="color: #64748b; font-size: 0.9rem;">v1.0.0</p>
            <div class="links">
                <a href="/docs">API Documentation</a>
                <a href="/health">Health Check</a>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run probes."""
    from app.core.database import db

    health_status = {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "database": "disconnected"
    }

    # Check database connection
    if db.client is not None:
        try:
            # Quick ping without blocking
            await db.client.admin.command('ping', check=False)
            health_status["database"] = "connected"
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            health_status["database"] = "error"

    return health_status


@app.get("/startup")
async def startup_probe():
    """Startup probe endpoint for Cloud Run."""
    # This endpoint just confirms the app is running
    # Cloud Run uses this to verify the container started
    return {"status": "ready"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
