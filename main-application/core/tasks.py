import logging
import motor.motor_asyncio
import asyncio
from typing import Dict, List, Any
from celery import Task
from datetime import datetime

from .celery_app import celery_app
from .config import settings
from .api_client import SilkSecurityApiClient

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base Celery database connection handler"""

    _db = None

    @property
    def db(self):
        if self._db is None:
            mongo_url = f"mongodb://{settings.db.user}:{settings.db.password}@{settings.db.host}:{settings.db.port}/{settings.db.database}?authSource=admin"
            client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
            self._db = client[settings.db.database]
        return self._db


@celery_app.task(bind=True, base=DatabaseTask, name="process_security_data")
def process_security_data(
    self, crowdstrike_data: List[Dict], qualys_data: List[Dict]
) -> Dict[str, Any]:
    """
    Celery task to process CrowdStrike and Qualys security data and save to the database

    Args:
        crowdstrike_data: List of CrowdStrike device data
        qualys_data: List of Qualys host asset data

    Returns:
        Dict containing task result information
    """
    logger.info("Starting security data processing task")
    result = asyncio.run(process_and_save_data(self.db, crowdstrike_data, qualys_data))
    logger.info(f"Completed security data processing task: {result}")
    return result


@celery_app.task(bind=True, base=DatabaseTask, name="fetch_and_process_security_data")
def fetch_and_process_security_data(
    self,
    api_token: str,
    max_records: int = 100,
    base_url: str = "https://api.recruiting.app.silk.security",
) -> Dict[str, Any]:
    """
    Celery task to fetch security data from API endpoints and process it

    Args:
        api_token: API token for authentication
        max_records: Maximum number of records to fetch from each API
        base_url: Base URL for the API (optional, uses default if not provided)

    Returns:
        Dict containing task result information
    """
    logger.info(f"Fetching security data from API (max_records={max_records})")

    try:
        client = SilkSecurityApiClient(base_url=base_url, token=api_token)
        data = client.fetch_all_hosts(max_records=max_records)
        return process_security_data(data["crowdstrike"], data["qualys"])
    except Exception as e:
        logger.error(f"Error fetching and processing security data: {str(e)}")
        raise


async def process_and_save_data(
    db, crowdstrike_data: List[Dict], qualys_data: List[Dict]
) -> Dict[str, Any]:
    """
    Process and save security data asynchronously

    Args:
        db: MongoDB database instance
        crowdstrike_data: List of CrowdStrike device data
        qualys_data: List of Qualys host asset data

    Returns:
        Dict containing task result information
    """
    start_time = datetime.now()

    try:
        integrated_hosts = process_data(crowdstrike_data, qualys_data)
        host_dicts = [
            host.dict(by_alias=True, exclude={"id"}) for host in integrated_hosts
        ]

        if host_dicts:
            result = await db.integrated_hosts.insert_many(host_dicts)
            inserted_count = len(result.inserted_ids)
        else:
            inserted_count = 0

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return {
            "status": "success",
            "processed_count": len(integrated_hosts),
            "inserted_count": inserted_count,
            "duration_seconds": duration,
            "timestamp": end_time.isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in process_and_save_data: {str(e)}")
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return {
            "status": "error",
            "error": str(e),
            "duration_seconds": duration,
            "timestamp": end_time.isoformat(),
        }
