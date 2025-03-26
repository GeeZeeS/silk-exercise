"""
API Router Configuration

This module sets up the main API router that includes all API version routers.
"""

from fastapi import APIRouter
from .api_v1 import router as api_v1_router

router = APIRouter()
router.include_router(api_v1_router)
