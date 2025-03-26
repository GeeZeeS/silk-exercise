import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from urllib.parse import quote_plus

from core.config import settings

logger = logging.getLogger(__name__)


class Database:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    @staticmethod
    def get_mongo_url() -> str:
        """Create MongoDB connection URL from settings"""
        host = settings.db.host
        port = settings.db.port
        user = settings.db.user
        password = settings.db.password
        database = settings.db.database

        # Escape username and password for URL
        if user and password:
            escaped_user = quote_plus(user)
            escaped_password = quote_plus(password)
            return f"mongodb://{escaped_user}:{escaped_password}@{host}:{port}/{database}?authSource=admin"
        return f"mongodb://{host}:{port}/{database}"

    async def connect_to_database(self) -> None:
        """Connect to MongoDB database"""
        if self.client is not None:
            return

        mongo_url = self.get_mongo_url()
        db_name = settings.db.database

        logger.info(f"Connecting to MongoDB at {settings.db.host}:{settings.db.port}")
        try:
            self.client = AsyncIOMotorClient(mongo_url)
            # Force a connection to verify it works
            await self.client.admin.command('ping')
            self.db = self.client[db_name]
            logger.info("Connected to MongoDB successfully")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    async def close_database_connection(self) -> None:
        """Close database connection"""
        if self.client is None:
            return

        self.client.close()
        self.client = None
        self.db = None
        logger.info("Closed MongoDB connection")


# Create a database instance
db_instance = Database()


async def get_database() -> AsyncIOMotorDatabase:
    """Get database connection for dependency injection"""
    if db_instance.db is None:
        await db_instance.connect_to_database()
    return db_instance.db
