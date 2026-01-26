from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio
import logging
import logging.config
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.core.limiter import limiter
from app.core.sentry import init_sentry
from app.routes import auth, users, calls, webrtc
from app.models.user import User, Call, BlockedUser, Report, VerificationToken


# Custom CORS middleware that handles OPTIONS first
class CORSPreflight(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin", "")
        
        # Handle preflight OPTIONS requests
        if request.method == "OPTIONS":
            response = Response(status_code=200)
            if origin in settings.ALLOWED_ORIGINS:
                response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Accept, Origin, X-Requested-With"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Max-Age"] = "3600"
            return response
        
        # For non-OPTIONS requests, proceed and add CORS headers to response
        response = await call_next(request)
        if origin in settings.ALLOWED_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

# Initialize Sentry for error tracking
init_sentry()

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


async def _init_db_with_retries() -> None:
    max_retries = 10
    for attempt in range(1, max_retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
            # Reset all users to offline on startup to avoid stale presence
            db = SessionLocal()
            try:
                db.query(User).update({User.is_online: False})
                db.commit()
                logger.info("All users set to offline on startup")
            finally:
                db.close()
            return
        except Exception as e:
            logger.error(f"Failed to initialize database (attempt {attempt}/{max_retries}): {e}")
            await asyncio.sleep(min(30, 2 * attempt))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Application starting up...")
    startup_task: asyncio.Task | None = None

    if settings.ENVIRONMENT == "production":
        # Don't block startup in production; retry DB init in background.
        startup_task = asyncio.create_task(_init_db_with_retries())
    else:
        await _init_db_with_retries()

    yield

    # Shutdown
    if startup_task and not startup_task.done():
        startup_task.cancel()
    logger.info("Application shutting down...")


app = FastAPI(
    title="UniLink API",
    description="1v1 Video Calling Platform for University Students",
    version="1.1.0",
    lifespan=lifespan
)

# Custom OpenAPI schema with Bearer token security
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="UniLink API",
        version="1.1.0",
        description="1v1 Video Calling Platform for University Students",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token",
        }
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Log CORS configuration
logger.info(f"ALLOWED_ORIGINS: {settings.ALLOWED_ORIGINS}")
logger.info(f"ALLOWED_ORIGINS type: {type(settings.ALLOWED_ORIGINS)}")

# Add custom CORS middleware (runs FIRST, handles OPTIONS before anything else)
app.add_middleware(CORSPreflight)

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
app.include_router(webrtc.router)


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
