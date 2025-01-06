import json
from stix_shifter_utils.modules.base.stix_transmission.base_json_sync_connector import BaseJsonSyncConnector
from stix_shifter_utils.stix_transmission.utils.RestApiClientAsync import RestApiClientAsync

from .api_client import APIClient
from stix_shifter_utils.utils.error_response import ErrorResponder
from stix_shifter_utils.utils import logger
from stix_shifter_modules.securonix.stix_transmission.api_client import APIResponseException
from requests.exceptions import ConnectionError
from datetime import datetime, timezone


class Connector(BaseJsonSyncConnector):
    init_error = None
    logger = logger.set_logger(__name__)
    PROVIDER = 'Securonix'

    def __init__(self, connection, configuration):
        self.connector = __name__.split('.')[1]
        self.api_client = APIClient()
        self.result_limit = connection['options'].get('result_limit', 1000)
        self.status = dict()

        headers = dict()
        self.client = RestApiClientAsync(connection.get('host'), None, headers)

        self.auth_headers = dict()
        self.auth_headers['Content-Type'] = 'application/json'
        self.auth_headers['user-agent'] = 'oca_stixshifter_1.0'
        auth = configuration.get('auth')
        self.username = auth["username"]
        self.password = auth["password"]
        self.auth_headers['username'] = self.username
        self.auth_headers['password'] = self.password
        self.auth_headers['validity'] = '365'
        self.base_url = connection.get('host')
        self.timeout = connection['options'].get('timeout')
        self.headers = dict()
        self.headers['Content-Type'] = 'application/json'
        self.headers['Accept'] = '*/*'
        self.headers['user-agent'] = 'oca_stixshifter_1.0'

    async def ping_connection(self):
        return_obj = {}
        try:
            self.logger.debug(f"Attempting to ping the service for an auth token")
            response = await self.api_client.ping_box(self.client, self.base_url, self.auth_headers, self.headers,
                                                      self.timeout)
            response_code = response.code
            response_msg = response.content.decode('utf-8')
            if response_code == 200:
                self.logger.debug(f"Successfully pinged the device for an auth token")
                return_obj['success'] = True
            else:
                response_type = response.headers.get('Content-Type')
                raise APIResponseException(response_code, response_msg, response_type, response)
        except Exception as e:
            return self._handle_Exception(e)

        return return_obj

    async def create_results_connection(self, query, offset, length, metadata=None):
        # Initialize the starting offset and initial variables to empty.
        return_obj = dict()
        length = int(length)
        offset = int(offset)

        if metadata is None:
            metadata = dict()
            current_offset = offset
            metadata["result_count"] = 0
            queryId = None
        else:
            current_offset = metadata["offset"]
            queryId = metadata.get('queryId')

        try:
            # Query the alert endpoint to get a list of ID's. The ID's are in a list of list format.
            securonix_data = await self._get_securonix_data(length, query, current_offset, metadata, queryId)
        except Exception as e:
            return self._handle_Exception(e)

        # If the total count is greater than the result limit,
        if metadata and metadata.get("offset", 0) > self.result_limit:
            securonix_data = securonix_data[0:(self.result_limit - offset) - 1]

        if metadata and (metadata["result_count"] >= self.result_limit or len(securonix_data) < length):
            metadata = None

        return_obj["success"] = True
        return_obj["metadata"] = metadata
        return_obj["data"] = securonix_data

        self.logger.debug(f"Data being returned : {return_obj}")
        print(json.dumps(return_obj, indent=4))
        return return_obj

    async def _get_securonix_data(self, length, query, current_offset, metadata, queryId):
        securonix_data = []
        self.logger.debug(f"Collecting results using the following query/filter : {query}")

        while (metadata and len(securonix_data) < length):
            # Get the next batch of results.
            self.logger.debug(
                f"Using the following settings to get a batch of results: offset : {current_offset}, length : {length}")
            get_data_response = await self.api_client.get_securonix_data(query, self.client, self.base_url,
                                                                         self.auth_headers, self.headers, self.timeout,
                                                                         queryId)
            if get_data_response.code == 200:
                self.logger.debug(f"Successfully got a list of results")
                get_data_response_data = get_data_response.content.decode('utf-8')
                self.logger.debug(f"Raw Response from API : {get_data_response_data}")
                try:
                    get_data_response_json = json.loads(get_data_response_data)
                    if "results" in get_data_response_json:
                        securonix_data.extend(get_data_response_json.get('results'))
                        if metadata:
                            metadata["result_count"] = metadata["result_count"] + len(
                                get_data_response_json.get('results'))
                        queryId = get_data_response_json.get('queryId')

                        if (queryId != None):
                            if metadata:
                                metadata['queryId'] = queryId
                        else:
                            metadata = None

                    else:
                        self.logger.warning(
                            f"Response did not contain 'results' key. Assuming empty result. Full response: {get_data_response_json}")

                        metadata = None
                        break
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to decode JSON: {e}. Full response: {get_data_response_data}")
                    raise e
                if (len(securonix_data) == 0):
                    metadata = None
                    break
                if (len(securonix_data) >= length):
                    break;

            else:
                raise APIResponseException(get_data_response.code, get_data_response.content,
                                           get_data_response.headers.get('Content-Type'), get_data_response)
            if metadata:
                current_offset = current_offset + length

        # We now know the next meta_data offset
        if metadata:
            metadata["offset"] = current_offset
        return securonix_data

    def _handle_Exception(self, exception):
        response_dict = {}
        return_obj = {}
        try:
            raise exception
        except APIResponseException as ex:
            return self._handle_api_response(ex)
        except Exception as ex:
            ErrorResponder.fill_error(return_obj, response_dict, error=ex, connector=self.connector)
            return return_obj

    def _handle_api_response(self, rest_api_exception):
        response_dict = {}
        return_obj = {}
        connection_error = None

        if (rest_api_exception.content_header_type == 'application/json'):
            response = json.loads(rest_api_exception.error_message)
            if 'error' in response:
                response_dict['message'] = response['error']
            elif 'message' in response:
                response_dict['message'] = response['message']
            else:
                response_dict['message'] = str(rest_api_exception.error_message)
            if (rest_api_exception.error_code == 400):
                response_dict['type'] = 'ValidationError'
            elif (rest_api_exception.error_code == 401):
                response_dict['type'] = 'AuthenticationError'
            elif (rest_api_exception.error_code == 403):
                response_dict['type'] = 'TokenError'
        elif (rest_api_exception.content_header_type == 'text/html'):
            response = rest_api_exception.error_message
            connection_error = ConnectionError(f'Error connecting the datasource: {rest_api_exception.error_message}')
        else:
            raise Exception(rest_api_exception.error_message)

        ErrorResponder.fill_error(return_obj, response_dict, ['message'], error=connection_error,
                                  connector=self.connector)
        return return_obj
