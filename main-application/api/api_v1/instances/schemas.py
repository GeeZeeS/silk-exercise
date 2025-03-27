from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TaskResponse(BaseModel):
    """Response model for asynchronous task endpoints"""
    status: str
    task_id: str
    message: str
    result: Optional[Dict[str, Any]] = None


class HostAssetResponse(BaseModel):
    """Simplified host asset response model for list endpoints"""
    id: str = Field(..., alias="_id", description="MongoDB ID")
    source: str = Field("unknown", description="Source of host data (crowdstrike, qualys, unknown)")
    source_id: str = Field("unknown", description="Original ID from source system")
    hostname: str = Field("unknown-host", description="Hostname of device")
    ip_address: Optional[str] = Field(None, description="Primary IP address")
    os_name: Optional[str] = Field(None, description="Operating system name")
    os_version: Optional[str] = Field(None, description="Operating system version")
    last_seen: Optional[datetime] = Field(None, description="Last seen timestamp")
    status: Optional[str] = Field(None, description="Status of device")
    
    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "id": "5f9b3b2b0f1c7d2b9c8f1c7d",
                "source": "crowdstrike",
                "source_id": "1234567890",
                "hostname": "host-1.example.com",
                "ip_address": "192.168.1.100",
                "os_name": "Windows",
                "os_version": "10.0.19044",
                "last_seen": "2023-03-15T12:30:45Z",
                "status": "normal"
            }
        }


class HostAsset(BaseModel):
    """Complete host asset model for detailed view"""
    id: str = Field(..., alias="_id", description="MongoDB ID")
    source: str = Field("unknown", description="Source of host data (crowdstrike, qualys, unknown)")
    source_id: str = Field("unknown", description="Original ID from source system")
    hostname: str = Field("unknown-host", description="Hostname of device")
    ip_address: Optional[str] = Field(None, description="Primary IP address") 
    external_ip: Optional[str] = Field(None, description="External IP address")
    mac_address: Optional[str] = Field(None, description="MAC address")
    os_name: Optional[str] = Field(None, description="Operating system name")
    os_version: Optional[str] = Field(None, description="Operating system version")
    last_seen: Optional[datetime] = Field(None, description="Last seen timestamp")
    first_seen: Optional[datetime] = Field(None, description="First seen timestamp")
    status: Optional[str] = Field(None, description="Status of device")
    hardware_info: Optional[Dict[str, Any]] = Field(None, description="Hardware information")
    cloud_info: Optional[Dict[str, Any]] = Field(None, description="Cloud provider information")
    connection_info: Optional[Dict[str, Any]] = Field(None, description="Network connection information")
    agent_info: Optional[Dict[str, Any]] = Field(None, description="Agent/sensor information")
    policies: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Applied policies")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags applied to host")
    software: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Installed software")
    vulnerabilities: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Vulnerabilities")
    network_interfaces: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Network interfaces")
    open_ports: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Open ports")
    volumes: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Storage volumes")
    accounts: Optional[List[str]] = Field(default_factory=list, description="User accounts")
    source_details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional source-specific details")
    additional_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="All remaining fields from the source")
    
    class Config:
        allow_population_by_field_name = True


class SearchParams(BaseModel):
    """Search parameters for filtering hosts"""
    source: Optional[str] = Field(None, description="Filter by source (crowdstrike, qualys)")
    hostname: Optional[str] = Field(None, description="Filter by hostname (partial match)")
    ip_address: Optional[str] = Field(None, description="Filter by IP address (exact match)")
    os_name: Optional[str] = Field(None, description="Filter by OS name (partial match)")
    status: Optional[str] = Field(None, description="Filter by status")
    tags: Optional[List[str]] = Field(None, description="Filter by tags (must have all specified tags)")
    
    def to_query(self) -> Dict:
        """Convert search parameters to MongoDB query"""
        query = {}
        
        # Build query based on provided parameters
        if self.source:
            # Special handling for source field which isn't directly stored
            if self.source.lower() == "crowdstrike":
                query["crowdstrike_device_id"] = {"$exists": True}
            elif self.source.lower() == "qualys":
                query["qualys_asset_id"] = {"$exists": True}
            
        if self.hostname:
            query["hostname"] = {"$regex": self.hostname, "$options": "i"}
            
        if self.ip_address:
            # Map to primary_ip in database schema
            query["primary_ip"] = self.ip_address
            
        if self.os_name:
            # Map to os in database schema
            query["os"] = {"$regex": self.os_name, "$options": "i"}
            
        if self.status:
            query["status"] = self.status
            
        if self.tags and len(self.tags) > 0:
            query["tags"] = {"$all": self.tags}
            
        return query 