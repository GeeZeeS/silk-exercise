import logging
import requests
from typing import Dict, List, Any
from urllib.parse import urljoin

from requests import HTTPError

logger = logging.getLogger(__name__)


class SilkSecurityApiClient:
    """Client for fetching security data from APIs"""

    def __init__(
        self,
        base_url: str = "https://api.recruiting.app.silk.security",
        token: str = None,
    ):
        """
        Initialize the API client

        Args:
            base_url: Base URL for the API
            token: API token for authentication
        """
        self.base_url = base_url
        self.token = token
        self.headers = {"accept": "application/json", "token": token}

    def _make_request(
        self, endpoint: str, method: str = "GET", params: Dict = None, data: Any = None
    ) -> Dict:
        """
        Make a request to the API

        Args:
            endpoint: API endpoint
            method: HTTP method (GET, POST, etc.)
            params: Query parameters
            data: Request body data

        Returns:
            Response data
        """
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

        logger.info(f"Fetching CrowdStrike hosts (skip={skip}, limit={limit})")
        try:
            data = self._make_request(endpoint, method="POST", params=params, data={})
        except HTTPError as e:
            logger.error(f"API request error: {str(e)}")
            return None
        return data

    def fetch_all_hosts(self, max_records: int = 100) -> Dict[str, List[Dict]]:
        """
        Fetch both CrowdStrike and Qualys host data

        Args:
            max_records: Maximum number of records to fetch from each API

        Returns:
            Dictionary with CrowdStrike and Qualys host data
        """

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
