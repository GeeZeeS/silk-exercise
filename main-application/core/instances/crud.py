from typing import List, Dict, Any, Optional
from bson import ObjectId

from core.database import db_instance


async def get_host_asset(host_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a host asset by its ID
    """
    if db_instance.db is None:
        await db_instance.connect_to_database()
    return await db_instance.db["host_assets"].find_one({"_id": ObjectId(host_id)})


async def get_host_assets(limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
    """
    Retrieve multiple host assets with pagination
    """
    if db_instance.db is None:
        await db_instance.connect_to_database()
    cursor = db_instance.db["host_assets"].find().skip(skip).limit(limit)
    return await cursor.to_list(length=limit)


async def get_host_by_asset_id(asset_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve a host asset by its original asset_id
    """
    if db_instance.db is None:
        await db_instance.connect_to_database()
    return await db_instance.db["host_assets"].find_one({"asset_id": asset_id})


async def insert_host_asset(host_data: Dict[str, Any]) -> str:
    """
    Insert a new host asset
    """
    if db_instance.db is None:
        await db_instance.connect_to_database()
    result = await db_instance.db["host_assets"].insert_one(host_data)
    return str(result.inserted_id)


async def update_host_asset(host_id: str, host_data: Dict[str, Any]) -> bool:
    """
    Update an existing host asset
    """
    if db_instance.db is None:
        await db_instance.connect_to_database()
    result = await db_instance.db["host_assets"].update_one(
        {"_id": ObjectId(host_id)}, {"$set": host_data}
    )
    return result.modified_count > 0


async def delete_host_asset(host_id: str) -> bool:
    """
    Delete a host asset
    """
    if db_instance.db is None:
        await db_instance.connect_to_database()
    result = await db_instance.db["host_assets"].delete_one({"_id": ObjectId(host_id)})
    return result.deleted_count > 0


async def get_host_vulnerabilities(asset_id: int) -> List[Dict[str, Any]]:
    """
    Get all vulnerabilities for a host
    """
    if db_instance.db is None:
        await db_instance.connect_to_database()
    host = await get_host_by_asset_id(asset_id)
    if not host:
        return []
    return host.get("vulnerabilities", [])


async def search_hosts(query: Dict[str, Any], limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
    """
    Search for hosts based on query criteria
    """
    if db_instance.db is None:
        await db_instance.connect_to_database()
    cursor = db_instance.db["host_assets"].find(query).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)
