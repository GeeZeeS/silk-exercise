import logging
import motor.motor_asyncio
import asyncio
from typing import Dict, List, Any
from celery import Task
from datetime import datetime

from .celery_app import celery_app
from .config import settings
from .api_client import SilkApiClient
from .scripts import merge_data

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


@celery_app.task(bind=True, base=DatabaseTask, name="process_hosts_data")
def process_hosts_data(
    self, crowdstrike_data: List[Dict], qualys_data: List[Dict]
) -> Dict[str, Any]:
    logger.info("Starting security data processing task")
    result = asyncio.run(process_and_save_data(self.db, crowdstrike_data, qualys_data))
    logger.info(f"Completed security data processing task: {result}")
    return result


@celery_app.task(bind=True, base=DatabaseTask, name="fetch_and_process_hosts_data")
def fetch_and_process_hosts_data(
    self,
    max_records: int = 100,
) -> Dict[str, Any]:
    logger.info(f"Fetching security data from API (max_records={max_records})")
    try:
        client = SilkApiClient(
            base_url=settings.api.api_url, token=settings.api.api_key
        )
        data = client.fetch_all_hosts(max_records=max_records)
        return process_hosts_data(data["crowdstrike"], data["qualys"])
    except Exception as e:
        logger.error(f"Error fetching and processing security data: {str(e)}")
        raise


async def process_and_save_data(
    db, crowdstrike_data: List[Dict], qualys_data: List[Dict]
) -> Dict[str, Any]:
    start_time = datetime.now()
    try:
        integrated_hosts = await process_data(db, crowdstrike_data, qualys_data)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return {
            "status": "success",
            "processed_count": len(integrated_hosts),
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


async def process_data(
    db, crowdstrike_data: List[Dict], qualys_data: List[Dict]
) -> List:
    logger.info(
        f"Processing data: {len(crowdstrike_data)} Crowdstrike records, {len(qualys_data)} Qualys records"
    )
    merged_records = []

    for qualys in qualys_data:
        if "address" not in qualys or "dnsHostName" not in qualys:
            logger.warning(
                f"Skipping Qualys record without address or dnsHostName: {qualys.get('_id', 'unknown')}"
            )
            continue

        for crowdstrike in crowdstrike_data:
            if "local_ip" not in crowdstrike or "hostname" not in crowdstrike:
                logger.warning(
                    f"Skipping Crowdstrike record without local_ip or hostname: {crowdstrike.get('device_id', 'unknown')}"
                )
                continue

            if (
                qualys["address"] == crowdstrike["local_ip"]
                and qualys["dnsHostName"] == crowdstrike["hostname"]
            ):
                logger.info(
                    f"Match found - Qualys ID: {qualys.get('id')}, "
                    f"Crowdstrike ID: {crowdstrike.get('device_id')}"
                )
                merged_data = merge_data(qualys, crowdstrike)
                existing = await db.integrated_hosts.find_one(
                    {
                        "address": qualys["address"],
                        "dns_host_name": qualys["dnsHostName"],
                    }
                )

                if existing:
                    logger.info(
                        f"Updating existing record for {qualys['address']} / {qualys['dnsHostName']}"
                    )
                    await db.integrated_hosts.replace_one(
                        {"_id": existing["_id"]}, merged_data
                    )
                else:
                    logger.info(
                        f"Inserting new record for {qualys['address']} / {qualys['dnsHostName']}"
                    )
                    await db.integrated_hosts.insert_one(merged_data)
                merged_records.append(merged_data)
                break

    logger.info(f"Processed {len(merged_records)} matched records")
    return merged_records
