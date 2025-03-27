import os
from typing import List, Dict, Any

from fastapi import APIRouter, Query, HTTPException, Body

from api.api_v1.instances.schemas import (
    HostAssetResponse,
    HostAsset,
    SearchParams,
    TaskResponse,
)
from core.security.crud import (
    get_host_assets,
    get_host_asset,
    get_host_by_asset_id,
    get_host_vulnerabilities,
    search_hosts,
)

from core.tasks import fetch_and_process_security_data

instances_router = APIRouter(
    prefix="/instances",
    tags=["Instances"],
)


@instances_router.get("/hosts", response_model=List[HostAssetResponse])
async def get_all_hosts(
    limit: int = Query(10, ge=1, le=10),
    skip: int = Query(0, ge=0),
):
    """
    Get all host assets with pagination
    """
    hosts = await get_host_assets(limit, skip)
    return hosts


@instances_router.get("/hosts/{host_id}", response_model=HostAsset)
async def get_host(host_id: str):
    """
    Get a single host by ID
    """
    host = await get_host_asset(host_id)
    if not host:
        raise HTTPException(status_code=404, detail=f"Host with ID {host_id} not found")
    return host


@instances_router.get("/hosts/asset/{asset_id}", response_model=HostAsset)
async def get_host_by_asset_id_endpoint(asset_id: int):
    """
    Get a single host by its original asset_id
    """
    host = await get_host_by_asset_id(asset_id)
    if not host:
        raise HTTPException(
            status_code=404, detail=f"Host with asset ID {asset_id} not found"
        )
    return host


@instances_router.post("/hosts/search", response_model=List[HostAssetResponse])
async def search_hosts_endpoint(
    search_params: SearchParams = Body(...),
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
):
    """
    Search for hosts based on criteria
    """
    query = search_params.to_query()
    hosts = await search_hosts(query, limit, skip)
    return hosts


@instances_router.get(
    "/vulnerabilities/{asset_id}", response_model=List[Dict[str, Any]]
)
async def get_vulnerabilities(asset_id: int):
    """
    Get all vulnerabilities for a host
    """
    host = await get_host_by_asset_id(asset_id)
    if not host:
        raise HTTPException(
            status_code=404, detail=f"Host with asset ID {asset_id} not found"
        )
    vulnerabilities = await get_host_vulnerabilities(asset_id)
    return vulnerabilities


@instances_router.get("/software/{asset_id}", response_model=List[Dict[str, Any]])
async def get_software(asset_id: int):
    """
    Get all software for a host
    """
    host = await get_host_by_asset_id(asset_id)
    if not host:
        raise HTTPException(
            status_code=404, detail=f"Host with asset ID {asset_id} not found"
        )
    return host.get("software", [])


@instances_router.post("/security-data/sync", response_model=TaskResponse)
async def trigger_scheduled_sync(
    max_records: int = Query(
        100, description="Maximum number of records to fetch", ge=1
    ),
):
    """
    Trigger the scheduled security data sync task

    This endpoint will trigger the same sequential processing task that runs automatically
    according to the schedule defined in Celery Beat. This ensures websites are parsed
    one by one (one result per page).
    """
    try:
        api_token = os.environ.get("API_TOKEN")
        if not api_token:
            raise HTTPException(
                status_code=400, detail="API_TOKEN environment variable is not set"
            )

        task = fetch_and_process_security_data.delay(api_token, max_records)

        return {
            "status": "submitted",
            "task_id": task.id,
            "message": f"Sequential processing task submitted successfully. Check task status with ID: {task.id}",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error triggering sequential processing: {str(e)}"
        )


@instances_router.get("/security-data/task/{task_id}")
async def get_task_status(task_id: str):
    """
    Get the status of data processing task
    """
    try:
        from core.celery_app import celery_app

        task = celery_app.AsyncResult(task_id)

        if task.state == "PENDING":
            response = {
                "status": "pending",
                "task_id": task_id,
                "message": "Task is pending execution",
            }
        elif task.state == "STARTED":
            response = {
                "status": "in_progress",
                "task_id": task_id,
                "message": "Task is in progress",
            }
        elif task.state == "SUCCESS":
            response = {
                "status": "completed",
                "task_id": task_id,
                "message": "Task completed successfully",
                "result": task.result,
            }
        else:
            response = {
                "status": "failed",
                "task_id": task_id,
                "message": f"Task failed with status: {task.state}",
                "result": {
                    "error": str(task.result) if task.result else "Unknown error"
                },
            }
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving task status: {str(e)}"
        )
