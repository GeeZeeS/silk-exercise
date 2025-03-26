#!/usr/bin/env python3

"""
Test script for MongoDB connection.
Run this to verify that your MongoDB connection is working properly.
"""

import asyncio
import sys
import logging
from motor.motor_asyncio import AsyncIOMotorClient

from core.config import settings
from core.database import db_instance


async def test_connection():
    """Test MongoDB connection"""
    try:
        print(f"Connecting to MongoDB at {settings.db.host}:{settings.db.port}...")
        print(f"Database: {settings.db.database}")
        print(f"Username: {settings.db.user}")
        
        # Connect to MongoDB
        await db_instance.connect_to_database()
        
        # Test ping
        if db_instance.db is not None:
            await db_instance.db.command("ping")
            print("MongoDB connection successful! ✅")
            
            # Check collections
            collections = await db_instance.db.list_collection_names()
            print(f"Available collections: {collections}")
            
            # Count records in host_assets
            if "host_assets" in collections:
                count = await db_instance.db.host_assets.count_documents({})
                print(f"Number of host assets: {count}")
            
            await db_instance.close_database_connection()
            return True
        else:
            print("Failed to connect to MongoDB. Database object is None. ❌")
            return False
    
    except Exception as e:
        print(f"Error connecting to MongoDB: {e} ❌")
        logging.exception("Database connection error")
        return False


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Run the test
    success = asyncio.run(test_connection())
    
    # Exit with appropriate code
    sys.exit(0 if success else 1) 