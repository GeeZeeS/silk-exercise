from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime


def transform_host_data(host: Dict) -> Dict:
    """
    Transform MongoDB host data to match the API response models
    
    Args:
        host: Host data from MongoDB
        
    Returns:
        Transformed host data matching API models
    """
    if not host:
        return None
        
    # Convert _id to string if it exists
    if "_id" in host:
        host["_id"] = str(host["_id"])
    
    # Determine source based on available IDs
    source = "unknown"  # Default source
    source_id = str(host.get("_id"))  # Use _id as default source_id
    
    if host.get("crowdstrike_device_id"):
        source = "crowdstrike"
        source_id = host.get("crowdstrike_device_id")
    elif host.get("qualys_asset_id"):
        source = "qualys"
        source_id = str(host.get("qualys_asset_id"))
    
    # Map fields to expected schema
    transformed = {
        "_id": host.get("_id"),
        "source": source,
        "source_id": source_id,
        "hostname": host.get("hostname") or "unknown-host",  # Default hostname
        "ip_address": host.get("primary_ip") or host.get("ip_address"),
        "os_name": host.get("os"),
        "os_version": host.get("os"),  # Using os for both fields
        "status": host.get("status"),
        # Initialize empty lists and dictionaries
        "policies": [],
        "tags": [],
        "software": [],
        "vulnerabilities": [],
        "network_interfaces": [],
        "open_ports": [],
        "volumes": [],
        "accounts": [],
        "source_details": {},
        "additional_fields": {}
    }
    
    # Add optional fields if they exist
    if "external_ip" in host:
        transformed["external_ip"] = host["external_ip"]
    
    if "mac_address" in host:
        transformed["mac_address"] = host["mac_address"]
    
    if "last_seen" in host:
        transformed["last_seen"] = host["last_seen"]
    
    if "first_seen" in host:
        transformed["first_seen"] = host["first_seen"]
    
    if "hardware_info" in host:
        transformed["hardware_info"] = host["hardware_info"]
    
    if "cloud_provider" in host:
        transformed["cloud_info"] = {"provider": host["cloud_provider"]}
    else:
        transformed["cloud_info"] = None
    
    if "connection_info" in host:
        transformed["connection_info"] = host["connection_info"]
    else:
        transformed["connection_info"] = None
    
    if "agent_info" in host:
        transformed["agent_info"] = host["agent_info"]
    else:
        transformed["agent_info"] = None
    
    if "policies" in host and host["policies"]:
        transformed["policies"] = host["policies"]
    
    if "tags" in host and host["tags"]:
        transformed["tags"] = host["tags"]
    
    if "software" in host and host["software"]:
        transformed["software"] = host["software"]
    
    if "vulnerabilities" in host and host["vulnerabilities"]:
        transformed["vulnerabilities"] = host["vulnerabilities"]
    
    if "network_interfaces" in host and host["network_interfaces"]:
        transformed["network_interfaces"] = host["network_interfaces"]
    
    if "open_ports" in host and host["open_ports"]:
        transformed["open_ports"] = host["open_ports"]
    
    if "volumes" in host and host["volumes"]:
        transformed["volumes"] = host["volumes"]
    
    if "accounts" in host and host["accounts"]:
        transformed["accounts"] = host["accounts"]
    
    # Create source_details with any additional fields that don't map directly
    source_details = transformed["source_details"]
    if "qualys_asset_id" in host:
        source_details["asset_id"] = host["qualys_asset_id"]
    
    # Store all unmapped fields in additional_fields
    additional_fields = transformed["additional_fields"]
    for key, value in host.items():
        if key not in transformed and key not in ["_id", "crowdstrike_device_id", "qualys_asset_id", "primary_ip", "os", "cloud_provider"]:
            additional_fields[key] = value
    
    return transformed


async def get_host_assets(
    db: AsyncIOMotorDatabase,
    limit: int = 10, 
    skip: int = 0,
    fetch_all: bool = False
) -> List[Dict]:
    """
    Get all host assets with pagination
    
    Args:
        db: Database connection
        limit: Maximum number of results to return
        skip: Number of results to skip (for pagination)
        fetch_all: If True, ignores pagination and returns all hosts
        
    Returns:
        List of host assets
    """
    if fetch_all:
        # Return all hosts without pagination
        cursor = db.integrated_hosts.find()
        hosts = await cursor.to_list(length=None)  # Fetch all documents
    else:
        # Use pagination
        cursor = db.integrated_hosts.find().skip(skip).limit(limit)
        hosts = await cursor.to_list(length=limit)
    
    # Transform the hosts to match the API response format
    transformed_hosts = [transform_host_data(host) for host in hosts]
    return transformed_hosts


async def get_host_asset(
    db: AsyncIOMotorDatabase,
    host_id: str
) -> Optional[Dict]:
    """
    Get a single host by its MongoDB ID
    
    Args:
        db: Database connection
        host_id: MongoDB ID of the host
        
    Returns:
        Host asset or None if not found
    """
    try:
        object_id = ObjectId(host_id)
    except:
        return None
        
    host = await db.integrated_hosts.find_one({"_id": object_id})
    if not host:
        return None
        
    # Transform the host to match the API response format
    return transform_host_data(host)


async def get_host_by_asset_id(
    db: AsyncIOMotorDatabase,
    asset_id: int
) -> Optional[Dict]:
    """
    Get a single host by its original asset_id
    
    Args:
        db: Database connection
        asset_id: Original asset ID from the source system
        
    Returns:
        Host asset or None if not found
    """
    # Try as qualys_asset_id
    host = await db.integrated_hosts.find_one({"qualys_asset_id": asset_id})
    
    # If not found, try as source_details.asset_id
    if not host:
        host = await db.integrated_hosts.find_one({"source_details.asset_id": asset_id})
    
    # If still not found, try as source_id
    if not host:
        host = await db.integrated_hosts.find_one({"source_id": str(asset_id)})
    
    if not host:
        return None
        
    # Transform the host to match the API response format
    return transform_host_data(host)


async def search_hosts(
    db: AsyncIOMotorDatabase,
    query: Dict,
    limit: int = 100,
    skip: int = 0
) -> List[Dict]:
    """
    Search for hosts based on criteria
    
    Args:
        db: Database connection
        query: MongoDB query dictionary
        limit: Maximum number of results to return
        skip: Number of results to skip (for pagination)
        
    Returns:
        List of matching host assets
    """
    # Map query fields if needed
    mapped_query = {}
    for key, value in query.items():
        if key == 'ip_address':
            mapped_query['primary_ip'] = value
        elif key == 'os_name':
            mapped_query['os'] = value
        else:
            mapped_query[key] = value
    
    cursor = db.integrated_hosts.find(mapped_query).skip(skip).limit(limit)
    hosts = await cursor.to_list(length=limit)
    
    # Transform the hosts to match the API response format
    transformed_hosts = [transform_host_data(host) for host in hosts]
    return transformed_hosts


async def get_host_vulnerabilities(
    db: AsyncIOMotorDatabase,
    asset_id: int
) -> List[Dict]:
    """
    Get all vulnerabilities for a host
    
    Args:
        db: Database connection
        asset_id: Original asset ID of the host
        
    Returns:
        List of vulnerabilities for the host
    """
    host = await get_host_by_asset_id(db, asset_id)
    
    if not host:
        return []
        
    return host.get("vulnerabilities", []) 