import logging
import requests
from typing import Dict, List, Any
from urllib.parse import urljoin

from requests import HTTPError

logger = logging.getLogger(__name__)


class SilkApiClient:
    """Client for fetching security data from APIs"""

    def __init__(
        self,
        base_url: str,
        token: str,
    ):
        self.base_url = base_url
        self.headers = {"accept": "application/json", "token": token}

    def _make_request(
        self, endpoint: str, method: str = "GET", params: Dict = None, data: Any = None
    ) -> Dict:
        url = urljoin(self.base_url, endpoint)
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, params=params)
            elif method.upper() == "POST":
                response = requests.post(
                    url, headers=self.headers, params=params, json=data
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request error: {str(e)}")
            raise

    def fetch_hosts(self, host_type: str, skip: int = 0, limit: int = 1) -> Dict | None:
        endpoint = f"/api/{host_type}/hosts/get"
        params = {"skip": skip, "limit": limit}

        logger.info(f"Fetching {host_type} hosts (skip={skip}, limit={limit})")
        try:
            data = self._make_request(endpoint, method="POST", params=params, data={})
        except HTTPError as e:
            logger.error(f"API request error: {str(e)}")
            return None
        return data

    def fetch_all_hosts(self, max_records: int = 100) -> Dict[str, List[Dict]]:
        crowdstrike_hosts = []
        qualys_hosts = []

        for skip in range(0, max_records):
            batch = self.fetch_hosts("crowdstrike", skip=skip, limit=1)
            if not batch:
                break

            crowdstrike_hosts.extend(batch)

        for skip in range(0, max_records):
            batch = self.fetch_hosts("qualys", skip=skip, limit=1)
            if not batch:
                break
            qualys_hosts.extend(batch)

        return {"crowdstrike": crowdstrike_hosts, "qualys": qualys_hosts}
