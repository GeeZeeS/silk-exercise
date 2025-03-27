import os
import logging

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse, JSONResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from api import router as api_router
from core.config import settings
from core.database import db_instance, get_database


logging.basicConfig(
    level=logging.INFO if not settings.is_production else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(
    title=settings.app_name,
    description="Silk Software/Data Engineer Exercise",
    version="0.1.0",
    default_response_class=ORJSONResponse,
    openapi_url="/openapi.json" if not settings.is_production else None,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_db_client():
    """Connect to database when app starts"""
    await db_instance.connect_to_database()


@app.on_event("shutdown")
async def shutdown_db_client():
    """Close database connection when app shuts down"""
    await db_instance.close_database_connection()


@app.get("/health", tags=["Health"])
async def health_check(db: AsyncIOMotorDatabase = Depends(get_database)):
    """Health check endpoint to verify the API and database connection"""
    try:
        # Verify database connection by performing a simple command
        await db.command("ping")
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "database": "connected",
                "version": "0.1.0",
                "environment": settings.environment,
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
            },
        )


app.include_router(api_router, prefix="/api")
