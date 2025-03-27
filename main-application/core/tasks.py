import logging
import motor.motor_asyncio
import asyncio
from typing import Dict, List, Any
from celery import Task
from datetime import datetime

from .celery_app import celery_app
from .config import settings
from .api_client import SilkSecurityApiClient
from core.models import IntegratedHost

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


def process_data(crowdstrike_data: List[Dict], qualys_data: List[Dict]) -> List[IntegratedHost]:
    """
    Process and normalize data from different sources into a unified format
    
    Args:
        crowdstrike_data: List of CrowdStrike device data
        qualys_data: List of Qualys host asset data
        
    Returns:
        List of integrated host objects
    """
    integrated_hosts = []
    
    # Define fields that are already explicitly mapped for CrowdStrike
    crowdstrike_mapped_fields = {
        "device_id", "_id", "hostname", "local_ip", "external_ip", "mac_address", 
        "platform_name", "os_version", "first_seen", "last_seen", "status", 
        "bios_manufacturer", "bios_version", "system_manufacturer", "system_product_name", 
        "cpu_signature", "serial_number", "chassis_type", "chassis_type_desc", 
        "product_type_desc", "service_provider", "service_provider_account_id", 
        "instance_id", "zone_group", "connection_ip", "connection_mac_address", 
        "default_gateway_ip", "agent_version", "agent_load_flags", "agent_local_time", 
        "cid", "config_id_base", "config_id_build", "config_id_platform", 
        "reduced_functionality_mode", "provision_status", "major_version", 
        "minor_version", "kernel_version", "policies", "device_policies", "tags"
    }
    
    # Define fields that are already explicitly mapped for Qualys
    qualys_mapped_fields = {
        "_id", "id", "name", "dnsHostName", "fqdn", "address", "modified", "created", 
        "manufacturer", "model", "biosDescription", "totalMemory", "timezone", 
        "os", "cloudProvider", "agentInfo", "networkInterface", "account", 
        "openPort", "processor", "software", "volume", "vuln", "sourceInfo", 
        "trackingMethod", "type", "lastComplianceScan", "lastVulnScan", "isDockerHost", 
        "lastSystemBoot", "lastLoggedOnUser", "networkGuid", "qwebHostId", "tags"
    }
    
    # Process CrowdStrike data
    for host in crowdstrike_data:
        # Extract hardware information
        hardware_info = {
            "bios_manufacturer": host.get("bios_manufacturer"),
            "bios_version": host.get("bios_version"),
            "system_manufacturer": host.get("system_manufacturer"),
            "system_product_name": host.get("system_product_name"),
            "cpu_signature": host.get("cpu_signature"),
            "serial_number": host.get("serial_number"),
            "chassis_type": host.get("chassis_type"),
            "chassis_type_desc": host.get("chassis_type_desc"),
            "product_type_desc": host.get("product_type_desc")
        }
        
        # Extract cloud provider information
        cloud_info = None
        if host.get("service_provider"):
            cloud_info = {
                "provider": host.get("service_provider"),
                "account_id": host.get("service_provider_account_id"),
                "instance_id": host.get("instance_id"),
                "zone": host.get("zone_group"),
            }
        
        # Extract network connection information
        connection_info = {
            "local_ip": host.get("local_ip"),
            "external_ip": host.get("external_ip"),
            "connection_ip": host.get("connection_ip"),
            "connection_mac_address": host.get("connection_mac_address"),
            "default_gateway_ip": host.get("default_gateway_ip"),
            "mac_address": host.get("mac_address")
        }
        
        # Extract agent/sensor information
        agent_info = {
            "agent_version": host.get("agent_version"),
            "agent_load_flags": host.get("agent_load_flags"),
            "agent_local_time": host.get("agent_local_time"),
            "cid": host.get("cid"),
            "config_id_base": host.get("config_id_base"),
            "config_id_build": host.get("config_id_build"),
            "config_id_platform": host.get("config_id_platform"),
            "reduced_functionality_mode": host.get("reduced_functionality_mode"),
            "provision_status": host.get("provision_status"),
            "major_version": host.get("major_version"),
            "minor_version": host.get("minor_version"),
            "kernel_version": host.get("kernel_version")
        }
        
        # Extract policies
        policies = []
        if host.get("policies"):
            policies = host.get("policies")
        elif host.get("device_policies"):
            policies = [policy for policy in host.get("device_policies", {}).values()]
        
        # Parse dates if they exist
        first_seen = None
        if host.get("first_seen"):
            try:
                first_seen = datetime.fromisoformat(host["first_seen"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass
                
        last_seen = None
        if host.get("last_seen"):
            try:
                last_seen = datetime.fromisoformat(host["last_seen"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass
                
        # Collect any unmapped fields from the host
        additional_fields = {}
        for key, value in host.items():
            if key not in crowdstrike_mapped_fields:
                additional_fields[key] = value
        
        # Create integrated host object
        integrated_host = IntegratedHost(
            source="crowdstrike",
            source_id=host.get("device_id") or host.get("_id"),
            hostname=host.get("hostname"),
            ip_address=host.get("local_ip"),
            external_ip=host.get("external_ip"),
            mac_address=host.get("mac_address"),
            os_name=host.get("platform_name"),
            os_version=host.get("os_version"),
            first_seen=first_seen,
            last_seen=last_seen,
            status=host.get("status"),
            hardware_info=hardware_info,
            cloud_info=cloud_info,
            connection_info=connection_info,
            agent_info=agent_info,
            policies=policies,
            tags=host.get("tags", []),
            additional_fields=additional_fields
        )
        
        integrated_hosts.append(integrated_host)
    
    # Process Qualys data
    for host in qualys_data:
        # Extract accounts
        accounts = []
        if host.get("account") and host.get("account").get("list"):
            for account_entry in host["account"]["list"]:
                if account_entry.get("HostAssetAccount") and account_entry["HostAssetAccount"].get("username"):
                    accounts.append(account_entry["HostAssetAccount"]["username"])
        
        # Extract network interfaces
        network_interfaces = []
        primary_interface = None
        if host.get("networkInterface") and host.get("networkInterface").get("list"):
            for interface in host["networkInterface"]["list"]:
                if "HostAssetInterface" in interface:
                    interface_data = interface["HostAssetInterface"]
                    interface_info = {
                        "name": interface_data.get("interfaceName"),
                        "mac_address": interface_data.get("macAddress"),
                        "address": interface_data.get("address"),
                        "hostname": interface_data.get("hostname"),
                        "gateway": interface_data.get("gatewayAddress")
                    }
                    network_interfaces.append(interface_info)
                    
                    # Use first interface with MAC address as primary
                    if not primary_interface and interface_data.get("macAddress"):
                        primary_interface = interface_info
        
        # Extract open ports
        open_ports = []
        if host.get("openPort") and host.get("openPort").get("list"):
            for port_entry in host["openPort"]["list"]:
                if "HostAssetOpenPort" in port_entry:
                    port_data = port_entry["HostAssetOpenPort"]
                    open_ports.append({
                        "port": port_data.get("port"),
                        "protocol": port_data.get("protocol"),
                        "service": port_data.get("serviceName")
                    })
        
        # Extract hardware information
        hardware_info = {
            "manufacturer": host.get("manufacturer"),
            "model": host.get("model"),
            "bios_description": host.get("biosDescription"),
            "total_memory": host.get("totalMemory"),
            "timezone": host.get("timezone"),
        }
        
        # Extract processor information
        if host.get("processor") and host.get("processor").get("list"):
            processors = []
            for processor in host["processor"]["list"]:
                if "HostAssetProcessor" in processor:
                    processors.append({
                        "name": processor["HostAssetProcessor"].get("name"),
                        "speed": processor["HostAssetProcessor"].get("speed")
                    })
            if processors:
                hardware_info["processors"] = processors
        
        # Extract software
        software_list = []
        if host.get("software") and host.get("software").get("list"):
            for sw in host["software"]["list"]:
                if "HostAssetSoftware" in sw:
                    software_list.append({
                        "name": sw["HostAssetSoftware"].get("name"),
                        "version": sw["HostAssetSoftware"].get("version")
                    })
        
        # Extract volumes
        volumes = []
        if host.get("volume") and host.get("volume").get("list"):
            for volume in host["volume"]["list"]:
                if "HostAssetVolume" in volume:
                    volumes.append({
                        "name": volume["HostAssetVolume"].get("name"),
                        "size": volume["HostAssetVolume"].get("size"),
                        "free": volume["HostAssetVolume"].get("free")
                    })
        
        # Extract vulnerabilities
        vulnerabilities = []
        if host.get("vuln") and host.get("vuln").get("list"):
            for vuln in host["vuln"]["list"]:
                if "HostAssetVuln" in vuln:
                    vulnerabilities.append({
                        "id": vuln["HostAssetVuln"].get("hostInstanceVulnId"),
                        "qid": vuln["HostAssetVuln"].get("qid"),
                        "first_found": vuln["HostAssetVuln"].get("firstFound"),
                        "last_found": vuln["HostAssetVuln"].get("lastFound")
                    })
        
        # Extract cloud information
        cloud_info = None
        if host.get("cloudProvider"):
            cloud_info = {"provider": host.get("cloudProvider")}
            
            # Add additional cloud data if available from sourceInfo
            if host.get("sourceInfo") and host.get("sourceInfo").get("list"):
                for source_entry in host["sourceInfo"]["list"]:
                    if "Ec2AssetSourceSimple" in source_entry:
                        ec2_data = source_entry["Ec2AssetSourceSimple"]
                        cloud_info.update({
                            "account_id": ec2_data.get("accountId"),
                            "instance_id": ec2_data.get("instanceId"),
                            "instance_type": ec2_data.get("instanceType"),
                            "region": ec2_data.get("region"),
                            "vpc_id": ec2_data.get("vpcId"),
                            "subnet_id": ec2_data.get("subnetId"),
                            "availability_zone": ec2_data.get("availabilityZone"),
                            "image_id": ec2_data.get("imageId")
                        })
        
        # Extract agent information from agentInfo
        agent_info = {}
        if host.get("agentInfo"):
            agent_data = host.get("agentInfo")
            agent_info = {
                "agent_id": agent_data.get("agentId"),
                "status": agent_data.get("status"),
                "version": agent_data.get("agentVersion"),
                "platform": agent_data.get("platform"),
                "activated_module": agent_data.get("activatedModule"),
            }
            
            # Parse last check-in date if available
            if agent_data.get("lastCheckedIn") and agent_data["lastCheckedIn"].get("$date"):
                try:
                    last_checked_in = datetime.fromisoformat(agent_data["lastCheckedIn"]["$date"].replace("Z", "+00:00"))
                    agent_info["last_checked_in"] = last_checked_in
                except (ValueError, TypeError):
                    pass
        
        # Determine primary IP and MAC addresses
        primary_ip = host.get("address")
        primary_mac = None
        if primary_interface:
            primary_mac = primary_interface.get("mac_address")
        
        # Determine external IP
        external_ip = None
        for interface in network_interfaces:
            # If the interface has an address that doesn't start with private address ranges
            addr = interface.get("address")
            if addr and not any([
                addr.startswith("10."),
                addr.startswith("172.16."),
                addr.startswith("192.168."),
                addr.startswith("fe80:"),
                addr.startswith("169.254."),
                addr.startswith("127.")
            ]) and addr != primary_ip:
                external_ip = addr
                break
        
        # Parse created/modified dates
        created_date = None
        if host.get("created"):
            try:
                created_date = datetime.fromisoformat(host["created"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass
                
        modified_date = None
        if host.get("modified"):
            try:
                modified_date = datetime.fromisoformat(host["modified"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass
        
        # Extract tags
        tags = []
        if host.get("tags") and host.get("tags").get("list"):
            for tag_entry in host["tags"]["list"]:
                if "TagSimple" in tag_entry and tag_entry["TagSimple"].get("name"):
                    tags.append(tag_entry["TagSimple"]["name"])
        
        # Collect any unmapped fields
        additional_fields = {}
        for key, value in host.items():
            if key not in qualys_mapped_fields:
                additional_fields[key] = value
        
        # Create integrated host object
        integrated_host = IntegratedHost(
            source="qualys",
            source_id=str(host.get("_id") or host.get("id")),
            hostname=host.get("name") or host.get("dnsHostName") or host.get("fqdn"),
            ip_address=primary_ip,
            external_ip=external_ip,
            mac_address=primary_mac,
            os_name=host.get("os"),
            os_version=host.get("os"),
            first_seen=created_date,
            last_seen=modified_date,
            status=agent_info.get("status"),
            hardware_info=hardware_info,
            cloud_info=cloud_info,
            software=software_list,
            vulnerabilities=vulnerabilities,
            agent_info=agent_info,
            network_interfaces=network_interfaces,
            open_ports=open_ports,
            volumes=volumes,
            accounts=accounts,
            tags=tags,
            source_details={
                "asset_id": host.get("id"),
                "qweb_host_id": host.get("qwebHostId"),
                "tracking_method": host.get("trackingMethod"),
                "type": host.get("type"),
                "last_compliance_scan": host.get("lastComplianceScan"),
                "last_vuln_scan": host.get("lastVulnScan").get("$date") if host.get("lastVulnScan") and host.get("lastVulnScan").get("$date") else None,
                "is_docker_host": host.get("isDockerHost"),
                "last_system_boot": host.get("lastSystemBoot"),
                "last_logged_on_user": host.get("lastLoggedOnUser"),
                "network_guid": host.get("networkGuid")
            },
            additional_fields=additional_fields
        )
        
        integrated_hosts.append(integrated_host)
    
    return integrated_hosts
