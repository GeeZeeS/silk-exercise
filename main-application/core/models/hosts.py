from datetime import datetime
from typing import List, Dict
from pydantic import BaseModel


class NetworkInterface(BaseModel):
    # Qualys -> networkInterface -> list -> HostAssetInterface

    interface_name: str | None = None
    mac_address: str | None = None
    gateway_address: str | None = None
    address: str
    hostname: str


class OpenPort(BaseModel):
    # Qualys -> openPort -> list -> HostAssetOpenPort

    service_name: str
    protocol: str
    port: int


class Account(BaseModel):
    # Qualys -> account -> list -> HostAssetAccount -> username
    username: str


class Processor(BaseModel):
    # Qualys -> processor -> list -> HostAssetProcessor
    name: str
    speed: int


class Software(BaseModel):
    # Qualys -> software -> list -> HostAssetSoftware
    name: str
    version: str


class Volume(BaseModel):
    # Qualys -> volume -> list -> HostAssetVolume (root Dict)
    free: str
    name: str
    size: str


class Vulnerability(BaseModel):
    # Qualys -> vuln -> list -> HostAssetVuln (hostInstanceVulnId Dict)
    qid: int
    vulnerability_id: str
    last_found: datetime
    first_found: datetime


class ServiceID(BaseModel):
    service_name: str  # Qualys or Crowdstrike
    service_id: str  # Qualys -> id # Crowdstrike -> device_id


class QualysSourceInfo(BaseModel):
    instance_type: str | None = (
        None  # Qualys -> sourceInfo -> list -> [0] -> instanceType
    )
    subnet_id: str | None = None  # Qualys -> sourceInfo -> list -> [0] -> subnetId
    image_id: str | None = None  # Qualys -> sourceInfo -> list -> [0] -> imageId
    group_name: str | None = None  # Qualys -> sourceInfo -> list -> [0] -> groupName
    account_id: str | None = None  # Qualys -> sourceInfo -> list -> [0] -> accountId
    created_date: str | None = (
        None  # Qualys -> sourceInfo -> list -> [0] -> createdDate
    )
    reservation_id: str | None = (
        None  # Qualys -> sourceInfo -> list -> [0] -> reservationId
    )
    instance_id: str | None = None  # Qualys -> sourceInfo -> list -> [0] -> instanceId
    monitoring_enabled: str | None = (
        None  # Qualys -> sourceInfo -> list -> [0] -> monitoringEnabled
    )
    spot_instance: str | None = (
        None  # Qualys -> sourceInfo -> list -> [0] -> spotInstance
    )
    zone: str | None = None  # Qualys -> sourceInfo -> list -> [0] -> zone
    instance_state: str | None = (
        None  # Qualys -> sourceInfo -> list -> [0] -> instanceState
    )
    private_dns_name: str | None = (
        None  # Qualys -> sourceInfo -> list -> [0] -> privateDnsName
    )
    vpc_id: str | None = None  # Qualys -> sourceInfo -> list -> [0] -> vpcId
    type: str | None = None  # Qualys -> sourceInfo -> list -> [0] -> type
    availability_zone: str | None = (
        None  # Qualys -> sourceInfo -> list -> [0] -> availabilityZone
    )
    first_discovered: datetime | None = (
        None  # Qualys -> sourceInfo -> list -> [0] -> firstDiscovered
    )
    last_updated: datetime | None = (
        None  # Qualys -> sourceInfo -> list -> [0] -> firstDiscovered
    )
    region: str | None = None  # Qualys -> sourceInfo -> list -> [0] -> region
    group_id: str | None = None  # Qualys -> sourceInfo -> list -> [0] -> groupId


class DevicePolicy(BaseModel):
    # Crowdstrike -> device_policies -> Dict
    policy_type: str | None = None
    policy_id: str | None = None
    applied: bool | None = None
    settings_hash: str | None = None
    assigned_date: datetime | None = None
    applied_date: datetime | None = None
    rule_groups: list | None = []
    uninstall_protection: str | None = None


class Host(BaseModel):
    service_ids: List[ServiceID]

    local_ip: str  # Qualys -> address # Crowdstrike -> local_ip
    external_ip: str  # Crowdstrike -> external_ip
    default_gateway_ip: str  # Crowdstrike -> default_gateway_ip
    hostname: str  # Qualys -> name # Crowdstrike -> hostname
    mac_address: str  # Crowdstrike -> mac_address (- to : formatting)
    public_dns_name: str | None = (
        None  # Qualys -> sourceInfo -> list -> [0] -> publicDnsName
    )
    zone_group: str | None = None  # Crowdstrike -> zone_group

    product_type_desc: str | None = None  # Crowdstrike -> product_type_desc
    provision_status: str | None = None  # Crowdstrike -> provision_status
    serial_number: str | None = None  # Crowdstrike -> serial_number
    status: str | None = None  # Crowdstrike -> status
    system_manufacturer: str | None = None  # Crowdstrike -> system_manufacturer
    system_product_name: str | None = None  # Crowdstrike -> system_product_name

    first_seen: datetime | None = None  # Crowdstrike -> first_seen
    last_seen: datetime | None = None  # Crowdstrike -> last_seen
    modified_at: datetime | None = None  # Crowdstrike -> modified_timestamp -> $date
    meta: Dict | None = None

    os: str | None = None  # Crowdstrike -> os_version # Qualys -> os
    bios_description: str | None = None  # Qualys -> biosDescription
    cloud_provider: str | None = None  # Qualys -> cloudProvider
    service_provider: str | None = None  # Crowdstrike -> service_provider
    service_provider_account_id: str | None = (
        None  # Crowdstrike -> service_provider_account_id
    )
    groups: List[str] | None = []  # Crowdstrike -> groups
    group_hash: str | None = None  # Crowdstrike -> group_hash

    network_interfaces: List[NetworkInterface]
    qualys_source_info: QualysSourceInfo | None = None

    open_ports: List[OpenPort]
    processors: List[Processor]
    software: List[Software]
