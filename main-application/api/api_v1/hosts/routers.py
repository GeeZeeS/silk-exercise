from datetime import datetime, timedelta

from fastapi import APIRouter, Query, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from core.database import get_database
from core.tasks import fetch_and_process_hosts_data
from typing import Optional

instances_router = APIRouter(
    prefix="/hosts",
    tags=["Hosts"],
)


@instances_router.get("/")
async def get_hosts(
    operating_system: Optional[str] = Query(None),
    is_old: Optional[bool] = Query(None),
    limit: int = Query(1, ge=1),
    skip: int = Query(0, ge=0),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get hosts with filtering options.

    Filters:
    - operating_system: Filter hosts by their OS name
    - is_old: When true, returns hosts last seen more than 30 days ago.
              When false, returns hosts seen within the last 30 days.
    """
    try:
        query = {}

        if operating_system:
            query["os"] = {"$regex": f".*{operating_system}.*", "$options": "i"}

        if is_old is not None:
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)

            if is_old:
                query["last_seen"] = {"$lt": thirty_days_ago}
            else:
                query["last_seen"] = {"$gte": thirty_days_ago}

        cursor = db.integrated_hosts.find(query).skip(skip).limit(limit)
        hosts = await cursor.to_list(length=limit)
        for host in hosts:
            if "_id" in host:
                host["_id"] = str(host["_id"])

        return {"status": "success", "hosts": hosts}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving hosts: {str(e)}")


@instances_router.post("/sync/")
async def trigger_scheduled_sync(
    max_records: int = Query(
        100, description="Maximum number of records to fetch", ge=1
    ),
):
    """
    Trigger the scheduled security data sync task

    This endpoint will trigger the same sequential processing task that runs automatically
    according to the schedule defined in Celery Beat.
    """
    try:
        task = fetch_and_process_hosts_data.delay(max_records)

        return {
            "status": "submitted",
            "task_id": task.id,
            "message": f"Task submitted successfully.",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error triggering sequential processing: {str(e)}"
        )
