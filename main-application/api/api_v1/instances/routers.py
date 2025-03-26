from typing import List, Dict, Any

from fastapi import APIRouter, Query, HTTPException, Body, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from api.api_v1.instances.schemas import HostAssetResponse, HostAsset, SearchParams
from core.instances.crud import (
    get_host_assets,
    get_host_asset,
    get_host_by_asset_id,
    get_host_vulnerabilities,
    search_hosts,
)
from core.database import get_database

instances_router = APIRouter(
    prefix="/instances",
    tags=["Instances"],
)


@instances_router.get("/hosts", response_model=List[HostAssetResponse])
async def get_all_hosts(
    limit: int = Query(10, description="Number of hosts to return", ge=1, le=100),
    skip: int = Query(0, description="Number of hosts to skip", ge=0),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get all host assets with pagination
    """
    hosts = await get_host_assets(limit, skip)
    return hosts


@instances_router.get("/hosts/{host_id}", response_model=HostAsset)
async def get_host(
    host_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get a single host by its MongoDB ID
    """
    host = await get_host_asset(host_id)
    if not host:
        raise HTTPException(status_code=404, detail=f"Host with ID {host_id} not found")
    return host


@instances_router.get("/hosts/asset/{asset_id}", response_model=HostAsset)
async def get_host_by_asset_id_endpoint(
    asset_id: int,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
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
    limit: int = Query(100, description="Number of hosts to return", ge=1, le=1000),
    skip: int = Query(0, description="Number of hosts to skip", ge=0),
    db: AsyncIOMotorDatabase = Depends(get_database),
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
async def get_vulnerabilities(
    asset_id: int,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get all vulnerabilities for a host
    """
    # Check if host exists
    host = await get_host_by_asset_id(asset_id)
    if not host:
        raise HTTPException(
            status_code=404, detail=f"Host with asset ID {asset_id} not found"
        )

    # Return the vulnerabilities
    vulnerabilities = await get_host_vulnerabilities(asset_id)
    return vulnerabilities


@instances_router.get("/software/{asset_id}", response_model=List[Dict[str, Any]])
async def get_software(
    asset_id: int,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get all software for a host
    """
    # Check if host exists
    host = await get_host_by_asset_id(asset_id)
    if not host:
        raise HTTPException(
            status_code=404, detail=f"Host with asset ID {asset_id} not found"
        )

    # Return the software
    return host.get("software", [])
