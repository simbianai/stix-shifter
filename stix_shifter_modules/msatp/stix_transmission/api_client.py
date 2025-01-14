"""Apiclient for MSATP"""
import datetime

from azure.identity import ClientSecretCredential
from azure.monitor.query import LogsQueryClient

DEFAULT_LIMIT = 10000
DEFAULT_OFFSET = 0


class APIClient:
    """API Client to handle all calls."""

    def __init__(self, connection, configuration):
        """Initialization.
        :param connection: dict, connection dict
        :param configuration: dict,config dict"""

        self.auth = configuration.get('auth')
        self.workspace_id = self.auth["workspaceId"]
        self.client_id = self.auth["clientId"]
        self.client_secret = self.auth["clientSecret"]
        self.tenant_id = self.auth["tenant"]

    async def ping_box(self):
        """Ping the endpoint."""
        credential = ClientSecretCredential(self.tenant_id, self.client_id, self.client_secret)
        client = LogsQueryClient(credential)
        return client.query_workspace(self.workspace_id, "1", timespan=datetime.timedelta(days=100))

    async def run_search(self, query_expression, offset=DEFAULT_OFFSET, length=DEFAULT_LIMIT):
        """get the response from MSatp endpoints
        :param query_expression: str, search_id
        :param offset: int,offset value
        :param length: int,length value
        :return: response, json object"""
        serialize = '| serialize rn = row_number() | where rn >= {offset} | limit {length}'
        query_expression = query_expression + serialize.format(offset=offset, length=length)
        
        credential = ClientSecretCredential(self.tenant_id, self.client_id, self.client_secret)
        client = LogsQueryClient(credential)
        response = client.query_workspace(self.workspace_id, query_expression, timespan=datetime.timedelta(days=100))
        return response
        