"""
app/main.py
-----------
FastAPI Application Entrypoint for SIMS — Sales Intelligence and Management System.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from app.core.logging import logger
from app.api.router import api_router
from app.db.mongo import get_db, ensure_indexes
from app.db.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes MongoDB indexes and seeds demo data on application startup."""
    try:
        db = get_db()
        ensure_indexes(db)
        if db.companies.count_documents({}) < 3:
            logger.info("Initializing demo seed data...")
            seed_database(db)
        logger.info(f"{settings.APP_NAME} initialized successfully.")
    except Exception as e:
        logger.warning(f"Startup database initialization notice: {e}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise Multi-Tenant Sales Operations & Analytical Platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Formats validation errors into standardized error payload."""
    errors = exc.errors()
    error_msg = "; ".join([f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in errors])
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": error_msg, "error_code": "ERR_VALIDATION"}
    )


# Mount versioned API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.DEBUG)
