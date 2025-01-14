import json
from stix_shifter_utils.stix_transmission.utils.RestApiClientAsync import (
    RestApiClientAsync,
)
from stix_shifter_utils.utils import logger


class APIClient:
    # API METHODS

    # These methods are used to call Ariel's API methods through http requests.
    # Each method makes use of the http methods below to perform the requests.

    # This class will encode any data or query parameters which will then be
    # sent to the call_api() method of the RestApiClient

    def __init__(self, connection, configuration):
        # This version of the ariel APIClient is designed to function with
        # version 6.0 of the ariel API.
        self.logger = logger.set_logger(__name__)
        self.endpoint_start = "api/ariel/"
        headers = dict()
        host_port = connection.get("host") + ":" + str(connection.get("port", ""))
        headers["version"] = "8.0"
        headers["accept"] = "application/json"
        auth = configuration.get("auth")
        if auth != None and auth.get("sec", None) != None:
            headers["sec"] = auth.get("sec")
        url_modifier_function = None
        proxy = connection.get("proxy")
        if proxy is not None:
            proxy_url = proxy.get("url")
            proxy_auth = proxy.get("auth")
            if proxy_url is not None and proxy_auth is not None:
                headers["proxy"] = proxy_url
                headers["proxy-authorization"] = "Basic " + proxy_auth
            if proxy.get("x_forward_proxy", None) is not None:
                headers["x-forward-url"] = (
                    "https://" + host_port + "/"
                )  # + endpoint, is set by 'add_endpoint_to_url_header'
                host_port = proxy.get("x_forward_proxy")
                if proxy.get("x_forward_proxy_auth", None) is not None:
                    headers["x-forward-auth"] = proxy.get("x_forward_proxy_auth")
                headers["user-agent"] = "UDS"
                url_modifier_function = self.add_endpoint_to_url_header

        self.timeout = connection["options"].get("timeout")
        if self.timeout < 300:
            self.timeout = 300
        self.logger.info("timeout value: {}".format(self.timeout))

        self.client = RestApiClientAsync(
            host_port,
            None,
            headers,
            url_modifier_function,
            cert_verify=connection.get("selfSignedCert"),
        )

    def add_endpoint_to_url_header(self, url, endpoint, headers):
        # this function is called from 'call_api' with proxy forwarding,
        # it concatenates the endpoint to the header containing the url.
        headers["x-forward-url"] += endpoint
        # url is returned since it points to the proxy for initial call
        return url

    async def ping_box(self):
        # Sends a GET request
        # to https://<server_ip>/api/help/resources
        endpoint = "api/help/resources"  # no 'ariel' in the path
        return await self.client.call_api(endpoint, "GET", timeout=self.timeout)

    async def get_databases(self):
        # Sends a GET request
        # to  https://<server_ip>/api/ariel/databases
        endpoint = self.endpoint_start + "databases"
        return await self.client.call_api(endpoint, "GET", timeout=self.timeout)

    async def get_database(self, database_name):
        # Sends a GET request
        # to https://<server_ip>/api/ariel/databases/<database_name>
        endpoint = self.endpoint_start + "databases" + "/" + database_name
        return await self.client.call_api(endpoint, "GET", timeout=self.timeout)

    async def get_searches(self):
        # Sends a GET request
        # to https://<server_ip>/api/ariel/searches
        endpoint = self.endpoint_start + "searches"

        return await self.client.call_api(endpoint, "GET", timeout=self.timeout)

    async def create_search(self, query_expression):
        # Sends a POST request
        # to https://<server_ip>/api/ariel/searches
        endpoint = self.endpoint_start + "searches"
        data = {"query_expression": query_expression}

        return await self.client.call_api(
            endpoint, "POST", data=data, timeout=self.timeout
        )

    async def get_search(self, search_id):
        # Sends a GET request to
        # https://<server_ip>/api/ariel/searches/<search_id>
        endpoint = self.endpoint_start + "searches/" + search_id

        return await self.client.call_api(endpoint, "GET", timeout=self.timeout)

    async def get_search_results(
        self, search_id, response_type, range_start=None, range_end=None
    ):
        # Sends a GET request to
        # https://<server_ip>/api/ariel/searches/<search_id>
        # response object body should contain information pertaining to search.
        headers = dict()
        headers["Accept"] = response_type
        if (range_start is not None) and (range_end is not None):
            headers["Range"] = "items=" + str(range_start) + "-" + str(range_end)
        endpoint = self.endpoint_start + "searches/" + search_id + "/results"

        return await self.client.call_api(
            endpoint, "GET", headers, timeout=self.timeout
        )

    async def update_search(self, search_id, save_results=None, status=None):
        # Sends a POST request to
        # https://<server_ip>/api/ariel/searches/<search_id>
        # posts search result to site
        endpoint = self.endpoint_start + "searches/" + search_id
        data = {}
        if save_results:
            data["save_results"] = save_results
        if status:
            data["status"] = status

        return await self.client.call_api(
            endpoint, "POST", data=data, timeout=self.timeout
        )

    async def get_table_columns(self, database_name: str):
        """
        Retrieve the columns defined for a specific Ariel database.
        Endpoint: GET /ariel/databases/{database_name}

        Args:
            database_name (str): The name of the Ariel database.

        Returns:
            list: A list of column definitions (name, indexable, argument_type), or an empty list on failure.
        """
        endpoint = f"{self.endpoint_start}databases/{database_name}"
        try:
            # Make the API call
            response = await self.client.call_api(endpoint, "GET", timeout=self.timeout)

            # Handle response
            if response.code == 200:
                try:
                    json_body = (
                        response.read()
                    )  # Replace with `await response.read()` if asynchronous
                    data = json.loads(json_body)
                    return data.get("columns", [])
                except json.JSONDecodeError:
                    self.logger.error(
                        f"Failed to parse JSON response for database: {database_name}"
                    )
            elif response.code == 404:
                self.logger.error(
                    f"Database not found: {database_name} (status code 404)"
                )
            elif response.code == 422:
                self.logger.error(
                    f"Invalid request parameter for database: {database_name} (status code 422)"
                )
            elif response.code == 500:
                self.logger.error(
                    f"Server error while retrieving columns for database: {database_name} (status code 500)"
                )
            else:
                self.logger.error(
                    f"Unexpected response code {response.code} while retrieving columns for database: {database_name}"
                )
        except Exception as e:
            self.logger.error(
                f"An exception occurred while retrieving columns for database {database_name}: {e}"
            )

        return []

    async def delete_search(self, search_id):
        # Sends a DELETE request to
        # https://<server_ip>/api/ariel/searches/<search_id>
        # deletes search created earlier.
        endpoint = self.endpoint_start + "searches" + "/" + search_id

        return await self.client.call_api(endpoint, "DELETE", timeout=self.timeout)
