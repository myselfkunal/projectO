from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import logging.config
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.core.limiter import limiter
from app.routes import auth, users, calls
from app.models.user import User, Call, BlockedUser, Report, VerificationToken

# Configure structured logging
logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "detailed",
            "level": "INFO" if settings.ENVIRONMENT == "production" else "DEBUG",
        },
    },
    "root": {
        "level": "INFO" if settings.ENVIRONMENT == "production" else "DEBUG",
        "handlers": ["console"],
    },
}

logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - create database tables
    logger.info("Application starting up...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    yield
    # Shutdown
    logger.info("Application shutting down...")


app = FastAPI(
    title="UniLink API",
    description="1v1 Video Calling Platform for University Students",
    version="1.1.0",
    lifespan=lifespan
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware with hardened settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,
)

# Add error handling middleware
@app.middleware("http")
async def error_handler_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        if settings.ENVIRONMENT == "production":
            return JSONResponse(status_code=500, content={"detail": "Internal server error"})
        else:
            return JSONResponse(status_code=500, content={"detail": str(exc)})

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(calls.router)


@app.get("/health")
def health_check():
    """Health check endpoint with database connectivity test"""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("Health check passed")
        return {"status": "healthy", "database": "connected", "version": "1.1.0"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "degraded", "database": "disconnected", "error": str(e)}


@app.get("/")
def root():
    return {
        "message": "Welcome to UniLink API",
        "version": "1.1.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development"
    )
