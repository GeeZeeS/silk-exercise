from fastapi import APIRouter

from api.api_v1.hosts.routers import instances_router

router = APIRouter(
    prefix="/v1",
)

router.include_router(instances_router)
