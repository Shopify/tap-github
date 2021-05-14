"""REST client handling, including GitHubStream base class."""

import requests
from typing import Any, Dict, Optional, Iterable, cast

from singer_sdk.streams import RESTStream


class GitHubStream(RESTStream):
    """GitHub stream class."""

    MAX_PER_PAGE = 1000
    MAX_RESULTS_LIMIT: Optional[int] = None

    url_base = "https://api.github.com"
    primary_keys = ["id"]
    replication_key: Optional[str] = None

    @property
    def http_headers(self) -> dict:
        """Return the http headers needed."""
        headers = {"Accept": "application/vnd.github.v3+json"}
        if "user_agent" in self.config:
            headers["User-Agent"] = self.config.get("user_agent")
        if "auth_token" in self.config:
            headers["Authorization"] = f"token {self.config['auth_token']}"
        return headers

    def get_next_page_token(
        self, response: requests.Response, previous_token: Optional[Any] = None
    ) -> Optional[Any]:
        """Return a token for identifying next page or None if no more pages."""
        if (
            previous_token
            and self.MAX_RESULTS_LIMIT
            and (
                cast(int, previous_token) * self.MAX_PER_PAGE >= self.MAX_RESULTS_LIMIT
            )
        ):
            return None

        resp_json = response.json()
        if isinstance(resp_json, list):
            results = resp_json
        else:
            results = resp_json.get("items")

        if results:
            # Paginate as long as the response has items
            return (previous_token or 1) + 1

        return None

    def get_url_params(
        self, partition: Optional[dict], next_page_token: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Return a dictionary of values to be used in URL parameterization."""
        params: dict = {"per_page": self.MAX_PER_PAGE}
        if next_page_token:
            params["page"] = next_page_token
        # if self.replication_key:
        #     params["sort"] = "asc"
        #     params["order_by"] = self.replication_key
        return params

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse the response and return an iterator of result rows."""
        resp_json = response.json()
        if isinstance(resp_json, list):
            results = resp_json
        else:
            results = resp_json.get("items")
        for row in results:
            yield row
