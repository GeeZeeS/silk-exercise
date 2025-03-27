from typing import List, Dict, Any, Optional, Annotated
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict

from core.security.schemas import PydanticObjectId


class Account(BaseModel):
    username: str


class HostAssetInterface(BaseModel):
    interfaceName: Optional[str] = None
    macAddress: Optional[str] = None
    gatewayAddress: Optional[str] = None
    address: Optional[str] = None
    hostname: Optional[str] = None


class OpenPort(BaseModel):
    serviceName: str
    protocol: str
    port: int


class Processor(BaseModel):
    name: str
    speed: int


class Software(BaseModel):
    name: str
    version: str


class Volume(BaseModel):
    name: str
    size: int
    free: int


class Vulnerability(BaseModel):
    qid: int
    firstFound: datetime
    lastFound: datetime
    hostInstanceVulnId: int


class EC2SourceInfo(BaseModel):
    instanceType: str
    subnetId: str
    imageId: str
    groupName: str
    accountId: str
    macAddress: str
    createdDate: datetime
    reservationId: str
    instanceId: str
    monitoringEnabled: str
    spotInstance: str
    zone: str
    instanceState: str
    privateDnsName: str
    vpcId: str
    type: str
    availabilityZone: str
    privateIpAddress: str
    firstDiscovered: datetime
    ec2InstanceTags: Optional[Dict[str, Any]] = None
    publicIpAddress: Optional[str] = None
    lastUpdated: datetime
    region: str
    assetId: int
    groupId: str
    localHostname: str
    publicDnsName: str


class Tag(BaseModel):
    id: int
    name: str


class HostAsset(BaseModel):
    """Host asset model with all details"""

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "asset_id": 305003660,
                "address": "172.31.19.223",
                "name": "ip-172-31-19-223.ec2.internal",
                "os": "Amazon Linux 2",
            }
        },
    )

    id: PydanticObjectId = Field(default_factory=ObjectId, alias="_id")
    asset_id: int
    address: str
    agentInfo: Dict[str, Any]
    biosDescription: str
    cloudProvider: str
    created: datetime
    dnsHostName: str
    fqdn: str
    isDockerHost: str
    lastComplianceScan: datetime
    lastLoggedOnUser: str
    lastSystemBoot: datetime
    lastVulnScan: datetime
    manufacturer: str
    model: str
    modified: datetime
    name: str
    networkGuid: str
    os: str
    qwebHostId: int
    timezone: str
    totalMemory: int
    trackingMethod: str
    type: str

    accounts: List[Account]
    interfaces: List[HostAssetInterface]
    openPorts: List[OpenPort]
    processors: List[Processor]
    software: List[Software]
    volumes: List[Volume]
    vulnerabilities: List[Vulnerability]
    sourceInfo: EC2SourceInfo
    tags: List[Tag]


class HostAssetResponse(BaseModel):
    """Simplified host asset response model"""

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    id: str = Field(..., alias="_id")
    asset_id: int
    address: str
    name: str
    os: str
    created: datetime
    modified: datetime
    cloudProvider: str


class SearchParams(BaseModel):
    """Search parameters for filtering hosts"""

    asset_id: Optional[int] = None
    address: Optional[str] = None
    name: Optional[str] = None
    os: Optional[str] = None
    cloudProvider: Optional[str] = None

    def to_query(self) -> Dict[str, Any]:
        """Convert search parameters to MongoDB query"""
        query = {}
        for field, value in self.model_dump(exclude_none=True).items():
            if isinstance(value, str) and ("*" in value or "?" in value):
                # Handle wildcard searches using regex
                pattern = value.replace("*", ".*").replace("?", ".")
                query[field] = {"$regex": f"^{pattern}$", "$options": "i"}
            else:
                query[field] = value
        return query


class TaskResponse(BaseModel):
    """Response model for task submission"""

    status: str = "submitted"
    task_id: Optional[str] = None
    message: str
    result: Optional[Dict[str, Any]] = None
