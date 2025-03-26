"""
API Version 1 Routes

This module contains all the API endpoints for version 1 of the API.
"""

from fastapi import APIRouter

from api.api_v1.instances.routers import instances_router

router = APIRouter(
    prefix="/v1",
)

router.include_router(instances_router)
